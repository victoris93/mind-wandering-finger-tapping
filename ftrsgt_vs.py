#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import division  # so that 1/3=0.333 instead of 1/3=0
from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']
from psychopy import visual, core, data, event, logging, sound, gui, clock
from psychopy.constants import *  # things like STARTED, FINISHED
import numpy as np  # whole numpy lib is available, prepend 'np.'
import time
from numpy import sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray, round
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys


## global variables
fullscreen=True
quit_button="escape"
#key_confirm="return"
key_left="s" 
key_right="l" 
key_yes = "y"
key_no = "n"
probe_keys=["1","2", "3", "4", "5"]
n_trials_training_session=10
ISI = 0.75
sleeptime=0 # 5
stimcolor="white"


## Likert-scale
class LikertScale:
	def __init__(self, win, nposs=5, instruction_text=u"", scale_labels=[]):
		start,end=-.5, .5
		ypad=.05
		instru = visual.TextStim(win=win, ori=0, name='instru',units='norm',
			text=instruction_text,    font='Arial',
			pos=[0, 0.5], height=0.07, wrapWidth=None,
			color='white', colorSpace='rgb', opacity=1,
			depth=0.0)
		self.nposs=nposs
		self.show_arrow=False
		line=visual.Line(win, start=(start, 0), end=(end,0), units='norm', lineColor=stimcolor, lineWidth=5)
		ticks=start+np.arange(0,nposs)*(end-start)/float(nposs-1)
		poss=[visual.Line(win, start=(tick, -ypad), end=(tick,ypad), units='norm', lineColor=stimcolor,
						  lineWidth=3) for tick in ticks]
		lab=[visual.TextStim(win, pos=(ticks[i], -.1), units='norm', text=scale_labels[i], height=.05, color=stimcolor) for i in range(len(scale_labels))]

		self.arrow_v=0.4*np.array([ [0,0], [.2, .2], [.1, .2], [.1, .5], [-.1, .5], [-.1, .2], [-.2, .2], [0, 0]])
		self.arrow_v[:,1]+=ypad+.01
		self.ticks=ticks
		self.arrow=visual.ShapeStim(win, vertices=self.arrow_v, fillColor=stimcolor, units='norm')

		self.init_random()

		self.elements=[line]+poss+lab+[instru]

	def init_random(self):
		## initialize to either 0 or nposs-1
		initial_pos=np.random.choice([0,self.nposs-1])
		self.set_arrow(initial_pos)
	def init_middle(self):
		## initialize to either 0 or nposs-1
		initial_pos=int(self.nposs/2)
		self.set_arrow(initial_pos)

	def set_arrow(self, pos):
		self.current_pos=pos
		v=self.arrow_v.copy()
		v[:,0]+=self.ticks[pos]
		self.arrow.setVertices(v)
		self.show_arrow=True

	def arrow_left(self):
		if self.current_pos==0:
			return
		else:
			self.set_arrow(self.current_pos-1)

	def arrow_right(self):
		if self.current_pos==self.nposs-1:
			return
		else:
			self.set_arrow(self.current_pos+1)
	def draw(self):
		for el in self.elements:
			el.draw()
		if self.show_arrow:
			self.arrow.draw() 


# Ensure that relative paths start from the same directory as this script
thisDir = os.getcwd()

# Store info about the experiment session
expName = 'FT-RSG tACS'  # from the Builder filename that created this script
expInfo = {"participant": '', 'session':["training","baseline","stimulation"]}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False: core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName


## duration for baseline
session_duration=3*60 # in s
num_probes=3

# overwrite in case of real stimulation session
if expInfo["session"]=="stimulation":
	session_duration=20*60 # in s
	num_probes=20

min_probe_interval=30 # in s
max_probe_interval=60 # in s

## randomization
ntrials=int(session_duration/ISI)
probe_times=np.array(np.random.randint( min_probe_interval, max_probe_interval+1, num_probes-1)/ISI, dtype=np.int)
probe_trials=np.cumsum(np.array(probe_times/sum(probe_times)*(ntrials-20/ISI), dtype=np.int))
probe_trials=np.append(probe_trials, ntrials)

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename =  thisDir+ "/data/%s_%s_%s_%s" %(expInfo['participant'], expInfo["session"], expName, expInfo['date'])
#filename='data/test'
datafile= filename + ".csv"

#save a log file for detail verbose info
logFile = logging.LogFile("Log"+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

# Setup the Window
win = visual.Window(size=(800, 600), fullscr=fullscreen, screen=0, allowGUI=False, allowStencil=False,
	monitor='Monitor', color=[0,0,0], colorSpace='rgb',
	blendMode='avg', useFBO=False,
	)

# store frame rate of monitor if we can measure it successfully
expInfo['frameRate']=win.getActualFrameRate()
if expInfo['frameRate']!=None:
	frameDur = 1.0/round(expInfo['frameRate'])
else:
	frameDur = 1.0/60.0 # couldn't get a reliable measure so guess

# Initialize components for Routine "instruction"
instruction1 = visual.TextStim(win=win, ori=0, name='text',
	text=u'Place your left index finger on S and your right index finger on L.\n Please hold this position during the entire experiment.\n\nDuring the experiment, you will hear a tone playing in a set rhythm.\nYour task is to try and press the buttons in a random sequence of S/L presses to the rhythm of the tone.\n\nTry to replicate the rhythm of the tone as accurately as possible.\nYou may only press ONE of the buttons at a time.\n\nPress any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1b = visual.TextStim(win=win, ori=0, name='text', #Talk about this at the meeting
	text=u'Try to stay as concentrated on the task as you can throughout the entire experiment. It is however, not unusual for your thoughts to start wandering.\nAt some point, you will be interrupted to answer the questions on the screen relative to your mind-wandering.\n\n Press any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1c = visual.TextStim(win=win, ori=0, name='text',
	text='The first question will probe your state of mind prior to its appearance. If you reply "On task", this means you kept your focus/thoughts on the task (your compliance with the task instructions).\n\nIf you reply "Off-task, but trying to concentrate", this means your focus/thoughts unintentionally drifted elsewhere(daydreaming, memories, future plans, friends etc..).\n\nHowever, if you reply "Off-task, and not trying to concentrate", this means you intentionally engaged in these thoughts (which is fine :)). You will be further asked to assess how confident you feel about your answer on the scale of 1 to 5.\n\n Press any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)
	
instruction1d = visual.TextStim(win=win, ori=0, name='text',
 #    text=u'Importantly, mind-wandering can occur either because you INTENTIONALLY decided to think about things that are unrelated to the task, OR because your thoughts UNINTENTIONALLY drifted away to task-unrelated thoughts, despite your best intentions to focus on the task. \n\nTherefore, if you want to answer MIND WANDERING, you have to choose if it was ???INTENTIONALLY??? or ???UNINTENTIONALLY???.\n\nNote that there is no right or wrong answer and that there will not be any consequences related to your answers, so please just be honest when answering those questions.\n\nPress any button to continue.',    font='Arial',
	text=u'It is important to note that there are no right or wrong answers, and they have no consequences, so please answer as truthfully as possible.\n\nPress any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)
	 
instruction1f = visual.TextStim(win=win, ori=0, name='text',
	text=u'There will be a cross on the screen in front of you during the experiment, please keep your gaze focused on this cross throughout.\n\nIf you have any questions regarding the experiment, please call for the experimenter and ask them now.\n\nOtherwise, press any button to continue',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

training_session_starts=visual.TextStim(win=win, ori=0, name='text',
	text=u'The experiment starts with a training.\n\nPress any key to start.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)
training_repeat=visual.TextStim(win=win, ori=0, name='text',
	text=u'Would you like another round of training?\n\nPress N for NO or Y for YES.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

real_experiment_starts=visual.TextStim(win=win, ori=0, name='text',
	text=u'The real experiment starts now.\n If you have any questions, please call for the experimenter.\n If not, press any key to start the experiment.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

### PROBES ###
#probe_thoughts = visual.TextStim(win, text = "Were you engaging in any thoughts prior to this probe? Press Y for YES or N for NO.", pos = (0,0.2), height=0.07)
# probe_confidence = visual.TextStim(win, text = "Are you confident about your answer? Press Y for YES or N for NO.", pos = (0,0.2), height=0.07)
# probe_content_1 = visual.TextStim(win, text = "Were these thoughts about the task? Press Y for YES or N for NO.", pos = (0,0.2), height=0.07)
# probe_content_2 = visual.TextStim(win, text = "Were they about sensations (e.g. itching, hunger etc.) or external distractions like sounds? Press Y for YES or N for NO.", pos = (0,0.2), height=0.07)
# probe_intention= visual.TextStim(win, text = "Did you deliberately engage in these thoughts? Press Y for YES or N for NO.", pos = (0,0.2), height=0.07)

probe_task=LikertScale(win, 3,
	instruction_text=u"Which sentence best describes your state prior to this probe? Use keys 1 to 3 to respond.",
	scale_labels=["On task", "Off task,\nbut trying to concetrate", "Off task, \nand not trying to concentrate"])

probe_confidence=LikertScale(win, 5,
	instruction_text=u"How confident are you about your answer? Use keys 1 to 6 to respond.",
	scale_labels=["Not at all confident", "", "", "", "Very confident"])

task_stimulus=visual.TextStim(win=win, ori=0, name='text',
	text=u'+',    font='Arial',
	pos=[0, 0], height=0.15, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

thankyou=visual.TextStim(win=win, ori=0, name='text',
	text=u'All done! Thank you!',    font='Arial',
	pos=[0, 0], height=0.15, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

def waitforkey():
	while 1:
		keys=event.getKeys()
		if quit_button in keys:
			sys.exit()
		elif len(keys)>0:
			break

def show_probe(probe):
	probe.show_arrow=False
	while(1):
		probe.draw()
		win.flip()
		keys=event.getKeys()
		if len(set(keys) & set(probe_keys))>0:
			k=int(list(set(keys) & set(probe_keys))[0])-1
			probe.set_arrow(k)
			probe.draw()
			win.flip()
			time.sleep(1.0)
			probe.show_arrow=False
			break
		elif quit_button in keys:
			sys.exit()
	return probe.current_pos
	
# def show_probe(probe):
#     while(1):
#         probe.draw()
#         win.flip()
#         event.waitKeys
#         keys=event.getKeys()
#         if key_yes in keys:
#             return 1
#             break
#         elif key_no in keys:
#             return 0
#             break
#         elif quit_button in keys:
#             sys.exit()
	
with open(datafile, "w") as f:
	f.write("# %s\n"%(str(expInfo)))
	f.write("subj,trial,time,stimulus,response\n")
	
task_clock = core.Clock()
trial_clock = core.Clock()
metronome_sound = sound.Sound('A', secs=0.075)
metronome_sound.setVolume(1)

# first instructions
instruction1.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

# first instructions part B
instruction1b.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

# first instructions part C
instruction1c.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

# first instructions part D
instruction1d.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

# first instructions part F
instruction1f.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

def add_countdown_timer(duration, message):
	timer = core.CountdownTimer(duration)
	message = visual.TextStim(win, text = message, pos = (0,0.2), height=0.07)
	while timer.getTime() > 0:
		message.draw()
		countdown = visual.TextStim(win, round(timer.getTime(), 0))
		countdown.draw()
		win.flip()

##############################################3
## Training
##############################################3

if expInfo["session"]=="training":
	training_session_starts.draw()
	win.flip()
	time.sleep(2)
	event.getKeys()
	waitforkey()
	add_countdown_timer(5, "The training starts in...")

	repeat_training=True
	while repeat_training==True:
		# stimulus shown during auditory beeps
		task_stimulus.draw()
		win.flip()

		time.sleep(0.5)
		event.getKeys()

		task_clock.reset()
		for trial in range(n_trials_training_session):
			trial_clock.reset()
			metronome_sound.play()
			while 1:
				current_time=trial_clock.getTime()
				keys=event.getKeys()
				if quit_button in keys:
					sys.exit()
				if current_time>ISI:
					#print current_time
					break

		response_task = show_probe(probe_task)
		response_confidence = show_probe(probe_confidence)
		
		## ask for repeating the training
		training_repeat.draw()
		win.flip()
		time.sleep(sleeptime)
		event.getKeys()

		while 1:
			keys=event.getKeys()
			if key_no in keys:
				repeat_training=False
				break
			elif key_yes in keys:
				repeat_training=True
				add_countdown_timer(5, "Place your index fingers on S and L.\nThe training restarts in...")
				break
			elif quit_button in keys:
				sys.exit()


##############################################3
## Experiment starts
##############################################3
if expInfo["session"] in ["baseline", "stimulation"]:
	real_experiment_starts.draw()
	win.flip()
	time.sleep(sleeptime)
	event.getKeys()
	waitforkey()
	add_countdown_timer(5, "The experiment starts in...")

	# stimulus shown during auditory beeps
	task_stimulus.draw()
	win.flip()

	time.sleep(0.5)
	f=open(datafile, "a")

	# official session start
	task_clock.reset()

	for trial in range(ntrials):
		trial_clock.reset()

		if trial not in probe_trials:
			metronome_sound.play()
			logtext="{subj},{trial},{time},{type},{response}\n".format( \
				trial=trial,\
				subj=expInfo['participant'], \
				type="stimulus", response="", \
				time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			while 1:
				current_time=trial_clock.getTime()
				keys=event.getKeys()
				if quit_button in keys:
					sys.exit()
				if len(keys)>0:
					logtext="{subj},{trial},{time},{type},{response}\n".format( \
						trial=trial,\
						subj=expInfo['participant'], \
						type="tap", response=keys[0], \
						time="%.10f"%(task_clock.getTime()))
					f.write(logtext)
					f.flush()

				if current_time>ISI:
					break
		else:
			response_task=show_probe(probe_task)
			logtext="{subj},{trial},{time},{type},{response}\n".format(\
					trial=trial,\
					subj=expInfo['participant'], \
					type="probe_task", response= response_task, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			response_confidence=show_probe(probe_confidence)
			logtext="{subj},{trial},{time},{type},{response}\n".format(\
					trial=trial,\
					subj=expInfo['participant'], \
					type="probe_confidence", response= response_confidence, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			add_countdown_timer(3, "Place your index fingers on S and L. The trial restarts in...")


			task_stimulus.draw()
			win.flip()
			time.sleep(ISI)

#    f.close()

thankyou.draw()
win.flip()
time.sleep(2)
waitforkey()
