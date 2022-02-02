#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import division  # so that 1/3=0.333 instead of 1/3=0
from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']
from psychopy import visual, core, data, event, logging, sound, gui, clock, keyboard as kb
from psychopy.constants import *  # things like STARTED, FINISHED
import numpy as np  # whole numpy lib is available, prepend 'np.'
import time
from numpy import sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray, round
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys
import master8 as m
import threading
from pyfirmata import Arduino, util

eeg = False

def eeg_trigger(pins):
	for pin in pins:
		pin.write(1)
	for pin in pins:
		pin.write(0)

## global variables
fullscreen=False
quit_button="escape"
key_no = "n"
key_yes = "y"
key_left="s" 
key_right="l" 
task_probe_keys=["1","2", "3", "4"]
binary_probe_keys = ["1", "2"]
n_trials_training_session=20
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
		try:
			v[:,0]+=self.ticks[pos]
		except:
			pass
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
expName = 'FT-RSGT-rTMS'  # from the Builder filename that created this script
expInfo = {"participant": '', 'session':["training","baseline","rhTMS", "randTMS"], "EEG":["Select", "Yes", "No"]}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False: core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName

## duration for baseline
session_duration=3*60 # in s
num_probes=3

if expInfo["EEG"]=="Yes":
	eeg = True
	ArduinoBoard = Arduino('/dev/ttyACM0') # Assigning triggers to pins via Arduino UNO
	task_start_pin = [ArduinoBoard.get_pin('d:2:o')]
	left_key_pin = [ArduinoBoard.get_pin('d:3:o')] # S1
	right_key_pin = [ArduinoBoard.get_pin('d:4:o')] 
	tms_pin = [ArduinoBoard.get_pin('d:5:o')]
	probe_pin = [ArduinoBoard.get_pin('d:6:o')]
	probe_response_pin_1 = [ArduinoBoard.digital[2], ArduinoBoard.digital[3]]
	probe_response_pin_2 = [ArduinoBoard.digital[3], ArduinoBoard.digital[4]]
	probe_response_pin_3 = [ArduinoBoard.digital[4], ArduinoBoard.digital[5]]
	probe_response_pin_4 = [ArduinoBoard.digital[5], ArduinoBoard.digital[6]]
	tone_pin = [ArduinoBoard.get_pin('d:7:o')]

def make_interval_array(T, minInterval, maxInterval): # generates random intervals for TMS bursts
	interval_array = np.array((np.random.uniform(minInterval, maxInterval)))
	while np.cumsum(interval_array)[-1] +.5 <= T:
			nextInterval = np.random.uniform(minInterval, maxInterval)
			interval_array = np.append(interval_array, nextInterval)
	return interval_array[:-1]

min_probe_interval=30 # in s
max_probe_interval=60 # in s

## randomization

if expInfo["session"]=="rhTMS" or expInfo["session"]=="randTMS":
	rhythmic_tms = True
	session_duration=15*60 # in s
	num_probes=15
	TMS = m.Master8('/dev/ttyUSB0')
	TMS.changeChannelMode(1, "G")
	if expInfo["session"]=="randTMS":
		rhythmic_tms = False

ntrials=int(session_duration/ISI)
probe_times=np.array(np.random.randint(min_probe_interval, max_probe_interval+1, num_probes-1)/ISI, dtype=np.int)
print(probe_times)
probe_trials=np.cumsum(np.array(probe_times/sum(probe_times)*(ntrials-num_probes/ISI), dtype=np.int))
probe_trials=np.append(probe_trials, ntrials)
stim_times = np.append(probe_trials[0], np.diff(probe_trials)) * ISI -5
print(stim_times)

def generate_random_ipi(frequency, n_pulses):
	ipis = np.empty(2)
	for n_ipi in range(n_pulses - 2):
		ipi = np.random.uniform(.025, 1/frequency + .003) #generate a random ipi from 20 ms to [period + 3] ms. 
		while ipi > 1/frequency - .003 and ipi < 1/frequency + .003: #check whether the generated ipi falls within the range of periods corresponding to the frequency of the rhythmic condition (highly unlikely)
			ipi = np.random.uniform(.025, 1/frequency + .003)
		ipis[n_ipi] = ipi
	ipis = np.append(ipis, 1/frequency *(n_pulses-1) - sum(ipis)) # append the last ipi so that the sum of ipi equates to the duration of the burst in the rhythmic condition
	return(ipis)

if expInfo["session"]== "rhTMS" or expInfo["session"]=="randTMS":
	pulse_intervals = []# Create random intervals between 3 and 5 secs for pulses. They are predefined for the entire experiment		
	for task_period in stim_times:
		pulse_intervals.append(make_interval_array(task_period, 3, 5)) # a list of arrays containing intervals: each array corresponds to the period before the following probe
	
def rTMS(tms, interval_array, frequency, n_pulses, rhythmic, current_task_time, outputFile, participant, eeg = eeg):
	pulse_num = 1
	TMSclock = core.Clock()
	TMSclock.add(-1 * current_task_time)
	for interval in interval_array:
		time.sleep(interval - .001) #1 ms to send the trigger to master-8
		ipis = np.full(3, 1/frequency)
		if rhythmic == False:
			ipis = generate_random_ipi(6, 4)
		for ipi in ipis:
			tms.trigger(1)
			if eeg == True:
				eeg_trigger(tms_pin)
			logtext="{subj}, {EEG},{trial},{time},{type},{response}\n".format( \
						subj=participant, \
						EEG = eeg, \
						trial=pulse_num,\
						time="%.10f"%(TMSclock.getTime()), \
						type="pulse", \
						response = "NA")
			f.write(logtext)
			f.flush()
			time.sleep(ipi)
			pulse_num += 1
		tms.trigger(1)
		pulse_num += 1
		if eeg == True:
			eeg_trigger(tms_pin)
		logtext="{subj},{trial},{time},{type},{response}\n".format( \
						trial=pulse_num,\
						subj=participant, \
						time="%.10f"%(TMSclock.getTime()), \
						type="pulse", \
						response = "NA")
		f.write(logtext)
		f.flush()

		
filename =  thisDir+ "/Analyses/data/%s_%s_%s_%s" %(expInfo['participant'], expInfo["session"], expName, expInfo['date'])
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
	text=u'Place your left index finger on S and your right index finger on L.\n Please hold this position during the entire experiment.\n\nDuring the experiment, you will hear a tone playing in a set rhythm.\nYour task is to try and press the buttons in a random sequence of left/right presses to the rhythm of the tone. Try to make this sequence as unpredictable as possible. For example: "left-right-left-right-left" is more predictable than "left-left-right-left-right"\n\nTry to replicate the rhythm of the tone as accurately as possible.\nYou may only press ONE of the buttons at a time.\n\nPress any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1b = visual.TextStim(win=win, ori=0, name='text', #Talk about this at the meeting
	text=u'Try to stay as concentrated on the task as you can throughout the entire experiment. It is however, not unusual for your thoughts to start wandering.\nAt some point, you will be interrupted to answer the questions on the screen relative to your mind-wandering.\n\n Press any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1c = visual.TextStim(win=win, ori=0, name='text',
	text='The first question will ask you to evaluate your state of mind prior to the appearance of the question. You will have to choose a score on the scale of 1 ("completely on-task") to 4 ("completely off-task"). Next, you will be asked whether you intentionally tried to concentrate or not. Finally, you will be asked to evaluate the degree of confidence of your answers on the scale on 1 to 4. \n\n Press any key to continue.',    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)
	
instruction1d = visual.TextStim(win=win, ori=0, name='text',
 #    text=u'Importantly, mind-wandering can occur either because you INTENTIONALLY decided to think about things that are unrelated to the task, OR because your thoughts UNINTENTIONALLY drifted away to task-unrelated thoughts, despite your best intentions to focus on the task. \n\nTherefore, if you want to answer MIND WANDERING, you have to choose if it was “INTENTIONALLY” or “UNINTENTIONALLY”.\n\nNote that there is no right or wrong answer and that there will not be any consequences related to your answers, so please just be honest when answering those questions.\n\nPress any button to continue.',    font='Arial',
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

probe_task=LikertScale(win, 4,
	instruction_text=u"To what extent were your thoughts related to the task? Use keys 1 to 4 to respond.",
	scale_labels=["Not at all", "", "", "Completely"])

probe_intention=LikertScale(win, 2,
	instruction_text=u"Did you intend to stay on task? Use keys 1 or 2 to respond.",
	scale_labels=["no", "yes"])

probe_distraction=LikertScale(win, 2,
	instruction_text=u"Were you distracted by your surroundings? Use keys 1 or 2 to respond.",
	scale_labels=["no", "yes"])

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

	
def show_probe(probe, probe_keys, eeg = eeg):
	probe.show_arrow=False
	if eeg == True:
		eeg_trigger(probe_pin)
	while(1):
		probe.draw()
		win.flip()
		keys=event.getKeys()
		if len(set(keys) & set(probe_keys))>0:
			if eeg == True:
				if "1" in keys:
					eeg_trigger(probe_response_pin_1)
				elif "2" in keys:
					eeg_trigger(probe_response_pin_2)
				elif "3" in keys:
					eeg_trigger(probe_response_pin_3)
				elif "4" in keys:
					eeg_trigger(probe_response_pin_4)
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
	
with open(datafile, "w") as f:
	f.write("# %s\n"%(str(expInfo)))
	f.write("subj, EEG,trial,time, stimulus, response\n")
	
task_clock = core.Clock()
trial_clock = core.Clock()
metronome_sound = sound.Sound('A', secs=0.075)
metronome_sound.setVolume(1)

# instructions = [instruction1, instruction1b, instruction1c, instruction1d]
# 	
# for i in range(0, len(instructions)):
# 	instructions[i].draw()
# 	win.flip()
# 	keys = kb.getKeys(keyList = ["left", "right"])
# 	if "right" in keys:
# 		i+=1
# 	elif ("left" in keys and i > 0):
# 		i-=1
# 	elif ("left" in keys and i == 0):
# 		pass
		
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
	add_countdown_timer(3, "The training starts in...")

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
					break

		response_task = show_probe(probe_task, task_probe_keys)
		response_intention = show_probe(probe_intention, binary_probe_keys)
		response_distraction = show_probe(probe_distraction, binary_probe_keys)
		
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
				add_countdown_timer(3, "Place your index fingers on S and L.\nThe training restarts in...")
				break
			elif quit_button in keys:
				sys.exit()

##############################################3
## Experiment starts
##############################################3
if expInfo["session"] in ["baseline", "rhTMS", "randTMS"]:
	real_experiment_starts.draw()
	win.flip()
	time.sleep(sleeptime)
	event.getKeys()
	waitforkey()
	# stimulus shown during auditory beeps
	
	task_stimulus.draw()
	if eeg == True:
 		eeg_trigger(task_start_pin)
	win.flip()
	time.sleep(0.5)
	f=open(datafile, "a")

	# official session start
	task_clock.reset()
	if 	expInfo["session"]=="rhTMS" or expInfo["session"]=="randTMS":
		rTMS_interval_index = 1
		if __name__ == "__main__":
			rTMS_Thread = threading.Thread(target=rTMS, args=(TMS, pulse_intervals[0], 6, 4, rhythmic_tms, task_clock.getTime(), datafile, expInfo["participant"]))
			rTMS_Thread.start()
	for trial in range(ntrials):
		trial_clock.reset()

		if trial not in probe_trials:
			metronome_sound.play()
			if eeg == True:
				eeg_trigger(tone_pin)
			stimulus_time = task_clock.getTime()
			logtext="{subj},{EEG},{trial},{time},{type},{response}\n".format( \
				trial=trial,\
				subj=expInfo['participant'], \
				EEG = expInfo['EEG'], \
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
					if eeg == True:
						if key_left in keys:
							eeg_trigger(left_key_pin)
						elif key_right in keys:
							eeg_trigger(right_key_pin)
					logtext="{subj}, {EEG},{trial},{time},{type},{response}\n".format( \
						trial=trial,\
						subj=expInfo['participant'], \
						EEG = expInfo['EEG'], \
						type="tap", response=keys[0], \
						time="%.10f"%(task_clock.getTime()))
					f.write(logtext)
					f.flush()

				if current_time>ISI:
					break
		else:
			response_task=show_probe(probe_task, task_probe_keys)
			logtext="{subj},{EEG},{trial},{time},{type},{response}\n".format(\
					trial=trial,\
					subj=expInfo['participant'], \
					EEG = expInfo['EEG'], \
					type="probe_task", response= response_task, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			response_intention=show_probe(probe_intention, binary_probe_keys)
			logtext="{subj}, {EEG},{trial},{time},{type},{response}\n".format(\
					trial=trial,\
					subj=expInfo['participant'], \
					EEG = expInfo['EEG'], \
					type="probe_intention", response= response_intention, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			response_distraction=show_probe(probe_distraction, binary_probe_keys)
			logtext="{subj}, {EEG},{trial},{time},{type},{response}\n".format(\
					trial=trial,\
					subj=expInfo['participant'], \
					EEG = expInfo['EEG'], \
					type="probe_distraction", response= response_distraction, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			add_countdown_timer(3, "Place your index fingers on S and L. The trial restarts in...")
			if 	(expInfo["session"]=="rhTMS" or expInfo["session"]=="randTMS" and rTMS_interval_index < len(pulse_intervals)):
				if __name__ == "__main__":
					rTMS_Thread = threading.Thread(target=rTMS, args=(TMS, pulse_intervals[rTMS_interval_index], 6, 4, rhythmic_tms, task_clock.getTime(), datafile, expInfo["participant"]))
					rTMS_Thread.start() 
				task_stimulus.draw()
				win.flip()
				time.sleep(ISI)
				rTMS_interval_index += 1
			else:
				task_stimulus.draw()
				win.flip()
				time.sleep(ISI)

thankyou.draw()
win.flip()
time.sleep(2)
waitforkey()
