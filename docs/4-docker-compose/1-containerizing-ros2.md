# Containerizing ROS 2

Web developers containerize to isolate processes. Roboticists containerize and then spend their
time punching holes back through that isolation — for the webcam, the GPU, the display server and
the network. This document explains every hole in
[`docker-compose.yml`](../../docker-compose.yml) and what it is for.

### 1. The General Concept: Docker & Compose

**Docker** is a way to package software, libraries, and a stripped-down operating system into an isolated box called a **Container**. It solves the classic *"it works on my machine but not yours"* problem. Because ROS 2 versions are hard-locked to specific Ubuntu releases (e.g., ROS 2 Jazzy strictly requires Ubuntu 24.04), Docker allows you to run Jazzy on any machine—even Windows or older Linux distros—without wiping your hard drive.

**Docker Compose** is the conductor. When an application requires multiple containers talking to each other (like a database container and a web server container), typing out `docker run` with 20 configuration flags for each one becomes a nightmare. Compose lets you define the entire multi-container architecture in a single `docker-compose.yml` file and launch it with one command: `docker compose up`.

---

### 2. The ROS 2 Specifics: Deconstructing Your Compose File

Standard web developers use Docker to isolate web servers and databases. As a roboticist, you are doing something much harder: you are forcing an isolated container to access physical hardware (webcams, GPUs) and render 3D desktop applications (RViz, Gazebo).

Here is exactly what the strange flags in your `docker-compose.yml` are actually doing:

#### A. Shattering the Network Wall (DDS Discovery)

```yaml
    network_mode: "host"
    ipc: host
    pid: host

```

By default, Docker isolates containers on a virtual bridge network. However, ROS 2 relies on a middleware called DDS (Data Distribution Service) which uses UDP multicast to auto-discover other nodes on the network. If you leave containers on the default bridge, nodes cannot find each other.

* **`network_mode: "host"`**: Strips away the virtual network. The container shares your computer's actual network interface, allowing the MediaPipe node and the RViz node to instantly see each other's topics.
* **`ipc: host`**: Inter-Process Communication. ROS 2 uses shared memory to pass massive data (like uncompressed video frames) between nodes instantly without network overhead. This allows containers to share that memory pool.

#### B. Punching Through to the Graphics Server (GUI Rendering)

```yaml
    environment:
      - DISPLAY=${DISPLAY:-:0}
      - QT_X11_NO_MITSHM=1
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw

```

Docker containers have no desktop environment; they are completely headless.

* **`/tmp/.X11-unix`**: Your Linux host renders windows using the X11 display server, which listens via a socket file in the `/tmp` directory. By mounting this socket into the container as a volume, you give the container a portal to your monitor.
* **`DISPLAY=:0`**: Tells the ROS 2 container which monitor screen to draw RViz and Gazebo on.

#### C. Injecting Physical Hardware

```yaml
    devices:
      - /dev/video0:/dev/video0
      - /dev/dri:/dev/dri

```

* **`/dev/video0`**: Your physical webcam. The `hand_tracker` container needs this explicit permission to capture frames.
* **`/dev/dri`**: Direct Rendering Infrastructure. Without this, Gazebo and RViz would try to render 3D physics using the CPU (software rendering), running at 2 frames per second and melting your processor. This line hands the container direct access to your physical GPU for hardware acceleration.

#### D. Live Code Injection (Volumes)

```yaml
    volumes:
      - /mnt/data/projects/ros2-mediapipe-robotic-hand-digital-twin-vision-teleoperation:/workspace:rw

```

Instead of baking your Python scripts and URDF files into the container image—which would force you to wait 3 minutes for `docker compose build` every time you change a single variable—you mount your live directory into the container. When you hit save on `hand_tracker_node.py` in your host editor, the file instantly updates inside the running container.

By combining these flags, your Docker setup provides the strict dependencies of ROS 2 Jazzy while retaining the hardware access and GUI capabilities of a native desktop installation.