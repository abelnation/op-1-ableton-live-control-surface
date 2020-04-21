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

VERSION="1.0.9"

# Sentinel values

BUTTON_ON = 127
BUTTON_OFF = 0

NOTE_OFF = 0
NOTE_ON = 100

# Number of tracks

NUM_TRACKS = 13
NUM_SCENES = 10
NUM_RETURN_TRACKS = 2
NUM_MODES = 4

NUM_DISPLAY_CLIP_SLOTS = 14

CHANNEL = 0

# MIDI CC's

OP1_MODE_SYNTH = 0
OP1_MODE_DRUM = 1
OP1_MODE_TAPE = 2
OP1_MODE_MIXER = 3

OP1_ENCODER_1 = 1 # Blue
OP1_ENCODER_2 = 2 # Green
OP1_ENCODER_3 = 3 # White
OP1_ENCODER_4 = 4 # Red

OP1_U01_ENCODER_1 = 53 # Blue
OP1_U01_ENCODER_2 = 54 # Green
OP1_U01_ENCODER_3 = 55 # White
OP1_U01_ENCODER_4 = 56 # Red

OP1_U02_ENCODER_1 = 57 # Blue
OP1_U02_ENCODER_2 = 58 # Green
OP1_U02_ENCODER_3 = 59 # White
OP1_U02_ENCODER_4 = 60 # Red

OP1_U03_ENCODER_1 = 61 # Blue
OP1_U03_ENCODER_2 = 62 # Green
OP1_U03_ENCODER_3 = 63 # White
OP1_U03_ENCODER_4 = 64 # Red

OP1_ENCODER_1_BUTTON = 64 # Blue
OP1_ENCODER_2_BUTTON = 65 # Green
OP1_ENCODER_3_BUTTON = 66 # White
OP1_ENCODER_4_BUTTON = 67 # Red

OP1_HELP_BUTTON = 5
OP1_METRONOME_BUTTON = 6

OP1_MODE_1_BUTTON = 7  # Synth
OP1_MODE_2_BUTTON = 8  # Drums
OP1_MODE_3_BUTTON = 9  # Tape
OP1_MODE_4_BUTTON = 10 # Mixer

# Mode buttons under the display
OP1_T1_BUTTON = 11
OP1_T2_BUTTON = 12
OP1_T3_BUTTON = 13
OP1_T4_BUTTON = 14

OP1_ARROW_UP_BUTTON = 15
OP1_ARROW_DOWN_BUTTON = 16
OP1_SCISSOR_BUTTON = 17

OP1_SS1_BUTTON = 50 # In (green)
OP1_SS2_BUTTON = 51 # Out (green)
OP1_SS3_BUTTON = 52 # Loop (green)
OP1_SS4_BUTTON = 21 # Tape scrub (red)
OP1_SS5_BUTTON = 22 # Reverse (red)
OP1_SS6_BUTTON = 23 # Begin bar (red)
OP1_SS7_BUTTON = 24 # M1 (grey)
OP1_SS8_BUTTON = 25 # M2 (grey)

OP1_REC_BUTTON = 38
OP1_PLAY_BUTTON = 39
OP1_STOP_BUTTON = 40

OP1_LEFT_ARROW = 41
OP1_RIGHT_ARROW = 42
OP1_SHIFT_BUTTON = 43

OP1_MICROPHONE = 48
OP1_COM = 49
OP1_SEQUENCER = 26

# Notes

OP1_F3_NOTE = 53
OP1_FS3_NOTE = 54
OP1_GF3_NOTE = 54
OP1_G3_NOTE = 55
OP1_GS3_NOTE = 56
OP1_AF3_NOTE = 56
OP1_A3_NOTE = 57
OP1_AS3_NOTE = 58
OP1_BF3_NOTE = 58
OP1_B3_NOTE = 59

OP1_C4_NOTE = 60
OP1_CS4_NOTE = 61
OP1_DF4_NOTE = 61
OP1_D4_NOTE = 62
OP1_F4_NOTE = 63
OP1_E4_NOTE = 64
OP1_F4_NOTE = 65
OP1_FS4_NOTE = 66
OP1_GF4_NOTE = 66
OP1_G4_NOTE = 67
OP1_GS4_NOTE = 68
OP1_AF4_NOTE = 68
OP1_A4_NOTE = 69
OP1_AS4_NOTE = 70
OP1_BF4_NOTE = 70
OP1_B4_NOTE = 71

OP1_C5_NOTE = 72
OP1_CS5_NOTE = 73
OP1_DF5_NOTE = 73
OP1_D5_NOTE = 74
OP1_DS5_NOTE = 75
OP1_EF5_NOTE = 75
OP1_E5_NOTE = 76

OP1_MIN_NOTE = 53
OP1_MAX_NOTE = 76
