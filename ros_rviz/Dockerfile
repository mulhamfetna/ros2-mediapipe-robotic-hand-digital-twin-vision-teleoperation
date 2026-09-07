FROM ros:jazzy

RUN apt-get update && apt-get install -y \
    ros-jazzy-urdf-tutorial \
    ros-jazzy-rviz2 \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-xacro \
    libglu1-mesa \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# This launches both the TF calculator and RViz2 simultaneously
CMD ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.bash && ros2 launch urdf_tutorial display.launch.py model:=/workspace/ros_rviz/urdf/robot.urdf jsp_gui:=false"]