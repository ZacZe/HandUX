import pyautogui
import time
from math import hypot

def process_one_hand(hands_data, frame, state, frame_w, frame_h, screen_w, screen_h, sensitivity):
    if len(hands_data) == 0:
        state.gesture_text = "MISSING HANDS"
        return frame

    state.gesture_text = ""
    active = hands_data[0]["landmarks"]

    x_thumb, y_thumb = active[4][1], active[4][2]
    x_index, y_index = active[8][1], active[8][2]
    x_middle, y_middle = active[12][1], active[12][2]

    # relative movement
    rel_x = (x_index - (frame_w // 2)) / (frame_w / 2)
    rel_y = (y_index - (frame_h // 2)) / (frame_h / 2)

    scaled_x = max(min(rel_x * sensitivity, 1), -1)
    scaled_y = max(min(rel_y * sensitivity, 1), -1)

    screen_x = (scaled_x + 1) / 2 * screen_w
    screen_y = (scaled_y + 1) / 2 * screen_h

    try:
        pyautogui.moveTo(screen_x, screen_y)
    except pyautogui.FailSafeException:
        print("Fail-safe triggered, pausing cursor control.")
        state.paused = True

    # LEFT CLICK / HOLD
    if hypot(x_index - x_thumb, y_index - y_thumb) < state.left_detection_threshold:
        if state.left_pinch_start is None:
            state.left_pinch_start = time.time()
        if not state.left_down and (time.time() - state.left_pinch_start >= state.left_hold_threshold):
            state.gesture_text = "Left Hold"
            pyautogui.mouseDown()
            state.left_down = True
    else:
        if state.left_pinch_start is not None:
            pinch_duration = time.time() - state.left_pinch_start
            if pinch_duration < state.left_hold_threshold:
                state.gesture_text = "Left Click"
                pyautogui.click()
            elif state.left_down:
                pyautogui.mouseUp()
                state.left_down = False
            state.left_pinch_start = None

    # RIGHT CLICK / HOLD
    if hypot(x_middle - x_thumb, y_middle - y_thumb) < state.right_detection_threshold:
        if state.right_pinch_start is None:
            state.right_pinch_start = time.time()
        if not state.right_down and (time.time() - state.right_pinch_start >= state.right_hold_threshold):
            state.gesture_text = "Right Hold"
            pyautogui.mouseDown(button="right")
            state.right_down = True
    else:
        if state.right_pinch_start is not None:
            pinch_duration = time.time() - state.right_pinch_start
            if pinch_duration < state.right_hold_threshold:
                state.gesture_text = "Right Click"
                pyautogui.click(button="right")
            elif state.right_down:
                pyautogui.mouseUp(button="right")
                state.right_down = False
            state.right_pinch_start = None

    # MIDDLE CLICK / HOLD
    if hypot(x_middle - x_index, y_middle - y_index) < state.middle_detection_threshold:
        if state.middle_pinch_start is None:
            state.middle_pinch_start = time.time()
        if not state.middle_down and (time.time() - state.middle_pinch_start >= state.middle_hold_threshold):
            state.gesture_text = "Middle Hold"
            pyautogui.mouseDown(button="middle")
            state.middle_down = True
    else:
        if state.middle_pinch_start is not None:
            pinch_duration = time.time() - state.middle_pinch_start
            if pinch_duration < state.middle_hold_threshold:
                state.gesture_text = "Middle Click"
                pyautogui.click(button="middle")
            elif state.middle_down:
                pyautogui.mouseUp(button="middle")
                state.middle_down = False
            state.middle_pinch_start = None

    return frame