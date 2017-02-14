#! /usr/bin/python

# -*- coding: utf-8 -*-
#
#    Copyright 2015: Frank Stollmeier
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

__version__ = 1.0

import cv2
import numpy as np
from scipy import ndimage
import threading
import colorsys
import pdb
import time
import io
from multiprocessing import Process, Pipe
from brian import *
from brian.hears import *

import matplotlib
matplotlib.use('pdf') #Actually, we don't need pdf, but it doesn't use gtk which avoids a conflict between GTK2 and GTK3 (matplotlib and opencv) 
import pylab as pl

try:
    #load my dirty hack derived from scikits.audiolab
    from _alsa_backend import AlsaDevice
    ALSA = True
except ImportError, e:
    #warnings.warn("Could not import alsa backend; most probably, "
    #                  "you did not have alsa headers when building audiolab.soundio")
    ALSA = False


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print "Unable to initialize webcam. This can happen if another process is using the webcam."

def find_position(mask):
    labeled_mask,num_label = ndimage.label(mask)
    objects = ndimage.find_objects(labeled_mask)
    object_sizes = [(slice1.stop-slice1.start)*(slice2.stop-slice2.start) for slice1,slice2 in objects]
    biggest_object = objects[np.argmax(object_sizes)]
    x,y = int(0.5*(biggest_object[0].start+biggest_object[0].stop)), int(0.5*(biggest_object[1].start+biggest_object[1].stop))
    return x,y

mouseclick_position = None
def mouse_event(event,x,y,flags,param):
    global mouseclick_position
    if event==cv2.EVENT_LBUTTONDOWN:
        mouseclick_position = np.array([x,y])
        print 'recieved coordinates: ' + repr([x,y])

hue_tolerance = 5
saturation_tolerance = 100
value_tolerance = 100
color1range = []
color2range = []
shape = None
frame_rate = None
shift_color = lambda color,factor: np.array([np.clip(color[0]+factor*hue_tolerance,0,255),np.clip(color[1]+factor*saturation_tolerance,0,255),np.clip(color[2]+factor*value_tolerance,0,255)],dtype=np.uint8)


def calibration():
    '''Show the video from the webcam and set color of the first marker and color of the second marker double clicks'''
    global shape
    global frame_rate
    global color1range
    color1range = []
    global color2range
    color2range = []
    global mouseclick_position
    mouseclick_position = None
    counter = 0
    cv2.namedWindow('calibration')
    def set_hue_tolerance(x):
        global hue_tolerance
        hue_tolerance = x
    def set_saturation_tolerance(x):
        global saturation_tolerance
        saturation_tolerance = x
    def set_value_tolerance(x):
        global value_tolerance
        value_tolerance = x
    cv2.createTrackbar('hue tolerance', 'calibration', 5, 255, set_hue_tolerance)
    cv2.createTrackbar('saturation tolerance', 'calibration', 50, 255, set_saturation_tolerance)
    cv2.createTrackbar('value tolerance', 'calibration', 50, 255, set_value_tolerance)
    print 'Calibration: please click on the object which controls the frequency.'
    cv2.setMouseCallback('Videotheremin',mouse_event)
    time_start = time.time()
    frames = 0
    while True:
        _, frame = cap.read()
        frames += 1
        #Videotheremin window
        cv2.imshow('Videotheremin',frame)
        if mouseclick_position is not None:
            if counter == 0: #set color for marker 1
                x,y = mouseclick_position
                mouseclick_position = None
                hsv1 = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                color1 = hsv1[y][x]
                color1range.append(shift_color(color1,-1))
                color1range.append(shift_color(color1,+1))
                counter += 1
                print 'Please click on the object which controls the amplitude.'
            elif counter == 1: #set color for marker 2
                x,y = mouseclick_position
                mouseclick_position = None
                hsv2 = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                color2 = hsv2[y][x]
                color2range.append(shift_color(color2,-1))
                color2range.append(shift_color(color2,+1))
                counter += 1
            elif counter == 2:
                break
        #calibration window
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if counter == 0:
            mask = hsv
        elif counter == 1:
            lower_color1,upper_color1 = color1range
            mask = cv2.inRange(hsv, lower_color1, upper_color1)
            color1range[0] = shift_color(color1,-1)
            color1range[1] = shift_color(color1,+1)
        elif counter == 2:
            lower_color2,upper_color2 = color2range
            mask = cv2.inRange(hsv, lower_color2, upper_color2)
            color2range[0] = shift_color(color2,-1)
            color2range[1] = shift_color(color2,+1)
        cv2.imshow('calibration', mask)
        #
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            print "calibration failed."
            return False
    frame_rate = frames / float(time.time() - time_start)
    shape = frame.shape
    cv2.destroyWindow('calibration')
    print "calibration complete"
    return True


def capture(overlay = None):
    '''capture one frame, locate the markers and return position'''
    _, frame = cap.read()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_color1,upper_color1 = color1range
    lower_color2,upper_color2 = color2range
    
    # Threshold the HSV image
    mask_color1 = cv2.inRange(hsv, lower_color1, upper_color1)
    mask_color2 = cv2.inRange(hsv, lower_color2, upper_color2)
    #locate markers
    x1,y1 = find_position(mask_color1)
    cv2.circle(frame, (y1, x1), 2, (255, 255, 255), 20)
    x2,y2 = find_position(mask_color2)
    cv2.circle(frame, (y2, x2), 2, (255, 255, 255), 20)
    #display the image
    if overlay is not None:
        weights = np.zeros(frame.shape)
        weights[:,:,0] = weights[:,:,1] = weights[:,:,2] = overlay[:,:,3]/float(255)
        frame = np.array((1-weights)*frame + weights*overlay[:,:,:3], dtype=np.uint8)
    cv2.imshow('Videotheremin',frame)
    k = cv2.waitKey(5) & 0xFF
    return x1,y1,x2,y2,k

class Tracking(threading.Thread):
    def __init__(self, process_coordinates = None):
        cv2.namedWindow('Videotheremin')
        if callable(process_coordinates):
            self.process_coordinates = process_coordinates
        else:
            self.process_coordinates = lambda x1,y1,x2,y2: None
        while not calibration():
            print 'Calibration failed. Try again.'
        print 'measured frame rate: ', frame_rate
        self.overlay_type = 'notes'
        self.overlay = generate_overlay(self.overlay_type)
        threading.Thread.__init__(self)
    def run(self):
        self.time = 0
        while True:
            try:
                x1,y1,x2,y2,key = capture(self.overlay)
                self.process_coordinates(x1,y1,x2,y2)
                self.time += 1
                if key != 255:
                    self.handle_key_event(key)
            except ValueError:
                print "Oh no, I've lost the marker!"
    def handle_key_event(self, key):
        if key == 27: #key 'ESC'
            cv2.destroyWindow('Videotheremin')
            parent_conn.send(('stop',1))
            self.stop()
            return 0
        elif 49 <= key <= 57: #keys '1' - '9'
            index = key - 49
            if index < len(spectra):
                parent_conn.send(('spectrum',spectra[index]))
                print 'chosen spectrum: ' + str(index+1)
            else:
                print 'spectrum %i not defined' %(index+1)
        elif key == 82: #key 'up'
            global echo
            if echo < 1:
                echo = echo + 0.01
                parent_conn.send(('echo', echo))
            print 'echo ' + str(echo)
        elif key == 84: #key 'down'
            global echo
            if echo > 0:
                echo = echo - 0.01
            print 'echo ' + str(echo)
        elif key == 111: #key 'o'
            #toggle overlay type
            if self.overlay_type == 'notes':
                self.overlay_type = 'frequencies'
            else:
                self.overlay_type = 'notes'
            self.overlay = generate_overlay(self.overlay_type)
        elif key == 99: #key 'c'
            while not calibration():
                print 'Calibration failed. Try again.'
        else:
            print key


#spectra are defined by numpy array of shape (2,n) containing the frequencies (relative to the base frequency) and the amplitudes (between 0 and 1).
spectra = []
spectra.append( np.array([[1],[1]]) ) #a sine wave
spectra.append( np.array([np.arange(1,11),np.exp(-1.7*np.arange(10))]) ) #exp decreasing harmonics
spectra.append( np.array([[1,4.0/3.0,5.0/3.0],[1,1,1]]) ) #major chord
spectra.append( np.array([[1,5.0/4.0,5.0/3.0],[1,1,1]]) ) #minor chord


def make_music(conn):
#    init_wave = np.sin(int(5)*2*np.pi*np.linspace(0,1,1024))
#    init_wave = np.zeros(1024)
#    sound = Sound(init_wave)
#    sound.play()
    while True:
        a_sound = vowel('a', duration=1*second)
        a_sound = a_sound.ramped(duration=1*second).ramped(when='offset', duration=1*second)
        a_sound.play()
    #play(init_wave, conn, fs=44100)
    #new:
    #dev = AlsaDevice(fs=44100, nchannels=1)
    #dev.play(spectra[0], conn)

def adjust_sound(x1,y1,x2,y2):
    frequency = frequency_map( y1/float(shape[1]) )
    a_zero = 0.1*shape[0] #below this line the amplitude is zero
    amplitude = np.clip( (shape[0]-x2-a_zero)/float(shape[0]-a_zero), 0, 1)
    parent_conn.send(('frequency, amplitude', (frequency, amplitude)))

def generate_overlay(label = 'notes'):
    dpi = pl.rcParams['savefig.dpi']
    fig = pl.figure(figsize=(shape[1]/float(dpi),shape[0]/float(dpi)))
    pl.plot()
    if label == 'frequencies':
        x_ticks = base_frequency * 2**np.arange(5)
        xt_labels = [str(int(x)) for x in x_ticks]
    elif label == 'notes':
        n = np.arange(88)
        x_ticks = 440 * 2**((n-49)/12.0)
        xt_labels = ['C D EF G A H'[i%12] for i in n]
    pl.xticks(frequency_map_inverse(x_ticks),xt_labels)
    pl.xlim(0,1)
    fig.subplots_adjust(left=0.0, bottom=0.1, top=1, right=1)
    pl.grid(axis='x')
    buf = io.BytesIO()
    pl.savefig(buf, format='png', transparent=True)
    return ndimage.imread(buf)

if __name__ == '__main__':
    
    #definitions
    echo = 0.55 #value between 0 (no reverberation) and 1.0 (infinite reverberation)
    base_frequency = 220 #the lowest frequency
    n_octaves = 4 #the number of octaves above the base_frequency
    frequency_map = lambda y: base_frequency*2**(n_octaves*y) #this function translates the position on the screen (0 to 1) to a frequency
    frequency_map_inverse = lambda f: np.log2(f/base_frequency)/n_octaves #the inverse is required to plot the overlay
    
    #start process to generate the sound
    parent_conn, child_conn = Pipe()
    p = Process(target=make_music, args=(child_conn,))
    p.start()

    #start tracking
    track = Tracking(process_coordinates=adjust_sound)
    track.start()
