import cv2
import numpy as np

if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Video")
    frames = 0
    while True:
        _, frame = cap.read()
        frames +=1
        cv2.imshow("Video",cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY));
        k = cv2.waitKey(5) & 0xFF