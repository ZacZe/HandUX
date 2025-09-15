import cv2
import mediapipe as mp
import pyautogui
from math import hypot
import numpy as np
import threading
import time

# threaded webcam capture
class WebcamStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
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

# flags + states
display_skeleton = False
display_text = True
gesture_text = ""
paused = False
settings_open = False
left_down, right_down, middle_down = False, False, False
left_pinch_start, right_pinch_start, middle_pinch_start = None, None, None

def nothing(x): pass

# default values if settings window isn’t open yet
detection_threshold = 40
hold_threshold = 0.25

# screen size
screen_w, screen_h = pyautogui.size()

# start threaded capture
stream = WebcamStream(0)

while True:
    frame = stream.read()
    if frame is None:
        continue
    frame = cv2.flip(frame, 1)

    # if settings window is open → update trackbar values
    if settings_open:
        detection_threshold = cv2.getTrackbarPos("Detection Threshold", "Settings")
        hold_threshold = cv2.getTrackbarPos("Holding Threshold (x100ms)", "Settings") / 100.0

    if not paused:
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frameRGB)

        landmarkList = []
        if results.multi_hand_landmarks:
            for handlm in results.multi_hand_landmarks:
                h, w, _ = frame.shape
                for _id, lm in enumerate(handlm.landmark):
                    x, y = int(lm.x * w), int(lm.y * h)
                    landmarkList.append([_id, x, y])

                if display_skeleton:
                    Draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

        if landmarkList:
            x_thumb, y_thumb = landmarkList[4][1], landmarkList[4][2]
            x_index, y_index = landmarkList[8][1], landmarkList[8][2]
            x_middle, y_middle = landmarkList[12][1], landmarkList[12][2]

            # move cursor
            screen_x = np.interp(x_index, [0, frame.shape[1]], [0, screen_w])
            screen_y = np.interp(y_index, [0, frame.shape[0]], [0, screen_h])
            pyautogui.moveTo(screen_x, screen_y)

            # LEFT CLICK / HOLD
            if hypot(x_index - x_thumb, y_index - y_thumb) < detection_threshold:
                if left_pinch_start is None:
                    left_pinch_start = time.time()
                if not left_down and (time.time() - left_pinch_start >= hold_threshold):
                    gesture_text = "Left Hold"
                    pyautogui.mouseDown()
                    left_down = True
            else:
                if left_pinch_start is not None:
                    pinch_duration = time.time() - left_pinch_start
                    if pinch_duration < hold_threshold:
                        gesture_text = "Left Click"
                        pyautogui.click()
                    elif left_down:
                        gesture_text = ""
                        pyautogui.mouseUp()
                        left_down = False
                    left_pinch_start = None

            # RIGHT CLICK / HOLD
            if hypot(x_middle - x_thumb, y_middle - y_thumb) < detection_threshold:
                if right_pinch_start is None:
                    right_pinch_start = time.time()
                if not right_down and (time.time() - right_pinch_start >= hold_threshold):
                    gesture_text = "Right Hold"
                    pyautogui.mouseDown(button="right")
                    right_down = True
            else:
                if right_pinch_start is not None:
                    pinch_duration = time.time() - right_pinch_start
                    if pinch_duration < hold_threshold:
                        pyautogui.click(button="right")
                        gesture_text = "Right Click"

                    elif right_down:
                        pyautogui.mouseUp(button="right")
                        gesture_text = ""
                        right_down = False
                    right_pinch_start = None

            # MIDDLE CLICK / HOLD 
            if hypot(x_index - x_middle, y_index - y_middle) < detection_threshold: 
                if middle_pinch_start is None:
                    middle_pinch_start = time.time()
                if not middle_down and (time.time() - middle_pinch_start >= hold_threshold):
                    gesture_text = "Middle Hold"
                    pyautogui.mouseDown(button="middle")
                    middle_down = True
            else:
                if middle_pinch_start is not None:
                    pinch_duration = time.time() - middle_pinch_start
                    if pinch_duration < hold_threshold:
                        pyautogui.click(button="middle")
                        gesture_text = "Middle Click"

                    elif middle_down:
                        pyautogui.mouseUp(button="middle")
                        gesture_text = ""
                        middle_down = False
                    middle_pinch_start = None

            # display gesture text
            if display_text and gesture_text:
                cv2.putText(frame, gesture_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    else: 
        cv2.putText(frame, "PAUSE", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)


    # show feed
    window_name = "Hand Mouse"
    cv2.imshow(window_name, frame)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    # key press actions
    key = cv2.waitKey(1) & 0xFF
    if key == 27:   # ESC = quit
        break
    elif key == 32: # SPACE = pause/resume
        paused = not paused
    elif key == ord("s"): # toggle skeleton
        display_skeleton = not display_skeleton
    elif key == ord("t"): # toggle text
        display_text = not display_text
    elif key == ord("x"): # toggle settings 
        if not settings_open:
            cv2.namedWindow("Settings")
            cv2.createTrackbar("Detection Threshold", "Settings", detection_threshold, 100, nothing)
            cv2.createTrackbar("Holding Threshold (x100ms)", "Settings", int(hold_threshold*100), 100, nothing)
            settings_open = True
        else:
            cv2.destroyWindow("Settings")
            settings_open = False

stream.stop()
cv2.destroyAllWindows()
