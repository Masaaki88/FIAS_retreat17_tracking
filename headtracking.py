import cv2
import numpy as np
import pdb
import matplotlib.cm as cm
import threading
from sound_output import SoundManager


def find_faces(input):

    faces = frontal_faces_cascade.detectMultiScale(input, 1.3, 5)

    #if np.asarray(faces).size == 0:
        #faces = profile_faces_cascade.detectMultiScale(input, 1.3, 5)

    centers = []
    for (x,y,w,h) in faces:
        centers.append((int(x + (w/2)), int(y + (h/2))))

    return centers, faces

def draw_faces(grayscale_frame, frame, faces, centers):

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        if len(centers) > 0:
            cv2.circle(frame,centers[0],5,(0,0,255),2)
        roi_gray = grayscale_frame[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
        #smiles = smile_cascade.detectMultiScale(roi_gray)
        #for (ex, ey, ew, eh) in smiles:
        #    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 255), 2)
            

    return frame

def color_frame(grayscale_frame, frame, scale, faces, centers, eye, eye_mask):

    #if len(centers) > 0:
        #factor = int((centers[0][1] - frame.shape[1] / 2) / 10)
    #else:
        #factor = 0

    factor = scale * 10
    #factor = scale * factor
    #factor = factor

    frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    b = np.roll(np.squeeze((cm.prism(np.arange(256))[:,2]*255).astype(np.uint8)), factor)
    g = np.roll(np.squeeze((cm.prism(np.arange(256))[:,1]*255).astype(np.uint8)), factor)
    r = np.roll(np.squeeze((cm.prism(np.arange(256))[:,0]*255).astype(np.uint8)), factor)

    b_ = np.roll(np.squeeze((cm.flag(np.arange(256))[:, 2] * 255).astype(np.uint8)), factor)
    g_ = np.roll(np.squeeze((cm.flag(np.arange(256))[:, 1] * 255).astype(np.uint8)), factor)
    r_ = np.roll(np.squeeze((cm.flag(np.arange(256))[:, 0] * 255).astype(np.uint8)), factor)

    frame_b = cv2.LUT(frame_grayscale, b)
    frame_g = cv2.LUT(frame_grayscale, g)
    frame_r = cv2.LUT(frame_grayscale, r)
    for (x, y, w, h) in faces:
        frame_b[y:y+h,x:x+w] = frame[y:y+h,x:x+w,0]
        frame_g[y:y+h,x:x+w] = frame[y:y+h,x:x+w,1]
        frame_r[y:y+h,x:x+w] = frame[y:y+h,x:x+w,2]

        roi_gray = grayscale_frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            centerX = int(x + ex + (ew / 2))
            centerY = int(y + ey + (eh / 2))

            centerXOffset = int(centerX-eye.shape[0]/2)
            centerYOffset = int(centerY-eye.shape[1]/2)
            fg = eye[:,:,0]
            fg = cv2.bitwise_or(fg, fg, mask=eye_mask)
            bg = frame_b[centerYOffset:centerYOffset+eye.shape[1],centerXOffset:centerXOffset+eye.shape[0]]
            bg = cv2.bitwise_or(bg, bg, mask=cv2.bitwise_not(eye_mask))
            frame_b[centerYOffset:centerYOffset+eye.shape[1],centerXOffset:centerXOffset+eye.shape[0]] = cv2.bitwise_or(fg, bg)

            fg = eye[:, :, 1]
            fg = cv2.bitwise_or(fg, fg, mask=eye_mask)
            bg = frame_g[centerYOffset:centerYOffset + eye.shape[1], centerXOffset:centerXOffset + eye.shape[0]]
            bg = cv2.bitwise_or(bg, bg, mask=cv2.bitwise_not(eye_mask))
            frame_g[centerYOffset:centerYOffset+eye.shape[1],centerXOffset:centerXOffset+eye.shape[0]] = cv2.bitwise_or(fg, bg)

            fg = eye[:, :, 2]
            fg = cv2.bitwise_or(fg, fg, mask=eye_mask)
            bg = frame_r[centerYOffset:centerYOffset + eye.shape[1], centerXOffset:centerXOffset + eye.shape[0]]
            bg = cv2.bitwise_or(bg, bg, mask=cv2.bitwise_not(eye_mask))
            frame_r[centerYOffset:centerYOffset+eye.shape[1],centerXOffset:centerXOffset+eye.shape[0]] = cv2.bitwise_or(fg, bg)

    frame = cv2.merge((frame_b,frame_g,frame_r))

    return frame

class Tracking(threading.Thread):
    def __init__(self, graphics_out, Sound_Manager):
        #cv2.namedWindow('Facetracker')

        self.graphics_in = graphics_out
        self.time = 1
        self.lstFoundFaces = []
        self.lstFoundCenters = []
        self.running = True
        self.Sound_Manager = Sound_Manager
        
        threading.Thread.__init__(self)
		
    def run(self):

        eye = cv2.imread('assets/eye.png')
        eye_mask = cv2.imread('assets/eye_mask')

        while self.running:
            # self.graphics_in(inputParams) #
            self.time += 1

            _, frame = self.graphics_in.read()
            frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            centers, faces = find_faces(frame_grayscale)
            self.Sound_Manager.adjust_sound(centers)

            if np.asarray(faces).size == 0:
                faces = self.lstFoundFaces
                centers = self.lstFoundCenters
            else:
                self.lstFoundFaces = faces
                self.lstFoundCenters = centers

            #print 'time:', self.time
            cv2.imshow("Facetracker", draw_faces(frame_grayscale, color_frame(frame_grayscale, frame, self.time, faces, centers, eye, eye_mask),faces, centers));
            #print 'showed image'
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
            #parent_conn.send(['kill', sound_process])
            print 'closing'
            return 0
        elif 49 <= key <= 57: #keys '1' - '9'
            pass
        elif key == 82: #key 'up'
            pass
        elif key == 84: #key 'down'
            pass
        elif key == 111: #key 'o'
            pass
        elif key == 99: #key 'c'
            pass
        else:
            print key

if __name__ == '__main__':
    
    #parent_conn = None
    #p_process = None

    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml')
    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt2.xml')
    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt_tree.xml')
    #smile_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_smile.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')
    #profile_faces_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_profileface.xml')
    cap = cv2.VideoCapture(0)

    Sound_Manager = SoundManager()
    parent_conn, sound_process = Sound_Manager.start_sound_output()

    tracker = Tracking(graphics_out = cap, Sound_Manager = Sound_Manager) # geht das oder muss das eine function sein?
    tracker.start()
    
    #main()
