import cv2
import numpy as np

"""
# frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
# frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml')
# frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt2.xml')
# frontal_faces_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt_tree.xml')
# smile_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_smile.xml')
# eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')
# profile_faces_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_profileface.xml')
"""

class TrackedObject:
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

    options = None

    frameCount = 0
    frame = None
    frameG = None

    childTypes = ["Face"]

    listOf = []

    def __init__( self ):
        self.parent = None

        self.x = None
        self.y = None
        self.w = None
        self.h = None

        self.xAbs = None
        self.yAbs = None

        self.center = None
        self.centerAbs = None

        self.childs = []

        self.lastDetection = None

        if self.__class__ == TrackedObject:
            TrackedObject.listOf.append(self)

    def factory(type):
        if type == "Face": return Face()
        if type == "Eyes": return Eyes()
        assert 0, "Trackable object " + type + " not defined"
    factory = staticmethod(factory)

    def setCurFrame( frameCount, frame ):
        """
        Receive current frame
        :param frameCount:
        :param frame:
        :return:
        """

        TrackedObject.frameCount = frameCount
        TrackedObject.frame = frame
        TrackedObject.frameG = cv2.cvtColor( frame, cv2.COLOR_BGR2GRAY )
    setCurFrame = staticmethod(setCurFrame)

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

    def setBoundingBox( self, x, y, w, h ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.xAbs, self.yAbs = self.getAbsCoords( x, y )

        self.center = ( int( x + w/2 ), int( y + h/2 ) )
        self.centerAbs = ( int( self.xAbs + w/2 ), int( self.yAbs + h/2 ) )

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

    def getSubframe( self, x, y, w, h):
        """
        Returns the subframe defined by the bounding box of the Object
        :param x:
        :param y:
        :param w:
        :param h:
        :return:
        """

        return TrackedObject.frame[y:y+h,x:x+w,:], \
            TrackedObject.frameG[y:y+h,x:x+w]


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
            x = self.xAbs
        if y is None:
            y = self.yAbs
        if w is None:
            w = self.w
        if h is None:
            h = self.h

        childs = []

        subframe, subframeG = self.getSubframe( x, y, w, h )

        for childType in self.__class__.childTypes:
            #trackableObjects = eval(childType + ".detect( subframeG )")
            tmpObj = TrackedObject.factory( childType )
            trackableObjects = tmpObj.__class__.detect( subframeG )
            tmpObj.__class__.listOf.pop()


            if len(trackableObjects) > 0:
                TrackedObject.factory(childType).__class__.listOf = []

            for ( x, y, w, h ) in trackableObjects:
                trackableObject = TrackedObject.factory( childType )
                trackableObject.parent = self
                trackableObject.setBoundingBox( int(x), int(y), int(w), int(h) )
                trackableObject.findObjects()
                childs.append(trackableObject)

        if len(childs) > 0:
            self.childs = childs
            self.lastDetection = TrackedObject.frameCount

    def detect(self, subframeG):
        pass
    detect = staticmethod(detect)

    def drawBoundingBox(self, frame):

        for child in self.childs:
            child.drawBoundingBox( frame )

        return frame

class Face(TrackedObject):

    childTypes = ["Eyes"]
    cascadeClassifier = [cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')]

    listOf = []

    def __init__( self ):
        TrackedObject.__init__( self )

        Face.listOf.append(self)

    def detect(subframeG):
        if TrackedObject.options.trackFaces:
            faces = []
            for classifier in Face.cascadeClassifier:
                faces.append(classifier.detectMultiScale(subframeG, 1.3, 5))
            faces = np.asarray(*faces)
            return faces
        else:
            return []
    detect = staticmethod(detect)

    def drawBoundingBox(self, frame):

        if TrackedObject.options.trackFaces:
            cv2.rectangle(frame, (self.xAbs, self.yAbs),
                          (self.xAbs + self.w, self.yAbs + self.h),
                          (255, 0, 0),
                          2)

            TrackedObject.drawBoundingBox( self, frame )

        return frame


class Eyes(TrackedObject):

    childTypes = []
    cascadeClassifier = [cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')]

    listOf = []

    replacement = cv2.imread('assets/eye.png')
    replacementMask = cv2.imread('assets/eye_mask')

    def __init__( self ):
        TrackedObject.__init__( self )

        Eyes.listOf.append(self)

    def detect( subframeG ):
        if TrackedObject.options.trackEyes:
            eyes = []
            for classifier in Eyes.cascadeClassifier:
                eyes.append(classifier.detectMultiScale( subframeG ))
            eyes = np.asarray(*eyes)
            return eyes
        else:
            return []
    detect = staticmethod(detect)

    def drawBoundingBox( self, frame ):

        if TrackedObject.options.trackEyes:
            cv2.rectangle(frame, (self.xAbs, self.yAbs),
                          (self.xAbs + self.w, self.yAbs + self.h),
                          (0, 255, 0),
                          2)

            TrackedObject.drawBoundingBox( self, frame )

        return frame

    def replaceEyes( frame ):
        # TODO: Implement
        return frame
    replaceEyes = staticmethod(replaceEyes)

if __name__ == '__main__':
    root = TrackedObject()