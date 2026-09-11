"""ROS2 node to collect labeled training frames from the simulated camera.

Auto-labels frames using the robot's LIDAR scan as a proxy: if the closest
obstacle in front of the robot is within OBSTACLE_THRESHOLD_M, the current
camera frame is saved as "obstacle"; otherwise "clear". This gives a cheap,
reasonably accurate label without manual annotation, since LIDAR range is
ground truth for "is something physically close in front of the robot."

Run this while driving/teleoperating the robot around the Gazebo world to
build up a training set.
"""

import os
import time

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan

OBSTACLE_THRESHOLD_M = 0.6
FRONT_ARC_DEGREES = 30  # +/- degrees around the robot's forward direction
SAVE_EVERY_N_FRAMES = 5  # avoid saving near-duplicate consecutive frames

DATA_DIR = os.environ.get("EXPLAINABLE_NAV_DATA_DIR", "/ros2_ws/training/data")


class DataCollectorNode(Node):
    def __init__(self):
        super().__init__("data_collector_node")

        self.bridge = CvBridge()
        self.latest_scan_min_front = None
        self.frame_count = 0

        self.image_sub = self.create_subscription(
            Image, "/camera/image_raw", self.image_callback, 10
        )
        self.scan_sub = self.create_subscription(
            LaserScan, "/scan", self.scan_callback, 10
        )

        for label in ("obstacle", "clear"):
            os.makedirs(os.path.join(DATA_DIR, label), exist_ok=True)

        self.get_logger().info(f"Data collector started. Saving to {DATA_DIR}")

    def scan_callback(self, msg: LaserScan):
        ranges = np.array(msg.ranges)
        n = len(ranges)
        if n == 0:
            return

        arc = int((FRONT_ARC_DEGREES / 360.0) * n)
        front = np.concatenate([ranges[:arc], ranges[-arc:]])
        front = front[np.isfinite(front)]
        front = front[front > 0.0]

        self.latest_scan_min_front = float(np.min(front)) if len(front) else None

    def image_callback(self, msg: Image):
        self.frame_count += 1
        if self.frame_count % SAVE_EVERY_N_FRAMES != 0:
            return
        if self.latest_scan_min_front is None:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        label = "obstacle" if self.latest_scan_min_front < OBSTACLE_THRESHOLD_M else "clear"
        filename = os.path.join(DATA_DIR, label, f"{int(time.time() * 1000)}.jpg")

        import cv2
        cv2.imwrite(filename, frame)
        self.get_logger().info(f"Saved {label} frame: {filename}")


def main(args=None):
    rclpy.init(args=args)
    node = DataCollectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
