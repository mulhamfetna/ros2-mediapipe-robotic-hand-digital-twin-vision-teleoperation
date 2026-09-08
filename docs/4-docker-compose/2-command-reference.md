# Command Reference

The commands that make the stack run, and — more usefully — what each one is defending against.
Every entry here corresponds to a failure that actually happened during development.

A breakdown of the terminal commands needed to get the GUI and the physics engine working, and what each one is actually defending against.

### 1. `xhost +local:root`

**What it does:** Unlocks your computer's display server security.
**Why you needed it:** Your Kubuntu host machine uses the X11 display server to draw windows on your monitor. X11 is highly paranoid by design—it aggressively blocks external or isolated processes from drawing on your screen to prevent malicious software from keylogging or hijacking your desktop. Because Docker containers run as an isolated `root` user, X11 treats them as hostile strangers and blocks RViz and Gazebo from rendering (throwing the `Authorization required` error). This command tells your host: *"Allow any local process running as root to project graphics onto my monitor."*

### 2. `docker compose up --force-recreate`

**What it does:** Destroys and rebuilding the container states.
**Why you needed it:** If a container crashed or was stopped, simply typing `docker compose up` tells Docker to wake up the existing, sleeping containers with their old configurations. `--force-recreate` commands Docker to completely trash the existing containers and spin up fresh ones from scratch. This was required to force the containers to recognize the new X11 display permissions you just unlocked on the host.

### 3. `docker exec -it gazebo_sim bash`

**What it does:** Teleports your terminal session into a running container.
**Why you needed it:** Your containers were running in the background (or logging to your main terminal window), meaning you had no way to type commands *inside* the Gazebo environment.

* `exec`: Execute a command inside a live container.
* `-it`: Interactive TTY (allocates a live, typing terminal session instead of just running a silent background task).
* `gazebo_sim`: The target container name.
* `bash`: The shell program you want to open.

This punched a hole through the Docker isolation and dropped you directly into the Gazebo container's command line.

### 4. `ros2 run ros_gz_sim create -file /workspace/ros_rviz/urdf/robot.urdf -name robotic_hand -z 0.5`

**What it does:** Injects a physical object into the running simulation.
**Why you needed it:** Gazebo starts as a completely empty universe (`empty.sdf`). It does not automatically know your robot exists.

* `ros2 run ros_gz_sim create`: Executes the specific bridging node responsible for translating a URDF file into a Gazebo physics entity.
* `-file`: Points to the live-mounted URDF blueprint on your drive.
* `-name robotic_hand`: Tags the object in the Gazebo Entity Tree so you can right-click it, track it, or apply joint controllers to it later.
* `-z 0.5`: Spawns the hand 0.5 meters above the origin. If you spawned it at `0.0`, the collision meshes of the hand would intersect with the ground plane mesh, causing the physics engine to violently launch the hand into the sky to resolve the mathematical collision conflict.