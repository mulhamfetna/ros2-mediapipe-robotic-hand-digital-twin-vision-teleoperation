# The Mapping Table

`JOINT_MAPPING` is the contract between the vision layer and the mechanical model. Fifteen rows,
each one binding a computed angle to a named joint and its physical range. Get a row wrong and
nothing errors — a finger simply moves incorrectly.

**The Landmark Triplet Engine (`compute_15_joint_angles`)**
MediaPipe outputs 21 global 3D landmark coordinates for a tracked hand. To calculate joint flexion, this function groups those coordinates into 15 anatomical triplets `(p1, p2, p3)`. For every triplet, it creates two directional vectors meeting at the joint pivot (`p2`) and computes the interior angle using the vector dot product formula. This outputs an array of 15 raw radian values representing the physical curvature of each finger joint.

**The Biometric Calibration Bounds**
`RAW_STRAIGHT_ANGLE` ($3.10$ radians or $\approx 177^\circ$) and `RAW_CURLED_ANGLE` ($1.60$ radians or $\approx 90^\circ$) establish the baseline normalization window. Because camera projections shift and human fingers vary, these constants define the expected physical limits of raw vector tracking, providing a stable frame of reference for the math that follows.

**The Translation Table (`JOINT_MAPPING`)**
This list serves as the hardware dictionary, bridging the 15 raw calculation indices (`0` through `14`) directly to the Onshape-exported URDF joint names. Each tuple dictates:

* The target URDF joint name (e.g., `thumb_mcp`, `index_pip`).
* The source index pointing to the corresponding raw computed angle.
* The physical open-state and closed-state radian limits extracted directly from your robot's URDF file.

**The Linear Interpolation Bridge (`map_raw_to_urdf_angles`)**
This loop processes each joint independently through two mathematical operations:

1. **Normalization (`flexion`)**: It takes the raw tracked angle, evaluates it against the straight baseline, and computes a ratio of how bent the finger is. `np.clip` restricts this value strictly between `0.0` (fully open) and `1.0` (fully closed) so sudden tracking glitches or over-extensions do not break the calculation.
2. **Scaling (`urdf_angle`)**: It applies linear interpolation (`lerp`) to map that `0.0`–`1.0` ratio onto your CAD model's exact mechanical constraints, ensuring a natural transition between human motion and digital twin movement.

The resulting parallel arrays (`joint_names` and `mapped_positions`) are then packed into the ROS 2 `JointState` message to drive the 3D meshes in RViz.