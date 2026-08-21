"""ROS2 node: subscribes to the robot's camera, runs Grad-CAM explainable
perception on each frame, publishes the heatmap overlay, and logs each
decision (confidence + timestamp) to a CSV file.
"""

import csv
import os
import time

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

from explainable_nav.gradcam import ObstacleGradCAM

LOG_DIR = os.environ.get("EXPLAINABLE_NAV_LOG_DIR", "/ros2_ws/logs")
LOG_PATH = os.path.join(LOG_DIR, "decisions.csv")


class PerceptionNode(Node):
    def __init__(self):
        super().__init__("explainable_perception_node")

        self.bridge = CvBridge()
        self.gradcam = ObstacleGradCAM()

        self.subscription = self.create_subscription(
            Image, "/camera/image_raw", self.image_callback, 10
        )
        self.heatmap_pub = self.create_publisher(
            Image, "/explainable_nav/heatmap", 10
        )

        os.makedirs(LOG_DIR, exist_ok=True)
        self._init_log()

        self.get_logger().info(
            "Explainable perception node started. "
            "Subscribed to /camera/image_raw, publishing /explainable_nav/heatmap"
        )

    def _init_log(self):
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "confidence", "predicted_class"])

    def _log_decision(self, confidence: float, predicted_class: int):
        with open(LOG_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([time.time(), confidence, predicted_class])

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        overlay, confidence, predicted_class = self.gradcam.infer(frame)
        self._log_decision(confidence, predicted_class)

        out_msg = self.bridge.cv2_to_imgmsg(overlay, encoding="bgr8")
        out_msg.header = msg.header
        self.heatmap_pub.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
