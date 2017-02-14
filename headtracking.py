import cv2
import numpy as np
import pdb
import matplotlib.cm as cm

def find_faces(input):

    faces = frontal_faces_cascade.detectMultiScale(input, 1.3, 5)

    if np.asarray(faces).size == 0:
        faces = profile_faces_cascade.detectMultiScale(input, 1.3, 5)

    return faces

def draw_faces(grayscale_frame, frame, faces):

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = grayscale_frame[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
        #smiles = smile_cascade.detectMultiScale(roi_gray)
        #for (ex, ey, ew, eh) in smiles:
        #    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 255), 2)
            

    return frame

def color_frame(frame, scale):

    factor = 10

    frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    print(cm.hot(np.arange(256))[:,2])

    b = np.roll(np.squeeze((cm.prism(np.arange(256))[:,2]*255).astype(np.uint8)), scale * factor)
    g = np.roll(np.squeeze((cm.prism(np.arange(256))[:,1]*255).astype(np.uint8)), scale * factor)
    r = np.roll(np.squeeze((cm.prism(np.arange(256))[:,0]*255).astype(np.uint8)), scale * factor)

    frame_b = cv2.LUT(frame_grayscale, b)
    frame_g = cv2.LUT(frame_grayscale, g)
    frame_r = cv2.LUT(frame_grayscale, r)

    frame = cv2.merge((frame_b,frame_g,frame_r))

    return frame

def main():
    lstFoundFaces = []
    cv2.namedWindow("Video")
    frames = 0
    while True:
        frames += 1

        _, frame = cap.read()
        frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = find_faces(frame_grayscale)

        if np.asarray(faces).size == 0:
            faces = lstFoundFaces
        else:
            lstFoundFaces = faces

        cv2.imshow("Video", draw_faces(frame_grayscale, color_frame(frame, frames), faces));

        k = cv2.waitKey(5) & 0xFF


if __name__ == '__main__':
	
    frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml')
    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt2.xml')
    #frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt_tree.xml')
    #smile_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_smile.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')
    profile_faces_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_profileface.xml')


    cap = cv2.VideoCapture(0)

    main()
