#!/usr/bin/env python

##############################################################
#                                                            #
#       2/9/2013                                             #
#       Jeff Zemla                                           #
#                                                            #
#       + Random dot motion - coherence 5%, 10%, 15%         #
#       + Trials randomly interspersed - NO TIME LIMITS      #
#                                                            #
##############################################################


############################
#  Import various modules  #
############################

import VisionEgg
VisionEgg.start_default_logging(); VisionEgg.watch_exceptions()
from VisionEgg.FlowControl import Presentation, Controller, FunctionController
from VisionEgg.Dots import DotArea2D
from VisionEgg.DaqKeyboard import *
from VisionEgg.Textures import *
from VisionEgg.Core import *
from VisionEgg.Text import *
from VisionEgg.WrappedText import *
import OpenGL.GL as gl
import random, math

from array import array
from time import sleep
 
import pygame
from generate import GenerateTone

pygame.mixer.init()

#############################
#  Constants & globals      # 
#############################

# flags for functions
fixOn=0
dotsOn=0
changeCoh=0
changeDir=0

# dot properties -- just initializations!!
cohLevel=0.15
dirx=0.0

# user response
keyPressed=0

normalFix=Texture('images/fixation.png')
sound_a=GenerateTone(freq='F')

# chronology
practice_length=600 # length of each sub-block (600==10 min)
static_isi=1
seconds_in_minute=60 # used only for demoing. should be 60 during real experiment.

trialnum=0
#practicenum=1 # number of value practice trials (hack)
rt=0
fixOn_start=0
dotsOn_start=0
exp_length=7200 # arbitrarily long (2hr)
main_start=0 # start of 'main' exp after instructions
main_curr = 0 # current of completed sub-blocks
block_start=0

# vectors to choose from
direction = [0.0, 180.0]
coherence = [0.20] # all the same coherence, change value only!!

# instruction/practice
inst="intro"
inst_on=1
num_practice=10

# timed blocks
blocktypes=[1]
resetblocktype=blocktypes[:]
blockround=1
random.shuffle(blocktypes)
block_total=len(blocktypes)*2
block_curr=0
blocklengthstring='xxx minutes'
blockscore=0
totalscore=0 # sum of all block scores
block_length=10 # just an initialization...
fb_block=round(random.random())+1
demo=1
if demo:
    seconds_in_minute=6 # for timed blocks, not main block
    practice_length=10
    num_practice=10

#################################
#  Initialize OpenGL objects    #
#################################

# Initialize OpenGL graphics screen.
#screen = get_default_screen()
screen = VisionEgg.Core.Screen(fullscreen=0,size=(1024,768))          # get_default_screen crashes my laptop

screen.parameters.bgcolor = (0.0,0.0,0.0,0.0)

screen_half_x = screen.size[0]/2
screen_half_y = screen.size[1]/2

str_instruct_1 = Text(text='Experiment',
        position=(screen_half_x,screen_half_y),
        font_size=40,
        anchor='center')

str_instruct_2 = WrappedText(text='placeholder',
        position=(150,screen.size[1]-100),
        font_size=40,
        size=(800,500))

str_instruct_3 = Text(text='0 minutes',
        position=(400, screen.size[1]-100),
        font_size=40,
        color=(1.0,0.0,0.0))

fixation = TextureStimulus(texture=normalFix,
        internal_format = gl.GL_RGBA,
        max_alpha = 1.0,
        size = (150,150),
        position=(screen_half_x,screen_half_y),
        anchor='center')

dotStim = DotArea2D( position                = ( screen_half_x, screen_half_y ),
                      anchor                  = 'center',
                      size                    = ( 300.0 , 300.0 ),
                      signal_fraction         = cohLevel,
                      signal_direction_deg    = dirx,
                      velocity_pixels_per_sec = 100.0,
                      dot_lifespan_sec        = 0.08,
                      dot_size                = 3.0, 
                      num_dots                = 200)

# Create a Viewport instance
viewport = Viewport(screen=screen, stimuli=[str_instruct_1, fixation, dotStim, str_instruct_2, str_instruct_3])

p = Presentation(
    go_duration = (exp_length,'seconds'),
    trigger_go_if_armed = 0,            #wait for trigger
    viewports = [viewport])

#initialize log file
logname=time.strftime('log_%m-%d-%Y_%Hh-%Mm.csv')
logfile = open(logname, 'w')
logfile.write("# LOGFILE: {0}\n".format(logname))
logfile.write("# Coherence,Direction,Response\n")

#################################
#  Main procedure               #
#################################

def getState(t):
    global fixOn, dotsOn, changeCoh, changeDir, keyPressed, fixOn_start, dotsOn_start, rt, main_curr, block_total, block_curr, practicenum
    global trialnum, inst, inst_on, main_start, practice_length, block_start, block_length, blockscore, blocklengthstring, totalscore

    # for instructions only
    if (inst == "intro") and (keyPressed == 3): 
        inst = "intro2"
        keyPressed=0
    if (inst == "intro2") and (keyPressed == 3):
        inst = "practice"
        fixOn = 1
        fixOn_start = t
        logfile.write("# Practice trials begin: {0}\n".format(t))
    if (inst == "practice") and (trialnum > num_practice):   
        inst = "done_practice"
        fixOn = 0
        dotsOn = 0
        logfile.write("# End practice trials begin: {0}\n".format(t))
    if (inst == "done_practice") and (keyPressed == 3):  
        blockscore = 0
        inst = "calibration"
        fixOn = 1
        fixOn_start = t
        inst_on = 0
        main_start = t
        logfile.write("# Start calibration {0}: {1}\n".format(main_curr+1, t))                            
    if (inst == "calibration") and (t > main_start + practice_length) and (dotsOn == 0):    
        main_curr = main_curr + 1            
        setBlockLength()            
        inst = "done_calibration"
        logfile.write("# End calibration {0} ({1} points): {2}\n".format(main_curr, blockscore, t))
        totalscore=totalscore+blockscore
        inst_on = 1
        fixOn = 0
    if (inst == "done_calibration") and (keyPressed == 3):
        logfile.write("# Start timed segment {0} ({1} minutes): {2}\n".format(block_curr+1, block_length/60, t))            
        blockscore = 0
        inst = "timed_segment"
        fixOn = 1
        fixOn_start = t
        inst_on = 0
        block_start = t
    if (inst == "timed_segment") and (t > block_start + block_length):
        block_curr = block_curr + 1
        if block_curr < block_total:
            setBlockLength()             
            inst = "mid_timed_segment"
        else:
            inst = "done_experiment"
        fixOn = 0
        dotsOn = 0
        inst_on = 1
        logfile.write("# End timed segment {0} ({1} points): {2}\n".format(block_curr, blockscore, t))
        totalscore=totalscore+blockscore
    if (inst == "mid_timed_segment") and (keyPressed == 3):
        blockscore = 0
        inst = "timed_segment"
        fixOn = 1
        fixOn_start = t
        inst_on = 0
        block_start = t
        logfile.write("# Start timed segment {0} ({1} minutes): {2}\n".format(block_curr+1, block_length/60, t))            

    # main exp
    if (t > fixOn_start+static_isi) and (fixOn==1):
       trialnum=trialnum+1
       fixOn=0
       dotsOn=1
       changeCoh=1
       changeDir=1
       dotsOn_start=t

    if dotsOn:
        if (keyPressed == 1) or (keyPressed == 2):
            rt=t-dotsOn_start
            dotsOn=0
            fixOn=1
            fixOn_start=t
            if (dirx==180) and (keyPressed==1): correct=1
            if (dirx==180) and (keyPressed==2): correct=0
            if (dirx==0) and (keyPressed==1): correct=0
            if (dirx==0) and (keyPressed==2): correct=1
            
            if correct == 1: blockscore = blockscore + 1
            if (correct == 0) and (blockround==fb_block) and (inst=="timed_segment"): sound_a.play(5)

            if (blockround==fb_block) and (inst=="timed_segment"): fbon=1
            else: fbon=0

            #print keyPressed

            logfile.write("{0},{1},{2},{3},{4},{5},{6}\n".format(trialnum,cohLevel,dirx,keyPressed,rt,correct,fbon))
            
    keyPressed = 0
    return 1 


def setBlockLength():
        global blocktypes, block_length, blocklengthstring, blockscore, resetblocktype, blockround

        if (blocktypes==[]) and (blockround==1):
            blockround=2
            blocktypes=resetblocktype
            random.shuffle(blocktypes)
        
        tmp = blocktypes.pop()
        block_length = tmp * seconds_in_minute 
        if tmp == 5:
            blocklengthstring = "five minutes"
        if tmp == 1:
            blocklengthstring = "one minute"

def setFixation(t):
    global fixOn
    return fixOn

def setDots(t):
    global dotsOn
    return dotsOn

def setCoherence(t):
    global changeCoh, cohLevel
    if changeCoh:
        changeCoh=0
        cohLevel = random.choice(coherence)
    return cohLevel

def setDirection(t):
    global changeDir, dirx
    if changeDir:
        changeDir=0
        dirx = random.choice(direction)
        print dirx
    return dirx

def setInstructions(t):
    global inst_on
    return inst_on

def changeInstructions(t):
    global inst, blocklengthstring, blockscore
    if inst == "intro":
        stry = 'In this experiment, you will see a cluster of moving dots.\n\n' \
               'On average, the dots will be moving to the left or to the right.\n\n' \
               'Your task is to decide whether the dots are moving to the left or right.\n\n' \
               'Each trial will take roughly 0-2 seconds to complete.\n\n' \
               'Press the space bar to continue.'
    elif inst == "intro2":
        stry = 'Your goal is to get as many trials correct as possible in the time allotted.\n\n' \
               'To do so, you will need to respond both QUICKLY and ACCURATELY.\n\n' \
               'Please try some practice trials.\n\n' \
               'Press the space bar to continue.' 
    elif inst == "practice":
        stry = 'PRACTICE TRIAL: \n' \
               'Press \'j\' if the dots are moving to the left on average\n' \
               'Press \'k\' if the dots are moving to the right on average'
    elif inst == "done_practice":
        stry = 'End of practice trials. Your score for the previous round: \n\n\t\t\t' + str(blockscore) + '\n\n' \
               'If you have any questions, please ask the experimenter NOW.\n\n' \
               'The next section of the experiment will take 10 minutes.\n\n' \
               'When you are ready, press the space bar to begin.'
    elif inst == "done_calibration":
        stry = 'Your score for the previous round: \n\n\t\t\t' + str(blockscore) + '\n\n' \
               'In the next section, you will have:\nto attain as many points as possible.\n\n'+str(blockround)+str(fb_block)
        if blockround==fb_block:
            stry=stry+'Each INCORRECT response will be followed by a tone.\n\n'
        else:
            stry=stry+'You will NOT recieve any feedback after an incorrect response\n\n'
        stry=stry+ 'If you have any questions, please ask the experimenter before you begin.\n\n' \
                   'When you are ready to begin, press the space bar.'
    elif inst == "mid_timed_segment":
        stry = 'Your score for the previous round: \n\n\t\t\t' + str(blockscore) + '\n\n' \
               'In the next round you will have:\nto attain as many points as possible.\n\n'+str(blockround)+str(fb_block)
        if blockround==fb_block:
            stry=stry+'Each INCORRECT response will be followed by a tone.\n\n'               
        else:
            stry=stry+'You will NOT recieve any feedback after an incorrect response\n\n'                
        stry=stry+'When you are ready to begin the next round, press the space bar.'
    elif inst == "done_experiment":
        stry = 'Your score for the previous round: \n\n\t\t\t' + str(blockscore) + '\n\n' \
               'You have completed the experiment.\n\nYour total score for the experiment is: ' + str(totalscore) + '\n\n' \
               'There is a short demographic survey you must complete before leaving.\n\n' \
               'Please contact the experimenter.'
    else:
        stry = 'this text should not be visible. if you can read this, please contact the experimenter.'
        #print inst
    return stry

def setTimeOn(t):
    if (inst=="done_calibration") or (inst=="mid_timed_segment"):
        return 1
    else:
        return 0

def setTimePos(t):
    if (inst=="done_calibration"):
        return (630, screen.size[1]-240)
    else:
        return (590, screen.size[1]-239)

def setTimeText(t):
    return blocklengthstring.upper()

def keydown(event):
        global keyPressed

        if event.key == pygame.locals.K_SPACE:
            keyPressed = 3
        if event.key == pygame.locals.K_j:
            keyPressed = 1
        if event.key == pygame.locals.K_k:
            keyPressed = 2
        if (event.key == pygame.locals.K_ESCAPE) and (pygame.key.get_mods() & pygame.locals.KMOD_LCTRL):
            p.parameters.go_duration = (0, 'frames')    # Quit presentation 'p' with LEFT CTRL + ESC
      
#######################
#  Define controllers #
#######################
###### Create an instance of the Controller class
trigger_in_controller = KeyboardTriggerInController(pygame.locals.K_5)

stimulus_on_controller = ConstantController(during_go_value=1,between_go_value=0)
stimulus_off_controller = ConstantController(during_go_value=0,between_go_value=1)
fixation_controller = FunctionController(during_go_func=setFixation)
dot_controller = FunctionController(during_go_func=setDots)
coherence_controller = FunctionController(during_go_func=setCoherence)
direction_controller = FunctionController(during_go_func=setDirection)
inst_controller = FunctionController(during_go_func=changeInstructions)
inst_on_controller = FunctionController(during_go_func=setInstructions)
inst3_on_controller = FunctionController(during_go_func=setTimeOn)
inst3_text_controller = FunctionController(during_go_func=setTimeText)
inst3_position_controller = FunctionController(during_go_func=setTimePos)

state_controller = FunctionController(during_go_func=getState)

#######################################################
#  Connect the controllers with objects they control  #
#######################################################
p.add_controller(p,'trigger_go_if_armed',trigger_in_controller)

# on or off before pres
p.add_controller(str_instruct_1,'on', stimulus_off_controller)
p.add_controller(str_instruct_2,'text', inst_controller)
p.add_controller(str_instruct_2,'on', stimulus_on_controller)
p.add_controller(str_instruct_2,'on', inst_on_controller)
p.add_controller(str_instruct_3,'on', inst3_on_controller)
p.add_controller(str_instruct_3,'text', inst3_text_controller)
p.add_controller(str_instruct_3,'position', inst3_position_controller)
p.add_controller(str_instruct_3,'on', stimulus_on_controller)
p.add_controller(dotStim,'on', stimulus_on_controller)
p.add_controller(fixation,'on', stimulus_on_controller)

# on or off during pres
p.add_controller(fixation,'max_alpha', fixation_controller)
p.add_controller(dotStim,'on', dot_controller)
p.add_controller(dotStim,'signal_fraction', coherence_controller)
p.add_controller(dotStim,'signal_direction_deg', direction_controller)

p.add_controller(p, 'trigger_go_if_armed', state_controller)
p.parameters.handle_event_callbacks = [(pygame.locals.KEYDOWN, keydown)]

#######################
#  Run the stimulus!  #
#######################
p.go()
logfile.close
