# ROS 2 MediaPipe Robotic Hand: Real-Time Teleoperation Digital Twin

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-34a853?logo=ros)](https://docs.ros.org/en/jazzy/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ed?logo=docker)](https://www.docker.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) 
*(Note: Update DOI badge once published to Zenodo)*

<div align="center">
  <img src="docs/hero_demo.webm" alt="Real-time Hand Tracking Demo" width="800">
  <p><em>Real-time teleoperation mapping human hand kinematics to a custom URDF CAD model via computer vision.</em></p>
</div>

## 📖 Overview
This project implements a fully containerized, vision-based digital twin of a robotic hand. By leveraging a standard RGB webcam, the system tracks human hand landmarks in real-time, computes the forward kinematics, maps the raw angles to mechanical joint limits, and drives a custom 3D CAD model (URDF) inside ROS 2 RViz. 

This repository is part of a broader series on vision-based robotic teleoperation and digital twins.

## ✨ Key Features
* **Markerless Teleoperation:** Real-time 3D hand landmark tracking using Google MediaPipe and OpenCV.
* **Explicit Kinematic Mapping:** Custom Python algorithms to calculate joint angles via vector dot products and linear interpolation, mapping human flexion directly to physical CAD joint limits.
* **ROS 2 Distributed Architecture:** Utilizes the `robot_state_publisher` and `rviz2` nodes for high-fidelity 3D rendering and TF transformations.
* **Hardware-Accelerated Docker Environment:** A highly optimized `docker-compose` setup with Intel DRI/GPU passthrough, native X11 window forwarding, and isolated network layers.

## 🏗️ System Architecture
The pipeline is divided into three completely isolated computational layers:

1. **The Vision Pipeline (`hand_tracker`):** An OpenCV node captures webcam frames and passes them to MediaPipe. The neural network infers 21 spatial landmarks of the human hand.
2. **The Kinematic Engine:** The spatial landmarks are converted into 15 distinct joint angles using relative vector math. These angles are normalized (0.0 to 1.0 flexion) and mapped to the exact mechanical rotation limits of the 3D model to prevent CAD collisions.
3. **The Simulation Layer (`ros_rviz`):** The custom joint angles are published as `sensor_msgs/JointState` to the ROS 2 network, overriding the default state publisher to animate the URDF digital twin in real-time.

## 🧰 Prerequisites
* Ubuntu 24.04 (or compatible Linux host)
* Docker Engine & Docker Compose V2
* Standard USB Webcam (`/dev/video0`)

## 🚀 Quick Start

### 1. Configure the Host System
Because this stack relies heavily on native GUI rendering and hardware acceleration, you must authorize Docker to access your local X11 display. 
```bash
# Clone the repository
git clone [https://github.com/YOUR_USERNAME/ros2-mediapipe-robotic-hand.git](https://github.com/YOUR_USERNAME/ros2-mediapipe-robotic-hand.git)
cd ros2-mediapipe-robotic-hand

# Run the automated host setup script
chmod +x setup_host.sh
./setup_host.sh

```

### 2. Launch the Digital Twin

Build and launch the containerized ROS 2 network:

```bash
docker compose up --build

```

### 3. Configure RViz (First Run)

When RViz opens, load the custom configuration to display the digital twin:

1. In the **Displays** panel, ensure **Fixed Frame** is set to `base_link`.
2. Ensure the **RobotModel** Description Topic is set to `/robot_description`.
*(Note: A persistent `.rviz` config file is loaded automatically in subsequent runs).*

## ⚙️ CAD & Hardware Design

The 3D model utilized in this simulation was designed in Onshape and exported to URDF using `onshape-to-robot`. The joints are explicitly named (e.g., `index_mcp`, `thumb_pip`) for accurate kinematic mapping.

* 🔗 **[View the Public Onshape CAD Model](https://www.google.com/search?q=INSERT_YOUR_ONSHAPE_LINK_HERE)**

## 📄 License

This project is open-source and licensed under the GNU Affero General Public License v3.0 (`AGPL-3.0`). See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## 🎓 Citation

If you use this software, simulation architecture, or kinematic mapping methodology in your academic research, please cite it using the following metadata:

**BibTeX:**

```bibtex
@software{fetna_ros2_robotic_hand_2026,
  author       = {Mulham Mohammed Fetna},
  title        = {ROS 2 MediaPipe Robotic Hand: Real-Time Teleoperation Digital Twin},
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {[https://github.com/YOUR_USERNAME/ros2-mediapipe-robotic-hand](https://github.com/YOUR_USERNAME/ros2-mediapipe-robotic-hand)}
}

```
