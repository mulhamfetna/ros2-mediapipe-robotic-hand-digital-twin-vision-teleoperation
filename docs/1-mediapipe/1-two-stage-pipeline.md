# The Two-Stage Pipeline

MediaPipe Hands is the vision layer of this project — the thing that turns a webcam frame into
21 numbered points. Understanding that it is *two* networks rather than one explains both its
speed and every way it fails.

MediaPipe Hands is not a single neural network. It is a two-stage cascaded pipeline consisting of a detector and a regressor.

### Stage 1: BlazePalm (The Detector)

* **Function:** An SSD (Single Shot Detector) operating on the full input frame to find the hand.
* **The Engineering Trick:** Attempting to detect fingers is computationally expensive because they articulate, occlude each other, and vary wildly in shape. BlazePalm bypasses this by training the network to detect only the **rigid bounding box of the palm**.
* **Architecture:** It uses a feature extractor similar to MobileNetV3, combined with an encoder-decoder (FPN-like) structure to maintain high-resolution context. It outputs an oriented, cropped bounding box of the hand.
* **Failure Mode:** If the palm is completely occluded (e.g., pointing directly at the camera with fingers blocking the palm), BlazePalm fails, and tracking drops.

### Stage 2: Hand Landmark Model (The Regressor)

* **Function:** This network ignores the full frame and operates *only* on the cropped palm tensor provided by Stage 1.
* **Output:** It is a pure regression network. The final dense layer outputs a vector of 63 continuous floats (21 landmarks $\times$ 3 spatial coordinates: $x, y, z$) plus a handedness score (left/right) and a confidence score.
* **The 2.5D Depth Illusion ($z$-axis):** Your webcam does not have a depth sensor. MediaPipe fakes the $z$-axis through relative scale estimation. The network is trained on a massive dataset of synthetic 3D hands. It anchors the $z$-origin $(0,0,0)$ to the wrist (Landmark 0). As the perceived 2D spread of the fingers shrinks, the network mathematically infers that the depth ($z$) is pushing further away from the wrist. It is not true metric depth; it is relative depth.

### The Temporal Tracking Loop

In your `hand_tracker_node.py`, you initialized the model with `min_tracking_confidence=0.5` and `min_detection_confidence=0.5`.

MediaPipe is capable of running at 30+ FPS on a CPU because **Stage 1 (BlazePalm) almost never runs.**

1. Frame 1: BlazePalm scans the whole image, finds the palm, and passes the crop to the Regressor.
2. Frame 2: MediaPipe skips BlazePalm entirely. It assumes the hand is roughly in the same spot, applies a slight margin to the bounding box from Frame 1, and feeds that directly to the Regressor.
3. This loop continues infinitely until the Regressor's confidence drops below your 0.5 threshold (due to fast movement or occlusion). Only then does the pipeline flush the cache and wake up BlazePalm to scan the full frame again.
