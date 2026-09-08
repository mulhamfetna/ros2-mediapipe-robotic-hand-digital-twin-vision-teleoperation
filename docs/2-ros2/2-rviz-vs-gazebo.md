# RViz vs Gazebo

Two tools that render a 3D robot on your screen and are otherwise nothing alike. Choosing wrongly
costs days, because the failure is not an error message — it is a tool quietly not doing the thing
you assumed it was doing.

RViz and Gazebo look identical at first glance—both render a 3D robot model on your screen—but they serve entirely opposite purposes in the ROS ecosystem.

| Feature | RViz (The Visualizer) | Gazebo (The Simulator) |
| --- | --- | --- |
| **Primary Role** | Displays what the robot *currently thinks* it is doing based on incoming sensor data and state topics. | Simulates a complete virtual world, including physics, gravity, friction, and collisions. |
| **Physics Engine** | **None.** It does not calculate forces, mass, or gravity. It only does forward kinematics (math mapping joint angles to bone positions). | **Full Physics.** Uses engines (like DART, ODE, or Bullet) to calculate how motors pull against weight, inertia, and contact forces. |
| **Data Flow** | Listens passively to ROS topics (`/tf`, `/joint_states`) and paints them on screen. | Acts as a virtual environment; it can *publish* simulated camera/IMU data and *subscribe* to motor commands. |
| **Resource Cost** | Lightweight. Runs smoothly even on modest hardware. | Heavyweight. Demands significant CPU/GPU power to calculate physical interactions. |

**When to Use Which**

* **Use RViz when debugging telemetry and kinematics:** If you want to verify that your MediaPipe hand tracking angles match your digital twin's joints in real-time, you pipe data into RViz. It shows you if your URDF axis definitions or coordinate frames are twisted. It is your visual debugger.
* **Use Gazebo when testing control algorithms or physics:** If you want to test whether your robotic hand can pick up a virtual ball without crushing it, or how motor controllers react to physical resistance and gravity, you load your model into Gazebo.

For your current project, RViz is what allowed you to see your 15-DOF hand mirror your movements. Gazebo would only enter the picture if you needed to test physical contact dynamics before flashing code to your actual hardware.