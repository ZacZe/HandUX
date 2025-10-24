import cv2
import state

class SettingsWindow:
    def __init__(self, state):
        self.state = state
        self.window_name = "Settings"

    def show(self):
        cv2.namedWindow(self.window_name)
        cv2.resizeWindow(self.window_name, 600, 300)
        # Left mouse settings
        cv2.createTrackbar("Left Mouse Detection Threshold", self.window_name, self.state.left_detection_threshold, 100, lambda x: None)
        cv2.createTrackbar("Left Mouse Holding Threshold (x100ms)", self.window_name, int(self.state.left_hold_threshold*100), 100, lambda x: None)
        # Right mouse settings
        cv2.createTrackbar("Right Mouse Detection Threshold", self.window_name, self.state.right_detection_threshold, 100, lambda x: None)
        cv2.createTrackbar("Right Mouse Holding Threshold (x100ms)", self.window_name, int(self.state.right_hold_threshold*100), 100, lambda x: None)

    def read(self):
        # update thresholds from trackbars
        self.state.left_detection_threshold = cv2.getTrackbarPos("Left Mouse Detection Threshold", self.window_name)
        self.state.left_hold_threshold = cv2.getTrackbarPos("Left Mouse Holding Threshold (x100ms)", self.window_name) / 100.0
        self.state.right_detection_threshold = cv2.getTrackbarPos("Right Mouse Detection Threshold", self.window_name)
        self.state.right_hold_threshold = cv2.getTrackbarPos("Right Mouse Holding Threshold (x100ms)", self.window_name) / 100.0

    def close(self):
        cv2.destroyWindow(self.window_name)
