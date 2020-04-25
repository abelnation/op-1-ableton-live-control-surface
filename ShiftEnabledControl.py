import time

from _Framework.Util import lazy_attribute


class ShiftEnabledControl(object):
    """
    Proactively re-maps value listener and mapped device param for
    wrapped control based on specified shift button being engaged or not.
    """
    def __init__(self, wrapped_control, shift_button, shift_value_to_activate, surface):
        self._wrapped_control = wrapped_control
        self._shift_button = shift_button
        self._shift_value_to_activate = shift_value_to_activate
        self._surface = surface

        self._listener = None
        self._param = None

        self._shift_button.add_value_listener(self._on_shift)

    def log_message(self, msg):
        self._surface.log_message(msg)

    def _on_shift(self, value):
        control_is_activated = (bool(value) == self._shift_value_to_activate)

        self.log_message('shift: %s, value_needed: %s, control_activated: %s' % (bool(value), self._shift_value_to_activate, control_is_activated))
        if control_is_activated:
            self._activate()
        else:
            self._deactivate()

    def _activate(self):
        # self.log_message('ShiftEnabledControl._activate')
        if self._listener:
            self._wrapped_control.add_value_listener(self._listener)
        if self._param:
            self.log_message('Connecting to : %s' % self._param.name)
            self._wrapped_control.connect_to(self._param)

    def _deactivate(self):
        # self.log_message('ShiftEnabledControl._deactivate')
        if self._listener:
            self._wrapped_control.remove_value_listener(self._listener)

        # Only release control if currently mapped to ours
        if self._param == self._wrapped_control.mapped_parameter:
            self.log_message('Disconnecting: %s' % self._param.name)
            self._wrapped_control.release_parameter()

    def _reset(self):
        self._deactivate()
        self._activate()

    def connect_to(self, param):
        # self.log_message('ShiftEnabledControl.connect_to: %s' % param.name)
        self._param = param
        if not self._shift_value_to_activate:
            self._reset()

    def release_parameter(self):
        self._param = None
        if not self._shift_value_to_activate:
            self._reset()

    def add_value_listener(self, callback):
        self.log_message('ShiftEnabledControl.add_value_listener: %s' % callback)
        self._listener = callback
        if not self._shift_value_to_activate:
            self._reset()

    def remove_value_listener(self, callback):
        self._listener = None
        if not self._shift_value_to_activate:
            self._reset()
