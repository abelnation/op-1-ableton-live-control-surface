from functools import partial

from . import ui
from .consts import *

DEFAULT_DEVICE_PARAM_MAPPINGS = {
    # Channel EQ
    'ChannelEq': ['Low Gain', 'Mid Gain', 'High Gain', 'Gain', 'Low Gain', 'Mid Freq', 'High Gain', 'Gain'],
    # Chorus
    'Chorus': ['Delay 1 HiPass', 'Delay 1 Time', 'Delay 2 Mode', 'Delay 2 Time', 'LFO Amount', 'LFO Rate', 'Feedback', 'Dry/Wet'],
    # Compressor
    'Compressor2': ['Threshold', 'Output Gain', 'Knee', 'Dry/Wet', 'Ratio', 'Attack', 'Release', 'Dry/Wet'],
    # EQ Three
    'FilterEQ3': ['GainLo', 'GainMid', 'GainHi', 'Slope', 'FreqLo', 'GainMid', 'FreqHi', 'Slope'],
    # Reverb
    # TODO: decide default param mappings
    'Reverb': [None, None, None, 'Dry/Wet', None, None, None, None],
}


class OP1Mode(object):
    def __init__(self, surface, view):
        self._surface = surface
        self._view = view

    @property
    def surface(self):
        return self._surface

    @property
    def view(self):
        return self._view

    def song(self):
        return self.surface.song()

    def log_message(self, msg):
        self.surface.log_message(msg)

    def activate(self):
        with self._surface.component_guard():
            self.do_activate()

    def deactivate(self):
        with self._surface.component_guard():
            self.do_deactivate()

    def do_activate(self):
        raise NotImplementedError()

    def do_deactivate(self):
        raise NotImplementedError()


class TracksMode(OP1Mode):
    def __init__(self, surface):
        super(TracksMode, self).__init__(
            surface=surface,
            view=ui.CurrentTrackInfoView(surface),
        )

    def do_activate(self):
        self.log_message('TracksMode.do_activate')
        self.map_mixer_controls_for_current_track()
        self.song().view.add_selected_track_listener(
            self.map_mixer_controls_for_current_track)

    def do_deactivate(self):
        self.log_message('TracksMode.do_deactivate')
        self.unmap_mixer_controls()
        self.song().view.remove_selected_track_listener(
            self.map_mixer_controls_for_current_track)

    def map_mixer_controls_for_current_track(self):
        self.log_message('map_mixer_controls_for_current_track()')

        self.unmap_mixer_controls()

        self.surface._mixer.set_select_buttons(
            prev_button=self.surface._button_up,
            next_button=self.surface._button_down,
        )

        # getting selected strip
        channel_strip = self.surface._mixer.selected_strip()

        # perform track assignments
        channel_strip.set_volume_control(self.surface._encoder_1)
        channel_strip.set_pan_control(self.surface._encoder_2)

        # setting send encoders
        channel_strip.set_send_controls((
            self.surface._encoder_3,
            self.surface._encoder_4,
        ))

        # if track is no master, set mute button
        if (channel_strip._track!=self.song().master_track):
            channel_strip.set_mute_button(self.surface._button_stop)

        # setting solo button
        channel_strip.set_solo_button(self.surface._button_play)

        # if track can be armed, set arm button
        if (channel_strip._track.can_be_armed):
            channel_strip.set_arm_button(self.surface._button_record)

    def clear_return_track_assignment(self, strip):
        # clear return track assingments
        strip.set_volume_control(None)
        strip.set_pan_control(None)
        strip.set_mute_button(None)
        strip.set_solo_button(None)

    def clear_track_assignment(self, strip):
        # clear track assignments
        strip.set_volume_control(None)
        strip.set_pan_control(None)
        strip.set_mute_button(None)
        strip.set_solo_button(None)
        strip.set_arm_button(None)

    def unmap_mixer_controls(self):
        self.surface._mixer.set_select_buttons(
            prev_button=None,
            next_button=None,
        )

        # for all normal tracks, clear assignments
        for i in range(NUM_TRACKS):
            strip = self.surface._mixer.channel_strip(i)
            if (strip!=None):
                self.clear_track_assignment(strip)

        # for all return tracks, clear assignments
        for i in range(NUM_RETURN_TRACKS):
            return_strip = self.surface._mixer.return_strip(i)
            if (return_strip!=None):
                self.clear_return_track_assignment(return_strip)


class EffectsMode(OP1Mode):
    def __init__(self, surface):
        super(EffectsMode, self).__init__(
            surface=surface,
            view=ui.CurrentTrackEffectsView(surface),
        )

        self._device_encoders = [
            self.surface._unshift_encoder_1,
            self.surface._unshift_encoder_2,
            self.surface._unshift_encoder_3,
            self.surface._unshift_encoder_4,
            self.surface._shift_encoder_1,
            self.surface._shift_encoder_2,
            self.surface._shift_encoder_3,
            self.surface._shift_encoder_4,
        ]

        self._param_mappings = {
            i: None for i in range(len(self._device_encoders))
        }

    @property
    def num_encoders(self):
        return len(self._device_encoders)

    def do_activate(self):
        self.log_message('EffectsMode.do_activate')

        for param_num, encoder in enumerate(self._device_encoders):
            encoder.add_value_listener(partial(self.encoder_value_changed, param_num))

        # self.song().view.add_selected_chain_listener(self.selected_device_changed)
        # self.song().add_appointed_device_listener(self.selected_device_changed)
        self.surface.selected_track.view.add_selected_device_listener(self.selected_device_changed)

        self.reset_param_mappings()

    def do_deactivate(self):
        self.log_message('EffectsMode.do_deactivate')

        for param_num, encoder in enumerate(self._device_encoders):
            encoder.remove_value_listener(partial(self.encoder_value_changed, param_num))

        # self.song().remove_appointed_device_listener(self.selected_device_changed)
        self.surface.selected_track.view.remove_selected_device_listener(self.selected_device_changed)

    def encoder_value_changed(self, encoder_num, value):
        param_num = self._param_mappings[encoder_num]
        if param_num is not None:
            param = self.surface.selected_device.parameters[param_num]
            self.log_message('%s: %s' % (param.name, value))
            self.update_displayed_param(param)
        else:
            self.log_message('Encoder %s: %s' % (encoder_num, value))

    def update_displayed_param(self, param):
        self.view.set_displayed_device_param(param)

    def reset_param_mappings(self):
        for i in range(self.num_encoders):
            self._param_mappings[i] = None

        device = self.surface.selected_device
        if device is None:
            self.view.set_displayed_device_param(None)
            return

        self.log_message('Device class: %s' % device.class_name)
        for param in device.parameters:
            self.log_message('- %s' % param.name)

        params = device.parameters
        if device.class_name in DEFAULT_DEVICE_PARAM_MAPPINGS:
            mappings = DEFAULT_DEVICE_PARAM_MAPPINGS[device.class_name]
            for encoder_num, param_name in enumerate(mappings):
                self.log_message('mapping encoder %s to param %s' % (encoder_num, param_name))
                # No param mapped
                if param_name is None:
                    continue

                encoder = self._device_encoders[encoder_num]
                param_num, param = next((i,p) for i,p in enumerate(params) if p.name == param_name)

                self._param_mappings[encoder_num] = param_num
                encoder.connect_to(param)
        else:
            # Map first N encoders to first N params
            for encoder_num in range(min(len(params), self.num_encoders)):
                encoder = self._device_encoders[encoder_num]
                param = params[encoder_num]

                self._param_mappings[encoder_num] = encoder_num
                encoder.connect_to(param)

        first_param_num = self._param_mappings[0]
        self.view.set_displayed_device_param(params[first_param_num] if params else None)

    def selected_device_changed(self):
        self.log_message('Selected device changed')
        self.reset_param_mappings()


