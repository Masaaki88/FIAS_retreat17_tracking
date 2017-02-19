import cv2
import numpy as np
import threading
from sound_output import SoundManager
from TrackedObject import *
from VisualTransformations import *
from Options import Options

class Tracking(threading.Thread):
    def __init__(self, graphics_out, Sound_Manager):
        #cv2.namedWindow('Facetracker')

        self.graphics_in = graphics_out
        self.time = 1
        self.lstFoundFaces = []
        self.lstFoundCenters = []
        self.running = True
        self.Sound_Manager = Sound_Manager
        self.options = Options()

        _, frame = self.graphics_in.read()
        TrackedObject.options = self.options
        self.root = TrackedObject()
        self.root.setBoundingBox( 0, 0, frame.shape[0], frame.shape[1] )

        threading.Thread.__init__(self)

    def run(self):

        while self.running:
            self.time += 1

            _, frame = self.graphics_in.read()

            TrackedObject.setCurFrame( self.time, frame )
            self.root.findObjects()

            frame = self.root.drawBoundingBox( frame )

            masks = np.empty((len(Face.listOf),4),dtype=np.uint)
            for i in range(0,len(Face.listOf)):
                face = Face.listOf[i]
                masks[i] = np.asarray([face.xAbs,face.yAbs,face.w,face.h],dtype=np.uint8)

            frame = applyColormap(frame,
                                  self.options.colorMap,
                                  scale=self.time,
                                  factor=5,
                                  masks=masks)
            frame = Eyes.replaceEyes( frame )

            self.Sound_Manager.adjust_sound(Face.listOf, self.options)

            frame = self.options.drawOptions(frame)
            cv2.imshow("Facetracker", frame)

            key = cv2.waitKey(5) & 0xFF
            if key != 255:
                self.handle_key_event(key)

    def handle_key_event(self, key):
        global parent_conn
        ## TODO: implement keybindings
        if key == 27: #key 'ESC'
            cv2.destroyWindow('Facetracker')
            self.running = False
            self.Sound_Manager.kill_process()
            print 'closing'
            return 0
        elif 49 <= key <= 57: #keys '1' - '9'
            pass
        elif key == 82: #key 'up'
            pass
        elif key == 84: #key 'down'
            pass
        elif key == 115: #key 's'
            if self.options.playSound:
                print('Muting sound')
                self.options.playSound = False
            else:
                print('Turn on sound output')
                self.options.playSound = True
        elif key == 99: #key 'c'
            if self.options.applyColormap:
                print('Turn off colormaps')
                self.options.colorMap = None
                self.options.applyColormap = False
            else:
                print('Turn on colormaps')
                self.options.changeColormap(self.options.lstColorMap)
                self.options.applyColormap = True
        elif key == 102: #key 'f'
            if self.options.trackFaces:
                print('Turn off face tracking')
                self.options.trackFaces = False
            else:
                print('Turn on face tracking')
                self.options.trackFaces = True
        elif key == 101:  # key 'e'
            if self.options.trackEyes:
                print('Turn off eye tracking')
                self.options.trackEyes = False
            else:
                print('Turn on eye tracking')
                self.options.trackEyes = True
        elif key == 114: #key 'r'
            if self.options.replaceEyes:
                print('Start replacing eyes')
                self.options.replaceEyes = False
            else:
                print('Stop replacing eyes')
                self.options.replaceEyes = True
        elif key == 111: #key 'o'
            if self.options.showOptions:
                self.options.showOptions = False
            else:
                self.options.showOptions = True
        else:
            print key

if __name__ == '__main__':

    cap = cv2.VideoCapture(0)

    Sound_Manager = SoundManager()
    parent_conn, sound_process = Sound_Manager.start_sound_output()

    tracker = Tracking(graphics_out = cap, Sound_Manager = Sound_Manager) # geht das oder muss das eine function sein?
    tracker.start()
