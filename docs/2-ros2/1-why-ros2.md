# Why ROS 2 At All

The honest version of the question every mechatronics engineer asks the first time they meet this
framework: why not just open a socket?

Building raw sockets with an ESP32 is infinitely cleaner on day one, and every mechatronics engineer hits that exact wall where ROS 2 feels like a massive, over-engineered tax just to move a few servos. The brutal truth is that ROS 2 is not a plug-and-play toy; it is a distributed middleware designed to solve nightmares you only encounter when systems scale—like time-syncing asynchronous nodes, standardizing message types across C++ and Python, and managing complex coordinate transforms.

**The Core Anatomy of ROS Topics**
At its heart, a ROS topic is an anonymous publish-subscribe conduit.

* **Publishers** fire messages into the ether without caring who is listening.
* **Subscribers** listen to a named topic without caring who produces the data.
* **The DDS Middleware:** Behind the scenes, the Data Distribution Service handles the network routing. For your robotic hand, your vision script acts as a publisher broadcasting a standard `sensor_msgs/msg/JointState` message containing 15 float values representing your joint angles.

**What RViz Actually Is (and Isn't)**
RViz is a **visualizer**, not a physics simulator like Gazebo.

* It reads your robot's mechanical blueprint (**URDF**) via the `robot_description` topic to know what links and joints exist.
* It listens to the `/tf` (Transform) topic to calculate where every single bone and joint is located in 3D space using forward kinematics.
* When your tracking script publishes new joint angles, RViz transforms those numbers into visual mesh rotations. If your URDF joint limits, axis alignments, or parent-child link definitions are off by even a fraction, RViz breaks, twists the meshes inside out, or throws silent transform errors. Budget days for this, not hours — the errors are rarely loud.

**The Interpolation and Bridge Layer**
When your Python script bridges tracking data to ROS, raw coordinate frames are converted into joint angles via vector math.

* **The Bridge Node:** A Python node takes those 15 angles, packs them into a `JointState` array, and publishes them to `/joint_states`.
* **State Interpolation:** To prevent your digital twin from snapping violently between published frames (this project publishes at 10 Hz; the camera itself delivers ~30 FPS), controllers often apply trajectory interpolation (like cubic splines) to smooth out the transition before updating the visual tree or forwarding commands to hardware drivers.
