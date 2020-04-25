import time

from .consts import *
from .util import color_to_bytes


COLOR_BLACK_BYTES = [0x00, 0x00, 0x00]
COLOR_WHITE_BYTES = [0x7F, 0x7F, 0x7F]

# Used to indicate an update to the display text on screen
TEXT_START_SEQUENCE = (0xf0, 0x0, 0x20, 0x76, 0x00, 0x03)
# Used to indicate an update to the key diagram color display on screen
TEXT_COLOR_START_SEQUENCE = (0xf0, 0x0, 0x20, 0x76, 0x00, 0x04)
# Signals the end of a display update
TEXT_END_SEQUENCE = (0xf7,)


class OP1View(object):
    def __init__(self, surface):
        self._surface = surface

        self._bottom_text = ''
        self._top_text = ''
        self.display_color_by_slot_num = {
            i: COLOR_BLACK_BYTES for i in range(NUM_DISPLAY_CLIP_SLOTS)
        }

    def log_message(self, msg):
        self.surface.log_message(msg)

    @property
    def surface(self):
        return self._surface

    def song(self):
        return self.surface.song()

    def render(self):
        self.update()

        # Sync key slot colors
        self._sync_text_to_display()
        self._sync_key_colors_to_display()

    def update(self):
        """Override in sub-classes"""
        raise NotImplementedError()

    def set_top_text(self, top_text):
        self._top_text = top_text

    def set_bottom_text(self, bottom_text):
        self._bottom_text = bottom_text

    def set_key_slot_color(self, slot_num, color_bytes):
        """
        Args:
            slot_num (int): key slot to set color on
            color_bytes (List[int]): Use `color_to_bytes` to generate these
        """
        self.display_color_by_slot_num[slot_num] = color_bytes

    def _sync_key_colors_to_display(self):
        colors = []
        for i in range(NUM_DISPLAY_CLIP_SLOTS):
            key_color_bytes = self.display_color_by_slot_num[i]
            colors.extend(key_color_bytes)
        sequence = TEXT_COLOR_START_SEQUENCE + (NUM_DISPLAY_CLIP_SLOTS, ) + tuple(colors) + TEXT_END_SEQUENCE
        self.surface._send_midi(sequence)

    def _sync_text_to_display(self):
        """
        Ascii codes mapped to either letters or icons.

        Use lower-case ascii chars for normal letters.
        Uppercase will be encoded as custom icons.
        """
        msg = self._top_text.strip() + '\r' + self._bottom_text.strip()
        msg = msg.lower()
        text_bytes = [ord(c) for c in msg]
        sequence = TEXT_START_SEQUENCE + (len(msg), ) + tuple(text_bytes) + TEXT_END_SEQUENCE
        self.surface._send_midi(sequence)


class ApplicationView(OP1View):
    def __init__(self, surface):
        super(ApplicationView, self).__init__(surface)

        self.current_track_view = CurrentTrackInfoView(surface)

        self.active_view = self.current_track_view

        self.flash_expire_ts = None
        self.flash_return_view = None

    def flash(self, view, duration):
        # If main view displayed, back it up before switching to flash view
        # subsequent flash views simply overwrite the active flash if one is present.
        if self.flash_return_view is None:
            self.flash_return_view = self.active_view

        self.active_view = view
        self.flash_expire_ts = time.time() + duration

    def update(self):
        # Check for flash view expiring
        if self.flash_return_view is not None and time.time() >= self.flash_expire_ts:
            self.active_view = self.flash_return_view
            self.flash_expire_ts = None
            self.flash_return_view = None

        self.active_view.update()


class CurrentTrackInfoView(OP1View):
    """
    Displays info about current track:
    - Track name
    - Mute/Solo/Arm status
    - Clips w/ colors for the track
    - Selected clip indicated with WHITE slot indicator
    """
    def update(self):
        self.display_track_info()
        self.display_selected_track_clips()

    def display_track_info(self):
        selected_track = self.surface.selected_track
        self.set_top_text('%s. %s' % (
            self.surface.selected_track_num,
            selected_track.name,
        ))

        track_attrs = []
        if selected_track.mute:
            track_attrs.append('Muted')
        if selected_track.solo:
            track_attrs.append('Solo')
        if selected_track.arm:
            track_attrs.append('Armed')

        bottom_text = 'Track'
        if track_attrs:
            bottom_text += ': ' + ','.join(track_attrs)
        self.set_bottom_text(bottom_text)

    def display_selected_track_clips(self):
        selected_track = self.surface.selected_track
        selected_scene_num = self.surface.selected_scene_num
        num_clip_slots = len(selected_track.clip_slots)

        colors = []

        # Alternate indicator every half second
        now_ms = time.time() * 1000
        show_selection_indicator = (now_ms % 1000) > 500

        for i, clip_slot in enumerate(selected_track.clip_slots):
            if i == selected_scene_num and show_selection_indicator:
                self.set_key_slot_color(i, COLOR_WHITE_BYTES)

            elif clip_slot is not None and clip_slot.has_clip:
                clip_color = clip_slot.clip.color
                color_bytes = color_to_bytes(clip_color)
                self.set_key_slot_color(i, color_bytes)

            else:
                self.set_key_slot_color(i, COLOR_BLACK_BYTES)

        for i in range(num_clip_slots, NUM_DISPLAY_CLIP_SLOTS):
            self.set_key_slot_color(i, COLOR_BLACK_BYTES)


class CurrentTrackEffectsView(OP1View):
    def __init__(self, surface):
        super(CurrentTrackEffectsView, self).__init__(surface)
        self._param = None

    def update(self):
        self.display_device_info()

    @property
    def param(self):
        return self._param

    def set_displayed_device_param(self, param):
        self.log_message('set_displayed_device_param: %s' % (param.name if param else 'None'))
        self._param = param

    def format_param_value_for_dispay(self, param):
        name = self.param.name
        if len(name) > 9:
            name = name[:9]
        value = self.param.str_for_value(self.param.value)
        if len(value) > 7:
            value = value[:7]
        return '%s: %s' % (name, value)

    def display_device_info(self):
        device = self.surface.selected_device
        self.set_top_text('%s' % device.name)

        if self.param is not None:
            self.set_bottom_text(self.format_param_value_for_dispay(self.param))
