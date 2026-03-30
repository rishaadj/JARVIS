try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

import pyautogui
import threading
import time
import numpy as np

class GestureEngine:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.active = False
        self.cap = None
        self.has_dependencies = HAS_MEDIAPIPE
        
        if HAS_MEDIAPIPE:
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5
                )
                self.mp_draw = mp.solutions.drawing_utils
            except AttributeError:
                print("[GESTURE ENGINE] Error: mediapipe.solutions not found. Disabling gesture engine.")
                self.has_dependencies = False
        
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Smoothing variables
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 7 # Higher = smoother but more lag
        
        # State tracking
        self.is_pinch = False

    def start(self):
        if not self.has_dependencies or not HAS_CV2:
            print("[GESTURE ENGINE] Cannot start - dependencies missing.")
            return

        if not self.active:
            self.active = True
            self.cap = cv2.VideoCapture(0)
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.active = False
        if self.cap:
            self.cap.release()

    def _run_loop(self):
        print("[GESTURE ENGINE] Physical Control Interface Active.")
        while self.active:
            success, img = self.cap.read()
            if not success:
                continue

            # Flip for mirror effect
            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)

            status = "LOST"
            if results.multi_hand_landmarks:
                status = "TRACKING"
                hand_landmarks = results.multi_hand_landmarks[0]
                
                # Get Index Finger Tip (8) and Thumb Tip (4)
                index_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]
                
                # 🖱️ MOUSE MOVE (Index Finger)
                # Map camera coordinates to screen coordinates
                target_x = np.interp(index_tip.x, [0.2, 0.8], [0, self.screen_w])
                target_y = np.interp(index_tip.y, [0.2, 0.8], [0, self.screen_h])
                
                # Smoothing
                curr_x = self.prev_x + (target_x - self.prev_x) / self.smooth_factor
                curr_y = self.prev_y + (target_y - self.prev_y) / self.smooth_factor
                
                pyautogui.moveTo(curr_x, curr_y, _pause=False)
                self.prev_x, self.prev_y = curr_x, curr_y

                # 👆 PINCH TO CLICK (Distance between Index and Thumb)
                distance = np.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
                if distance < 0.05: # Threshold for pinch
                    if not self.is_pinch:
                        pyautogui.click(_pause=False)
                        self.is_pinch = True
                else:
                    self.is_pinch = False

            # Update HUD status
            if self.socketio:
                self.socketio.emit('gesture_status', {'status': status})

            # Optional: 30 FPS cap to save CPU
            time.sleep(0.01)

    def __del__(self):
        self.stop()
