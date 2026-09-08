# This Project's Node Graph

The previous three documents describe ROS 2 in general. This one describes the graph that actually
runs when you type `docker compose up` in this repository — the real topics, message types, rates
and containers, with the surprising parts called out.

## The graph in one picture

```text
  /dev/video0
       │
       ▼
┌──────────────────────┐
│   hand_tracker       │  container: hand_tracker
│   node: hand_tracker_node
│   10 Hz timer        │
└───────┬──────────┬───┘
        │          │
        │          └────────────────────────────┐
        ▼                                       ▼
  /hand/joint_angles                       /joint_states
  hand_msgs/JointAngles                    sensor_msgs/JointState
  float32[15], RAW radians                 15 named joints, URDF radians
        │                                       │
        ▼                                       ▼
┌──────────────────┐              ┌───────────────────────────┐
│  topic_sniffer   │              │  robot_state_publisher    │  container: ros_rviz
│  node: sniffer   │              │  + /robot_description     │
│  prints to stdout│              └─────────────┬─────────────┘
└──────────────────┘                            │  /tf, /tf_static
                                                ▼
                                         ┌─────────────┐
                                         │    rviz2    │
                                         └─────────────┘
```

All four containers share `ROS_DOMAIN_ID=42` and run with `network_mode: host`, so discovery
happens over the host's own network interface rather than a Docker bridge. There is no compose
network to inspect — from the host, `ROS_DOMAIN_ID=42 ros2 topic list` inside any `ros:jazzy`
container sees the whole graph.

## The two published topics, and why there are two

`hand_tracker_node.py` publishes **twice per frame**, and the distinction matters:

| Topic | Type | Contents | Consumer |
|---|---|---|---|
| `/hand/joint_angles` | `hand_msgs/JointAngles` | `float32[15]` — the **raw** interior angles straight out of the dot-product math, in radians, roughly 1.6–3.1 | `topic_sniffer` |
| `/joint_states` | `sensor_msgs/JointState` | 15 **named** joints with positions already remapped into the URDF's mechanical limits | `robot_state_publisher` |

The first is telemetry: unprocessed measurement, useful for debugging the vision layer in
isolation. The second is the command signal that actually animates the twin. If the model moves
wrongly, comparing the two tells you immediately whether the fault is in the vision (raw angles
look wrong) or the mapping (raw angles fine, mapped angles wrong).

## The joint_state_publisher that isn't there

Standard ROS 2 URDF demos run three nodes: `joint_state_publisher` invents joint positions,
`robot_state_publisher` turns them into transforms, and `rviz2` draws them.

**This project deliberately removes the first one.** The tracker *is* the joint state publisher —
it publishes `/joint_states` itself at 10 Hz from live camera data. Running both would produce two
publishers fighting over the same topic, and the model would flicker between the tracked pose and
whatever the slider GUI last held.

This is why the compose service overrides the image's default command:

```yaml
command: >
  bash -c "
    source /opt/ros/jazzy/setup.bash &&
    ros2 run robot_state_publisher robot_state_publisher /workspace/ros_rviz/urdf/robot.urdf &
    exec rviz2 -d /workspace/ros_rviz/config.rviz
  "
```

The `ros_rviz/Dockerfile` still carries a `CMD` that launches `urdf_tutorial display.launch.py`
with `jsp_gui:=false`. That path works standalone, but the compose `command:` wins — and it is the
one used in practice, because it also loads the saved `config.rviz` view.

## The custom message package

`hand_msgs` is a minimal interface package containing exactly one definition:

```text
# hand_msgs/msg/JointAngles.msg
float32[15] angles
```

A fixed-size array, not a `float32[]`, so the ABI is stable and a malformed message cannot silently
resize. It is built with `ament_cmake` + `rosidl_default_generators`, not `ament_python`, because
message generation requires the C++ toolchain even for a Python-only consumer.

**The package is duplicated.** It exists at both `hand_tracker/src/hand_msgs/` and
`topic_sniffer/src/hand_msgs/`, and each container compiles its own copy at startup via the
`colcon build --packages-select hand_msgs` in its entrypoint. The two copies are currently
byte-identical, and they must stay that way: DDS matches publishers to subscribers by type hash, so
a field added to one copy and not the other produces no error — just a subscriber that silently
never fires.

## Rate: 10 Hz, not 30

```python
self.timer = self.create_timer(1.0 / 10.0, self.timer_callback)
```

The camera delivers ~30 FPS and MediaPipe can keep up with it on CPU, but the ROS side runs at
**10 Hz**. The timer callback does the frame grab, the inference, the mapping and both publishes
synchronously, so the tracker's real ceiling is one full pipeline pass per tick. 10 Hz is smooth
enough for a visual twin and leaves headroom on a laptop CPU that is simultaneously rendering
RViz.

Raising it means editing the timer, and — past roughly 20 Hz — moving the capture off the callback
thread so a slow frame read cannot stall the publisher.

## The fallback pose

If MediaPipe finds no hand in a frame, the node does not skip publishing. It publishes a synthetic
open hand:

```python
msg.angles = [RAW_STRAIGHT_ANGLE] * 15
```

All fifteen raw angles are set to 3.10 rad, which maps to every joint's open limit. The practical
effect is that the twin springs back to a flat palm the moment tracking is lost, rather than
freezing in the last tracked pose. You can see this directly in `topic_sniffer` output: a wall of
`np.float32(3.1)` means "no hand in frame", not "hand held perfectly straight".

Whether that is the right behaviour depends on the application — for a physical hand, snapping to
open on a dropped frame would be a safety problem, and a hold-last-pose with a timeout would be the
conservative choice.

## Inspecting the running graph

Everything below assumes the stack is up. Run from the host with a throwaway container on the same
domain:

```bash
docker run --rm -it --network host -e ROS_DOMAIN_ID=42 ros:jazzy \
  bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic list"
```

Or, more simply, exec into a container that is already running:

```bash
docker compose exec ros_rviz bash -c \
  "source /opt/ros/jazzy/setup.bash && ros2 topic hz /joint_states"
```

Useful checks:

| Command | Answers |
|---|---|
| `ros2 topic hz /joint_states` | Is the tracker actually publishing at 10 Hz, or stalling on frame reads? |
| `ros2 topic echo /joint_states --once` | Are the joint *names* right? A typo here means RViz silently ignores that joint |
| `ros2 run tf2_tools view_frames` | Is the TF tree complete from `base_link` to every fingertip? |
| `docker compose logs -f topic_sniffer` | Raw angles — the vision layer in isolation |

The name check is the one that catches the most time-consuming class of bug. `robot_state_publisher`
does not warn about a `JointState` entry naming a joint that does not exist in the URDF; it just
drops it. A finger that refuses to move while the other four work is almost always a name mismatch,
not a math error.
