##################################################################
#
#   Copyright (C) 2012 Imaginando, Lda & Teenage Engineering AB
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   For more information about this license please consult the
#   following webpage: http://www.gnu.org/licenses/gpl-2.0.html
#
##################################################################

# OP-1 Python Scripts V0.0.1 (Abel custom)
# Customization by: Abel Allison

from functools import partial
import time

import Live


# Ableton Live Framework imports
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ComboElement import ComboElement
from _Framework.ControlSurface import ControlSurface
from _Framework.DeviceComponent import DeviceComponent
from _Framework.EncoderElement import EncoderElement
from _Framework.Layer import Layer
from _Framework.MixerComponent import MixerComponent
from _Framework.Resource import PrioritizedResource
from _Framework.SessionComponent import SessionComponent
from _Framework.TransportComponent import TransportComponent

# Provides many constants
from _Framework.InputControlElement import *

# Utils from APC libs
from _APC import ControlElementUtils as APCUtils
from _APC.DetailViewCntrlComponent import DetailViewCntrlComponent

from . import modes
from . import ui
from .consts import *
from .ShiftEnabledControl import ShiftEnabledControl
from .util import color_to_bytes
from .util import midi_bytes_to_values

COLOR_BLACK_BYTES = [0x00, 0x00, 0x00]
COLOR_WHITE_BYTES = [0x7F, 0x7F, 0x7F]

CONNECTION_MAX_RETRIES = 5

ENCODER_MODE = Live.MidiMap.MapMode.relative_two_compliment

#
# OP-1 Internal Implementation Constants
#

ENABLE_SEQUENCE = (0xf0, 0x00, 0x20, 0x76, 0x00, 0x01, 0x02, 0xf7)
DISABLE_SEQUENCE = (0xf0, 0x00, 0x20, 0x76, 0x00, 0x01, 0x00, 0xf7)
ID_SEQUENCE = (0xf0, 0x7e, 0x7f, 0x06, 0x01, 0xf7)


class OP1(ControlSurface):
	def __init__(self, *args, **kwargs):
		ControlSurface.__init__(self, *args, **kwargs)

		self.log_message('__init__()')
		self.show_message("Version: " + VERSION)

		# Data for tracking connection attempts
		self.device_connected = False
		self.next_retry_delay = 1
		self.next_retry_ts = None
		self.retries_count = 0
		self._current_midi_map = None

		# State of display text
		self.text_top = ''
		self.text_bottom = ''

		# State of display key slots
		self.display_color_by_slot_num = {}
		for i in range(NUM_DISPLAY_CLIP_SLOTS):
		 	self.display_color_by_slot_num[i] = COLOR_BLACK_BYTES

		with self.component_guard():
			self._build_components()
			self.init_modes()
	#
	# Ableton Helpers
	#

	@property
	def num_tracks(self):
		return min(NUM_TRACKS, len(self.song().tracks))

	@property
	def num_scenes(self):
		return min(NUM_SCENES, len(self.song().scenes))

	@property
	def selected_track(self):
		return self.song().view.selected_track

	@property
	def selected_track_num(self):
		return list(self.song().tracks).index(self.selected_track)

	@property
	def selected_scene(self):
		return self.song().view.selected_scene

	@property
	def selected_scene_num(self):
		return list(self.song().scenes).index(self.selected_scene)

	@property
	def selected_clip_slot(self):
		return self.selected_track.clip_slots[self.selected_scene_num]

	@property
	def selected_device(self):
		return self.selected_track.view.selected_device

	def get_selected_track_devices(self, class_name):
		return [
			device for device in self.selected_track.devices
			if device.class_name == class_name
		]

	#
	# Connected Components
	#

	def _with_shift(self, control):
		return ComboElement(control, modifiers=[self._button_shift])

	def _build_components(self):

		self._buttons = {}
		for identifier in range(5, 53) + range(64, 68):
			# We create the shift button in a special way
			if identifier == OP1_SHIFT_BUTTON:
				continue
			# Encoders present as buttons when values are changed
			button = APCUtils.make_pedal_button(identifier)
			button.add_value_listener(self.debug_button_handler)
			self._buttons[identifier] = button

		# Encoder buttons
		# See notes below for explanation of exclusion of first button
		# for identifier in [OP1_ENCODER_2_BUTTON, OP1_ENCODER_3_BUTTON, OP1_ENCODER_4_BUTTON]:
		# 	button = APCUtils.make_pedal_button(identifier)
		# 	button.add_value_listener(self.debug_button_handler)
		# 	APCUtils.make_pedal_button(identifier] = butto)

		self._notes = {}
		for identifier in range(OP1_MIN_NOTE, OP1_MAX_NOTE+1):
			note = APCUtils.make_button(CHANNEL, identifier)
			note.add_value_listener(self.debug_note_handler)
			self._notes[identifier] = note

		# Buttons
		self._button_shift = ButtonElement(
			is_momentary=True,
			msg_type=MIDI_CC_TYPE,
			channel=0,
			identifier=OP1_SHIFT_BUTTON,
			# Required for modifier buttons
			resource_type=PrioritizedResource,
			name='ShiftButton',
		)
		# self._button_shift.add_value_listener(self.on_shift_button)

		self._button_mode_synth = self._buttons[OP1_MODE_1_BUTTON]
		self._button_mode_drum = self._buttons[OP1_MODE_2_BUTTON]
		self._button_mode_tape = self._buttons[OP1_MODE_3_BUTTON]
		self._button_mode_mixer = self._buttons[OP1_MODE_4_BUTTON]

		self._button_mode_1 = self._buttons[OP1_T1_BUTTON]
		self._button_mode_2 = self._buttons[OP1_T2_BUTTON]
		self._button_mode_3 = self._buttons[OP1_T3_BUTTON]
		self._button_mode_4 = self._buttons[OP1_T4_BUTTON]

		self._button_down = self._buttons[OP1_ARROW_DOWN_BUTTON]
		self._button_up = self._buttons[OP1_ARROW_UP_BUTTON]
		self._button_left = self._buttons[OP1_LEFT_ARROW]
		self._button_right = self._buttons[OP1_RIGHT_ARROW]

		self._button_metronome = self._buttons[OP1_METRONOME_BUTTON]
		self._button_scissors = self._buttons[OP1_SCISSOR_BUTTON]

		self._button_ss1 = self._buttons[OP1_SS1_BUTTON]
		self._button_ss2 = self._buttons[OP1_SS2_BUTTON]
		self._button_ss3 = self._buttons[OP1_SS3_BUTTON]
		self._button_ss4 = self._buttons[OP1_SS4_BUTTON]
		self._button_ss5 = self._buttons[OP1_SS5_BUTTON]
		self._button_ss6 = self._buttons[OP1_SS6_BUTTON]
		self._button_ss7 = self._buttons[OP1_SS7_BUTTON]
		self._button_ss8 = self._buttons[OP1_SS8_BUTTON]

		self._button_record = self._buttons[OP1_REC_BUTTON]
		self._button_play = self._buttons[OP1_PLAY_BUTTON]
		self._button_stop  = self._buttons[OP1_STOP_BUTTON]

		self._button_microphone = self._buttons[OP1_MICROPHONE]
		self._button_com = self._buttons[OP1_COM]
		self._button_sequencer = self._buttons[OP1_SEQUENCER]

		# Encoders
		self._encoder_1 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_ENCODER_1, ENCODER_MODE)
		self._encoder_2 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_ENCODER_2, ENCODER_MODE)
		self._encoder_3 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_ENCODER_3, ENCODER_MODE)
		self._encoder_4 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_ENCODER_4, ENCODER_MODE)

		self._unshift_encoder_1 = ShiftEnabledControl(self._encoder_1, self._button_shift, False, self)
		self._unshift_encoder_2 = ShiftEnabledControl(self._encoder_2, self._button_shift, False, self)
		self._unshift_encoder_3 = ShiftEnabledControl(self._encoder_3, self._button_shift, False, self)
		self._unshift_encoder_4 = ShiftEnabledControl(self._encoder_4, self._button_shift, False, self)
		self._shift_encoder_1 = ShiftEnabledControl(self._encoder_1, self._button_shift, True, self)
		self._shift_encoder_2 = ShiftEnabledControl(self._encoder_2, self._button_shift, True, self)
		self._shift_encoder_3 = ShiftEnabledControl(self._encoder_3, self._button_shift, True, self)
		self._shift_encoder_4 = ShiftEnabledControl(self._encoder_4, self._button_shift, True, self)

		self._encoder_u01_1 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U01_ENCODER_1, ENCODER_MODE)
		self._encoder_u01_2 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U01_ENCODER_2, ENCODER_MODE)
		self._encoder_u01_3 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U01_ENCODER_3, ENCODER_MODE)
		self._encoder_u01_4 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U01_ENCODER_4, ENCODER_MODE)

		self._unshift_encoder_u01_1 = ShiftEnabledControl(self._encoder_u01_1, self._button_shift, False, self)
		self._unshift_encoder_u01_2 = ShiftEnabledControl(self._encoder_u01_2, self._button_shift, False, self)
		self._unshift_encoder_u01_3 = ShiftEnabledControl(self._encoder_u01_3, self._button_shift, False, self)
		self._unshift_encoder_u01_4 = ShiftEnabledControl(self._encoder_u01_4, self._button_shift, False, self)
		self._shift_encoder_u01_1 = ShiftEnabledControl(self._encoder_u01_1, self._button_shift, True, self)
		self._shift_encoder_u01_2 = ShiftEnabledControl(self._encoder_u01_2, self._button_shift, True, self)
		self._shift_encoder_u01_3 = ShiftEnabledControl(self._encoder_u01_3, self._button_shift, True, self)
		self._shift_encoder_u01_4 = ShiftEnabledControl(self._encoder_u01_4, self._button_shift, True, self)

		self._encoder_u02_1 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U02_ENCODER_1, ENCODER_MODE)
		self._encoder_u02_2 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U02_ENCODER_2, ENCODER_MODE)
		self._encoder_u02_3 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U02_ENCODER_3, ENCODER_MODE)
		self._encoder_u02_4 = EncoderElement(MIDI_CC_TYPE, CHANNEL, OP1_U02_ENCODER_4, ENCODER_MODE)

		# NOTE: encoder_1_button conflicts with encoder_U03_4
		self._encoder_button_1 = self._buttons[OP1_ENCODER_1_BUTTON]
		self._encoder_button_2 = self._buttons[OP1_ENCODER_2_BUTTON]
		self._encoder_button_3 = self._buttons[OP1_ENCODER_3_BUTTON]
		self._encoder_button_4 = self._buttons[OP1_ENCODER_4_BUTTON]

		self._mixer = MixerComponent(
			num_tracks=NUM_TRACKS,
			num_returns=2,
		)
		# self._mixer.set_select_buttons(
		# 	prev_button=self._button_up,
		# 	next_button=self._button_down,
		# )
		# self.map_mixer_controls_for_current_track()

		def on_down_button(value):
			if value == BUTTON_ON:
				self.set_selected_scene(self.scene_offset + 1)

		def on_up_button(value):
			if value == BUTTON_ON:
				self.set_selected_scene(self.scene_offset - 1)

		self.scene_offset = 0
		self.song().view.add_selected_scene_listener(self.selected_scene_changed)
		self._button_right.add_value_listener(on_down_button)
		self._button_left.add_value_listener(on_up_button)

		self._transport = TransportComponent()
		self._transport.set_metronome_button(self._button_metronome)

		#
		# Controls for navigating the bottom detail pane
		#
		self._device_navigation = DetailViewCntrlComponent()

		# Toggle hide/show of bottom detail pane
		self._device_navigation.set_detail_toggle_button(self._button_ss1)

		# Toggle between clip detail and effects detail in bottom detail pane
		self._device_navigation.set_device_clip_toggle_button(self._button_ss2)

		# Nav left/right in the device chain detail view in bottom pane
		self._device_navigation.device_nav_left_button.set_control_element(self._button_ss7)
		self._device_navigation.device_nav_right_button.set_control_element(self._button_ss8)

		# Clip firing
		self._notes[OP1_F3_NOTE].add_value_listener(partial(self.clip_fired, 0))
		self._notes[OP1_G3_NOTE].add_value_listener(partial(self.clip_fired, 1))
		self._notes[OP1_A3_NOTE].add_value_listener(partial(self.clip_fired, 2))
		self._notes[OP1_B3_NOTE].add_value_listener(partial(self.clip_fired, 3))
		self._notes[OP1_C4_NOTE].add_value_listener(partial(self.clip_fired, 4))
		self._notes[OP1_D4_NOTE].add_value_listener(partial(self.clip_fired, 5))
		self._notes[OP1_E4_NOTE].add_value_listener(partial(self.clip_fired, 6))
		self._notes[OP1_F4_NOTE].add_value_listener(partial(self.clip_fired, 7))

		self._button_scissors.add_value_listener(self.selected_clip_deleted)

		#
		# Device Controls
		#

		# self._device = DeviceComponent(
		# 	name='Device_Component',
		# 	is_enabled=False,
		# 	layer=Layer(
		# 		parameter_controls=ButtonMatrixElement(rows=[[
  #    				self._encoder_u01_1,
		# 			self._encoder_u01_2,
		# 			self._encoder_u01_3,
		# 			self._encoder_u01_4,
		# 			self._encoder_u02_1,
		# 			self._encoder_u02_2,
		# 			self._encoder_u02_3,
		# 			self._encoder_u02_4,
  #        		]]),
		# 		# bank_buttons=ButtonMatrixElement(rows=[[
		# 		# 	self._encoder_button_1,
		# 		# 	self._encoder_button_2,
		# 		# 	self._encoder_button_3,
		# 		# 	self._encoder_button_4,
		# 		# ]]),
		# 		bank_prev_button=self._button_ss5,
		# 		bank_next_button=self._button_ss6,
		# 		on_off_button=self._button_record,
		# 	),
		# 	device_selection_follows_track_selection=True
		# )
		# self._device.set_enabled(True)
		# self.set_device_component(self._device)

	#
	# Mode configuration
	#

	def init_modes(self):
		self.tracks_mode = modes.TracksMode(self)
		self.effects_mode = modes.EffectsMode(self)

		self.current_mode = None

		self._button_mode_synth.add_value_listener(
			partial(self.on_mode_button, self.tracks_mode))
		self._button_mode_drum.add_value_listener(
		 	partial(self.on_mode_button, self.effects_mode))
		# self._button_mode_3.add_value_listener(
		# 	partial(self.on_mode_button, ))
		# self._button_mode_4.add_value_listener(
		# 	partial(self.on_mode_button, ))

		self.set_mode(self.tracks_mode)

	def set_mode(self, mode):
		self.log_message('set_mode()')
		if self.current_mode is not None:
			self.current_mode.deactivate()
		self.current_mode = mode
		self.current_mode.activate()

	def on_mode_button(self, mode, value):
		if value:
			self.set_mode(mode)

	#
	# Shift Button Alternative modes
	#

	def on_shift_button(self, value):
		if value == BUTTON_ON:
			self.log_message('shift on')
			pass
		else:
			self.log_message('shift off')
			pass

	#
	# Scene selection
	#

	def selected_scene_changed(self):
		self.log_message('selected_scene_changed()')
		self.scene_offset = self.selected_scene_num
		self.map_clip_controls_for_current_scene()

	def set_selected_scene(self, scene_offset):
		scene_offset = max(0, scene_offset)
		scene_offset = min(scene_offset, self.num_scenes-1)

		next_scene = self.song().scenes[scene_offset]
		next_scene = self.song().view.selected_scene = next_scene

		self.scene_offset = scene_offset

	def clear_key_assignments(self):
		pass

	def map_clip_controls_for_current_scene(self):
		for clip_slot in self.selected_scene.clip_slots:
			pass

	#
	# Clip triggers
	#

	def clip_fired(self, clip_num, value):
		if value == NOTE_ON:

			self.log_message('clip_fired(clip_num=%s, value=%s)' % (clip_num, value))
			clip_slot = self.selected_track.clip_slots[clip_num]

			# if clip_slot.is_playing:
			# 	self.log_message('stoping clip')
			# 	clip_slot.stop()
			# else:
			# 	self.log_message('firing clip. has_clip=%s has_stop=%s, playing_status=%s' % (
			# 		clip_slot.has_clip,
			# 		clip_slot.has_stop_button,
			# 		clip_slot.playing_status,
			# 	))
			# 	clip_slot.fire()

			self.log_message('firing clip. has_clip=%s has_stop=%s, playing_status=%s' % (
				clip_slot.has_clip,
				clip_slot.has_stop_button,
				clip_slot.playing_status,
			))
			clip_slot.fire()



			# Update scene selection to fired clip's row.
			self.set_selected_scene(clip_num)

	def selected_clip_deleted(self, value):
		if value == BUTTON_ON:
			self.log_message('deleting clip')
			self.selected_clip_slot.delete_clip()

	#
	# Looper triggers
	#

	def looper_fired(looper_device):
		fire_param = [param for param in looper_device.parameters if param.name == 'State']
		self.log_message(fire_param)

	#
	# Refresh handling
	#

	def handle_sysex(self, midi_bytes):
		super(OP1, self).handle_sysex(midi_bytes)
		if (len(midi_bytes) >= 8 and (midi_bytes[6]==32) and (midi_bytes[7]==118)):
			self.handle_device_connection_success()
		else:
			self.log_message("sysex: %s" % (midi_bytes, ))

	def refresh_state(self):
		super(OP1, self).refresh_state()

		self.log_message("refresh_state()")
		self.retries_count = 0
		self.next_retry_ts = None
		self.next_retry_delay = 1
		self.device_connected = False

	def update_display(self):
		super(OP1, self).update_display()

		if not(self.device_connected):
			if self.next_retry_ts is None or time.time() >= self.next_retry_ts:
				self.attempt_connection_with_device()
			return

		# Render the currently active view
		self.current_mode.view.render()

	#
	# Connection Management
	#

	def build_midi_map(self, midi_map_handle):
		super(OP1, self).build_midi_map(midi_map_handle)

		# map mixer controls to currently selected track
		# self.map_mixer_controls_for_current_track()

	def attempt_connection_with_device(self):
		self.log_message("Attempting to connect to OP-1... (num_retries: %s)" % self.retries_count)
		self.retries_count += 1
		self.next_retry_ts = time.time() + self.next_retry_delay
		self.next_retry_delay *= 2
		self._send_midi(ID_SEQUENCE)

	def handle_device_connection_success(self):
		self.device_connected = True
		self.retries_count = 0
		self.log_message("OP-1 Connected")
		self._send_midi(ENABLE_SEQUENCE)

	def disconnect(self):
		self.log_message("disconnect()")
		self.retries_count = 0
		self.device_connected = False
		self._send_midi(DISABLE_SEQUENCE)
		super(OP1, self).disconnect()

	def suggest_input_port(self):
		return "OP-1 Midi Device"

	def suggest_output_port(self):
		return "OP-1 Midi Device"

	#
	# Debug utils
	#

	def param_value_updated(self, param):
		self.log_message('Param update: %s(%s)' % (param.name, param.value))
		self.log_message('    value_items: %s' % (list(param.value_items), ))

	def debug_button_handler(self, value, *args, **kwargs):
		self.log_message('button: %s' % value)

	def debug_note_handler(self, value, *args, **kwargs):
		self.log_message('note: %s' % value)

	def handle_nonsysex(self, midi_bytes):
		super(OP1, self).handle_nonsysex(midi_bytes)
		channel, identifier, value, is_pitchbend = midi_bytes_to_values(midi_bytes)
		if not is_pitchbend:
			self.log_message('midi ch:%s value:%s(%s)' % (channel, identifier, value))

