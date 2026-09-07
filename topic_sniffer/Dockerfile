FROM ros:jazzy

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3.12-venv \
    ros-jazzy-rclpy \
    ros-jazzy-rosidl-default-generators \
    ros-jazzy-ament-cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws_sniffer

# Create virtual environment
RUN python3 -m venv /ws_sniffer/.venv

# Activate venv and install Python deps
ENV PATH="/ws_sniffer/.venv/bin:$PATH"

# ROS Python deps needed by rosidl_adapter / colcon
RUN pip install --no-cache-dir \
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
  exec python3 /ws_sniffer/src/sniffer_node.py"]