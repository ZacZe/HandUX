import threading
import time

import cv2

from hands_processing import init_hands, process_hands


class HandProcessorThread:
    def __init__(self, num_hands):
        self.num_hands = num_hands
        self.hands = init_hands(num_hands)

        self.lock = threading.Lock()
        self.frame_ready = threading.Event()
        self.stopped = False

        self.input_frame = None
        self.display_skeleton = True
        self.pending_num_hands = None
        self.latest_result = None
        self.result_id = 0
        self.processing_fps = 0.0
        self._last_processed_at = None

        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def submit(self, frame, display_skeleton):
        with self.lock:
            self.input_frame = frame.copy()
            self.display_skeleton = display_skeleton
        self.frame_ready.set()

    def read(self):
        with self.lock:
            if self.latest_result is None:
                return None
            return {
                "hands_data": self.latest_result["hands_data"],
                "frame_w": self.latest_result["frame_w"],
                "frame_h": self.latest_result["frame_h"],
                "processing_fps": self.processing_fps,
                "result_id": self.latest_result["result_id"],
                "num_hands": self.latest_result["num_hands"],
            }

    def set_num_hands(self, num_hands):
        with self.lock:
            active_num_hands = self.pending_num_hands or self.num_hands
            if active_num_hands == num_hands:
                return
            self.pending_num_hands = num_hands
            self.latest_result = None
            self.processing_fps = 0.0
            self._last_processed_at = None
        self.frame_ready.set()

    def update(self):
        while not self.stopped:
            self.frame_ready.wait(timeout=0.1)
            if self.stopped:
                break

            with self.lock:
                pending_num_hands = self.pending_num_hands
                self.pending_num_hands = None
                frame = self.input_frame
                display_skeleton = self.display_skeleton
                self.input_frame = None
                self.frame_ready.clear()

            if pending_num_hands is not None:
                self.hands.close()
                self.hands = init_hands(pending_num_hands)
                with self.lock:
                    self.num_hands = pending_num_hands
                    self.latest_result = None
                    self.processing_fps = 0.0
                    self._last_processed_at = None

            if frame is None:
                continue

            frame = cv2.flip(frame, 1)
            results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hands_data = process_hands(frame, results, False)

            now = time.perf_counter()
            if self._last_processed_at is not None:
                elapsed = now - self._last_processed_at
                if elapsed > 0:
                    self.processing_fps = 1.0 / elapsed
            self._last_processed_at = now

            with self.lock:
                self.result_id += 1
                self.latest_result = {
                    "hands_data": hands_data,
                    "frame_w": frame.shape[1],
                    "frame_h": frame.shape[0],
                    "result_id": self.result_id,
                    "num_hands": self.num_hands,
                }

    def stop(self):
        self.stopped = True
        self.frame_ready.set()
        self.thread.join(timeout=1)
        self.hands.close()
