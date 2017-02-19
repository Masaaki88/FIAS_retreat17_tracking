import cv2
import numpy as np

def applyColormap(frame, colormap, scale=0, factor=0, masks=None):

    if colormap is None:
        return frame

    frameG = cv2.cvtColor( frame, cv2.COLOR_BGR2GRAY )

    b = np.roll(colormap[:,0], factor * scale)
    g = np.roll(colormap[:,1], factor * scale)
    r = np.roll(colormap[:,2], factor * scale)

    frame_b = cv2.LUT(frameG, b)
    frame_g = cv2.LUT(frameG, g)
    frame_r = cv2.LUT(frameG, r)

    if masks is not None:
        for (x,y,w,h) in masks:
            frame_b[y:y+h,x:x+w] = frame[y:y+h,x:x+w,0]
            frame_g[y:y+h,x:x+w] = frame[y:y+h,x:x+w,1]
            frame_r[y:y+h,x:x+w] = frame[y:y+h,x:x+w,2]

    frame = cv2.merge((frame_b,frame_g,frame_r))

    return frame