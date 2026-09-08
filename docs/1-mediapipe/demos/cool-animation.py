import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import urllib.request
import os

model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

def sort_points_clockwise(pts):
    centroid = np.mean(pts, axis=0)
    angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
    return pts[np.argsort(angles)]

avatar_path = 'anime_avatar.png'
if not os.path.exists(avatar_path):
    print(f"Error: Could not find '{avatar_path}'. Please place your anime image in this folder.")
    exit()

avatar_img = cv2.imread(avatar_path)

cap = cv2.VideoCapture(0)

smoothed_pts = None
SMOOTHING_FACTOR = 4.0
missing_frames = 0
MAX_MISSING_FRAMES = 5

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Scale the anime image to cover the entire camera frame dimensions
    avatar_full = cv2.resize(avatar_img, (w, h))

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    detection_result = detector.detect(mp_image)

    left_points = []
    right_points = []

    if detection_result.hand_landmarks:
        for i, landmarks in enumerate(detection_result.hand_landmarks):
            hand_category = detection_result.handedness[i][0].category_name
            
            pt_thumb = [landmarks[4].x * w, landmarks[4].y * h]
            pt_index = [landmarks[8].x * w, landmarks[8].y * h]
            
            if hand_category == 'Left':
                left_points = [pt_thumb, pt_index]
            elif hand_category == 'Right':
                right_points = [pt_thumb, pt_index]

    if len(left_points) == 2 and len(right_points) == 2:
        missing_frames = 0
        current_pts = np.array(left_points + right_points, dtype=np.float32)
        
        if smoothed_pts is None:
            smoothed_pts = current_pts
        else:
            smoothed_pts = smoothed_pts + (current_pts - smoothed_pts) / SMOOTHING_FACTOR
    else:
        missing_frames += 1
        if missing_frames > MAX_MISSING_FRAMES:
            smoothed_pts = None

    if smoothed_pts is not None:
        quad_pts = sort_points_clockwise(smoothed_pts).astype(np.float32)
        quad_pts_int = quad_pts.astype(np.int32)
        
        # 1. Create a polygonal mask matching the hand quadrilateral
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [quad_pts_int], 255)
        
        # 2. Extract live video outside the window, and anime image inside the window
        inverse_mask = cv2.bitwise_not(mask)
        background = cv2.bitwise_and(frame, frame, mask=inverse_mask)
        window_content = cv2.bitwise_and(avatar_full, avatar_full, mask=mask)
        
        # 3. Combine layers
        frame = cv2.add(background, window_content)
        
        # 4. Draw HUD borders
        cv2.polylines(frame, [quad_pts_int], isClosed=True, color=(0, 255, 255), thickness=2)
        for pt in quad_pts_int:
            cv2.circle(frame, tuple(pt), 6, (0, 255, 255), cv2.FILLED)
            cv2.circle(frame, tuple(pt), 12, (0, 255, 255), 1)

    cv2.imshow("Anime AR Window", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()