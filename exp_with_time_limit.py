#!/usr/bin/env python

###############################################################
#                                                             #
#       2/9/2013                                              #
#       Jeff Zemla                                            #
#                                                             #
#       + Random dot motion - coherence 5%, 10%, 15%          #
#       + Trials randomly interspersed                        #
#       + Timed at 8 intervals - 0.25--3sec quarter-sec intvl #
#         (to determine gain function)                        #
#       + Must watch full interval, then 1 second to respond  #
#                                                             #
###############################################################


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
import OpenGL.GL as gl
import random
import numpy as np

#############################
#  Constants & globals      # 
#############################

# flags for functions
fixOn=1
dotsOn=0
changeCoh=0
changeDir=0

# dot properties
cohLevel=0.05
dirx=0.0
triallength=0.5

# user response
keyPressed=0

# chronology
trialnum=0
rt=0
fixOn_start=0
dotsOn_start=0
isi=2
exp_length=1800

# vectors to choose from
direction = [0.0, 180.0]
coherence = [0.10]
timeints = list(np.linspace(0.20, 1.6, 8))

############################
# Initiation               #
############################


#################################
#  Initialize OpenGL objects    #
#################################

# Initialize OpenGL graphi cs screen.
#screen = get_default_screen()
screen = VisionEgg.Core.Screen(fullscreen=1,size=(1440,900))          # get_default_screen crashes my laptop
#screen = VisionEgg.Core.Screen(fullscreen=0,size=(1024,768))

screen.parameters.bgcolor = (0.0,0.0,0.0,0.0)

screen_half_x = screen.size[0]/2
screen_half_y = screen.size[1]/2

str_instruct_1 = Text(text='Experiment',
        position=(screen_half_x,screen_half_y),
        font_size=50,
        anchor='center')

fixation = TextureStimulus(texture=Texture('images/fixation.png'),
        internal_format = gl.GL_RGBA,
        max_alpha = 1.0,
        size = (80,80),
        position=(screen_half_x,screen_half_y),
        anchor='center')

dotStim = DotArea2D( position                = ( screen_half_x, screen_half_y ),
                      anchor                  = 'center',
                      size                    = ( 300.0 , 300.0 ),
                      signal_fraction         = cohLevel,
                      signal_direction_deg    = dirx,
                      velocity_pixels_per_sec = 100.0,
                      dot_lifespan_sec        = 0.1,
                      dot_size                = 3.0, 
                      num_dots                = 200)

# Create a Viewport instance
viewport = Viewport(screen=screen, stimuli=[str_instruct_1, fixation, dotStim])

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
    global fixOn, dotsOn, changeCoh, changeDir, keyPressed, fixOn_start, dotsOn_start, rt, trialnum, triallength

    if (t > fixOn_start+isi) & (fixOn==1):
       trialnum=trialnum+1
       fixOn=0
       dotsOn=1
       changeCoh=1
       changeDir=1
       triallength = random.choice(timeints)
       dotsOn_start=t

    if t > dotsOn_start + triallength:
        dotsOn=0
        if keyPressed > 0:
            rt=t-dotsOn_start
            dotsOn=0
            fixOn=1
            fixOn_start=t
            if (dirx==180) & (keyPressed==1): correct=1
            if (dirx==180) & (keyPressed==2): correct=0
            if (dirx==0) & (keyPressed==1): correct=0
            if (dirx==0) & (keyPressed==2): correct=1

            logfile.write("{0},{1},{2},{3},{4},{5},{6}\n".format(trialnum,cohLevel,dirx,triallength,keyPressed,rt,correct))

#    print "fixOn_start: {0}, dotsOn_start: {1}".format(fixOn_start, dotsOn_start)
    
    keyPressed = 0
    return 1 


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
    return dirx

def keydown(event):
        global keyPressed
        if event.key == pygame.locals.K_1:
            keyPressed = 1
        if event.key == pygame.locals.K_2:
            keyPressed = 2
        if event.key == pygame.locals.K_ESCAPE:
            p.parameters.go_duration = (0, 'frames')    # Quit presentation 'p' with esc press
      
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

state_controller = FunctionController(during_go_func=getState)

#######################################################
#  Connect the controllers with objects they control  #
#######################################################
p.add_controller(p,'trigger_go_if_armed',trigger_in_controller)

# on or off before pres
p.add_controller(str_instruct_1,'on', stimulus_off_controller)
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
