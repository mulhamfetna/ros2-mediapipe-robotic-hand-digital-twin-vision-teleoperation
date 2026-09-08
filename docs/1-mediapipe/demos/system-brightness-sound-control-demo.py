import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
import subprocess
import urllib.request
import os

# 1. Auto-download the required Tasks API model weights
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print("Downloading hand_landmarker.task weights...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)
    print("Download complete.")

# 2. Initialize the modern Tasks API
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

# State trackers to prevent lagging the system with continuous terminal commands
last_volume = -1
last_brightness = -1
CHANGE_THRESHOLD = 3  

def set_volume(vol_percentage):
    """Uses PulseAudio/PipeWire to set system volume on Kubuntu"""
    global last_volume
    if abs(vol_percentage - last_volume) > CHANGE_THRESHOLD:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(vol_percentage)}%"], capture_output=True)
        last_volume = vol_percentage
        print(f"Volume set to: {int(vol_percentage)}%")

def set_brightness(bright_percentage):
    """Uses brightnessctl to set screen backlight"""
    global last_brightness
    if abs(bright_percentage - last_brightness) > CHANGE_THRESHOLD:
        subprocess.run(["brightnessctl", "set", f"{int(bright_percentage)}%"], capture_output=True)
        last_brightness = bright_percentage
        print(f"Brightness set to: {int(bright_percentage)}%")

cap = cv2.VideoCapture(0)
print("Starting Gesture Control... Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Mirror the frame so Left/Right hand classifications match your physical body
    frame = cv2.flip(frame, 1)
    
    # The Tasks API requires a specific mp.Image object
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    
    # Run inference
    detection_result = detector.detect(mp_image)

    # Parse the new output structure
    if detection_result.hand_landmarks:
        for i, hand_landmarks in enumerate(detection_result.hand_landmarks):
            
            # Handedness is now stored in a separate array mapping to the same index
            hand_category = detection_result.handedness[i][0].category_name
            
            thumb_tip = hand_landmarks[4]
            index_tip = hand_landmarks[8]
            
            h, w, _ = frame.shape
            cx1, cy1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            cx2, cy2 = int(index_tip.x * w), int(index_tip.y * h)
            
            # Draw interactive control points
            cv2.circle(frame, (cx1, cy1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (cx2, cy2), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(frame, (cx1, cy1), (cx2, cy2), (255, 0, 255), 3)
            
            # Calculate 2D Euclidean Distance using normalized coordinates
            distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
            
            # Interpolate distance (0.02 closed, 0.25 fully open) to a 0-100 percentage
            percentage = np.interp(distance, [0.02, 0.25], [0, 100])
            
            # Route to the correct system controller based on handedness
            if hand_category == 'Right':
                set_volume(percentage)
                cv2.putText(frame, f"Vol: {int(percentage)}%", (cx1, cy1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            elif hand_category == 'Left':
                set_brightness(percentage)
                cv2.putText(frame, f"Bright: {int(percentage)}%", (cx1, cy1 - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()