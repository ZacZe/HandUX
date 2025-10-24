import cv2
import threading

class WebcamStream:
    def __init__(self, src=0, width=480, height=320):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.grabbed, self.frame = self.cap.read()
        self.stopped = False

        # for thread safety
        self.lock = threading.Lock()

        # start background frame grab thread
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def getResHeight(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def getResWidth(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    def update(self):
        while not self.stopped:
            grabbed, frame = self.cap.read()
            if not grabbed:
                self.stop()
                break
            # safely store only the latest frame
            with self.lock:
                self.frame = frame

    def read(self):
        # safely return a copy of the latest frame
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        self.stopped = True
        self.thread.join(timeout=1)
        self.cap.release()
