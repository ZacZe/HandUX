import cv2
import pyautogui
import state
from gesture_one_hand import process_one_hand
from gesture_two_hands import process_two_hands
from settings import SettingsWindow
from hands_processing import mpHands, Draw, init_hands, process_hands
from webcam_stream import WebcamStream

# -------- state --------
state = state.State()

# -------- mediapipe --------
hands = init_hands(state.num_hands)

# -------- screen --------
og_screen_w, og_screen_h = pyautogui.size()
screen_w = og_screen_w + (og_screen_w/10)
screen_h = og_screen_h + (og_screen_h/10)
sensitivity = 1.25

# -------- start Capture --------
stream = WebcamStream(0)
settings_win = SettingsWindow(state)

while True:
    frame = stream.read()
    if frame is None: 
        continue

    frame = cv2.flip(frame, 1)
    frame_h, frame_w = frame.shape[:2]

    # read settings window
    if state.display_settings:
        settings_win.read()

    # mediapipe
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    hands_data = process_hands(frame, results, state.display_skeleton)

    # gestures
    if not state.paused:
        if state.num_hands == 1 and hands_data:
            state.gesture_text = ""
            process_one_hand(hands_data, frame, state, frame_w, frame_h, screen_w, screen_h, sensitivity)
        elif state.num_hands == 2:
            cursor_hand = next((h for h in hands_data if h["label"]=="Right"), None)
            action_hand = next((h for h in hands_data if h["label"]=="Left"), None)
            state.gesture_text = "" if cursor_hand and action_hand else "MISSING HANDS"
            if cursor_hand and action_hand:
                process_two_hands(cursor_hand, action_hand, frame, state, frame_w, frame_h, screen_w, screen_h, sensitivity)
    else: 
        state.gesture_text = "PAUSED"
                

    # display
    if state.display_text: 
        if state.gesture_text!="MISSING HANDS" and state.gesture_text!="PAUSED":
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)
        
        cv2.putText(frame, state.gesture_text, (10,70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

    hands_text = "HAND" if state.num_hands==1 else "HANDS"
    cv2.putText(frame, str(state.num_hands)+hands_text, (stream.getResHeight()-10,70), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,0,255), 3)

    cv2.imshow("HandUX", frame)
    cv2.setWindowProperty("HandUX", cv2.WND_PROP_TOPMOST, 1)

    # keys
    key = cv2.waitKey(1) & 0xFF
    if key==27: 
        break
    elif key==32: 
        state.paused = not state.paused
    elif key==ord("s"): 
        state.display_skeleton = not state.display_skeleton
    elif key==ord("t"): 
        state.display_text = not state.display_text
    elif key==ord("n"): 
        state.num_hands = 2 if state.num_hands==1 else 1
        hands = init_hands(state.num_hands)
    elif key==ord("x"):
        if not state.display_settings:
            settings_win.show()
            state.display_settings = True
        else:
            settings_win.close()
            state.display_settings = False

stream.stop()
cv2.destroyAllWindows()