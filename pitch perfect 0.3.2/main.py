#!/usr/bin/python

# main.py : starts the main program and handles interactions
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

from generate import GetExponent, GenerateTone, GeneratePitchedSample


black = (   0,   0,   0, 255 )
grey  = (  95,  95,  95, 255 )
white = ( 255, 255, 255, 255 )


octave_limits = (-3, 3)


def MakeColorWheel(w, h, colors=(0x010000, 0x000100, 0x000001)):
    """ Create an array filled with interpolated color values,
        including first and last array elements.
        'w' is color-band width.
        'h' is height of colors going to black.
        'colors' is hexadecimal color placeholder iterable.
    """

    # Set up working arrays.
    ary = np.zeros((w * 2 * len(colors), h), dtype=np.uint32)
    tmp = np.concatenate((np.linspace(0.0, 1.0, w), np.ones(w)))
    tmp = tmp.reshape((tmp.size, 1)) * np.indices((tmp.size, h))[1]
    tmp = tmp.astype(np.uint32)

    for i in range(len(colors)):
        j = (i + 1) % len(colors)
        c_from, c_twrd = colors[i], colors[j]
        # col_ary starts at c_from and ends up at c_twrd.
        col_ary = (tmp[: : -1] * c_from * 256 / h) | (tmp * c_twrd * 256 / h)
        # Make sure 1st dimension is sized and placed properly.
        ary[i * w * 2: (i + 1) * w * 2, ...] = col_ary

    return ary


def DrawLineToArray(ary, xa, ya, xb, yb, color, alpha=255):
    """ Outputs a line of the given color and alpha to the input array.
        This is a numpy-only method. Why? I'm waiting for pygame to get
        more mathematically accurate.
    """

    xa, xb = xa + 0.5, xb + 0.5
    ya, yb = ya + 0.5, yb + 0.5
    if abs(xb - xa) > abs(yb - ya):
        if xa > xb:
            xa, xb = xb, xa
            ya, yb = yb, ya
        x_ary = np.arange(xa, xb).astype(np.int)
        y_ary = np.linspace(ya, yb, num=x_ary.size).astype(np.int)
    else:
        if ya > yb:
            xa, xb = xb, xa
            ya, yb = yb, ya
        y_ary = np.arange(ya, yb).astype(np.int)
        x_ary = np.linspace(xa, xb, num=y_ary.size).astype(np.int)

    # Alpha code-rant
    dest = ary[x_ary, y_ary]
    r = (color[0] * alpha + ((dest >> 16) & 0xff) * (255 - alpha)) / 256
    g = (color[1] * alpha + ((dest >>  8) & 0xff) * (255 - alpha)) / 256
    b = (color[2] * alpha + ((dest >>  0) & 0xff) * (255 - alpha)) / 256
    ary[x_ary, y_ary] = (r << 16) | (g << 8) | (b << 0)


class Main:
    """ The main part of the program. """

    def __init__( self, width, height, pb_freq, pb_bits,
                  tone=0, accidentals='#', tiles=16 ):

        self.w, self.h = width, height
        self.pb_freq = pb_freq
        self.pb_bits = pb_bits
        # Semi-tones above/below 440 Hz (A).
        self.base_tone = tone
        self.def_freq = np.log2(440.0) + self.base_tone / 12.0
        self.octave = 0
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pg.display.init()
        icon = pg.image.load(os.path.join('data', 'speaker.png'))
        pg.display.set_icon(icon)
        pg.display.set_caption('pitch perfect')
        self.screen = pg.display.set_mode((self.w, self.h), 0)
        pg.mixer.init(self.pb_freq, self.pb_bits, 1, 512)

        # Prepare sound and channel variables.
        self.num_chns = 64
        pg.mixer.set_num_channels(self.num_chns)
        self.main_chn = pg.mixer.Channel(0)
        self.chns = [ pg.mixer.Channel(q) for q in range(1, self.num_chns) ]
        # Holds the self.chns indices that remain playing.
        self.chns_playing = [ ]
        self.chn_selected = None
        # Holds all samples that are chorded together to make sure
        # they are not deleted while being played.
        self.smps = [ ]
        self.frqs = [ ]
        self.vols = [ ]
        self.play = False
        # Set up the sample list for the main channel, which is
        # toggled back and forth.
        self.snds = [ None, None ]
        self.snd_i = 0

        # Create surface to indicate chorded samples.
        self.chrd_sfcs = [ pg.Surface((9, 9)).convert() for q in range(2) ]
        self.chrd_sfcs[0].fill(black)
        self.chrd_sfcs[0].set_colorkey(black)
        ary = pg.surfarray.pixels2d(self.chrd_sfcs[0])
        ary[3: 6, 2: 7: 4] = ary[2: 7: 4, 3: 6] = self.screen.map_rgb(white)
        del ary
        self.chrd_sfcs[1].fill(black)
        self.chrd_sfcs[1].set_colorkey(black)
        ary = pg.surfarray.pixels2d(self.chrd_sfcs[1])
        ary[3: 6, 2: 7] = ary[2: 7, 3: 6] = self.screen.map_rgb(white)
        del ary
        self.chrd_on = [ ]
        self.chrd_recs = [ ]
        self.chrd_insts = [ ]

        # Create instrument surfaces.
        self.radius = self.w * 3 / 8
        self.size = (self.radius * 2, ) * 2
        self.circ_sfcs = [ ]
        self.circ_i = 0
        self.sfc_pos = (self.w / 2 - self.radius, ) * 2
        # Part of radius that is deadened to zero-volume.
        self.dead_rad = self.radius / 8.0
        self.x_ind, self.y_ind = np.indices(self.size) - self.radius + 0.5
        # The distance array.
        self.dis_ary = np.hypot(self.x_ind, self.y_ind)
        self.dis_ary = np.maximum(0.0, self.dis_ary - self.dead_rad)
        # Angle from top of circle clockwise.
        self.ang_ary = np.arctan2(self.y_ind, self.x_ind) - 3.0 * np.pi / 2.0
        self.ang_ary %= 2.0 * np.pi
        # inside includes points on perimeter of and contained in circle.
        inside = (self.dis_ary <= self.radius - self.dead_rad)
        wheel = MakeColorWheel(64, 128)
        shade = (self.ang_ary / 2.0 / np.pi * wheel.shape[0]).astype(np.int)
        bright = (self.dis_ary / self.radius * 127).astype(np.int)
        color_ary = wheel[shade[inside], bright[inside]]
        tmp_sfc = pg.Surface(self.size).convert()
        tmp_sfc.fill(black)
        sfc_ary = pg.surfarray.pixels2d(tmp_sfc)
        # Fill surface with gradients.
        sfc_ary[inside] = color_ary
        # Draw perimeter. This is the best way I have found to do so
        # accurately with a filled circle.
        tmp = np.zeros((self.radius * 2 + 2, ) * 2, dtype=np.uint32)
        tmp[1: -1, 1: -1] = inside
        x_sum = tmp + np.roll(tmp, -1, axis=0) + np.roll(tmp, 1, axis=0)
        y_sum = tmp + np.roll(tmp, -1, axis=1) + np.roll(tmp, 1, axis=1)
        on_perimeter = np.logical_or(x_sum == 2, y_sum == 2)
        sfc_ary[on_perimeter[1: -1, 1: -1]] = self.screen.map_rgb(white)
        del sfc_ary
        # Draw pitch lines.
        for i in range(3):
            self.circ_sfcs.append(tmp_sfc.copy())
            sfc_ary = pg.surfarray.pixels2d(self.circ_sfcs[i])
            for a in range(12):
                angle = 2.0 * np.pi * a / 12.0 + 3.0 * np.pi / 2.0
                xa = self.dead_rad * np.cos(angle) + self.radius
                ya = self.dead_rad * np.sin(angle) + self.radius
                xb = self.radius * np.cos(angle) + self.radius
                yb = self.radius * np.sin(angle) + self.radius
                if i * 4 == a:
                    alpha = 192
                else:
                    alpha = 64
                DrawLineToArray(sfc_ary, xa, ya, xb, yb, white, alpha)
            del sfc_ary
        del tmp_sfc

        # Create note-name surfaces.
        pg.font.init()
        self.font_name = os.path.join('data', 'LiberationMono-Regular.ttf')
        self.font_size_l = 24
        self.font_size_s = 16
        self.font_l = pg.font.Font(self.font_name, self.font_size_l)
        self.font_s = pg.font.Font(self.font_name, self.font_size_s)
        if accidentals == '#':
            nl = [ 'A','A#','B','C','C#','D','D#','E','F','F#','G','G#' ]
        else:
            nl = [ 'A','Bb','B','C','Db','D','Eb','E','F','Gb','G','Ab' ]
        names = nl[int(self.base_tone): ] + nl[: int(self.base_tone)]
        txt_rad = self.radius + 24.0
        sfc_dk = pg.Surface((self.w, self.h)).convert()
        sfc_dk.fill(black)
        sfc_dk.set_colorkey(black)
        sfc_br = pg.Surface((self.w, self.h)).convert()
        sfc_br.fill(black)
        sfc_br.set_colorkey(black)
        for a in range(12):
            angle = 2.0 * np.pi * a / 12.0 + 3.0 * np.pi / 2.0
            txt_sfc = self.font_l.render(names[a], True, grey)
            txt_rec = txt_sfc.get_rect()
            txt_rec.centerx = self.w / 2 + txt_rad * np.cos(angle)
            txt_rec.centery = self.h / 2 + txt_rad * np.sin(angle)
            sfc_dk.blit(txt_sfc, txt_rec)
            txt_sfc = self.font_l.render(names[a], True, white)
            sfc_br.blit(txt_sfc, txt_rec)
        self.notes_sfcs = (sfc_dk, sfc_br)
        self.notes_mode = 0

        # Create octave label and number surfaces.
        self.oct_lbl_sfc = self.font_l.render("octave:  ", True, white)
        self.oct_lbl_rec = self.oct_lbl_sfc.get_rect()
        self.oct_lbl_rec.bottomright = (self.w - self.font_size_l, self.h)
        self.oct_sfcs = [ ]
        self.oct_recs = [ ]
        for i in range(octave_limits[1] - octave_limits[0] + 1):
            sfc = self.font_l.render(str(i + 1), True, white)
            self.oct_sfcs.append(sfc)
            rec = self.oct_sfcs[-1].get_rect()
            rec.bottomright = (self.w - self.font_size_l, self.h)
            self.oct_recs.append(rec)

        # Load waveform images and set selection rectangles and indices.
        w, h = 32, 32
        unsel_sfc = pg.image.load(os.path.join('data', 'inst-unselect.png'))
        sel_sfc = pg.image.load(os.path.join('data', 'inst-select.png'))
        self.inst_full_rec = unsel_sfc.get_rect()
        self.inst_full_rec.topleft = (2, 2)
        rec = self.inst_full_rec.copy()
        rec.size = (w, h)
        move = rec.move
        self.inst_sel_recs = [ rec, move(0, h), move(w, 0), move(w, h) ]
        self.inst_sfcs = [ unsel_sfc, sel_sfc ]
        self.inst_names = ( 'sine', 'sawtooth', 'square' )
        self.cur_inst_i = 0

        # Create instrument info.
        self.def_inst_sfcs = [ ]
        for text in self.inst_names:
            sfc = self.font_s.render(text + ' wave', True, white)
            self.def_inst_sfcs.append(sfc)
        self.cust_insts = [ ]
        self.cust_inst_i = 0
        inst_exists = False
        path = os.path.join('data', 'samples.txt')
        if os.path.exists(path):
            inp = open(path)
            for line in inp.readlines():
                line = line.strip()
                if len(line) > 0 and line[0] != '#':
                    fname, base_note, vol, text = eval(line)
                    sound = pg.mixer.Sound(os.path.join('data', fname))
                    ary = pg.sndarray.array(sound)
                    tiled_ary = np.tile(ary, max(1, tiles))
                    base_note = GetExponent(base_note)
                    vol = np.clip(vol, 0.0, 1.0)
                    sfc = self.font_s.render(text[: 16], True, white)
                    self.cust_insts.append((tiled_ary, base_note, vol, sfc))
                    inst_exists = True
            inp.close()
        if not inst_exists:
            # Default to empty wave if no samples found.
            sfc = self.font_s.render('silence', True, white)
            ary = np.array([ 0 ], dtype=np.int16)
            self.cust_insts.append((ary, 0.0, 0.0, sfc))


    def ModifyOctave(self, delta):
        self.octave = int(np.clip(self.octave + delta, *octave_limits))


    def NewChordRec(self, x, y):
        rec = self.chrd_sfcs[0].get_rect()
        rec.center = (x, y)
        return rec


    def BtnCollision(self, pos):
        for i in range(len(self.inst_sel_recs)):
            if self.inst_sel_recs[i].collidepoint(pos):
                return i

        return -1


    def Debug(self):
        """ Display some possibly helpful debugging information. """

        print 'Octave:', self.octave
        print 'Sound objects:', self.snds
        for i in range(len(self.snds)):
            if type(self.snds[i]) == pg.mixer.SoundType:
                print 'Length of sound %d:' % i, self.snds[i].get_length()
        print 'Channels playing:', self.chns_playing
        print 'Waveforms of each channel:', self.chrd_insts
        print 'Number of persistent notes:', len(self.smps)
        print 'Channel selected:', self.chn_selected
        print


    def ReadyIndex(self):
        """ Return an item of self.snds not being played. """

        for i in range(len(self.snds)):
            if self.snds[i] is not None:
                if self.main_chn.get_sound() == self.snds[i]:
                    # Make sure not to overwrite a sound queued to be
                    # played on the 'main' channel by queueing just the
                    # sound currently playing.
                    self.main_chn.queue(self.snds[i])
                    return 1 - i

        # No sound is being played on the main channel, so return
        # the first index.
        return 0


    def HandleEvents(self):
        """ Not an elegant function, but it simplifies the main cycle
            considerably.
        """

        (mx, my) = pg.mouse.get_pos()
        mb = pg.mouse.get_pressed()
        km = pg.key.get_mods()

        frq, vol = None, None

        if self.chn_selected is not None and mb[0]:
            # Adjusting a persistent note.
            i = self.chns_playing[self.chn_selected]
            x, y = mx - self.sfc_pos[0], my - self.sfc_pos[1]
            if 0 <= x < self.radius * 2 and 0 <= y < self.radius * 2:
                vol = self.dis_ary[x, y] / (self.radius - self.dead_rad)
                if vol <= 1.0:
                    if self.chns[i].get_busy():
                        self.chns[i].stop()
                    pitch = self.ang_ary[x, y] / 2.0 / np.pi
                    if pitch < self.circ_i / 3.0:
                        pitch += 1.0
                    if self.notes_mode == 1:
                        pitch = round(pitch * 12.0) / 12.0
                    frq = 2.0 ** (pitch + self.def_freq + self.octave)
                    self.snd_i = self.ReadyIndex()
                    if self.cur_inst_i < 3:
                        inst = self.inst_names[self.cur_inst_i]
                        vol /= 16.0
                        self.snds[self.snd_i] = GenerateTone(inst, frq, vol)
                    else:
                        inst = self.cust_insts[self.cust_inst_i][0]
                        base = self.cust_insts[self.cust_inst_i][1]
                        vol *= self.cust_insts[self.cust_inst_i][2]
                        self.snds[self.snd_i] = GeneratePitchedSample(
                                inst, base, frq, vol
                                )
                    self.frqs[self.chn_selected] = frq
                    self.vols[self.chn_selected] = vol
                    self.play = True
                    self.chrd_on[self.chn_selected] = (self.notes_mode == 1)
                    rec = self.NewChordRec(mx, my)
                    self.chrd_recs[self.chn_selected] = rec
            rec = pg.Rect(0, 0, self.radius * 2, self.radius * 2)
            if not rec.collidepoint(x, y) or vol > 1.0:
                if not self.chns[i].get_busy():
                    # Note has crossed bounds of instrument, repeat it
                    # where it was left behind, if not already playing.
                    frq = self.frqs[self.chn_selected]
                    vol = self.vols[self.chn_selected]
                    if self.cur_inst_i < 3:
                        inst = self.inst_names[self.cur_inst_i]
                        snd = GenerateTone(inst, frq, vol)
                    else:
                        inst = self.cust_insts[self.cust_inst_i][0]
                        base = self.cust_insts[self.cust_inst_i][1]
                        snd = GeneratePitchedSample(inst, base, frq, vol)
                    self.chns[i].play(snd, -1)
                    self.smps[self.chn_selected] = snd
        elif mb[0] or (km & pg.KMOD_CTRL):
            # No notes are selected, play normally.
            x, y = mx - self.sfc_pos[0], my - self.sfc_pos[1]
            if 0 <= x < self.radius * 2 and 0 <= y < self.radius * 2:
                vol = self.dis_ary[x, y] / (self.radius - self.dead_rad)
                if vol <= 1.0:
                    pitch = self.ang_ary[x, y] / 2.0 / np.pi
                    if pitch < self.circ_i / 3.0:
                        pitch += 1.0
                    if self.notes_mode == 1:
                        pitch = round(pitch * 12.0) / 12.0
                    frq = 2.0 ** (pitch + self.def_freq + self.octave)
                    self.snd_i = self.ReadyIndex()
                    if self.cur_inst_i < 3:
                        inst = self.inst_names[self.cur_inst_i]
                        vol /= 16.0
                        self.snds[self.snd_i] = GenerateTone(inst, frq, vol)
                    else:
                        inst = self.cust_insts[self.cust_inst_i][0]
                        base = self.cust_insts[self.cust_inst_i][1]
                        vol *= self.cust_insts[self.cust_inst_i][2]
                        self.snds[self.snd_i] = GeneratePitchedSample(
                                inst, base, frq, vol
                                )
                    self.play = True

        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                return True
            elif evt.type == pg.KEYDOWN:
                if evt.key == pg.K_ESCAPE:
                    return True
                elif evt.key == pg.K_d:
                    self.Debug()
                elif evt.key == pg.K_SPACE:
                    self.octave = 0
                elif evt.key == pg.K_UP:
                    self.ModifyOctave(1)
                elif evt.key == pg.K_DOWN:
                    self.ModifyOctave(-1)
                elif evt.key == pg.K_LEFT:
                    if self.circ_i == 0:
                        self.ModifyOctave(-1)
                    self.circ_i = (self.circ_i - 1) % len(self.circ_sfcs)
                elif evt.key == pg.K_RIGHT:
                    if self.circ_i == len(self.circ_sfcs) - 1:
                        self.ModifyOctave(1)
                    self.circ_i = (self.circ_i + 1) % len(self.circ_sfcs)
                elif evt.key in (pg.K_1, pg.K_KP1):
                    self.cur_inst_i = 0
                elif evt.key in (pg.K_2, pg.K_KP2):
                    self.cur_inst_i = 1
                elif evt.key in (pg.K_3, pg.K_KP3):
                    self.cur_inst_i = 2
                elif evt.key in (pg.K_4, pg.K_KP4):
                    # Custom sampled instrument selection.
                    if self.cur_inst_i != 3:
                        self.cur_inst_i = 3
                    else:
                        n = len(self.cust_insts)
                        self.cust_inst_i = (self.cust_inst_i + 1) % n
                elif evt.key == pg.K_s:
                    # Silence all persistent notes.
                    for chn in self.chns:
                        chn.stop()
                    for lst in (
                            self.smps, self.chns_playing, self.chrd_on,
                            self.chrd_recs, self.chrd_insts,
                            self.frqs, self.vols,
                            ):
                        lst[: ] = [ ]
                    self.chn_selected = None
                elif evt.key == pg.K_x:
                    # Delete selected note.
                    if self.chn_selected is not None:
                        self.chns[self.chns_playing[self.chn_selected]].stop()
                        for lst in (
                                self.smps, self.chns_playing, self.chrd_on,
                                self.chrd_recs, self.chrd_insts,
                                self.frqs, self.vols,
                                ):
                            lst.pop(self.chn_selected)
                        self.chn_selected = None
                elif evt.key == pg.K_c:
                    # Cancel selection.
                    self.chn_selected = None
                elif evt.key in (pg.K_LSHIFT, pg.K_RSHIFT):
                    # Select a note.
                    if len(self.chns_playing) > 0:
                        colls = [ ]
                        for i in range(len(self.chrd_recs)):
                            if self.chrd_recs[i].collidepoint(mx, my):
                                colls.append(i)
                        if len(colls) > 0:
                            if self.chn_selected in colls:
                                i = (self.chn_selected + 1) % len(colls)
                                self.chn_selected = colls[i]
                            else:
                                self.chn_selected = colls[0]
                        else:
                            if self.chn_selected is None:
                                self.chn_selected = 0
                            else:
                                self.chn_selected += 1
                            if self.chn_selected >= len(self.chns_playing):
                                self.chn_selected = None
                        if self.chn_selected is not None:
                            inst = self.chrd_insts[self.chn_selected]
                            if inst >= 3:
                                self.cust_inst_i = inst - 3
                            self.cur_inst_i = min(inst, 3)
            elif evt.type == pg.KEYUP:
                if evt.key in (pg.K_LCTRL, pg.K_RCTRL):
                    # Create new persistent note.
                    if self.play:
                        for i in range(0, self.num_chns - 1):
                            if i not in self.chns_playing:
                                self.chns_playing.append(i)
                                snd = self.snds[self.snd_i]
                                self.smps.append(snd)
                                self.chns[i].play(snd, -1)
                                self.frqs.append(frq)
                                self.vols.append(vol)
                                self.chrd_on.append(self.notes_mode == 1)
                                rec = self.NewChordRec(mx, my)
                                self.chrd_recs.append(rec)
                                inst = self.cur_inst_i
                                if inst == 3:
                                    inst += self.cust_inst_i
                                self.chrd_insts.append(inst)
                                break
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if evt.button == 1:
                    # Test for and apply button selection.
                    i = self.BtnCollision(evt.pos)
                    if i == 3:
                        if self.cur_inst_i != 3:
                            self.cur_inst_i = 3
                        else:
                            n = len(self.cust_insts)
                            self.cust_inst_i = (self.cust_inst_i + 1) % n
                    elif i > -1:
                        self.cur_inst_i = i
                    if self.chn_selected is not None:
                        inst = self.cur_inst_i
                        if inst == 3:
                            inst += self.cust_inst_i
                        self.chrd_insts[self.chn_selected] = inst
                elif evt.button == 2:
                    self.octave_changed = False
                elif evt.button == 3:
                    self.notes_mode = 1 - self.notes_mode
                elif evt.button == 4:
                    # Middle mouse scroll up
                    if mb[1]:
                        # Change octave upward if middle mouse button is
                        # also pressed.
                        self.ModifyOctave(1)
                        self.octave_changed = True
                    else:
                        # Move octave divider clockwise.
                        if self.circ_i == len(self.circ_sfcs) - 1:
                            self.ModifyOctave(1)
                        l = len(self.circ_sfcs)
                        self.circ_i = (self.circ_i + 1) % l
                elif evt.button == 5:
                    # Middle mouse scroll down
                    if mb[1]:
                        # Change octave downward if middle mouse button is
                        # also pressed.
                        self.ModifyOctave(-1)
                        self.octave_changed = True
                    else:
                        # Move octave divider ccw.
                        if self.circ_i == 0:
                            self.ModifyOctave(-1)
                        l = len(self.circ_sfcs)
                        self.circ_i = (self.circ_i - 1) % l
            elif evt.type == pg.MOUSEBUTTONUP:
                if evt.button == 1 and self.chn_selected is not None:
                    # Set the selected note based on previously created
                    # frequency and volume.
                    frq = self.frqs[self.chn_selected]
                    vol = self.vols[self.chn_selected]
                    if self.cur_inst_i < 3:
                        inst = self.inst_names[self.cur_inst_i]
                        snd = GenerateTone(inst, frq, vol)
                    else:
                        inst = self.cust_insts[self.cust_inst_i][0]
                        base = self.cust_insts[self.cust_inst_i][1]
                        snd = GeneratePitchedSample(inst, base, frq, vol)
                    i = self.chns_playing[self.chn_selected]
                    self.chns[i].play(snd, -1)
                    self.smps[self.chn_selected] = snd
                elif evt.button == 2:
                    if not self.octave_changed:
                        self.octave = 0


    def Run(self):
        """ Handle events, play main channel and update display. """

        while True:
            if self.HandleEvents():
                # User signalled an exit.
                return True

            if self.play:
                try:
                    # Main channel is being updated.
                    if not self.main_chn.get_busy():
                        # Free to play directly.
                        self.main_chn.play(self.snds[self.snd_i])
                    else:
                        # You're on the short list.
                        self.main_chn.queue(self.snds[self.snd_i])
                    # Make sure to reset boolean for next iteration.
                    self.play = False
                except:
                    print 'Exception raised'
                    print
                    self.Debug()
                    raise

            # clear screen to black.
            self.screen.fill(black)
            # draw main circle surface.
            self.screen.blit(self.circ_sfcs[self.circ_i], self.sfc_pos)
            # draw chorded notes onto screen.
            self.chrd_sfcs[0].set_alpha(96)
            self.chrd_sfcs[1].set_alpha(96)
            for i in range(len(self.chrd_recs)):
                on = self.chrd_on[i]
                rec = self.chrd_recs[i]
                self.screen.blit(self.chrd_sfcs[on], rec)
            if self.chn_selected is not None:
                on = self.chrd_on[self.chn_selected]
                self.chrd_sfcs[on].set_alpha(255)
                rec = self.chrd_recs[self.chn_selected]
                self.screen.blit(self.chrd_sfcs[on], rec)
            # notes around circle surface.
            self.screen.blit(self.notes_sfcs[self.notes_mode], (0, 0))
            # instrument buttons.
            self.screen.blit(self.inst_sfcs[0], self.inst_full_rec)
            rec_a = self.inst_sel_recs[self.cur_inst_i]
            rec_b = rec_a.move(-2, -2);  rec_b.w += 1;  rec_b.h += 1
            self.screen.blit(self.inst_sfcs[1], rec_a, rec_b)
            # draw instrument name along top edge.
            if self.cur_inst_i < 3:
                sfc = self.def_inst_sfcs[self.cur_inst_i]
            else:
                sfc = self.cust_insts[self.cust_inst_i][3]
            rec = sfc.get_rect()
            rec.midtop = (self.w * 3 / 4, 2)
            self.screen.blit(sfc, rec)
            # draw current octave text.
            i = self.octave - octave_limits[0]
            self.screen.blit(self.oct_lbl_sfc, self.oct_lbl_rec)
            self.screen.blit(self.oct_sfcs[i], self.oct_recs[i])
            # update full screen each frame.
            pg.display.update()


usage_str = """
Usage:  python %s [-h] [-8b|-16b] [-r rate] [-t tone] [-f] [-l multiplier]

Options:
    -h  displays usage string and exits.
    -8b sets sound resolution to 8 bits (unsigned), -16b for 16 bits (signed).
    -r  sets the playback frequency; default is 22050 Hz for 8-bit sound,
        44100 Hz for 16-bit.
    -t  sets the number of semitones above/below 440 Hz for the top note
        on the instrument; default value is -9 (C).
    -f  changes all accidentals from sharps to flats.
    -l  sets the number of times to multiply the sample lengths,
        which is useful for adding resolution to shorter samples;
        it does not affect the length of the three generated tones.
        default value is 16.

Example:
    python %s  -8b  -r 44100  -t 7  -f  -l 32
""" % ((sys.argv[0], ) * 2)


if __name__ == '__main__':

    if '-h' in sys.argv:
        print usage_str
        sys.exit()

    if '-8b' in sys.argv:
        bits = 8
        rate = 22050
    elif '-16b' in sys.argv:
        bits = -16
        rate = 44100
    elif sys.platform.startswith('win'):
        # Windows corrupts the sound in 16-bit mode; default to lower quality.
        bits = 8
        rate = 22050
    else:
        bits = -16
        rate = 44100

    if '-r' in sys.argv:
        try:
            i = sys.argv.index('-r')
            rate = int(sys.argv[i + 1])
        except:
            print usage_str
            sys.exit()

    if '-t' in sys.argv:
        try:
            i = sys.argv.index('-t')
            tone = int(sys.argv[i + 1])
        except:
            print usage_str
            sys.exit()
    else:
        tone = -9
    
    if '-f' in sys.argv:
        # Set accidentals to flat mode.
        accidentals = 'b'
    else:
        # Sharp mode is default.
        accidentals = '#'

    if '-l' in sys.argv:
        try:
            i = sys.argv.index('-l')
            tiles = int(sys.argv[i + 1])
        except:
            print usage_str
            sys.exit()
    else:
        tiles = 16

    program = Main(384, 384, rate, bits, tone, accidentals, tiles)
    program.Run()
