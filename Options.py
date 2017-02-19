import numpy as np
import matplotlib.cm as cm
import cv2

class Options:
    def __init__(self):
        self.applyColormap = False
        self.trackFaces = False
        self.trackEyes = False
        self.drawBoundingboxes = True
        self.replaceEyes = False
        self.playSound = False
        self.showOptions = True

        self.colorMap = None
        self.lstColorMap = None

        # Set default colormap
        self.changeColormap("prism")
        if not self.applyColormap:
            self.colorMap = None

    def drawOptions(self, frame):
        if self.showOptions:
            y = 20
            frame = cv2.putText(frame, "Options:", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0), thickness=1)
            y += 20
            frame = cv2.putText(frame, "'c': Apply colormap", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'f': Track faces", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'e': Track Eyes", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'r': Replace Eyes", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'s': Play Audio", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'o': Show Options", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0),
                                thickness=1)
            y += 20
            frame = cv2.putText(frame, "'Esc': Exit", (10, y), cv2.FONT_HERSHEY_COMPLEX, .5, (0, 255, 0), thickness=1)

        return frame

    def changeColormap(self, name):
        self.lstColorMap = name
        if name == "prism":
            self.colorMap = np.empty((256, 3), dtype=np.uint8)
            self.colorMap[:, 0] = np.squeeze((cm.prism(np.arange(256))[:, 2] * 255).astype(np.uint8))
            self.colorMap[:, 1] = np.squeeze((cm.prism(np.arange(256))[:, 1] * 255).astype(np.uint8))
            self.colorMap[:, 2] = np.squeeze((cm.prism(np.arange(256))[:, 0] * 255).astype(np.uint8))
        else:
            self.lstColorMap = None
            self.colorMap = None