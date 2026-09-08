# How to Pitch This

This is a first ROS 2 project, not a world-first invention, and the pitch should say so. What makes it worth showing is the *way* it was built: not a script on one machine, but a reproducible, containerized, multi-node architecture with a real CAD pipeline behind it.

When pitching a foundational project like this, the goal isn't to claim you invented robotic teleoperation, but to prove you have mastered the **integration of complex, modern robotics pipelines**. Here are three angles you can use to frame the project, depending on who is listening:

* **The Full-Stack Integration Angle:** Frame the project as a bridge between domains. You successfully connected real-time computer vision (MediaPipe) to custom kinematic math, piped it through an industry-standard middleware (ROS 2 Jazzy), and rendered it in a physics engine (Gazebo Harmonic). This proves you don't just know how to train a model or design a CAD part—you know how to make them talk to each other in real-time.
* **The "DevOps for Robotics" Angle:** Focus on the infrastructure. The notorious bottleneck in robotics is the phrase, "It works on my machine." By containerizing the entire ROS workspace, managing GPU passthrough, and automating the physics simulation startups with Docker Compose, you demonstrated that you write robust, deployable systems meant for real-world development environments.
* **The Digital Twin Angle:** Focus on the hardware-to-software pipeline. You learned the hard lessons of translating mechanical constraints (Onshape assemblies, joint limits, material inertia) into software realities (URDF). This shows you understand the mechanical realities of robotics, not just the software theory.

If you had to compress this into a single elevator pitch, it would sound something like:
*"I built a containerized digital twin of a 15-DOF robotic hand that translates real-time human gestures into a ROS 2 physics simulation by bridging computer vision, kinematic math, and custom CAD pipelines."*

## What not to claim

Three things this project does not do, which the pitch should never imply:

- **It does not control hardware.** There are no servos, no controllers and no transmissions —
  the URDF describes geometry, not actuation. See
  [known export defects](../5-onshape-urdf/3-known-export-defects.md).
- **It does not do physics.** The Gazebo container spawns the model into an empty world; nothing
  drives it. The working twin is the RViz one, and RViz is a visualizer.
- **The kinematics are forward-only and per-joint.** Each joint is mapped independently by linear
  interpolation. There is no inverse kinematics, no coupling between joints, and no filtering.

Naming these unprompted is worth more than hiding them. It is the difference between someone who
built a demo and someone who knows exactly where their demo ends.
