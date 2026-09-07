import sys
import time
import rclpy
from rclpy.node import Node
from hand_msgs.msg import JointAngles

class SnifferNode(Node):
    def __init__(self):
        super().__init__("sniffer_node")
        self.subscription = self.create_subscription(
            JointAngles,
            "/hand/joint_angles",
            self.callback,
            10,
        )
        self.msg_count = 0
        sys.stdout.write("[SNIFFER] NODE STARTED\n")
        sys.stdout.flush()

    def callback(self, msg: JointAngles):
        self.msg_count += 1
        now = time.time()
        angles = list(msg.angles)
        sys.stdout.write(f"[SNIFFER #{self.msg_count}] angles={angles}\n")
        sys.stdout.flush()

def main():
    rclpy.init()
    node = SnifferNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == "__main__":
    main()