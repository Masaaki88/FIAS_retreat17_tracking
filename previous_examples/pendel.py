# -*- coding: utf-8 -*-
#
#    Copyright 2015: Manuel Schottdorf, Frank Stollmeier
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

__version__ = 0.5


import cv2
import numpy as np
from scipy import ndimage
import threading
from matplotlib import animation
import colorsys
import pylab as pl
import pdb
from time import time
pl.ion()

cap = cv2.VideoCapture(1)

def find_position(mask):
    labeled_mask,num_label = ndimage.label(mask)
    objects = ndimage.find_objects(labeled_mask)
    object_sizes = [(slice1.stop-slice1.start)*(slice2.stop-slice2.start) for slice1,slice2 in objects]
    biggest_object = objects[np.argmax(object_sizes)]
    x,y = int(0.5*(biggest_object[0].start+biggest_object[0].stop)), int(0.5*(biggest_object[1].start+biggest_object[1].stop))
    return x,y

positions_for_calibration = []
def set_center_pos(event,x,y,flags,param):
    if event==cv2.EVENT_LBUTTONDBLCLK:
        positions_for_calibration.append(np.array([x,y]))
        print 'recieved coordinates: ' + repr([x,y])

center = np.array([0,0])
roi = [None,None,None,None]
color_tolerance = 5
saturation_tolerance = 100
value_tolerance = 100
t0 = time() #ref time
colors = []
color1range = []
color2range = []
shape = []
frame_rate = [None]
shift_color = lambda color,factor: np.array([np.clip(color[0]+factor*color_tolerance,0,255),np.clip(color[1]+factor*saturation_tolerance,0,255),np.clip(color[2]+factor*value_tolerance,0,255)],dtype=np.uint8)
circle_mask = None
zeroframe = None

def calibration():
    '''Show the video from the webcam and set position of the center, color of the first marker and color of the second marker chosen by the user with three consecutive double clicks'''
    cv2.namedWindow('calibration')
    #reset previous calibartion values
    if len(positions_for_calibration)==2:
        for i in range(2):
            shape.pop()
            positions_for_calibration.pop()
            colors.pop()
            color1range.pop()
            color2range.pop()
    print 'Calibration: please doubleclick on the center, the first marker and the second marker'
    cv2.setMouseCallback('calibration',set_center_pos)
    time_start = time()
    frames = 0
    while True:
        _, frame = cap.read()
        frames += 1
        cv2.imshow('calibration',frame)
        k = cv2.waitKey(5) & 0xFF
        if k == 27:
            break
        if len(positions_for_calibration)==3:
            break
    frame_rate[0] = frames / float(time() - time_start)
    shape.append(frame.shape[0])
    shape.append(frame.shape[1])
    center[0] = positions_for_calibration[0][0]
    center[1] = positions_for_calibration[0][1]
    x,y = positions_for_calibration[1]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color1 = hsv[y][x]
    colors.append(color1)
    color1range.append(shift_color(color1,-1))
    color1range.append(shift_color(color1,+1))
    x,y = positions_for_calibration[2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    color2 = hsv[y][x]
    colors.append(color2)
    color2range.append(shift_color(color2,-1))
    color2range.append(shift_color(color2,+1))
    #select region of interest
    v = np.array([x,y]) - center
    r = np.sqrt(np.dot(v,v))
    r = 1.1 * r
    roi[0] = int(center[0]-r)
    roi[1] = int(center[0]+r)
    roi[2] = int(center[1]-r)
    roi[3] = int(center[1]+r)
    print "calibration complete"
    if np.any(np.array(roi)<0):
        print "warning: chosen ROI exceeds frame", repr(roi)
        croi = np.clip(np.array(roi),0,np.inf)
        roi[0],roi[1],roi[2],roi[3] = int(croi[0]),int(croi[1]),int(croi[2]),int(croi[3])
    cv2.destroyWindow('calibration')
    #circle mask
    global circle_mask
    xc,yc = np.meshgrid(np.arange(frame.shape[0]),np.arange(frame.shape[1]))
    circle_mask = (xc-center[1])**2+(yc-center[0])**2 < r**2
    circle_mask = np.transpose(np.array([circle_mask,circle_mask,circle_mask]))
    global zeroframe 
    zeroframe = np.zeros(frame.shape,dtype=np.uint8)
    return None

def capture(rotate_frames, show_roi):
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
    #pdb.set_trace()
    frame = np.where(circle_mask,frame,zeroframe)
    if rotate_frames:
        phi1,phi2 = to_phase_coordinate(np.array([y1,x1]),np.array([y2,x2]))
        R = cv2.getRotationMatrix2D(tuple(center),-phi1*180/np.pi,1)
        frame = cv2.warpAffine(frame,R,(frame.shape[1],frame.shape[0]))
    if show_roi:
        frame = frame[roi[2]:roi[3],roi[0]:roi[1]]
    cv2.imshow('tracker',frame)
    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        return x1,y1,x2,y2,True
    else:
        return x1,y1,x2,y2,False

def to_phase_coordinate(p1,p2):
    '''convert positions p1 and p2 to angles phi1 and ph2'''
    v1 = p1-center
    v2 = p2-p1
    phi1 = np.arctan2(v1[0],float(v1[1]))
    phi2 = np.arctan2(v2[0],float(v2[1])) + phi1
    return phi1,phi2

class Tracking(threading.Thread):
    def __init__(self, rotate_frames = False, show_roi = True):
        cv2.namedWindow('tracker')
        self.rotate_frames = rotate_frames
        self.show_roi = show_roi
        threading.Thread.__init__(self)
    def run(self):
        self.time = 0
        self.time_sec = np.zeros(1000000)
        self.trajectory1 = np.zeros((2,1000000))
        self.trajectory2 = np.zeros((2,1000000))
        self.ptrajectory1 = np.zeros((2,1000000))
        self.ptrajectory2 = np.zeros((2,1000000))
        self.wtrajectory1 = np.zeros((2,1000000))
        self.wtrajectory2 = np.zeros((2,1000000))
        self.t_old = 0
        while True:
	    try:
	        x1,y1,x2,y2,end = capture(self.rotate_frames, self.show_roi)
                p1, p2 = to_phase_coordinate(np.array([x1, y1]),np.array([x2,y2]))
                self.ptrajectory1[:,self.time] = p1
                self.ptrajectory2[:,self.time] = p2
                self.wtrajectory1[:,self.time] = (p1 - self.ptrajectory1[:,(self.time-1)]) / (time() - self.t_old)
                self.wtrajectory2[:,self.time] = (p2 - self.ptrajectory2[:,(self.time-1)]) / (time() - self.t_old)
                self.trajectory1[:,self.time] = y1,shape[0]-x1
                self.trajectory2[:,self.time] = y2,shape[0]-x2
                self.time_sec[self.time] = time() - t0
                self.time += 1
                self.t_old = time()
                if end:
                    cv2.destroyWindow('tracker')
                    break
            except ValueError:
	        print "Oh no, I've lost the marker!"

class Plot(object):
    def __init__(self, track, frames=1000,interval=100):
        self.fig = pl.figure()
        ax = self.fig.add_subplot(231, autoscale_on=False, xlim=(0,shape[1]), ylim=(0,shape[0]))
	ax.grid()
	line0, = ax.plot([center[0]],[shape[0]-center[1]],'go',markersize=5)
        line1, = ax.plot([np.nan],[np.nan],'-', color = colorsys.hsv_to_rgb(*(colors[0]/255.0)))
        line1a, = ax.plot([np.nan],[np.nan],'o', color = colorsys.hsv_to_rgb(*(colors[1]/255.0)))
        line1b, = ax.plot([np.nan],[np.nan],'-', color = colorsys.hsv_to_rgb(*(colors[0]/255.0)))
        line1c, = ax.plot([np.nan],[np.nan],'o', color = colorsys.hsv_to_rgb(*(colors[1]/255.0)))
        
	ax5 = self.fig.add_subplot(232, autoscale_on=False, xlim=(0, 5), ylim=(0, 500))
	ax5.grid()
	line5, = ax5.plot([], [], 'b-', lw=1)
	line5a, = ax5.plot([], [], 'bo', lw=2)
	line5b, = ax5.plot([], [], 'g-', lw=1)
	line5c, = ax5.plot([], [], 'go', lw=2)
	ax5.set_xlabel('Time [sec]')
	ax5.set_ylabel('Position [px]')

	ax6 = self.fig.add_subplot(233, autoscale_on=False, xlim=(0, 15), ylim=(0, 3000))
	ax6.grid()
	line6, = ax6.plot([], [], 'b.', lw=1)
	ax6.set_xlabel('Frequency [Hz]')
	ax6.set_ylabel('Amplitude')
	
	ax2 = self.fig.add_subplot(234, autoscale_on=False, xlim=(0, 500), ylim=(-50, 50))
	ax2.grid()
	line2, = ax2.plot([], [], 'b.', lw=0.5)
	line2a, = ax2.plot([], [], 'ro', lw=2)
	ax2.set_xlabel('x-Pos 1')
	ax2.set_ylabel('Angular Speed 1')

	ax4 = self.fig.add_subplot(235, autoscale_on=False, xlim=(0,200), ylim=(0, 500))
	ax4.grid()
	line4, = ax4.plot([], [], 'ro', lw=0.2)
	ax4.set_xlabel('Pos x1')
	ax4.set_ylabel('Pos y1')

	ax3 = self.fig.add_subplot(236, autoscale_on=False, xlim=(0,500), ylim=(-100,100))
	ax3.grid()
	line3, = ax3.plot([], [], 'b.', lw=0.5)
	line3a, = ax3.plot([], [], 'ro', lw=2)
	ax3.set_xlabel('x-Pos 2')
	ax3.set_ylabel('Angular Speed 2')
	
	phi1_old = 0 # for derivatives
	phi2_old = 0
	ls = [] # list for poincare section
	
	
        def update(i):
	    x1 = track.trajectory1[0,:track.time]
	    y1 = track.trajectory1[1,:track.time]
	    x2 = track.trajectory2[0,:track.time]
	    y2 = track.trajectory2[1,:track.time]
	    phi1 = track.ptrajectory1[0,:track.time]
	    phi2 = track.ptrajectory2[0,:track.time]
	    w1 = track.wtrajectory1[0,:track.time]
	    w2 = track.wtrajectory2[0,:track.time]
	    time_elapsed = track.time_sec[0:track.time]
	    
	    if i>10:
	      line1.set_data(x1,y1)
	      line1a.set_data(x1[-1],y1[-1])
	      line1b.set_data(x2,y2)
	      line1c.set_data(x2[-1],y2[-1])
	      line2.set_data(x1, w1)
	      line2a.set_data(x1[-1], w1[-1])
	      line3.set_data(x2, w2)
	      line3a.set_data(x2[-1], w1[-1])
	      if ((w1[-1] > 0) and (w1[-2] < 0) ) or ((w1[-1] < 0) and (w1[-2] > 0) ): 
		ls.append([x1[-1],y1[-1]])
		a = np.array(ls)
		line4.set_data(a[:,0],a[:,1])
	    if i>100:
	      tt = time_elapsed[(-101):(-1)] - time_elapsed[-101]
	      line5.set_data(tt, y1[(-101):(-1)])
	      line5a.set_data(time_elapsed[-1], y1[-1])
	      line5b.set_data(tt,y2[(-101):(-1)])
	      line5c.set_data(time_elapsed[-1], y2[-1])
	      
	      spec = np.fft.fft(y1[(-101):(-1)])
	      timestep = np.mean(np.diff(tt))
	      freq = np.fft.fftfreq(spec.size, d=timestep)
	      sp = np.abs(spec)
	      line6.set_data(freq,sp)

      
            return [line1,line1a, line1b, line1c, line2, line2a, line3, line3a, line5, line5a, line5b, line5c, line6]
        self.animated_pendulum = animation.FuncAnimation(self.fig, update, frames=frames,interval=interval, blit = True)



calibration()
#x1,y1,x2,y2,end,frame = capture(True, False)
track = Tracking(rotate_frames=True, show_roi = False)
track.start()
#plot = Plot(track)
