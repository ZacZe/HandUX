import time

import cv2
import pyautogui

import state
from gesture_one_hand import process_one_hand
from gesture_two_hands import process_two_hands
from hand_processor_thread import HandProcessorThread
from hands_processing import draw_hand_skeleton
from settings import SettingsWindow
from webcam_stream import WebcamStream

# -------- state --------
state = state.State()

# -------- mouse --------
pyautogui.PAUSE = 0

# -------- screen --------
og_screen_w, og_screen_h = pyautogui.size()
screen_w = og_screen_w + (og_screen_w / 10)
screen_h = og_screen_h + (og_screen_h / 10)
sensitivity = 1.25

# -------- start capture / processing --------
stream = WebcamStream(0)
processor = HandProcessorThread(state.num_hands)
settings_win = SettingsWindow(state)

latest_hands_data = []
last_result_id = None
last_submitted_frame_id = None
display_fps = 0.0
last_display_at = time.perf_counter()
last_key_time = {}
KEY_COOLDOWN_SECONDS = 0.25


def key_ready(key):
    now = time.perf_counter()
    if now - last_key_time.get(key, 0) < KEY_COOLDOWN_SECONDS:
        return False
    last_key_time[key] = now
    return True


def release_mouse_buttons():
    if state.left_down:
        pyautogui.mouseUp()
        state.left_down = False
    if state.right_down:
        pyautogui.mouseUp(button="right")
        state.right_down = False
    if state.middle_down:
        pyautogui.mouseUp(button="middle")
        state.middle_down = False


def reset_gesture_state():
    release_mouse_buttons()
    state.left_pinch_start = None
    state.right_pinch_start = None
    state.middle_pinch_start = None

try:
    while True:
        raw_frame, frame_id = stream.read_with_id()
        if raw_frame is None:
            continue

        if frame_id != last_submitted_frame_id:
            processor.submit(raw_frame, state.display_skeleton)
            last_submitted_frame_id = frame_id

        frame = cv2.flip(raw_frame, 1)
        frame_h, frame_w = frame.shape[:2]

        now = time.perf_counter()
        elapsed = now - last_display_at
        if elapsed > 0:
            display_fps = 1.0 / elapsed
        last_display_at = now

        # read settings window
        if state.display_settings:
            settings_win.read()

        processed = processor.read()
        new_result = False
        processing_fps = 0.0
        if processed is not None:
            processing_fps = processed["processing_fps"]
            if processed["num_hands"] == state.num_hands:
                latest_hands_data = processed["hands_data"]
                new_result = processed["result_id"] != last_result_id
                last_result_id = processed["result_id"]

        if state.num_hands == 2:
            cv2.line(frame, (frame_w // 2, 0), (frame_w // 2, frame_h), (255, 255, 255), 3)

        if state.display_skeleton and latest_hands_data:
            draw_hand_skeleton(frame, latest_hands_data)

        # gestures are run once per processed frame so clicks do not repeat
        # just because the display loop is faster than MediaPipe.
        if new_result:
            if not state.paused:
                if state.num_hands == 1 and latest_hands_data:
                    state.gesture_text = ""
                    process_one_hand(
                        latest_hands_data,
                        frame,
                        state,
                        frame_w,
                        frame_h,
                        screen_w,
                        screen_h,
                        sensitivity,
                    )
                elif state.num_hands == 1:
                    state.gesture_text = "MISSING HANDS"
                elif state.num_hands == 2:
                    cursor_hand = next((h for h in latest_hands_data if h["label"] == "Right"), None)
                    action_hand = next((h for h in latest_hands_data if h["label"] == "Left"), None)
                    state.gesture_text = "" if cursor_hand and action_hand else "MISSING HANDS"
                    if cursor_hand and action_hand:
                        process_two_hands(
                            cursor_hand,
                            action_hand,
                            frame,
                            state,
                            frame_w,
                            frame_h,
                            screen_w,
                            screen_h,
                            sensitivity,
                        )
            else:
                state.gesture_text = "PAUSED"

        # display
        if state.display_text:
            color = (0, 255, 0)
            if state.gesture_text == "MISSING HANDS" or state.gesture_text == "PAUSED":
                color = (0, 0, 255)

            cv2.putText(frame, state.gesture_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

        hands_text = "HAND" if state.num_hands == 1 else "HANDS"
        cv2.putText(
            frame,
            f"{state.num_hands} {hands_text}",
            (frame_w - 130, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 0, 255),
            3,
        )
        cv2.putText(
            frame,
            f"Display: {display_fps:.1f} FPS",
            (10, frame_h - 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Tracking: {processing_fps:.1f} FPS",
            (10, frame_h - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

        cv2.imshow("HandUX", frame)
        cv2.setWindowProperty("HandUX", cv2.WND_PROP_TOPMOST, 1)

        # keys
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == 32 and key_ready(key):
            state.paused = not state.paused
            if state.paused:
                release_mouse_buttons()
                state.gesture_text = "PAUSED"
        elif key == ord("s") and key_ready(key):
            state.display_skeleton = not state.display_skeleton
        elif key == ord("t") and key_ready(key):
            state.display_text = not state.display_text
        elif key == ord("n") and key_ready(key):
            state.num_hands = 2 if state.num_hands == 1 else 1
            reset_gesture_state()
            latest_hands_data = []
            last_result_id = None
            last_submitted_frame_id = None
            state.gesture_text = "SWITCHING MODES"
            processor.set_num_hands(state.num_hands)
        elif key == ord("x") and key_ready(key):
            if not state.display_settings:
                settings_win.show()
                state.display_settings = True
            else:
                settings_win.close()
                state.display_settings = False
finally:
    processor.stop()
    stream.stop()
    cv2.destroyAllWindows()
