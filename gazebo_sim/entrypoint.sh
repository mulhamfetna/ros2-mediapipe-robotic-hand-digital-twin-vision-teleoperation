#!/bin/bash
source /opt/ros/jazzy/setup.bash

# 1. Start Gazebo simulation in the background
gz sim empty.sdf &
GZ_PID=$!

# 2. Give the physics server a few seconds to initialize its transport nodes
echo "Waiting for Gazebo physics server..."
sleep 4

# 3. Automatically spawn the robotic hand URDF
echo "Spawning robotic hand into Gazebo..."
ros2 run ros_gz_sim create -file /workspace/ros_rviz/urdf/robot.urdf -name robotic_hand -z 0.5

# 4. Keep container alive by tracking the background process
wait $GZ_PID