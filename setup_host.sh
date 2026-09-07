#!/bin/bash
# Host system preparation for ROS 2 Robotic Hand Simulation

echo "--- Configuring Host System for Docker GUI Passthrough ---"

# 1. Grant local Docker containers access to the X11 server
if command -v xhost &> /dev/null; then
    echo "[X11] Granting local root access to X server..."
    xhost +local:root
else
    echo "[WARNING] 'xhost' not found. If GUI fails, install x11-xserver-utils."
fi

# 2. Ensure the XDG runtime directory exists for Qt/RViz
if [ ! -d "/tmp/runtime-root" ]; then
    echo "[System] Creating /tmp/runtime-root for Qt processes..."
    sudo mkdir -p /tmp/runtime-root
    sudo chmod 700 /tmp/runtime-root
fi

# 3. Check for Intel GPU passthrough capabilities
if [ -c "/dev/dri/renderD128" ]; then
    echo "[GPU] Intel DRI device found. Hardware acceleration enabled."
else
    echo "[WARNING] /dev/dri not found. RViz may fallback to software rendering."
fi

echo "--- Setup Complete. You can now run 'docker compose up' ---"