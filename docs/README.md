# Documentation

Engineering notes for the ROS 2 + MediaPipe robotic hand digital twin — written against the code
that actually runs in this repository, not against a general tutorial. Where the implementation
has a known rough edge, these notes say so rather than describing the ideal version.

Read them in order for the full pipeline, or jump to the layer you care about.

## 1. Vision — [`1-mediapipe/`](1-mediapipe/)

How a plain RGB webcam becomes 21 spatial landmarks.

| Doc | What it covers |
|---|---|
| [1. The two-stage pipeline](1-mediapipe/1-two-stage-pipeline.md) | BlazePalm detector + landmark regressor, and the temporal tracking loop that lets the detector sleep |
| [2. Networks and losses](1-mediapipe/2-networks-and-losses.md) | Depthwise separable convolutions, focal loss, the multi-task heads, and where the fake *z*-axis comes from |
| [3. Landmarks to angles](1-mediapipe/3-landmarks-to-angles.md) | The dot-product geometry that turns coordinates into 15 joint angles, including the two numerical traps |
| [4. The 1€ filter](1-mediapipe/4-one-euro-filter.md) | The jitter-versus-lag tradeoff, and a from-scratch implementation. **Not yet wired into this project** — see the doc for why it is the next obvious upgrade |
| [5. Demo gallery](1-mediapipe/5-demo-gallery.md) | The four standalone MediaPipe demos in `demos/`, what each one teaches, and how to run them |

## 2. Middleware — [`2-ros2/`](2-ros2/)

Why a distributed middleware earns its complexity, and how this project's graph is wired.

| Doc | What it covers |
|---|---|
| [1. Why ROS 2 at all](2-ros2/1-why-ros2.md) | Topics, DDS discovery, and the honest case for and against the framework tax |
| [2. RViz vs Gazebo](2-ros2/2-rviz-vs-gazebo.md) | Visualizer versus physics simulator — they look identical and are not remotely the same tool |
| [3. Building a package from scratch](2-ros2/3-building-a-package.md) | Workspace → package → node → `setup.py` → `colcon build`, the minimal six steps |
| [4. This project's node graph](2-ros2/4-this-projects-node-graph.md) | The actual topics, message types, rates and containers in *this* repository |

## 3. Kinematics — [`3-kinematics/`](3-kinematics/)

The translation layer between a human hand and a CAD assembly.

| Doc | What it covers |
|---|---|
| [1. Vector math to flexion](3-kinematics/1-vector-math.md) | Triplets, dot products, normalization, and linear interpolation onto mechanical limits |
| [2. URDF anatomy](3-kinematics/2-urdf-anatomy.md) | Links, joints, inertials, and the 15-DOF tree this hand actually exports as |
| [3. The mapping table](3-kinematics/3-the-mapping-table.md) | `JOINT_MAPPING` line by line, the calibration constants, and the one row that is currently wrong |
| [4. Joint nomenclature](3-kinematics/4-joint-nomenclature.md) | What MCP/PIP/DIP/IP/CMC mean, in English and Arabic, and how the mechanism's naming differs from the anatomy |

## 4. Infrastructure — [`4-docker-compose/`](4-docker-compose/)

Running ROS 2 Jazzy, a webcam and two GUI applications inside containers.

| Doc | What it covers |
|---|---|
| [1. Containerizing ROS 2](4-docker-compose/1-containerizing-ros2.md) | Every non-obvious flag in `docker-compose.yml`: host networking, X11 sockets, device passthrough, live mounts |
| [2. Command reference](4-docker-compose/2-command-reference.md) | The host and container commands that make the stack run, and what each one is defending against |
| [3. Gazebo physics](4-docker-compose/3-gazebo-physics.md) | Moving from a kinematic visualizer to a physics engine, and what the URDF still lacks |

## 5. CAD → URDF — [`5-onshape-urdf/`](5-onshape-urdf/)

Where a mechanical model becomes a robot description.

| Doc | What it covers |
|---|---|
| [1. CAD rules for a clean export](5-onshape-urdf/1-cad-rules.md) | Five habits in Onshape that remove all manual XML editing downstream |
| [2. Exporter setup](5-onshape-urdf/2-exporter-setup.md) | Installing `onshape-to-robot`, API keys, `config.json`, and the flags that matter |
| [3. Known export defects](5-onshape-urdf/3-known-export-defects.md) | What this specific export got wrong, how each was patched, and what is still outstanding |

## 6. Positioning — [`6-positioning/`](6-positioning/)

| Doc | What it covers |
|---|---|
| [1. How to pitch this](6-positioning/1-how-to-pitch-this.md) | Three honest framings of the work, depending on who is listening |

## Conventions in these docs

- Code references point at real files and are written as `path:line` so they stay checkable.
- Angles are in **radians** unless a degree symbol appears. The URDF, MediaPipe and ROS 2 all
  work in radians; degrees appear only to build intuition.
- "The pinky is called `twinky`" is not a typo in these docs. It is a legacy CAD name that
  propagated into the URDF and the Python mapping. See
  [known export defects](5-onshape-urdf/3-known-export-defects.md).
