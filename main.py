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
        self.setRes()
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        t = threading.Thread(target=self.update, daemon=True)
        t.start()

    def setRes(self, width, height): 
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def setRes(self): 
        pass

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

# flags + states
display_skeleton, display_text, display_settings = True, True, False
gesture_text = ""
num_hands=1
paused = False
left_down, right_down, middle_down = False, False, False
left_pinch_start, right_pinch_start, middle_pinch_start = None, None, None

# mediapipe setup
mpHands = mp.solutions.hands
hands = mpHands.Hands(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=num_hands
)
Draw = mp.solutions.drawing_utils

def nothing(x): pass

# default values if settings window isn’t open yet
left_detection_threshold = 30
left_hold_threshold = 0.35

right_detection_threshold = 30
right_hold_threshold = 0.35

middle_detection_threshold = 30
middle_hold_threshold = 0.35

# screen size
og_screen_w, og_screen_h = pyautogui.size()
screen_w = og_screen_w + (og_screen_w / 10)
screen_h = og_screen_h + (og_screen_h / 10)

# start threaded capture
stream = WebcamStream(0)

while True:
    frame = stream.read()
    if frame is None:
        continue
    frame = cv2.flip(frame, 1)

    # if settings window is open → update trackbar values
    if display_settings:
        left_detection_threshold = cv2.getTrackbarPos("Left Mouse Detection Threshold", "Settings")
        left_hold_threshold = cv2.getTrackbarPos("Left Mouse Holding Threshold (x100ms)", "Settings") / 100.0

        right_detection_threshold = cv2.getTrackbarPos("Right Mouse Detection Threshold", "Settings")
        right_hold_threshold = cv2.getTrackbarPos("Right Mouse Holding Threshold (x100ms)", "Settings") / 100.0

    if not paused:
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frameRGB)


        hands_data = []
        if results.multi_hand_landmarks and results.multi_handedness:
            for handlm, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                h, w, _ = frame.shape
                lm_list = []
                for _id, lm in enumerate(handlm.landmark):
                    x, y = int(lm.x * w), int(lm.y * h)
                    lm_list.append([_id, x, y])

                # assign left or right hand
                hands_data.append({
                    "label": handedness.classification[0].label, # "Left" or "Right"
                    "landmarks": lm_list
                })

                if display_skeleton:
                    Draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

        #num_hands = len(hands_data)

        # move cursor
        # sensitivity factor (1 is normal but mid, under 1 is risky)
        sensitivity = 1.25

        # frame dimensions
        frame_h, frame_w = frame.shape[:2]

        # center of the frame
        center_x = frame_w // 2
        center_y = frame_h // 2

        # ---------------- ONE HAND MODE ----------------

        if num_hands == 1:
            if len(hands_data) > 0:
                gesture_text = ""
                active = hands_data[0]["landmarks"]

                x_thumb, y_thumb = active[4][1], active[4][2]
                x_index, y_index = active[8][1], active[8][2]
                x_middle, y_middle = active[12][1], active[12][2]

                # relative movement from center but scaled
                rel_x = (x_index - center_x) / (frame_w / 2)
                rel_y = (y_index - center_y) / (frame_h / 2)

                # apply sensitivity
                scaled_x = rel_x * sensitivity
                scaled_y = rel_y * sensitivity

                # clamp values to [-1, 1] to avoid overshoot
                scaled_x = max(min(scaled_x, 1), -1)
                scaled_y = max(min(scaled_y, 1), -1)

                # Map to screen coordinates
                screen_x = (scaled_x + 1) / 2 * screen_w
                screen_y = (scaled_y + 1) / 2 * screen_h

                try:
                    pyautogui.moveTo(screen_x, screen_y)
                except pyautogui.FailSafeException:
                    # corner reached which triggers fail-safe annoyingly
                    print("Fail-safe triggered: Mouse moved to corner. Pausing cursor control.")
                    paused = True 


                # LEFT CLICK / HOLD
                if hypot(x_index - x_thumb, y_index - y_thumb) < left_detection_threshold:
                    if left_pinch_start is None:
                        left_pinch_start = time.time()
                    if not left_down and (time.time() - left_pinch_start >= left_hold_threshold):
                        gesture_text = "Left Hold"
                        pyautogui.mouseDown()
                        left_down = True
                else:
                    if left_pinch_start is not None:
                        pinch_duration = time.time() - left_pinch_start
                        if pinch_duration < left_hold_threshold:
                            gesture_text = "Left Click"
                            pyautogui.click()
                        elif left_down:
                            gesture_text = ""
                            pyautogui.mouseUp()
                            left_down = False
                        left_pinch_start = None


                # RIGHT CLICK / HOLD
                if hypot(x_middle - x_thumb, y_middle - y_thumb) < right_detection_threshold:
                    if right_pinch_start is None:
                        right_pinch_start = time.time()
                    if not right_down and (time.time() - right_pinch_start >= right_hold_threshold):
                        gesture_text = "Right Hold"
                        pyautogui.mouseDown(button="right")
                        right_down = True
                else:
                    if right_pinch_start is not None:
                        pinch_duration = time.time() - right_pinch_start
                        if pinch_duration < right_hold_threshold:
                            gesture_text = "Right Click"
                            pyautogui.click(button="right")
                        elif right_down:
                            gesture_text = ""
                            pyautogui.mouseUp(button="right")
                            right_down = False
                        right_pinch_start = None

                
                # MIDDLE CLICK / HOLD
                if hypot(x_middle - x_index, y_middle - y_index) < middle_detection_threshold:
                    if middle_pinch_start is None:
                        middle_pinch_start = time.time()
                    if not middle_down and (time.time() - middle_pinch_start >= middle_hold_threshold):
                        gesture_text = "Middle Hold"
                        pyautogui.mouseDown(button="middle")
                        middle_down = True
                else:
                    if middle_pinch_start is not None:
                        pinch_duration = time.time() - middle_pinch_start
                        if pinch_duration < middle_hold_threshold:
                            gesture_text = "Middle Click"
                            pyautogui.click(button="middle")
                        elif middle_down:
                            gesture_text = ""
                            pyautogui.mouseUp(button="middle")
                            middle_down = False
                        middle_pinch_start = None
            else: 
                gesture_text = "MISSING HANDS"

        # --------------- END OF ONE HAND MODE ----------------


        # ---------------- START OF TWO HAND MODE ----------------

        elif num_hands == 2:
            # split roles
            cursor_hand = next((h for h in hands_data if h["label"] == "Right"), None)
            action_hand = next((h for h in hands_data if h["label"] == "Left"), None)

            # draw vertical line in center to show border between left / right handz
            cv2.line(frame, ((frame_w//2), 0), ((frame_w//2), int(frame_h)), (255,255,255), 3)

            # if both hands exist then work
            if cursor_hand and action_hand:
                gesture_text = ""
                # cursor hand (right hand controls cursor)
                cursor = cursor_hand["landmarks"]
                x_index, y_index = cursor[8][1], cursor[8][2]

                rel_x = (x_index - center_x) / (frame_w / 2)
                rel_y = (y_index - center_y) / (frame_h / 2)

                # only right side (for now...)
                rel_x = max(rel_x, 0)

                # apply sensitivity
                scaled_x = rel_x * sensitivity
                scaled_y = rel_y * sensitivity

                # clamp values to [0, 1] horizontally, [-1, 1] vertically
                scaled_x = min(scaled_x, 1)
                scaled_y = max(min(scaled_y, 1), -1)

                # map it all to screen
                screen_x = scaled_x * screen_w
                screen_y = (scaled_y + 1) / 2 * screen_h
                
                try:
                    pyautogui.moveTo(screen_x, screen_y)
                except pyautogui.FailSafeException:
                    # corner reached which triggers fail-safe annoyingly
                    print("Fail-safe triggered: Mouse moved to corner - Pausing cursor control.")
                    paused = True 

                # action hand (left hand does clicks)
                act = action_hand["landmarks"]
                x_thumb, y_thumb = act[4][1], act[4][2]
                x_index, y_index = act[8][1], act[8][2]
                x_middle, y_middle = act[12][1], act[12][2]

                # LEFT CLICK / HOLD
                if hypot(x_index - x_thumb, y_index - y_thumb) < left_detection_threshold:
                    if left_pinch_start is None:
                        left_pinch_start = time.time()
                    if not left_down and (time.time() - left_pinch_start >= left_hold_threshold):
                        gesture_text = "Left Hold"
                        pyautogui.mouseDown()
                        left_down = True
                else:
                    if left_pinch_start is not None:
                        pinch_duration = time.time() - left_pinch_start
                        if pinch_duration < left_hold_threshold:
                            gesture_text = "Left Click"
                            pyautogui.click()
                        elif left_down:
                            gesture_text = ""
                            pyautogui.mouseUp()
                            left_down = False
                        left_pinch_start = None 

                # RIGHT CLICK / HOLD
                if hypot(x_middle - x_thumb, y_middle - y_thumb) < right_detection_threshold:
                    if right_pinch_start is None:
                        right_pinch_start = time.time()
                    if not right_down and (time.time() - right_pinch_start >= right_hold_threshold):
                        gesture_text = "Right Hold"
                        pyautogui.mouseDown(button="right")
                        right_down = True
                else:
                    if right_pinch_start is not None:
                        pinch_duration = time.time() - right_pinch_start
                        if pinch_duration < right_hold_threshold:
                            gesture_text = "Right Click"
                            pyautogui.click(button="right")
                        elif right_down:
                            gesture_text = ""
                            pyautogui.mouseUp(button="right")
                            right_down = False
                        right_pinch_start = None

                # MIDDLE CLICK / HOLD
                if hypot(x_middle - x_index, y_middle - y_index) < middle_detection_threshold:
                    if middle_pinch_start is None:
                        middle_pinch_start = time.time()
                    if not middle_down and (time.time() - middle_pinch_start >= middle_hold_threshold):
                        gesture_text = "Middle Hold"
                        pyautogui.mouseDown(button="middle")
                        middle_down = True
                else:
                    if middle_pinch_start is not None:
                        pinch_duration = time.time() - middle_pinch_start
                        if pinch_duration < middle_hold_threshold:
                            gesture_text = "Middle Click"
                            pyautogui.click(button="middle")
                        elif middle_down:
                            gesture_text = ""
                            pyautogui.mouseUp(button="middle")
                            middle_down = False
                        middle_pinch_start = None

            else: 
                # missing hands, regardless of what hand(s) be missing
                gesture_text = "MISSING HANDS"

        # ---------------- END OF TWO HAND MODE ----------------

        # display gesture text
        if display_text and gesture_text == "MISSING HANDS":
            cv2.putText(frame, gesture_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        elif display_text and gesture_text:
            cv2.putText(frame, gesture_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)


    else: 
        cv2.putText(frame, "PAUSED", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    # display number of hands
    if num_hands == 1:
        hands_text = "HAND"
    else: 
        hands_text = "HANDS"
    cv2.putText(frame, str(num_hands)+hands_text, (stream.getResHeight()-10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 3)

    # show feed
    window_name = "HandUX"
    cv2.imshow(window_name, frame)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    # key press actions
    key = cv2.waitKey(1) & 0xFF
    if key == 27: # ESC = quit
        break
    elif key == 32: # SPACE = pause/resume
        paused = not paused
    elif key == ord("s"): # toggle skeleton
        display_skeleton = not display_skeleton
    elif key == ord("t"): # toggle text
        display_text = not display_text
    elif key == ord("n"): # toggle number of hands
        if num_hands == 1: # 1 -> 2
            num_hands+=1
        elif num_hands == 2: # 2 -> 1
            num_hands-=1

        hands = mpHands.Hands(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=num_hands
        )
    elif key == ord("x"): # toggle settings 
        if not display_settings:
            cv2.namedWindow("Settings")
            cv2.resizeWindow("Settings", 600, 300)

            # settings for left click / hold
            cv2.createTrackbar("Left Mouse Detection Threshold", "Settings", left_detection_threshold, 100, nothing)
            cv2.createTrackbar("Left Mouse Holding Threshold (x100ms)", "Settings", int(left_hold_threshold*100), 100, nothing)
            
            # settings for right click / hold 
            cv2.createTrackbar("Right Mouse Detection Threshold", "Settings", right_detection_threshold, 100, nothing)
            cv2.createTrackbar("Right Mouse Holding Threshold (x100ms)", "Settings", int(right_hold_threshold*100), 100, nothing)

            display_settings = True
        else:
            cv2.destroyWindow("Settings")
            display_settings = False

stream.stop()
cv2.destroyAllWindows()
