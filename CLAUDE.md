# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A vision-driven digital twin of a 15-DOF robotic hand: a webcam feed goes through MediaPipe Hands,
21 landmarks become 15 joint angles via vector math, those angles are remapped onto the mechanical
limits of a CAD-exported URDF, and published to ROS 2 so RViz (and optionally Gazebo) animates the
model. Everything runs in Docker containers on ROS 2 Jazzy — there is no host-side ROS install and
no test/lint suite.

## Running the stack

```bash
./setup_host.sh                     # xhost +local:root, /tmp/runtime-root, DRI check — required before first up
docker compose up --build           # starts the three active services; gazebo_sim is commented out in the compose file
docker compose up ros_rviz hand_tracker   # the usual pair: RViz twin + tracker
docker compose logs -f hand_tracker
docker compose restart hand_tracker  # picks up Python/URDF edits — see below
```

Source trees and the URDF are **bind-mounted**, and both Python containers re-run `colcon build` in
their entrypoint. So edits to `hand_tracker/src/`, `topic_sniffer/src/`, `ros_rviz/urdf/robot.urdf`
or `ros_rviz/config.rviz` need only `docker compose restart <service>`; rebuild the image only when
a `Dockerfile` or a pip/apt dependency changes.

All services use `network_mode: host`, `privileged: true`, and `ROS_DOMAIN_ID=42` — they talk over
the host's DDS, not a compose network. Debug from the host with a `ros:jazzy` container on the same
domain ID, or `docker compose exec`.

## Architecture and its coupling points

`hand_tracker_node.py` is where nearly all the logic lives. At 10 Hz it publishes two topics:

- `/hand/joint_angles` — `hand_msgs/JointAngles` (`float32[15]`), the **raw** MediaPipe joint angles
  in radians. Consumed by `topic_sniffer`; this is the debug/telemetry channel.
- `/joint_states` — `sensor_msgs/JointState` with **URDF joint names and URDF-space angles**. This
  is what actually drives `robot_state_publisher` → TF → RViz/Gazebo. The tracker deliberately
  replaces `joint_state_publisher`, which is why the compose `command:` for `ros_rviz` runs
  `robot_state_publisher` + `rviz2` directly instead of the `urdf_tutorial display.launch.py` in
  that service's Dockerfile `CMD` (the compose command wins).

Three couplings will silently break the twin if edited independently:

1. **`JOINT_MAPPING` ↔ `ros_rviz/urdf/robot.urdf`.** Each tuple is
   `(urdf_joint_name, mediapipe_triplet_index, open_at)` where `open_at` is `'lower'` or
   `'upper'` — which end of that joint's range is the open hand. **The angles themselves are no
   longer stored here**: `resolve_joint_mapping()` parses `<limit lower/upper>` out of the URDF at
   node startup (`URDF_PATH`, default `/urdf/robot.urdf`, mounted read-only into the container).
   Editing the URDF limits therefore needs no Python change. Renaming a joint still does — and now
   raises at startup instead of silently freezing that finger. **The pinky is named `twinky`** in
   the CAD and therefore in the URDF and the mapping.
2. **`RAW_STRAIGHT_ANGLE` / `RAW_CURLED_ANGLE`** (3.10 / 1.60 rad) define the normalization window
   from raw MediaPipe angle to 0.0–1.0 flexion, which is then linearly interpolated between the
   URDF limits. These are empirical calibration constants, not derived — tune here, not in the
   per-joint table, when the whole hand under/over-flexes.
3. **`hand_msgs` is duplicated** at `hand_tracker/src/hand_msgs/` and `topic_sniffer/src/hand_msgs/`
   (currently byte-identical). Each container builds its own copy, and mismatched definitions
   produce a silently dead subscription. Edit both.

The URDF hardcodes mesh paths as `file:///workspace/assets/part_N.stl`, and `docker-compose.yml`
hardcodes the host bind mount `/mnt/data/projects/ros2-mediapipe-robotic-hand-digital-twin-vision-teleoperation:/workspace`. Moving or cloning
this repo to another path breaks `ros_rviz` and `gazebo_sim` until both are updated.

`gazebo_sim/entrypoint.sh` launches `gz sim empty.sdf`, sleeps 4 s, then spawns the same URDF via
`ros_gz_sim create`. Gazebo needs `<inertial>` tags that the Onshape export does not fully provide —
see `docs/4-docker-compose/3-gazebo-physics.md` before touching that path.

## Regenerating the URDF from CAD

The root `.venv` (Python 3.14) holds `onshape-to-robot`; the root `config.json` holds the Onshape
document/workspace/element IDs and `.env` holds `ONSHAPE_API` / `ONSHAPE_ACCESS_KEY` /
`ONSHAPE_SECRET_KEY` (gitignored — never commit). `docs/5.onshape/3.md` documents the export
workflow and which flags matter (`mergeSTLs: "no"` and `ignoreLimits: false` are load-bearing —
merging destroys the articulated knuckles, ignoring limits discards the Onshape mate limits the
kinematic mapping depends on). Re-export overwrites the generated URDF, so re-apply the
`file:///workspace/assets/` mesh paths and re-verify `JOINT_MAPPING` afterwards.

## Repository conventions

- `docs/` is hand-written technical prose organised by topic (`1-mediapipe/`, `2-ros2/`,
  `3-kinematics/`, `4-docker-compose/`, `5-onshape-urdf/`, `6-positioning/`), indexed by
  `docs/README.md` — background material for articles/talks, not generated. It is written against
  the real code: `docs/5-onshape-urdf/3-known-export-defects.md` is the running list of what the
  CAD export got wrong, including the live `ring_mcp` limits mismatch.
- `logs/` is the `topic_sniffer` container's colcon log directory (mounted at `/ws_sniffer/log`),
  carrying a `COLCON_IGNORE` and `latest`/`latest_build` symlinks. It churns on every run; don't
  treat its diffs as meaningful changes.
- Licensed **AGPL-3.0** with a `CITATION.cff`. `README.md` and `CITATION.cff` still contain
  placeholders (`YOUR_USERNAME`, `10.5281/zenodo.XXXXXXX`, the Onshape link) to be filled at
  publication.
