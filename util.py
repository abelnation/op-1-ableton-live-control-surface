
# Provides many constants
from _Framework.InputControlElement import *

def color_to_bytes(color):
    """
    Args:
        color (int)
    Returns:
        List[int]
    """
    return [
        ((color >> 16) & 0x000000ff) >> 1,
        ((color >> 8) & 0x000000ff) >> 1,
        (color & 0x000000ff) >> 1,
    ]


def midi_bytes_to_values(midi_bytes):
    """From ControlSurface.py:handle_nonsysex()"""
    channel = midi_bytes[0] & 0x0F
    is_pitchbend = midi_bytes[0] & 240 == MIDI_PB_STATUS
    if is_pitchbend:
        identifier = None
        value = midi_bytes[1] + (midi_bytes[2] << 7)
    else:
        identifier = midi_bytes[1]
        value = midi_bytes[2]

    return channel, identifier, value, is_pitchbend
