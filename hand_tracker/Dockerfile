FROM ros:jazzy

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3.12-venv \
    python3-opencv \
    ros-jazzy-rclpy \
    ros-jazzy-rosidl-default-generators \
    ros-jazzy-ament-cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws_hand_tracker

# Create virtual environment
RUN python3 -m venv /ws_hand_tracker/.venv

# Activate venv and install Python deps
ENV PATH="/ws_hand_tracker/.venv/bin:$PATH"

# mediapipe + numpy + ROS Python deps needed by rosidl_adapter / colcon
RUN pip install --no-cache-dir \
    "mediapipe==0.10.14" \
    numpy \
    empy==4.2 \
    lark \
    pyyaml \
    setuptools \
    catkin_pkg

ENTRYPOINT ["/bin/bash", "-c", "\
  source /opt/ros/jazzy/setup.bash && \
  colcon build --symlink-install --packages-select hand_msgs && \
  source install/setup.bash && \
  exec python3 /ws_hand_tracker/src/hand_tracker_node.py"]