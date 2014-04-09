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
import sys

from array import array
from time import sleep
 
import pygame
from generate import GenerateTone

if len(sys.argv) < 2:
    print "\nSUBJECT NUMBER REQUIRED!!!!!!!!!!!"
    print "Use ./exp.py <subj #>\n"
    sys.exit()
else:
    ss_num=sys.argv[1]

pygame.mixer.init()

#############################
#  Constants & globals      # 
#############################

# flags for functions
fixOn=0
dotsOn=1
changeCoh=1
changeDir=0

# dot properties -- just initializations!!
cohLevel=0.15
dirx=0.0
# user response
keyPressed=0

normalFix=Texture('images/fixation.png')
hardFix=Texture('images/hardFix.png')
easyFix=Texture('images/easyFix.png')

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
easyCoh=0.25
hardCoh=0.2
direction = [0.0, 180.0]
easy=[easyCoh]
hard=[hardCoh]
mixed=[hardCoh, easyCoh]

# instruction/practice
inst="intro"
inst_on=1
num_practice=10

def shuffled(x):
    y=x[:]
    random.shuffle(y)
    return y

# timed blocks
block_length_const=5 # five minutes per block

# pseudo-randomization for solid/mixed + precue/no-precue

b1=[1,2] # 1= mixed pre-cue, 2= mixed no pre-cue
b2=[1,2] # 3= easy pre-cue, 4= hard pre-cue
c1=[3,4] # 5= easy no pre-cue, 6= hard no pre-cue
c2=[5,6]

b1.append(c1.pop(c1.index(random.choice(c1))))
b2.append(c1.pop(c1.index(random.choice(c1))))
b1.append(c2.pop(c2.index(random.choice(c2))))
b2.append(c2.pop(c2.index(random.choice(c2))))

b=b1,b2
b=[item for sublist in b for item in sublist] # flatten
b.append(1) # mixed pre-cue for practice blocks

blocktype=b.pop() # first block

###

block_total=8
block_curr=0
blocklengthstring='xxx minutes'
blockscore=0
totalscore=0 # sum of all block scores
block_length=10 # just an initialization...
demo=1
if demo:
    seconds_in_minute=5 # for timed blocks, not practice block
    practice_length=10 # in seconds
    num_practice=1

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
viewport = Viewport(screen=screen, stimuli=[str_instruct_1, fixation, dotStim, str_instruct_2])

p = Presentation(
    go_duration = (exp_length,'seconds'),
    trigger_go_if_armed = 0,            #wait for trigger
    viewports = [viewport])

#initialize log file
logname=time.strftime('_%m-%d-%Y_%Hh-%Mm.csv')
logname='log_'+ss_num+logname
logfile = open(logname, 'w')
logfile.write("# LOGFILE: {0}\n".format(logname))
logfile.write("# Coherence,Direction,Response\n")

#################################
#  Main procedure               #
#################################

def getState(t):
    global fixOn, dotsOn, changeCoh, changeDir, keyPressed, fixOn_start, dotsOn_start, rt, main_curr, block_total, block_curr, practicenum, blocktype
    global trialnum, inst, inst_on, main_start, practice_length, block_start, block_length, blockscore, blocklengthstring, totalscore

    # for instructions only
    if (inst == "intro") and (keyPressed == 3): 
        dotsOn=0
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
        blocktype=b.pop()
        logfile.write("# Start timed segment {0} ({1} minutes): {2}\n".format(block_curr+1, block_length/60.0, t))
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
            blocktype=b.pop()
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
        logfile.write("# Start timed segment {0} ({1} minutes): {2}\n".format(block_curr+1, block_length/60.0, t))            

    # main exp
    if (t > fixOn_start+static_isi) and (fixOn==1):
       trialnum=trialnum+1
       fixOn=0
       dotsOn=1
       changeCoh=1
       changeDir=1
       dotsOn_start=t

    if dotsOn and inst != "intro":
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
            if (correct == 0): sound_a.play(5)

            #print keyPressed

            logfile.write("{0},{1},{2},{3},{4},{5},{6}\n".format(trialnum,cohLevel,dirx,keyPressed,rt,correct,blocktype))
            
    keyPressed = 0
    return 1 


def setBlockLength():
        global block_length, blocklengthstring
        
        block_length = block_length_const * seconds_in_minute 
        blocklengthstring = "five minutes"

def setFixation(t):
    global fixOn
    return fixOn


def setFixationTexture(t):
    if (blocktype==2) or (blocktype==6) or (blocktype==5):
        fixtext=normalFix
    if (blocktype==3):
        fixtext=easyFix
    if (blocktype==4):
        fixtext=hardFix
    if (blocktype==1):
        if cohLevel==easyCoh:
            fixtext=easyFix
        if cohLevel==hardCoh:
            fixtext=hardFix
    return fixtext

def setDots(t):
    global dotsOn
    return dotsOn

def setCoherence(t):
    global changeCoh, cohLevel
    if changeCoh:
        changeCoh=0
        if (blocktype==1) or (blocktype==2):
            cohLevel = random.choice(mixed)
        if (blocktype==3) or (blocktype==5):
            cohLevel = random.choice(easy)
        if (blocktype==4) or (blocktype==6):
            cohLevel = random.choice(hard)

#    if (blocktype == 1) or (blocktype == 3) or (blocktype == 4):
#        print "pre-cue ",
#    else:
#        print "no pre-cue",
#    if (blocktype == 1) or (blocktype == 2):
#        print "mixed",
#    if (blocktype == 3) or (blocktype == 5):
#        print "easy",
#    if (blocktype == 4) or (blocktype == 6):
#        print "hard",
#    print cohLevel

    return cohLevel

def setDirection(t):
    global changeDir, dirx
    if changeDir:
        changeDir=0
        dirx = random.choice(direction)
    return dirx

def setInstructions(t):
    global inst_on
    return inst_on

def changeInstructions(t):
    global inst, blocklengthstring, blockscore
    if inst == "intro":
        stry = 'In this experiment, you will see a cluster of moving dots (like below). ' \
               'On average, the dots will be moving to the left or to the right.\n\n\n\n\n\n\n\n\n\n\n\n\n' \
               'Your task is to decide whether the dots are moving to the left or right.\n' \
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
               'In the next section, you will have FIVE MINUTES to attain as many points as possible.\n\n' \
               'Each INCORRECT response will be followed by a tone.\n\n' \
               'If you have any questions, please ask the experimenter before you begin.\n\n' \
               'When you are ready to begin, press the space bar.'
    elif inst == "mid_timed_segment":
        stry = 'Your score for the previous round: \n\n\t\t\t' + str(blockscore) + '\n\n' \
               'In the next round you will have FIVE MINUTES to attain as many points as possible.\n\n' \
               'Each INCORRECT response will be followed by a tone.\n\n' \
               'When you are ready to begin the next round, press the space bar.'
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
inst3_position_controller = FunctionController(during_go_func=setTimePos)
fixation_texture_controller = FunctionController(during_go_func=setFixationTexture)

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
p.add_controller(dotStim,'on', stimulus_on_controller)
p.add_controller(fixation,'on', stimulus_on_controller)

# on or off during pres
p.add_controller(fixation,'max_alpha', fixation_controller)
p.add_controller(dotStim,'on', dot_controller)
p.add_controller(dotStim,'signal_fraction', coherence_controller)
p.add_controller(dotStim,'signal_direction_deg', direction_controller)
p.add_controller(fixation,'texture', fixation_texture_controller)

p.add_controller(p, 'trigger_go_if_armed', state_controller)
p.parameters.handle_event_callbacks = [(pygame.locals.KEYDOWN, keydown)]

#######################
#  Run the stimulus!  #
#######################
p.go()
logfile.close
