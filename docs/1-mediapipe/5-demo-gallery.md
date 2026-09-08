# Demo Gallery

Four standalone MediaPipe programs live in [`demos/`](demos/). None of them is part of the robotic
hand pipeline — they exist because each one isolates a single technique that the main project
depends on, in a form you can run in ten seconds without Docker, ROS 2 or a URDF.

If you are learning this stack, run them in the order below. Each adds exactly one idea.

## A note on the two MediaPipe APIs

The demos and the ROS node use **different MediaPipe APIs**, which is worth understanding before
copying code between them.

| | Main project | The demos |
|---|---|---|
| API | Legacy Solutions | Modern Tasks |
| Import | `mp.solutions.hands` | `mediapipe.tasks.python.vision` |
| Model | Bundled in the pip wheel | Downloaded `.task` file |
| Input | Raw NumPy array | `mp.Image` wrapper |
| Landmarks | `results.multi_hand_landmarks` | `detection_result.hand_landmarks` |
| Handedness | Parallel `multi_handedness` | Parallel `handedness` array |

The Solutions API is deprecated upstream but still shipped and still simpler for a single
fixed-configuration pipeline, which is why `hand_tracker_node.py` uses it. The Tasks API is the
supported path forward and gives finer control over confidence thresholds, so the demos use it.
Landmark indices and semantics are identical across both — landmark 4 is the thumb tip in either.

The Tasks demos fetch their weights on first run:

```python
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, model_path)
```

That 7.8 MB file is gitignored rather than committed — it is a redistributable artifact with a
canonical URL, and there is no reason for it to live in a DOI-archived repository.

## Running them

The demos need a webcam and a desktop session; they are not containerized.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install mediapipe opencv-python numpy
cd docs/1-mediapipe/demos
python3 Virtual-Air-Canvas.py     # press q to quit
```

Two demos need extras: `hand-mouse.py` requires `pyautogui`, and
`system-brightness-sound-control-demo.py` shells out to `pactl` and `brightnessctl`, so it is
Linux-only and assumes PulseAudio/PipeWire.

## 1. `Virtual-Air-Canvas.py` — pinch detection and state

**The idea:** a gesture is not a pose, it is a *state transition*.

Draws a coloured trail that follows your index fingertip, but only while thumb and index are
pinched. Pinching thumb and middle clears the canvas.

The technique to steal is the pinch test — a normalized Euclidean distance against a threshold:

```python
dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
```

Because MediaPipe coordinates are normalized to the frame, this distance is scale-invariant: the
same threshold works whether your hand fills the frame or sits in a corner. The demo also keeps
`prev_x, prev_y` between frames, so it draws *segments* rather than dots — the first hint that
temporal state is what separates a gesture from a snapshot.

**Relevance to the main project:** the tracker's per-frame `if results.multi_hand_landmarks:` branch
is the same structure, and the same question — what do you do on the frames where there is no
hand? — produces [the fallback open-hand pose](../2-ros2/4-this-projects-node-graph.md#the-fallback-pose).

## 2. `system-brightness-sound-control-demo.py` — handedness and continuous mapping

**The idea:** map a continuous distance onto a continuous output, and know which hand is which.

Left hand controls system volume, right hand controls screen brightness, both by the thumb–index
gap. Two lessons:

**Handedness comes from a parallel array**, indexed alongside the landmarks:

```python
hand_category = detection_result.handedness[i][0].category_name
```

And it is only correct if you mirror the frame first (`cv2.flip(frame, 1)`), because MediaPipe
labels hands from the *camera's* point of view — your right hand appears on the camera's left.

**Rate-limiting matters when output is expensive.** Every frame that changed the volume would spawn
a `pactl` subprocess 30 times a second and lock up the desktop, so the demo gates on a deadband:

```python
CHANGE_THRESHOLD = 3
if abs(vol_percentage - last_volume) > CHANGE_THRESHOLD:
```

**Relevance to the main project:** the distance-to-percentage mapping here is the same shape as
[the flexion normalization](3-landmarks-to-angles.md) — take a raw geometric measurement, define
its expected physical range, and rescale it linearly onto an output range.

## 3. `hand-mouse.py` — the 1€ filter under real load

**The idea:** raw landmarks are far too noisy to drive anything that demands precision.

A full virtual mouse: index fingertip moves the cursor, thumb–index pinch is left click (with
proper press/release state so dragging works), thumb–middle is right click. It carries a complete
`OneEuroFilter` implementation, applied independently to screen X and Y.

Run it once with the filter bypassed and once with it active. Unfiltered, the cursor is unusable —
it quivers several pixels while your hand is perfectly still, because the landmark regressor's
sub-pixel output is not temporally stable. Filtered, it locks in place when still and still tracks
fast flicks without lag.

The demo also maps a margin-inset region of the camera frame to the full screen:

```python
raw_screen_x = np.interp(index_tip.x, [margin, 1 - margin], [0, screen_w])
```

so you can reach the screen edges without moving your hand out of frame.

**Relevance to the main project:** see [the 1€ filter document](4-one-euro-filter.md). This jitter
is present in the robotic hand pipeline too — it is simply less visible, because the twin's mesh
rotation is a lower-frequency output than a cursor position, and because publishing at 10 Hz
subsamples some of the noise away.

## 4. `cool-animation.py` — two hands as a geometric frame

**The idea:** landmarks define arbitrary geometry, not just gestures.

Both hands pinch, and the four fingertips become the corners of a quadrilateral that acts as a
window into a second image ([`anime_avatar.png`](demos/anime_avatar.png)) — an AR portal you can
resize and rotate by moving your hands.

Three techniques worth reading:

**Ordering the corners.** Four points arrive in landmark order, not spatial order, and filling a
polygon with mis-ordered vertices produces a bowtie. The demo sorts by angle about the centroid:

```python
angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
return pts[np.argsort(angles)]
```

**Compositing by mask** rather than pixel loops — `fillPoly` to build the mask, `bitwise_and` twice
against mask and inverse, then `cv2.add` to combine. This is fast because it stays in OpenCV's
vectorized path.

**Exponential smoothing with a grace period.** A simple first-order filter,

```python
smoothed_pts = smoothed_pts + (current_pts - smoothed_pts) / SMOOTHING_FACTOR
```

plus a `MAX_MISSING_FRAMES = 5` counter, so a single dropped detection does not collapse the
portal. Compare this against the 1€ filter in demo 3: it is the fixed-cutoff version, and you can
feel the difference — it either lags on fast motion or quivers when still, and one constant cannot
fix both.

## What none of them do

All four are single-file scripts with no message passing, no coordinate frames and no notion of a
robot. That is the gap the rest of this repository fills: once a second consumer needs the same
hand data, or the output has to drive a kinematic tree with mechanical limits, the single-file
approach stops scaling — and that is
[the honest argument for ROS 2](../2-ros2/1-why-ros2.md).
