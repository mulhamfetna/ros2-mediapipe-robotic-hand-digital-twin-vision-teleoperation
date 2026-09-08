import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
import urllib.request
import os

# Auto-download the required Tasks API model weights
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print("Downloading hand_landmarker.task weights...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)

# Initialize the Tasks API
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

# Memory variables for the drawing logic
canvas = None
prev_x, prev_y = 0, 0
is_drawing = False

print("Air Canvas Started. \n - Pinch Thumb + Index to DRAW. \n - Pinch Thumb + Middle to CLEAR. \n - Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: 
        break

    frame = cv2.flip(frame, 1)
    
    # Initialize the blank canvas array to perfectly match the webcam resolution
    if canvas is None:
        canvas = np.zeros_like(frame)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    detection_result = detector.detect(mp_image)

    if detection_result.hand_landmarks:
        hand_landmarks = detection_result.hand_landmarks[0]
        
        index_tip = hand_landmarks[8]
        thumb_tip = hand_landmarks[4]
        middle_tip = hand_landmarks[12]
        
        h, w, _ = frame.shape
        ix, iy = int(index_tip.x * w), int(index_tip.y * h)
        
        # Calculate pinch distances using normalized coordinates
        dist_draw = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        dist_clear = math.hypot(thumb_tip.x - middle_tip.x, thumb_tip.y - middle_tip.y)
        
        # LOGIC: Thumb + Middle Pinch = CLEAR CANVAS
        if dist_clear < 0.05:  
            canvas = np.zeros_like(frame)
            cv2.putText(frame, "CANVAS CLEARED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            is_drawing = False
            
        # LOGIC: Thumb + Index Pinch = DRAW NEON LINE
        elif dist_draw < 0.05: 
            if not is_drawing:
                prev_x, prev_y = ix, iy
                is_drawing = True
            
            # Draw on the memory buffer
            cv2.line(canvas, (prev_x, prev_y), (ix, iy), (0, 255, 255), 6)
            # Draw an interactive brush tip directly on the frame
            cv2.circle(frame, (ix, iy), 8, (0, 255, 255), cv2.FILLED)
            prev_x, prev_y = ix, iy
            
        # LOGIC: Hand Open = HOVER STATE
        else:
            is_drawing = False
            cv2.circle(frame, (ix, iy), 8, (200, 200, 200), 2)

    # Use cv2.add to overlay the pure black canvas onto the webcam feed
    final_output = cv2.add(frame, canvas)
    
    cv2.imshow("Virtual Air Canvas", final_output)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()