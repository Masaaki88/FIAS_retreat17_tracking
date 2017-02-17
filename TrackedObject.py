import cv2
import numpy as np
from enum import Enum

class TrackedObject(Enum):
    """
    Base class for tracked objects

    Symbolic names: Type of object

    Static Attributes:
        frameCount: Number of frames from the beginning of the application
        frame: Current frame as BGR image
        frameG: Same as frame as grayscale Version
        partialFrameLT: Lookup table for subframes
            First Level: x-coordinate
            Second Level: y-coordinate
            Third Level: Width
            Fourth Level: Height
        partialGrameGLT: Same as partialFrameLT for grayscale version

    Attributes:
        parent: parent object
        type: Type of Object, see symbolic names

        x: x coordinate relative to parent
        y: y coordinate relative to parent
        w: width of bounding box
        h: height of bounding box

        childs: List of tracked objects within the bounding box of this object
        cascadeClassifier: List of classifiers used for tracking objects within
            the bounding box of this object
    """

    ROOT = 0
    FACE = 1
    EYE = 2

    frameCount = 0
    frame = None
    frameG = None
    partialFrameLT = {}
    partialFrameGLT = {}

    def __init__(self):

        Enum.__init__(self)

        self.parent = None
        self.type = 0

        self.x = None
        self.y = None
        self.w = None
        self.h = None

        self.childs = []
        self.cascadeClassifier = []

        self.lastDetection = None

    def addChild( self, child ):
        """
        Adds a child object to this object
        :param child:
        :return: None
        """

        self.childs.append( child )

    def addCascadeClassifier( self, classifier ):
        """
        Adds a classifier to the list of classifiers
        :param classifier:
        :return: None
        """

        self.cascadeClassifier.append( classifier )

    def getAbsCoords( self, x=None, y=None ):
        """
        Returns the absolute coordinates of this object
        :param x:
        :param y:
        :return: Absolute x and y coordinates
        """

        if x is None:
            x = self.x
        if y is None:
            y = self.y

        p = self.parent

        absX = 0
        absY = 0

        while( p != None ):
            absX += p.x
            absY += p.y

            p = p.parent

        absX += x
        absY += y

        return absX, absY

    def setCurFrame( self, frameCount, frame ):
        """
        Receive current frame
        :param frameCount:
        :param frame:
        :return:
        """

        TrackedObject.frameCount = frameCount
        TrackedObject.frame = frame
        TrackedObject.frameG = cv2.cvtColor( frame, cv2.COLOR_BGR2GRAY )

    def getSubframe( self, x, y, w, h):
        """
        Returns the subframe defined by the bounding box of the Object
        First look in the lookup table if there is already such a subframe
        if not create on an save it in the corresponding lookup table
        :param x:
        :param y:
        :param w:
        :param h:
        :return:
        """

        if x in TrackedObject.partialFrameLT:
            if y in TrackedObject.partialFrameLT[x]:
                if w in TrackedObject.partialFrameLT[x][y]:
                    if h in TrackedObject.partialFrameLT[x][y][w]:
                        return TrackedObject.partialFrameLT[x][y][w][h], \
                            TrackedObject.partialFrameGLT[x][y][w][h]

        TrackedObject.partialFrameLT[x][y][w][h] = \
            TrackedObject.frame[y:y+h,x:x+w,:]
        TrackedObject.partialFrameGLT[x][y][w][h] = \
            TrackedObject.frameG[y:y+h,x:x+w]

        return TrackedObject.partialFrameLT[x][y][w][h], \
            TrackedObject.partialFrameGLT[x][y][w][h]


    def findObjects( self, x=None, y=None, w=None, h=None ):
        """
        Find objects based on the list of classifiers within the
        bounding box of this object or the bounding box that is
        specified by the parameters
        :param x:
        :param y:
        :param w:
        :param h:
        :return:
        """

        if x is None:
            x = self.x
        if y is None:
            y = self.y
        if w is None:
            w = self.w
        if h is None:
            h = self.h


        x, y = self.getAbsCoords( x, y )
        subframe, subframeG = self.getSubframe( x, y, w, h )

        for classifier in self.cascadeClassifier:
            childs = classifier.detectMultiScale( subframeG )



if __name__ == '__main__':
    root = TrackedObject()