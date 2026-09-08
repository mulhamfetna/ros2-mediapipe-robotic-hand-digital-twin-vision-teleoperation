import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
import pyautogui
import urllib.request
import os
import time

pyautogui.FAILSAFE = False
screen_w, screen_h = pyautogui.size()

# --- 1 EURO FILTER IMPLEMENTATION ---
class OneEuroFilter:
    def __init__(self, t0, x0, dx0=0.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def _alpha(self, rate, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def filter(self, t, x):
        t_e = t - self.t_prev
        if t_e <= 0.0:
            return self.x_prev

        rate = 1.0 / t_e

        # 1. Estimate and filter the velocity (derivative)
        dx = (x - self.x_prev) / t_e
        alpha_d = self._alpha(rate, self.d_cutoff)
        dx_hat = alpha_d * dx + (1.0 - alpha_d) * self.dx_prev

        # 2. Compute dynamic cutoff frequency based on velocity
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)

        # 3. Filter position
        alpha = self._alpha(rate, cutoff)
        x_hat = alpha * x + (1.0 - alpha) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat


# Download model weights if absent
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

# Filter instances for 2D screen coordinates
filter_x = None
filter_y = None

# Tuning Parameters:
# min_cutoff: Lower values (e.g. 0.1 - 0.5) eliminate micro-jitter when holding still.
# beta: Higher values (e.g. 0.005 - 0.05) eliminate lag during fast sweeps.
MIN_CUTOFF = 0.4
BETA = 0.015

margin = 0.15
is_left_clicked = False
is_right_clicked = False
PINCH_THRESHOLD = 0.04

print("1€ Filter Virtual Mouse active. Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Bounding box for cursor reachability
    cv2.rectangle(frame, (int(w * margin), int(h * margin)), 
                  (int(w * (1 - margin)), int(h * (1 - margin))), (0, 255, 0), 1)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    detection_result = detector.detect(mp_image)

    if detection_result.hand_landmarks:
        landmarks = detection_result.hand_landmarks[0]
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]

        # Raw target coordinates mapped to screen resolution
        raw_screen_x = np.interp(index_tip.x, [margin, 1 - margin], [0, screen_w])
        raw_screen_y = np.interp(index_tip.y, [margin, 1 - margin], [0, screen_h])

        # Initialize or update the 1 Euro Filters
        if filter_x is None or filter_y is None:
            filter_x = OneEuroFilter(now, raw_screen_x, min_cutoff=MIN_CUTOFF, beta=BETA)
            filter_y = OneEuroFilter(now, raw_screen_y, min_cutoff=MIN_CUTOFF, beta=BETA)
            smooth_x, smooth_y = raw_screen_x, raw_screen_y
        else:
            smooth_x = filter_x.filter(now, raw_screen_x)
            smooth_y = filter_y.filter(now, raw_screen_y)

        # Move cursor using filtered coordinates
        pyautogui.moveTo(smooth_x, smooth_y)

        # Draw tracking landmark
        ix, iy = int(index_tip.x * w), int(index_tip.y * h)
        cv2.circle(frame, (ix, iy), 6, (255, 0, 0), cv2.FILLED)

        # --- CLICK DETECTION ---
        dist_left = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        dist_right = math.hypot(thumb_tip.x - middle_tip.x, thumb_tip.y - middle_tip.y)

        # Left Click (Thumb + Index Pinch)
        if dist_left < PINCH_THRESHOLD:
            cv2.circle(frame, (ix, iy), 9, (0, 255, 0), cv2.FILLED)
            if not is_left_clicked:
                pyautogui.mouseDown(button='left')
                is_left_clicked = True
        else:
            if is_left_clicked:
                pyautogui.mouseUp(button='left')
                is_left_clicked = False

        # Right Click (Thumb + Middle Pinch)
        if dist_right < PINCH_THRESHOLD:
            mx, my = int(middle_tip.x * w), int(middle_tip.y * h)
            cv2.circle(frame, (mx, my), 9, (0, 0, 255), cv2.FILLED)
            if not is_right_clicked:
                pyautogui.click(button='right')
                is_right_clicked = True
        else:
            is_right_clicked = False

    else:
        filter_x, filter_y = None, None

    cv2.imshow("1 Euro Filter Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()