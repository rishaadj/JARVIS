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
import os
import urllib.request

class GestureEngine:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.active = False
        self.cap = None
        self.has_dependencies = HAS_MEDIAPIPE
        self.detector = None
        
        if HAS_MEDIAPIPE:
            try:
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision
                
                # Model provisioning
                model_path = 'hand_landmarker.task'
                if not os.path.exists(model_path):
                    print("[GESTURE ENGINE] Downloading HandLandmarker model (~5MB)...")
                    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                    urllib.request.urlretrieve(url, model_path)
                    print("[GESTURE ENGINE] Model download complete.")
                
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.7,
                    min_hand_presence_confidence=0.5
                )
                self.detector = vision.HandLandmarker.create_from_options(options)
                
            except Exception as e:
                print(f"[GESTURE ENGINE] Error initializing new Tasks API: {e}. Disabling gesture engine.")
                self.has_dependencies = False
        
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Smoothing variables
        self.prev_x, self.prev_y = 0, 0
        self.smooth_factor = 7 # Higher = smoother but more lag
        self.is_pinch = False

    def start(self):
        if not self.has_dependencies or not HAS_CV2:
            print("[GESTURE ENGINE] Cannot start - dependencies missing.")
            return

        if not self.active:
            self.active = True
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise ValueError("Camera not found or inaccessible.")
            except Exception as e:
                print(f"[GESTURE ENGINE] Camera Error: {e}")
                self.active = False
                return
                
            self.latest_frame = None
            self.reader_thread = threading.Thread(target=self._frame_reader_loop, daemon=True)
            self.reader_thread.start()

            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.active = False
        if self.cap:
            self.cap.release()

    def _frame_reader_loop(self):
        """Dedicated thread to read frames, dropping old ones to prevent input lag."""
        while self.active:
            try:
                if self.cap and self.cap.isOpened():
                    success, img = self.cap.read()
                    if not success:
                        print("[GESTURE ENGINE] Frame drop or camera disconnected.")
                        self.latest_frame = None
                        time.sleep(1) # Backoff if disconnected
                        continue
                    # Overwrite buffer with latest frame immediately (drops old frames)
                    self.latest_frame = img
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"[GESTURE ENGINE] Frame Reader Exception: {e}")
                time.sleep(1)

    def _run_loop(self):
        print("[GESTURE ENGINE] Physical Control Interface Active.")
        while self.active:
            frame = self.latest_frame
            if frame is None:
                time.sleep(0.05)
                continue
            
            # Consume the frame so we don't process the same one 10 times before the hardware gives us a new one
            self.latest_frame = None

            try:
                # Copy frame to avoid thread race conditions
                img = frame.copy()
                
                # Flip for mirror effect
                img = cv2.flip(img, 1)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Format image for MP Tasks
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                detection_result = self.detector.detect(mp_image)

                status = "LOST"
                if getattr(detection_result, 'hand_landmarks', []):
                    status = "TRACKING"
                    # Hand landmarks is a list of hands, get the first hand (which is a list of landmarks)
                    landmarks = detection_result.hand_landmarks[0]
                    
                    # Get Index Finger Tip (8) and Thumb Tip (4)
                    index_tip = landmarks[8]
                    thumb_tip = landmarks[4]
                    
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
                
            except Exception as e:
                print(f"[GESTURE ENGINE] Inference Error: {e}")
                time.sleep(0.1)

    def __del__(self):
        self.stop()
