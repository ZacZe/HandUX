import cv2
import threading

class WebcamStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.setRes()
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        t = threading.Thread(target=self.update, daemon=True)
        t.start()

    def setRes(self, width=None, height=None):
        if width and height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def getResWidth(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    def getResHeight(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def update(self):
        while not self.stopped:
            grabbed, frame = self.cap.read()
            if not grabbed:
                self.stop()
                break
            self.grabbed, self.frame = grabbed, frame

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()
