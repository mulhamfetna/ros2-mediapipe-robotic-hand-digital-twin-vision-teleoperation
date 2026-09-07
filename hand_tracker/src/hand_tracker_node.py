import cv2
import mediapipe as mp
import numpy as np
import rclpy
from rclpy.node import Node
from hand_msgs.msg import JointAngles
from sensor_msgs.msg import JointState

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def compute_15_joint_angles(landmarks):
    lm = np.array(landmarks)
    triplets = [
        (0, 1, 2), (1, 2, 3), (2, 3, 4),        # Thumb (Indices 0, 1, 2)
        (0, 5, 6), (5, 6, 7), (6, 7, 8),        # Index (Indices 3, 4, 5)
        (0, 9, 10), (9, 10, 11), (10, 11, 12),  # Middle (Indices 6, 7, 8)
        (0, 13, 14), (13, 14, 15), (14, 15, 16),# Ring (Indices 9, 10, 11)
        (0, 17, 18), (17, 18, 19), (18, 19, 20),# Pinky (Indices 12, 13, 14)
    ]
    angles = []
    for p1, p2, p3 in triplets:
        v1 = lm[p1] - lm[p2]
        v2 = lm[p3] - lm[p2]
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            angles.append(0.0)
        else:
            cosang = np.dot(v1, v2) / (norm1 * norm2)
            cosang = np.clip(cosang, -1.0, 1.0)
            angles.append(float(np.arccos(cosang)))
    return angles

# Min (curled) and Max (straight) angles expected from MediaPipe vector math
RAW_STRAIGHT_ANGLE = 3.10  # ~177 degrees (open hand)
RAW_CURLED_ANGLE = 1.60    # ~90 degrees (bent finger)

# Explicit Kinematic Mapping directly from your updated URDF limits
# Format: ('URDF_Joint_Name', MP_Index, URDF_Open_Angle, URDF_Closed_Angle)
JOINT_MAPPING = [
    # THUMB
    ('thumb_mcp',   0, -1.377,  0.194),
    ('thumb_pip',   1, -1.126,  0.445),
    ('thumb_dip',   2, -1.142,  0.429),
    
    # INDEX
    ('index_mcp',   3,  0.960, -0.611),
    ('index_pip',   4,  0.000, -1.571),
    ('index_dip',   5,  0.000, -1.571),
    
    # MIDDLE
    ('middle_mcp',  6,  0.652, -0.919),
    ('middle_pip',  7,  0.000,  1.571),
    ('middle_dip',  8, -0.087,  1.484),
    
    # RING (Requires manual URDF fix: rename duplicate 'twinky_mcp' to 'ring_mcp')
    ('ring_mcp',    9,  0.000, -1.571),
    ('ring_pip',   10,  0.000,  1.571),
    ('ring_dip',   11,  0.000, -1.571),
    
    # PINKY (Twinky in CAD)
    ('twinky_mcp', 12,  0.000, -1.571),
    ('twinky_pip', 13,  0.000,  1.571),
    ('twinky_dip', 14,  0.000, -1.571),
]

def map_raw_to_urdf_angles(raw_angles):
    joint_names = []
    mapped_positions = []
    
    for name, mp_idx, open_angle, closed_angle in JOINT_MAPPING:
        raw_angle = raw_angles[mp_idx]
        
        # Normalize flexion: 0.0 = completely straight, 1.0 = completely curled
        flexion = (RAW_STRAIGHT_ANGLE - raw_angle) / (RAW_STRAIGHT_ANGLE - RAW_CURLED_ANGLE)
        flexion = float(np.clip(flexion, 0.0, 1.0))
        
        # Interpolate directly between the URDF's true Open and Closed limits
        urdf_angle = open_angle + flexion * (closed_angle - open_angle)
        
        joint_names.append(name)
        mapped_positions.append(urdf_angle)
        
    return joint_names, mapped_positions

class HandTrackerNode(Node):
    def __init__(self):
        super().__init__("hand_tracker_node")
        self.publisher = self.create_publisher(JointAngles, "/hand/joint_angles", 10)
        self.rviz_publisher = self.create_publisher(JointState, "/joint_states", 10)
        self.timer = self.create_timer(1.0 / 10.0, self.timer_callback)
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error("Failed to open camera")
            raise RuntimeError("Camera not available")
        
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.get_logger().info("Hand tracker with Named Joints STARTED")

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("Failed to read frame")
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.ascontiguousarray(frame_rgb)

        results = self.hands.process(frame_rgb)

        # Default fallback variables using the mapped "Open" pose
        msg = JointAngles()
        msg.angles = [RAW_STRAIGHT_ANGLE] * 15
        urdf_names, urdf_angles = map_raw_to_urdf_angles(msg.angles)

        if results.multi_hand_landmarks:
            hand_object = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_object, mp_hands.HAND_CONNECTIONS)
            
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand_object.landmark]
            msg.angles = compute_15_joint_angles(landmarks)

            # Route angles through the explicit dictionary map
            urdf_names, urdf_angles = map_raw_to_urdf_angles(msg.angles)
            
            self.get_logger().info(f"Tracking Index MCP: {urdf_angles[3]:.2f}")
        
        cv2.imshow("MediaPipe Hand Tracker", frame)
        cv2.waitKey(1)
        
        self.publisher.publish(msg)
        
        # Publish exact joint names instead of Revolute 1-15
        rviz_msg = JointState()
        rviz_msg.header.stamp = self.get_clock().now().to_msg()
        rviz_msg.name = urdf_names
        rviz_msg.position = urdf_angles
        self.rviz_publisher.publish(rviz_msg)

def main():
    rclpy.init()
    node = HandTrackerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == "__main__":
    main()