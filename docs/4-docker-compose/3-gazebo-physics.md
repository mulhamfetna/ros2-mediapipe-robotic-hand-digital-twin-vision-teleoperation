# Gazebo Physics

## Overview
This document outlines the transition from a passive kinematic visualizer (**RViz**) to a physics-enabled simulation environment (**Gazebo Harmonic**) for the 15-DOF robotic hand project.

## Architecture Comparison
* **RViz**: Acts as a lightweight visual debugger. It performs forward kinematics purely based on mathematical transforms (`/tf`) and joint states without calculating mass, inertia, or gravity.
* **Gazebo**: Operates as a full-scale physics engine. It simulates gravity, friction, and rigid-body collisions, requiring complete inertial parameters (`<inertial>` tags) for every model link.

## Automated Startup Flow
1. **Container Initialization**: The `gazebo_sim` container launches using an automated entrypoint script (`entrypoint.sh`).
2. **Environment Sourcing**: Sources the ROS 2 Jazzy workspace and initiates Gazebo Harmonic (`gz sim empty.sdf`).
3. **Entity Spawning**: Automatically waits 4 seconds for the simulation server to initialize, then executes the spawn routine:
   ```bash
   ros2 run ros_gz_sim create -file /workspace/ros_rviz/urdf/robot.urdf -name robotic_hand -z 0.5