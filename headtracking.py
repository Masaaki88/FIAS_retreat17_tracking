import cv2
import numpy as np
import pdb

def find_faces(frame):
    frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(frame_grayscale, 1.3, 5)

    return faces

def draw_faces(frame, faces):

    frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = frame_grayscale[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
        #smiles = smile_cascade.detectMultiScale(roi_gray)
        #for (ex, ey, ew, eh) in smiles:
        #    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 255), 2)
            

    return frame

def main():
    lstFoundFaces = []
    cv2.namedWindow("Video")
    frames = 0
    while True:
        _, frame = cap.read()
        frames += 1
        faces = find_faces(frame)
        if np.asarray(faces).size == 0:
            faces = lstFoundFaces
        else:
            lstFoundFaces = faces
        cv2.imshow("Video", draw_faces(frame, faces));
        k = cv2.waitKey(5) & 0xFF


if __name__ == '__main__':
    face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
    #face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml')
    #face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt2.xml')
    #face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt_tree.xml')
    #smile_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_smile.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')

    cap = cv2.VideoCapture(0)

    main()
