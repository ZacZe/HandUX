import cv2
import mediapipe as mp
import pyautogui
from math import hypot
import numpy as np
import threading

# threaded webcam capture class
class WebcamStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        # start thread
        t = threading.Thread(target=self.update, daemon=True)
        t.start()

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


# mediapipe setup
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)
Draw = mp.solutions.drawing_utils

# screen size
screen_w, screen_h = pyautogui.size()

# start threaded capture
stream = WebcamStream(0)

while True:
    frame = stream.read()
    if frame is None:
        continue

    frame = cv2.flip(frame, 1)
    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frameRGB)

    landmarkList = []
    if results.multi_hand_landmarks:
        for handlm in results.multi_hand_landmarks:
            for _id, lm in enumerate(handlm.landmark):
                h, w, _ = frame.shape
                x, y = int(lm.x * w), int(lm.y * h)
                landmarkList.append([_id, x, y])

            # comment this line to save FPS
            #Draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

    if landmarkList:
        # coords
        x_thumb, y_thumb = landmarkList[4][1], landmarkList[4][2]
        x_index, y_index = landmarkList[8][1], landmarkList[8][2]
        x_middle, y_middle = landmarkList[12][1], landmarkList[12][2]

        # move cursor with index finger
        screen_x = np.interp(x_index, [0, frame.shape[1]], [0, screen_w])
        screen_y = np.interp(y_index, [0, frame.shape[0]], [0, screen_h])
        pyautogui.moveTo(screen_x, screen_y)

        # left click (thumb + index pinch)
        if hypot(x_index - x_thumb, y_index - y_thumb) < 40:
            pyautogui.click()
            #pyautogui.sleep(0.25)

        # right click (thumb + middle pinch)
        if hypot(x_middle - x_thumb, y_middle - y_thumb) < 40:
            pyautogui.click(button="right")
            #pyautogui.sleep(0.25)

    # display screen 
    window_name = "Testing Program"
    cv2.imshow(window_name, frame)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    # press ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

stream.stop()
cv2.destroyAllWindows()
