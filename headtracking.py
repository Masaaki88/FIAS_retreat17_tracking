import cv2
import numpy as np

def draw_rect(frame):

    frame_grayscale = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(frame_grayscale, 1.3, 5)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        roi_gray = frame_grayscale[y:y + h, x:x + w]
        roi_color = frame[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    return frame

def main():
    cv2.namedWindow("Video")
    frames = 0
    while True:
        _, frame = cap.read()
        frames += 1
        cv2.imshow("Video", draw_rect(frame));
        k = cv2.waitKey(5) & 0xFF


if __name__ == '__main__':
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

    cap = cv2.VideoCapture(0)

    main()
