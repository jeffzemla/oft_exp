# generate.py : defines tone-generating and sample-pitching functions
#
# Copyright (C) 2010  Sean McKean
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import os
import pygame as pg
import numpy as np


__all__ = [ 'GetExponent', 'GenerateTone', 'GeneratePitchedSample' ]


notes_dct = {
        'c': -9.0, 'c#': -8.0, 'db': -8.0, 'd': -7.0, 'd#': -6.0, 'eb': -6.0,
        'e': -5.0, 'f': -4.0, 'f#': -3.0, 'gb': -3.0, 'g': -2.0, 'g#': -1.0,
        'ab': -1.0, 'a': 0.0, 'a#': 1.0, 'bb': 1.0, 'b': 2.0,
        }


def GetExponent(note):
    """ Returns a float needed to obtain the frequency in Hz based on
        'note', which is a string with note name defaulting to 'A', and
        an optional trailing octave value, defaulting to 4; each octave
        begins at the C tone.

        Examples:
            # np is short for numpy
            GetExponent('A4') returns a value 'v' where
                2 ** (np.log2(440) + v) == 440.0  # in Hz

            GetExponent('C') (or C4) returns v where
                2 ** (np.log2(440) + v) == 261.6  # approximate;
                                                  # note that C4 is below A4

            GetExponent('Gb-1') (or G flat, octave -1) returns v where
                2 ** (np.log2(440) + v) == 11.6  # below usual hearing range
    """

    i = 0
    while i < len(note) and note[i] not in '1234567890-':
        i += 1

    if i == 0:
        name = 'a'
    else:
        name = note[: i].lower()

    if i == len(note):
        octave = 4
    else:
        octave = int(note[i: ])

    return notes_dct[name] / 12.0 + octave - 4


def GenerateTone(shape='sine', freq=440.0, vol=1.0):
    """ GenerateTone( shape='sine', freq=440.0, vol=1.0 )
            returns pygame.mixer.Sound object

        shape:  string designating waveform type returned; one of
                'sine', 'sawtooth', or 'square'
        freq:  frequency; can be passed in as int or float (in Hz),
               or a string (see GetExponent documentation above for
               string usage)
        vol:  relative volume of returned sound; will be clipped into
              range 0.0 to 1.0
    """

    # Get playback values that mixer was initialized with.
    (pb_freq, pb_bits, pb_chns) = pg.mixer.get_init()

    if type(freq) == str:
        # Set freq to frequency in Hz; GetExponent(freq) is exponential
        # difference from the exponent of note A4: log2(440.0).
        freq = 2.0 ** (np.log2(440.0) + GetExponent(freq))

    # Clip range of volume.
    vol = np.clip(vol, 0.0, 1.0)

    # multiplier and length pan out the size of the sample to help
    # keep the mixer busy between calls to channel.queue()
    multiplier = int(freq / 24.0)
    length = max(1, int(float(pb_freq) / freq * multiplier))
    # Create a one-dimensional array with linear values.
    lin = np.linspace(0.0, multiplier, num=length, endpoint=False)
    if shape == 'sine':
        # Apply a sine wave to lin.
        ary = np.sin(lin * 2.0 * np.pi)
    elif shape == 'sawtooth':
        # sawtooth keeps the linear shape in a modded fashion.
        ary = 2.0 * ((lin + 0.5) % 1.0) - 1.0
    elif shape == 'square':
        # round off lin and adjust to alternate between -1 and +1.
        ary = 1.0 - np.round(lin % 1.0) * 2.0
    else:
        print "shape param should be one of 'sine', 'sawtooth', 'square'."
        print
        return None

    # If mixer is in stereo mode, double up the array information for
    # each channel.
    if pb_chns == 2:
        ary = np.repeat(ary[..., np.newaxis], 2, axis=1)

    if pb_bits == 8:
        # Adjust for volume and 8-bit range.
        snd_ary = ary * vol * 127.0
        return pg.sndarray.make_sound(snd_ary.astype(np.uint8) + 128)
    elif pb_bits == -16:
        # Adjust for 16-bit range.
        snd_ary = ary * vol * float((1 << 15) - 1)
        return pg.sndarray.make_sound(snd_ary.astype(np.int16))
    else:
        print "pygame.mixer playback bit-size unsupported."
        print "Should be either 8 or -16."
        print
        return None


def GeneratePitchedSample(sample_array, base=0.0, freq=440.0, vol=1.0):
    """ GeneratePitchedSample( sample_array, base=0.0, freq=440.0, vol=1.0 )
            returns pygame.mixer.Sound object

        sample_array:  an array holding the integers representing the
                       sample; a pitch-shifted and volume-adjusted
                       version will be returned
        base:  relative base note name (string) or exponent (float);
               this value represents the note that the given sample
               is tuned to; naming the note will simply convert to the
               necessary exponent with function GetExponent(base), so
               specifying the exponent instead takes less time
        freq:  actual frequency; can be passed in as int or float (in Hz),
               or a string (see GetExponent documentation above for
               string usage)
        vol:  relative volume of returned sound; will be clipped into
              range 0.0 to 1.0
    """

    (pb_freq, pb_bits, pb_chns) = pg.mixer.get_init()

    if type(base) == str:
        base = GetExponent(base)

    if type(freq) == str:
        note = GetExponent(freq)
    else:
        note = np.log2(freq) - np.log2(440.0)

    vol = np.clip(vol, 0.0, 1.0)

    # The lower the base note, the higher the adjusted pitch.
    scale = 2.0 ** (note - base)
    # i_ary holds the indices of sample_array in a resized format.
    i_ary = np.arange(int(sample_array.size / scale)) * scale

    if len(i_ary) == 0:
        print "Sample given is too short."
        print
        return None

    # Retrieve values from sample_array and adjust for volume.
    new_ary = sample_array[i_ary.astype(np.int)] * vol
    # new_ary should be periodic, so it can be tiled (appended to
    # itself) until a desired size is reached for the purpose of
    # keeping the mixer continuously playing. Set the minimum
    # possible tile amount to 1 to avoid emptying the array.
    new_ary = np.tile(new_ary, max(1, int(pb_freq / 24.0 / new_ary.size)))

    # Re-center the output array if data format is unsigned.
    if sample_array.dtype == np.uint8:
        center = 128
    elif sample_array.dtype == np.uint16:
        center = 1 << 15
    else:
        center = 0

    return pg.sndarray.make_sound(new_ary.astype(sample_array.dtype) + center)
