# storing all flags, thresholds, and pinching statii here
class State:
    def __init__(self):
        # display options
        self.display_skeleton = True
        self.display_text = True
        self.display_settings = False

        # gesture text
        self.gesture_text = ""

        # number of hands
        self.num_hands = 1

        # pause
        self.paused = False

        # pinch states for mouse buttons
        self.left_down = False
        self.right_down = False
        self.middle_down = False
        self.left_pinch_start = None
        self.right_pinch_start = None
        self.middle_pinch_start = None

        # default thresholds
        self.left_detection_threshold = 30
        self.left_hold_threshold = 0.35

        self.right_detection_threshold = 30
        self.right_hold_threshold = 0.35

        self.middle_detection_threshold = 30
        self.middle_hold_threshold = 0.35
