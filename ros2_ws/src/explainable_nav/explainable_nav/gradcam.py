"""Grad-CAM wrapper for the obstacle perception classifier.

Reuses the same explainability approach as the PolyDetect / Beyond Binary
medical imaging work, just pointed at a robot's camera feed instead of
colonoscopy frames.
"""

import os

import cv2
import numpy as np
import torch
import torch.nn as nn
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from torchvision import models, transforms

CHECKPOINT_PATH = os.environ.get(
    "EXPLAINABLE_NAV_CHECKPOINT",
    "/ros2_ws/training/checkpoints/obstacle_classifier.pt",
)


class ObstacleGradCAM:
    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        self.classes = None

        if os.path.exists(CHECKPOINT_PATH):
            checkpoint = torch.load(CHECKPOINT_PATH, map_location=self.device)
            self.classes = checkpoint["classes"]
            self.model = models.mobilenet_v3_small(weights=None)
            in_features = self.model.classifier[-1].in_features
            self.model.classifier[-1] = nn.Linear(in_features, len(self.classes))
            self.model.load_state_dict(checkpoint["state_dict"])
        else:
            # Placeholder classifier: run training/train_classifier.py on
            # collected simulation frames to get a real obstacle/clear-path
            # model, then set EXPLAINABLE_NAV_CHECKPOINT (or drop the file
            # at the default path above) so this branch is no longer used.
            self.model = models.mobilenet_v3_small(weights="IMAGENET1K_V1")

        self.model.eval().to(self.device)

        target_layer = self.model.features[-1]
        self.cam = GradCAM(model=self.model, target_layers=[target_layer])

        self.preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225]),
        ])

    def infer(self, bgr_frame: np.ndarray):
        """Run classification + Grad-CAM on a single BGR camera frame.

        Returns:
            overlay_bgr: heatmap-overlaid frame, same size as input.
            confidence: softmax confidence of the top predicted class.
            top_class: predicted class index (ImageNet index; remap once
                you fine-tune on obstacle/clear-path labels).
        """
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        input_tensor = self.preprocess(rgb_frame).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = torch.softmax(logits, dim=1)
            confidence, top_class = torch.max(probs, dim=1)

        grayscale_cam = self.cam(input_tensor=input_tensor)[0]

        resized_rgb = cv2.resize(rgb_frame, (224, 224)) / 255.0
        overlay_rgb = show_cam_on_image(resized_rgb.astype(np.float32),
                                         grayscale_cam, use_rgb=True)
        overlay_bgr = cv2.cvtColor(overlay_rgb, cv2.COLOR_RGB2BGR)
        overlay_bgr = cv2.resize(overlay_bgr, (bgr_frame.shape[1], bgr_frame.shape[0]))

        return overlay_bgr, float(confidence.item()), int(top_class.item())
