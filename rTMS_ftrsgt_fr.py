#!/usr/bin/env python3
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
#import master8 as m
import threading
from pyfirmata import Arduino, util
eeg = False
session_name = "training"
tms_frequency = 6 #### SUBJECT-WISE VAR

## global variables
fullscreen=False
quit_button="escape"
key_left="s"
key_right="l"
probe_keys=["1","2", "3", "4"]
n_trials_training_session=1
ISI = 0.75
sleeptime=0 # 5
stimcolor="white"
probe_freq = "1_probe_min"

## Likert-scale
class LikertScale:
	def __init__(self, win, nposs=4, instruction_text=u"", scale_labels=[]):
		start,end=-.5, .5
		ypad=.15
		instru = visual.TextStim(win=win, ori=0, name='instru',units='norm',
			text=instruction_text,    font='Arial',
			pos=[0, 0.5], height=0.07, wrapWidth=None,
			color='white', colorSpace='rgb', opacity=1,
			depth=0.0)
		self.nposs=nposs
		self.show_arrow=False
		line=visual.Line(win, start=(start, 0.2), end=(end,0.2), units='norm', lineColor=stimcolor, lineWidth=5)
		ticks=start+np.arange(0,nposs)*(end-start)/float(nposs-1)
		poss=[visual.Line(win, start=(tick, .25), end=(tick,ypad), units='norm', lineColor=stimcolor,
						  lineWidth=3) for tick in ticks]
		lab=[visual.TextStim(win, pos=(ticks[i], .1), units='norm', text=scale_labels[i], height=.05, color=stimcolor) for i in range(len(scale_labels))]

		self.arrow_v=0.4*np.array([ [0,0], [.2, .2], [.1, .2], [.1, .5], [-.1, .5], [-.1, .2], [-.2, .2], [0, 0]])
		self.arrow_v[:,1]+=ypad+.08
		self.ticks=ticks
		self.arrow=visual.ShapeStim(win, vertices=self.arrow_v, fillColor=stimcolor, units='norm')

		self.init_random(nposs)

		self.elements=[line]+poss+lab+[instru]

	def init_random(self, nposs):
		## initialize to either 0 or nposs-1
		initial_pos=np.random.randint(0, nposs)
		self.set_arrow(initial_pos)
		return initial_pos
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
#N = baseline
#Ar = active_rhTMS
#Sr = sham_rhTMS
#AAr= active_arrhTMS
#SAr = sham_aarhTMS
expName = 'FT-RSGT'  # from the Builder filename that created this script
expInfo = {"participant": '', "age": '', "sex":["Select", "F", "M"], 'session':["training","N","Ar", "Sr", "AAr", "SAr"], "EEG":["Select", "Yes", "No"], "Block number": '', "duration in min": '', "P.freq":["1: 40-80 s", "2: 20-40 s"]}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False: core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName
if expInfo['session'] == "N":
	session_name = "baseline"

if expInfo["EEG"]=="Yes":
	eeg = True

	def eeg_trigger(pins):
		for pin in pins:
			pin.write(1)
			pin.write(0)

	ArduinoBoard = Arduino('/dev/ttyACM0') # Assigning triggers to pins via Arduino UNO
	start_session_pin=  [ArduinoBoard.get_pin('d:2:o')]
	tone_pin = [ArduinoBoard.get_pin('d:3:o')]
	tms_pin = [ArduinoBoard.get_pin('d:4:o')]
	right_key_pin = [ArduinoBoard.get_pin('d:5:o')]
	left_key_pin = [ArduinoBoard.get_pin('d:6:o')] # S1
	probe_pin = [ArduinoBoard.get_pin('d:7:o')]
	probe_response_pin = [ArduinoBoard.get_pin('d:8:o')]
	end_session_pin = [ArduinoBoard.get_pin('d:9:o')]

if expInfo["session"] !="training":
	session_duration=int(expInfo["duration in min"])*60
	if expInfo["P.freq"] == "1: 40-80 s":
		num_probes = int(expInfo["duration in min"])
		min_probe_interval=30 # in s
		max_probe_interval=60 # in s
	elif expInfo["P.freq"] ==  "2: 20-40 s":
		probe_freq = "2_probes_min"
		num_probes = int(expInfo["duration in min"]) * 2
		min_probe_interval=15 # in s
		max_probe_interval=30 # in s

	ntrials=int(session_duration/ISI)
	probe_times=np.array(np.random.randint(min_probe_interval, max_probe_interval+1, num_probes-1)/ISI, dtype=np.int)
	probe_trials=np.cumsum(np.array(probe_times/sum(probe_times)*(ntrials-20/ISI), dtype=np.int))

	probe_trials=np.append(probe_trials, ntrials)

if expInfo["session"]=="Ar" or expInfo["session"]=="Sr" or expInfo["session"]=="AAr" or expInfo["session"]=="SAr":
	session_duration=int(expInfo["duration in min"])*60
	rhythmic_tms = True
	stim_times = np.append(probe_trials[0], np.diff(probe_trials)) * ISI -5

	def make_interval_array(T, minInterval, maxInterval, frequency = tms_frequency): # generates random intervals for TMS bursts
		interval_array = np.array((np.random.uniform(minInterval, maxInterval)))
		while np.cumsum(interval_array)[-1] + (1/frequency*3) <= T:
				nextInterval = np.random.uniform(minInterval, maxInterval)
				interval_array = np.append(interval_array, nextInterval)
		return interval_array[:-2]

	def generate_random_ipi(n_pulses, frequency = tms_frequency):
		ipis = np.empty(2)
		for n_ipi in range(n_pulses - 2):
			ipi = np.random.uniform(.025, 1/frequency) #generate a random ipi from 20 ms to 1/frequency.
			while ipi > 1/frequency - .010 and ipi < 1/frequency + .010: #check whether the generated ipi falls within the range of periods corresponding to the frequency of the rhythmic condition (highly unlikely). added 10 ms on each side to make the IPI very different from 1/frequency
				ipi = np.random.uniform(.025, 1/frequency + .003)
			ipis[n_ipi] = ipi
		ipis = np.append(ipis, 1/frequency *(n_pulses-1) - sum(ipis))
		print(len(ipis))
		print(ipis)
		 # append the last ipi so that the sum of ipi equates to the duration of the burst in the rhythmic condition
		return(ipis)

	pulse_intervals = []# Create random intervals between 3 and 5 secs for pulses. They are predefined for the entire experiment
	for task_period in stim_times:
		pulse_intervals.append(make_interval_array(task_period, 3, 5)) # a list of arrays containing intervals: each array corresponds to the period before the following probe
	#TMS = m.Master8('/dev/ttyUSB0')
	#TMS.changeChannelMode(1, "G")
	if expInfo["session"]=="Ar":
		session_name = "active_rhTMS"
	elif expInfo["session"]=="Sr":
		session_name = "sham_rhTMS"
	elif expInfo["session"]=="SAr" or expInfo["session"]=="AAr":
		rhythmic_tms = False
		if expInfo["session"]=="SAr":
			session_name = "sham_arrhTMS"
		elif expInfo["session"]=="AAr":
			session_name = "active_arrhTMS"

	def rTMS(interval_array, n_pulses, rhythmic, current_task_time, outputFile, participant, eeg = eeg, frequency = tms_frequency):
		pulse_num = 1
		TMSclock = core.Clock()
		TMSclock.add(-1 * current_task_time)
		for interval in interval_array:
			time.sleep(interval - .001) #1 ms to send the trigger
			ipis = np.full(3, 1/frequency)
			if rhythmic == False:
				ipis = generate_random_ipi(4)
			for ipi in ipis:
				eeg_trigger(tms_pin)
				#tms.trigger(1)
				#if eeg == True:
					#eeg_trigger(tms_pin)
				logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format( \
						condition = condition, \
						subj=expInfo['participant'], \
						age=expInfo['age'], \
						sex=expInfo['sex'], \
						block_num=int(expInfo['Block number']), \
						EEG = eeg, \
						probe_freq = probe_freq, \
						trial=pulse_num,\
						time="%.10f"%(TMSclock.getTime()), \
						stimulus="pulse", \
						response = "NA")
				f.write(logtext)
				f.flush()
				pulse_num += 1
				time.sleep(ipi)
			eeg_trigger(tms_pin)
			#tms.trigger(1)
			pulse_num += 1
			#if eeg == True:
				#eeg_trigger(tms_pin)
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format( \
						condition = condition, \
						subj=expInfo['participant'], \
						age=expInfo['age'], \
						sex=expInfo['sex'], \
						block_num=int(expInfo['Block number']), \
						EEG = eeg, \
						probe_freq = probe_freq, \
						trial=pulse_num,\
						time="%.10f"%(TMSclock.getTime()), \
						stimulus="pulse", \
						response = "NA")
			f.write(logtext)
			f.flush()


filename =  thisDir+ "/data/%s_%s_%s_%s_%s_%s" %(expInfo['participant'], session_name, expInfo['Block number'],probe_freq, expName, expInfo['date'])
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
instruction_concepts_1 = visual.TextStim(win=win, ori=0, name='text',
	text=u"L???exp??rience ?? laquelle vous participez a pour but d?????tudier les diff??rentes formes du vagabondage mental. Celui-ci se rapporte au flux de nos pens??es lorsqu???elles s?????chappent vers autre chose que l???activit?? en cours. Un exemple courant est lorsqu???on laisse libre cours ?? ses pens??es tout en regardant par la fen??tre dans le bus ou le train, ou lorsque l???on se voit forc?? de relire un passage d???un texte car notre attention a diverg??.\n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction_concepts_2 = visual.TextStim(win=win, ori=0, name='text',
	text=u"De mani??re g??n??rale, le vagabondage mental survient de mani??re spontan??e mais parfois celui-ci peut ??tre volontairement recherch?? et entrepris.\nPar exemple, lorsque l'on assiste ?? une pr??sentation ennuyeuse et que l???on pr??f??re penser au d??ner de ce soir ou ?? cette amie que l???on voulait rappeler. Ce vagabondage mental dit ???intentionnel??? survient lorsque l???on d??cide de poursuivre un fil de pens??es d??connect?? de l???activit?? en cours alors que le vagadondage mental ???spontan????? correspond aux situations lors desquelles notre esprit d??vie de l???activit?? en cours sans que l'on s???en aper??oive.\n\n Appuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Placez votre index de la main gauche sur la touche S du clavier et votre index de la main droite sur la touche L du clavier. Pendant l???exp??rience, vous entendrez une tonalit?? ??mise ?? un rythme fixe. ?? chaque tonalit?? vous devrez presser soit ?? gauche (touche S) soit ?? droite (touche L). Vous ne pouvez cliquer qu???UNE SEULE touche ?? la fois. Il est important que vos clics individuels soient synchronis??s avec le rythme de la tonalit?? aussi pr??cis??ment que possible. \n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1b = visual.TextStim(win=win, ori=0, name='text', #Talk about this at the meeting
	text=u"Votre t??che principale consiste ?? rendre la s??quence de vos clics individuels aussi irr??guli??re que possible. Autrement dit essayez de rendre chaque clic aussi impr??visible que possible. Par exemple : ???gauche-droite-gauche-droite-gauche-droite??? est plus pr??visible que ???gauche-gauche-droite-gauche-droite-droite???. \nCes instructions sont critiques pour la bonne r??alisation de la t??che. Si vous n?????tes pas certain de les avoir comprises n???h??sitez pas ?? solliciter l???exp??rimentateur. \n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1c = visual.TextStim(win=win, ori=0, name='text', #Talk about this at the meeting
	text=u"Essayez de rester aussi concentr?? sur la t??che que vous le pouvez tout au long de l???exp??rience. Pour r??pondre, d??placez le curseur vers la gauche et la droite en utilisant les m??mes touches que pour la t??che (S et L). Pour valider votre choix, appuyez ensuite sur la touche ???ESPACE???.\n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

# instruction1d = visual.TextStim(win=win, ori=0, name='text',
# 	text="La premi??re question vous demandera d'??valuer votre ??tat d'esprit avant l'apparition de la question. Vous aurez ?? choisir un score sur une ??chelle de 1 ('compl??tement concentr?? sur la t??che') ?? 4 ('compl??tement d??concentr?? de la t??che'). Il vous sera ensuite demand?? d'??laborer. \n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
# 	pos=[0, 0], height=0.07, wrapWidth=None,
# 	color='white', colorSpace='rgb', opacity=1,
# 	depth=0.0)

instruction1d = visual.TextStim(win=win, ori=0, name='text',
	text=u"Il est important de souligner qu???il n???y a ni de bonnes ni de mauvaises r??ponses, et qu???elles n???ont aucune cons??quence pour vous, veuillez donc r??pondre aussi honn??tement que possible. \n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1e = visual.TextStim(win=win, ori=0, name='text',
	text=u"Il y aura une croix sur l?????cran en face de vous pendant l???exp??rience, veuillez garder votre regard fix?? sur cette croix tout au long de l???exp??rience. \n\nAppuyez n'importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

instruction1f = visual.TextStim(win=win, ori=0, name='text',
	text=u"En r??sum??: Gardez votre regard fix?? sur la croix; essayez de presser soit ?? gauche soit ?? droite de mani??re impr??visible et synchronis??e avec chaque tonalit??; r??pondez aux questions quand elles apparaissent du mieux que vous le pouvez. Si vous avez quelconque question par rapport ?? l???exp??rience, veuillez appeler l???exp??rimentateur et leur en faire part maintenant. \n\nSinon, appuyez n???importe quelle touche pour continuer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

training_session_starts=visual.TextStim(win=win, ori=0, name='text',
	text=u"L'exp??rience commence avec un entra??nement.\n\nAppuyez n'importe quelle touche pour commencer.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)
training_repeat=visual.TextStim(win=win, ori=0, name='text',
	text=u"Souhaitez-vous une autre session d???entra??nement ? \n\nAppuyez S (gauche) pour OUI et L (droite) pour NON",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

real_experiment_starts=visual.TextStim(win=win, ori=0, name='text',
	text=u"La v??ritable exp??rience commence maintenant.\n Si vous avez quelconque question, veuillez appeler l'exp??rimentateur.\n Sinon, appuyez n'importe quelle touche pour commencer l'exp??rience.",    font='Arial',
	pos=[0, 0], height=0.07, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

### PROBES ###

probe_task=LikertScale(win, 4,
	instruction_text=u"Juste avant l???interruption, votre attention ??tait: \n",
	scale_labels=["Enti??rement HORS t??che", "", "", "Enti??rement SUR la t??che"])

probe_task_instruction_1 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 1 ??? Enti??rement hors t??che ??,\n cela signifie que vous pensiez\n ?? d???autres choses\n (r??verie, souvenirs,\n planification future, amis, etc.).",    font='Arial',
	pos=[-.5, -.2], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_task_instruction_2 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 4 ??? Enti??rement sur la t??che ??,\n cela signifie que vous ??tiez\n concentr?? sur la t??che\n (sur quels boutons vous allez appuyer,\n sur quels boutons vous avez appuy??,\n et ?? quel rythme, etc.).",    font='Arial',
	pos=[.5, -.23], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_instruction_confirm = visual.TextStim(win=win, ori=0, name='text',
	text=u"Confirmez votre choix en appuyant ESPACE.",    font='Arial',
	pos=[0, -.8], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_intention=LikertScale(win, 4,
	instruction_text=u"Comment qualifieriez-vous la nature de votre attention ?\n",
	scale_labels=["Compl??tement INVOLONTAIRE", "", "", "Compl??tement VOLONTAIRE"])

probe_intention_instruction_1 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 1 ??? Compl??tement INVOLONTAIRE ??,\n cela signifie que votre esprit\n divaguait sans votre contr??le\n (vos pens??es se sont d??plac??es\n spontan??ment vers un examen\n que vous aurez bient??t\n ou votre attention a\n ??t?? distraite par un son).",    font='Arial',
	pos=[-.5, -.3], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_intention_instruction_2 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 4 ??? Compl??tement VOLONTAIRE ??,\n cela signifie que vous pensiez\n volontairement ?? quelque chose,\n que ce soit en lien avec la t??che\n ou non (vous comptiez le nombre\n d???appuis sur les boutons,\n ou vous vous disiez que\n vous ??tiez lass?? de la t??che,\n et que vous pr??f??reriez penser ?? ce\n que vous ferez plus tard).",    font='Arial',
	pos=[.5, -.37], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_somnolence=LikertScale(win, 4,
	instruction_text=u"Comment vous sentez-vous ? \n\n",
	scale_labels=["Tr??s SOMNOLENT", "", "", "Tr??s ALERTE"])

probe_somnolence_instruction_1 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 1 ??? tr??s SOMNOLENT ??,\n cela signifie que vous avez peine ??\n garder les yeux ouverts\n  et que vous vous ??tes assoupis quelques instants.",    font='Arial',
		pos=[-.5, -.25], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

probe_somnolence_instruction_2 = visual.TextStim(win=win, ori=0, name='text',
	text=u"Si vous r??pondez ?? 4 ??? tr??s ALERTE ??,\n cela signifie que vous ??tes sur le qui-vive.",    font='Arial',
		pos=[.5, -.17], height=0.06, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

# probe_intention=LikertScale(win, 2,
# 	instruction_text=u"Did you intend to stay on task? Use keys 1 or 2 to respond.",
# 	scale_labels=["no", "yes"])
#
# probe_distraction=LikertScale(win, 2,
# 	instruction_text=u"Were you distracted by your surroundings? Use keys 1 or 2 to respond.",
# 	scale_labels=["no", "yes"])

task_stimulus=visual.TextStim(win=win, ori=0, name='text',
	text=u'+',    font='Arial',
	pos=[0, 0], height=0.15, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

thankyou=visual.TextStim(win=win, ori=0, name='text',
	text=u"??a y est ! Merci !",    font='Arial',
	pos=[0, 0], height=0.15, wrapWidth=None,
	color='white', colorSpace='rgb', opacity=1,
	depth=0.0)

def show_probe(probe, probe_instruction_1, probe_instruction_2, instruction_confirm, nposs, pin = None, eeg = eeg):
	position = probe.init_random(nposs)
	probe.show_arrow=True #when True, the arrow appears above the last tick
	if eeg == True:
		eeg_trigger(pin)
	while(1):
		probe.draw()
		probe_instruction_1.draw()
		probe_instruction_2.draw()
		instruction_confirm.draw()
		win.flip()
		keys=event.getKeys()
		if len(set(keys))>0:
			if "space" not in keys:
				if (key_right in keys and position < nposs-1):
					if eeg == True:
						eeg_trigger(right_key_pin)
					position +=1
					probe.set_arrow(position)
				elif (key_left in keys and position > 0):
					if eeg == True:
						eeg_trigger(left_key_pin)
					position -=1
					probe.set_arrow(position)
				elif quit_button in keys:
					sys.exit()
			else:
				if eeg == True:
					eeg_trigger(probe_response_pin)
				return position
				probe.draw()
				win.flip()
				time.sleep(1.0)



def waitforkey():
	while 1:
		keys=event.getKeys()
		if quit_button in keys:
			sys.exit()
		elif len(keys)>0:
			break


task_clock = core.Clock()
trial_clock = core.Clock()
metronome_sound = sound.Sound('A', secs=0.075)
metronome_sound.setVolume(1)

event.Mouse(visible=0)

# Instructions explaining basic concepts
instruction_concepts_1.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

instruction_concepts_2.draw()
win.flip()
time.sleep(sleeptime)
event.getKeys()
waitforkey()

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

# first instructions part E
instruction1e.draw()
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

condition = session_name + "_" + expInfo["Block number"]
##############################################3
## Training
##############################################3

if expInfo["session"]=="training":
	with open(datafile, "w") as f:
		f.write("# %s\n"%(str(expInfo)))
		f.write("condition, subj, age,sex,block_num,EEG,trial,time, stimulus, response\n")
	n_trials_training_session = 20
	training_session_starts.draw()
	win.flip()
	time.sleep(2)
	event.getKeys()
	waitforkey()
	add_countdown_timer(3, "L'entra??nement commence dans...")

	repeat_training=True
	f=open(datafile, "a")
	while repeat_training==True:
		# stimulus shown during auditory beeps
		task_stimulus.draw()
		win.flip()
		event.getKeys()
		time.sleep(0.5)

		task_clock.reset()
		for trial in range(n_trials_training_session):
			trial_clock.reset()
			metronome_sound.play()
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format( \
				condition = condition, \
				trial=trial,\
				subj=expInfo['participant'], \
				age=expInfo['age'], \
				sex=expInfo['sex'], \
				block_num=int(expInfo['Block number']), \
				EEG = eeg, \
				stimulus="stimulus", \
				response="", \
				time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			while 1:
				current_time=trial_clock.getTime()
				keys=event.getKeys()
				if quit_button in keys:
					sys.exit()
				if len(keys) > 0:
					logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format( \
							condition = condition, \
							trial=trial,\
							subj=expInfo['participant'], \
							age=expInfo['age'], \
							sex=expInfo['sex'], \
							block_num=int(expInfo['Block number']), \
							EEG = eeg, \
							stimulus="tap", \
							response=keys[0], \
							time="%.10f"%(task_clock.getTime()))
					f.write(logtext)
					f.flush()
				if current_time>ISI:
					break
		response_task = show_probe(probe_task, probe_task_instruction_1,probe_task_instruction_2,  probe_instruction_confirm, nposs = 4)
		logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					stimulus="probe_task", \
					response= response_task, \
					time="%.10f"%(task_clock.getTime()))
		f.write(logtext)
		f.flush()
		response_intention = show_probe(probe_intention, probe_intention_instruction_1,probe_intention_instruction_2,  probe_instruction_confirm,  nposs = 4)
		logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					stimulus="probe_intention", \
					response= response_intention, \
					time="%.10f"%(task_clock.getTime()))
		f.write(logtext)
		f.flush()
# 		response_content = show_probe(probe_content, probe_content_instruction, nposs = 4)
# 		logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format(\
# 					condition = condition, \
# 					trial=trial,\
# 					subj=expInfo['participant'], \
# 					age=expInfo['age'], \
# 					sex=expInfo['sex'], \
# 					block_num=int(expInfo['Block number']), \
# 					EEG = eeg, \
# 					stimulus="probe_content", \
# 					response= response_content, \
# 					time="%.10f"%(task_clock.getTime()))
# 		f.write(logtext)
# 		f.flush()
		response_somnolence = show_probe(probe_somnolence, probe_somnolence_instruction_1,probe_somnolence_instruction_2, probe_instruction_confirm, nposs = 4)
		logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					stimulus="probe_somnolence", \
					response= response_somnolence, \
					time="%.10f"%(task_clock.getTime()))
		f.write(logtext)
		f.flush()

		## ask for repeating the training
		training_repeat.draw()
		win.flip()
		time.sleep(sleeptime)
		event.getKeys()

		while 1:
			keys=event.getKeys()
			if key_right in keys:
				repeat_training=False
				break
			elif key_left in keys:
				repeat_left=True
				break
			elif quit_button in keys:
				sys.exit()

##############################################3
## Experiment starts
##############################################3
if expInfo["session"] in ["N","Ar", "Sr", "AAr", "SAr"]:
	with open(datafile, "w") as f:
		f.write("# %s\n"%(str(expInfo)))
		f.write("condition,subj, age,sex,block_num,EEG,probe_freq,trial,time, stimulus, response\n")
	real_experiment_starts.draw()
	win.flip()
	time.sleep(sleeptime)
	event.getKeys()
	waitforkey()
	# stimulus shown during auditory beeps
	if eeg == True:
		eeg_trigger(start_session_pin)
	task_stimulus.draw()
	win.flip()
	time.sleep(0.5)
	f=open(datafile, "a")

	# official session start
	task_clock.reset()
	if 	expInfo["session"]=="Ar" or expInfo["session"]=="Sr" or expInfo["session"]=="AAr" or expInfo["session"]=="SAr":
		rTMS_interval_index = 1
		if __name__ == "__main__":
			rTMS_Thread = threading.Thread(target=rTMS, args=(pulse_intervals[0], 4, rhythmic_tms, task_clock.getTime(), datafile, expInfo["participant"]))
			rTMS_Thread.start()
	for trial in range(ntrials):
		trial_clock.reset()

		if trial not in probe_trials:
			metronome_sound.play()
			if eeg == True:
				eeg_trigger(tone_pin)
			stimulus_time = task_clock.getTime()
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format( \
				condition = condition, \
				trial=trial,\
				subj=expInfo['participant'], \
				age=expInfo['age'], \
				sex=expInfo['sex'], \
				block_num=int(expInfo['Block number']), \
				EEG = eeg, \
				probe_freq = probe_freq, \
				stimulus="stimulus", \
				response="", \
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
					logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format( \
						condition=condition, \
						trial=trial, \
						subj=expInfo['participant'], \
						age=expInfo['age'], \
						sex=expInfo['sex'], \
						block_num=int(expInfo['Block number']), \
						EEG = eeg, \
						probe_freq = probe_freq, \
						stimulus="tap", \
						response=keys[0], \
						time="%.10f"%(task_clock.getTime()))
					f.write(logtext)
					f.flush()

				if current_time>ISI:
					break
		else:
			if eeg == True:
				response_task=show_probe(probe_task,  probe_task_instruction_1,probe_task_instruction_2,  probe_instruction_confirm, nposs = 4, pin = probe_pin)
			else:
				response_task=show_probe(probe_task, probe_task_instruction_1,probe_task_instruction_2,  probe_instruction_confirm, nposs = 4)
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					probe_freq = probe_freq, \
					stimulus="probe_task", \
					response= response_task, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			if eeg == True:
				response_intention=show_probe(probe_intention, probe_intention_instruction_1,probe_intention_instruction_2,  probe_instruction_confirm, nposs = 4, pin = probe_pin)
			else:
				response_intention=show_probe(probe_intention,  probe_intention_instruction_1,probe_intention_instruction_2,  probe_instruction_confirm, nposs = 4)
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					probe_freq = probe_freq, \
					stimulus="probe_intention", \
					response= response_intention, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			if eeg == True:
				response_somnolence=show_probe(probe_somnolence, probe_somnolence_instruction_1,probe_somnolence_instruction_2,  probe_instruction_confirm, nposs = 4, pin = probe_pin)
			else:
				response_somnolence=show_probe(probe_somnolence, probe_somnolence_instruction_1,probe_somnolence_instruction_2,  probe_instruction_confirm, nposs = 4)
			logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
					condition = condition, \
					trial=trial,\
					subj=expInfo['participant'], \
					age=expInfo['age'], \
					sex=expInfo['sex'], \
					block_num=int(expInfo['Block number']), \
					EEG = eeg, \
					probe_freq = probe_freq, \
					stimulus="probe_somnolence", \
					response= response_somnolence, \
					time="%.10f"%(task_clock.getTime()))
			f.write(logtext)
			f.flush()
			if 	(expInfo["session"]=="Ar" or expInfo["session"]=="Sr" or expInfo["session"]=="AAr" or expInfo["session"]=="SAr" and rTMS_interval_index < len(pulse_intervals)):
				if __name__ == "__main__":
					rTMS_Thread = threading.Thread(target=rTMS, args=(pulse_intervals[rTMS_interval_index], 4, rhythmic_tms, task_clock.getTime(), datafile, expInfo['Block number']))
					rTMS_Thread.start()
				task_stimulus.draw()
				win.flip()
				time.sleep(ISI)
				rTMS_interval_index += 1
			else:
				task_stimulus.draw()
				win.flip()
				time.sleep(ISI)

	if eeg == True:
		response_task=show_probe(probe_task, probe_task_instruction_1,probe_task_instruction_2,  probe_instruction_confirm,nposs = 4, pin = probe_pin)
	else:
		response_task=show_probe(probe_task, probe_task_instruction_1,probe_task_instruction_2,  probe_instruction_confirm,nposs = 4)
	logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
						condition = condition, \
						trial=ntrials,\
						subj=expInfo['participant'], \
						age=expInfo['age'], \
						sex=expInfo['sex'], \
						block_num=int(expInfo['Block number']), \
						EEG = eeg, \
						probe_freq = probe_freq, \
						stimulus="probe_task", \
						response= response_task, \
						time="%.10f"%(task_clock.getTime()))
	f.write(logtext)
	f.flush()
	if eeg == True:
		response_intention=show_probe(probe_intention,  probe_intention_instruction_1,probe_intention_instruction_2,  probe_instruction_confirm,nposs = 4, pin = probe_pin)
	else:
		response_intention=show_probe(probe_intention,  probe_intention_instruction_1,probe_intention_instruction_2,  probe_instruction_confirm, nposs = 4)
	logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
						condition = condition, \
						trial=ntrials,\
						subj=expInfo['participant'], \
						age=expInfo['age'], \
						sex=expInfo['sex'], \
						block_num=int(expInfo['Block number']), \
						EEG = eeg, \
						probe_freq = probe_freq, \
						stimulus="probe_intention", \
						response= response_intention, \
						time="%.10f"%(task_clock.getTime()))
	f.write(logtext)
	f.flush()
	if eeg == True:
		response_somnolence=show_probe(probe_somnolence, probe_somnolence_instruction_1,probe_somnolence_instruction_2,  probe_instruction_confirm, nposs = 4, pin = probe_pin)
	else:
		response_somnolence=show_probe(probe_somnolence, probe_somnolence_instruction_1,probe_somnolence_instruction_2,  probe_instruction_confirm, nposs = 4)
	logtext="{condition},{subj},{age},{sex},{block_num},{EEG},{probe_freq},{trial},{time},{stimulus},{response}\n".format(\
				condition = condition, \
				trial=trial,\
				subj=expInfo['participant'], \
				age=expInfo['age'], \
				sex=expInfo['sex'], \
				block_num=int(expInfo['Block number']), \
				EEG = eeg, \
				probe_freq = probe_freq, \
				stimulus="probe_somnolence", \
				response= response_somnolence, \
				time="%.10f"%(task_clock.getTime()))
	f.write(logtext)
	f.flush()

thankyou.draw()
win.flip()
if eeg == True:
	eeg_trigger(end_session_pin)
time.sleep(2)
waitforkey()
