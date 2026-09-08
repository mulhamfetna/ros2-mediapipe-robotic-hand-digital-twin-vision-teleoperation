# Known Export Defects

[The CAD rules](1-cad-rules.md) describe how to get a clean export. This document is the honest
accounting of what *this* export actually produced, what was patched by hand, and what is still
outstanding. Every item was verified against `ros_rviz/urdf/robot.urdf` and
`hand_tracker/src/hand_tracker_node.py` as they currently stand.

## 1. The pinky is called `twinky` — everywhere

**Status:** Not fixed. Propagated by design.

A legacy name in the Onshape mate tree exported straight into the URDF, because
`onshape-to-robot` uses the mate name verbatim as `<joint name="...">`:

```xml
<joint name="twinky_dip" type="revolute">
<joint name="twinky_pip" type="revolute">
<joint name="twinky_mcp" type="revolute">
```

Since a `JointState` message is matched to the URDF by exact string, the Python mapping had to
adopt the same spelling:

```python
# PINKY (Twinky in CAD)
('twinky_mcp', 12,  0.000, -1.571),
('twinky_pip', 13,  0.000,  1.571),
('twinky_dip', 14,  0.000, -1.571),
```

Renaming is a three-place edit that must happen atomically — the Onshape mates, the URDF, and
`JOINT_MAPPING` — or the pinky silently stops moving while everything else works. It was left
alone deliberately: the cost is cosmetic, the risk of a partial rename is not. The real fix belongs
upstream in the CAD, before the next export.

## 2. `ring_mcp` is mapped to limits it does not have

**Status:** Outstanding. The one genuine numerical defect in the pipeline.

Fourteen of the fifteen rows in `JOINT_MAPPING` transcribe their joint's `<limit>` values exactly.
`ring_mcp` does not:

| Source | Open | Closed |
|---|---|---|
| `JOINT_MAPPING` in `hand_tracker_node.py` | `0.000` | `-1.571` |
| `<limit>` in `robot.urdf` | `0.39671` | `-1.17409` |

Neither endpoint matches. At full curl the node commands **−1.571 rad** into a joint whose
mechanical lower bound is **−1.174 rad** — roughly 23° past its stop.

`robot_state_publisher` does not enforce URDF limits; it applies whatever transform it is handed.
So RViz shows no error, no warning, and no obviously broken geometry — just a ring knuckle that
over-rotates slightly further than the mechanism physically could. It would become a hard failure
the moment this drove either a physics engine or real servos.

The cause is chronological. `ring_mcp` originally exported with the same generic ±1.5708 bounds as
the other fingers (see defect 3); the mapping was written against those. The CAD later gained a
real limit for that mate and the URDF was re-exported, but the Python table was not updated.

**The fix** is to bring the row in line with the joint it drives:

```python
('ring_mcp',    9,  0.397, -1.174),
```

## 3. The ring finger's MCP mate was missing entirely

**Status:** Fixed.

The first export produced no distinct `ring_mcp` joint. Duplicating a finger sub-assembly in
Onshape copies its mates *and their names*, so the ring finger arrived carrying the pinky's
`twinky_mcp` — a duplicate joint name, which the exporter resolved by dropping one.

This left a stale instruction in the source, which is no longer accurate:

```python
# RING (Requires manual URDF fix: rename duplicate 'twinky_mcp' to 'ring_mcp')
```

The URDF today contains a properly distinct `ring_mcp` with its own limits, so that comment
describes work already done and should be deleted. The generalized lesson is
[CAD rule 1](1-cad-rules.md): rename every mate in a duplicated sub-assembly *before* exporting.

## 4. Mesh paths are absolute container paths

**Status:** Intentional patch, but it makes the URDF non-portable.

The 32 mesh references do not use the conventional `package://` scheme. They are absolute paths
into the container's mount point:

```xml
<mesh filename="file:///workspace/assets/part_4.stl"/>
```

This works because `docker-compose.yml` bind-mounts the repository at `/workspace`, and it sidesteps
needing a real ROS package with an `ament_index` entry just to resolve meshes. The costs are real
though:

- The URDF cannot be loaded outside a container without those paths existing on the host.
- The bind mount source in `docker-compose.yml` is itself an absolute host path
  (`/mnt/data/projects/ros-robotic-hand`), so **cloning this repo anywhere else breaks both the
  mount and the meshes** until that line is edited.
- Re-exporting from Onshape overwrites the paths, so the patch has to be reapplied every time.

A portable version would wrap the description in a `hand_description` package and use
`package://hand_description/assets/part_4.stl`.

## 5. Inertials are present and correct — the Gazebo gap is elsewhere

**Status:** Not a defect. Worth recording because it is commonly assumed to be one.

The Onshape parts *do* carry material assignments, so the exporter computed real physical
properties for every link:

```xml
<inertial>
  <origin xyz="0.0366664 0.0353317 0.1069" rpy="0 0 0"/>
  <mass value="0.0611462"/>
  <inertia ixx="2.7277e-05" ixy="-0" ixz="8.34061e-07"
           iyy="4.36562e-05" iyz="-0" izz="1.87189e-05"/>
</inertial>
```

Link masses run from 1.86 g at the fingertips to 61 g for the palm, with full inertia tensors.
`base_link` alone carries the conventional `1e-09` dummy mass, which is correct for a massless
root anchor.

So the reason [the Gazebo path](../4-docker-compose/3-gazebo-physics.md) does not yet give a
working physics twin is **not** missing inertia. It is that the URDF describes geometry without
actuation:

- no `<transmission>` blocks,
- no `<gazebo>` plugin block loading `gz_ros2_control`,
- and therefore no controller subscribing to commands.

Spawned into Gazebo as-is, the hand is a passive rigid-body assembly: it will fall under gravity
and its joints will swing freely, and `/joint_states` will not drive it, because nothing in the
simulation is listening. Closing that gap is a controller-plumbing task, not a CAD one.

## 6. Joint axes are all `0 0 1` — by luck of good CAD, not by patch

**Status:** Clean. Recorded as a positive control.

Every revolute joint in the export rotates about its own local Z:

```xml
<axis xyz="0 0 1"/>
```

That is what [CAD rule 3](1-cad-rules.md) is meant to guarantee, and it held. It is worth checking
after every re-export, because the failure mode is memorable: fingers that bend sideways, or a
whole digit that inverts through the palm. Nothing warns you — the transform math is perfectly
valid, it is simply describing the wrong hinge.

## Summary

| # | Defect | Status | Cost if ignored |
|---|---|---|---|
| 1 | Pinky named `twinky` | Open, cosmetic | Confusion only |
| 2 | `ring_mcp` limits mismatch | **Open, real** | Commands 23° past the mechanical stop |
| 3 | Missing `ring_mcp` joint | Fixed | — (stale comment remains in source) |
| 4 | Absolute mesh paths | Patched, fragile | Repo is not relocatable; patch lost on re-export |
| 5 | Inertials | Correct | — |
| 6 | Joint axes | Correct | — |

Only defect 2 changes what appears on screen today. Defect 4 is the one that will bite the next
person who clones the repository.
