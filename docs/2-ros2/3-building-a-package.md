# Building a ROS 2 Package From Scratch

Strip away the containers, the URDF, the meshes and the simulators, and this is the irreducible
core of every ROS 2 project. If the rest of this repository feels like a lot, build this first —
it is the same skeleton, without the hardware.

Building a clean ROS 2 project from scratch requires stripping away complex multi-container setups, URDF meshes, and heavy simulators, and focusing purely on the core ROS 2 lifecycle: **Workspaces, Packages, Nodes, and Communication.**

This 6-step logical roadmap takes you from an empty directory to a fully functioning ROS 2 system.

---

### Step 1: Initialize the Workspace Structure

ROS 2 code cannot live loose in a directory; it must be organized inside a strict workspace hierarchy. The workspace acts as the root container for all your custom packages.

```bash
mkdir -p ~/my_robot_ws/src
cd ~/my_robot_ws/src

```

*Why?* The `src` (source) folder is where `colcon` (the ROS 2 build system) looks when compiling code.

### Step 2: Create a Package

Inside `src`, you create individual packages. A package is the atomic unit of software in ROS 2—it can contain nodes, configuration files, or launch files.

For a Python-based project, use the standard template generator:

```bash
ros2 pkg create --build-type ament_python my_first_package --dependencies rclpy

```

This generates a clean directory tree:

```text
my_first_package/
├── my_first_package      # Python module folder (where your node scripts go)
├── resource              # Package marker files
├── test                  # Unit testing folder
├── package.xml           # Dependency declarations
└── setup.py              # Build and entry-point configurations

```

### Step 3: Write the Logic (The Nodes)

A **Node** is simply an independent executable script that performs a specific task (e.g., reading a sensor, processing data, or driving a motor).

Create a simple script inside `my_first_package/my_first_package/talker_node.py` that publishes a periodic string message:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('talker_node')
        # Create a publisher on the topic 'chatter' with a queue size of 10
        self.publisher_ = self.create_publisher(String, 'chatter', 10)
        
        # Publish a message every 0.5 seconds
        self.timer = self.create_timer(0.5, self.timer_callback)

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello ROS 2 Infrastructure!'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

```

### Step 4: Expose the Executable in `setup.py`

For ROS 2 to recognize your Python script as an executable command (`ros2 run`), you must map it in the package’s `setup.py` file under `entry_points`:

```python
    entry_points={
        'console_scripts': [
            'talker = my_first_package.talker_node:main',
        ],
    },

```

### Step 5: Build the Workspace

Return to the root of your workspace and compile the code using `colcon`. This links your package into the workspace environment.

```bash
cd ~/my_robot_ws
colcon build --packages-select my_first_package

```

### Step 6: Source and Execute

Before running any ROS 2 command, you must **source** your workspace's local setup file so your terminal shell knows where the compiled binaries live.

```bash
# Overlay your local workspace onto the base ROS 2 installation
source install/setup.bash

# Run your custom node
ros2 run my_first_package talker

```

In a separate terminal, you can inspect the active ROS graph infrastructure:

* See active data streams: `ros2 topic list`
* Listen directly to the topic data: `ros2 topic echo /chatter`
* Inspect node connections: `ros2 node info /talker_node`

This minimalist workflow is the foundation of every advanced robot application, whether it controls a single micro-controller or a multi-DOF robotic arm.