# Explainable Obstacle Avoidance Robot

**Author:** Azizur Rahman ([Portfolio](http://azizurrahman.netlify.app/) · [Google Scholar](https://scholar.google.com/citations?hl=en&user=ZybW6NMAAAAJ))

A ROS2 and Gazebo simulation in which a TurtleBot3 performs obstacle-avoidance navigation while a live Grad-CAM explainability overlay shows not only *that* the robot detected an obstacle, but *why*: which region of its camera view drove that decision. The project extends explainable AI methods from my published and under-review medical imaging research into robotic perception, and serves as a first, deliberate step toward robotics-focused research.

## Motivation

My prior research develops explainable, uncertainty-aware deep learning for medical imaging: CNN-Transformer architectures for gastrointestinal endoscopy risk stratification, quality-aware polyp segmentation under image degradation, and multimodal Parkinson's disease detection. Across that work, a prediction is only clinically useful if its reasoning is visible, using techniques such as Grad-CAM saliency mapping, SHAP attribution, and Monte Carlo Dropout uncertainty quantification.

This project asks the same question in a different domain: instead of "why did the model flag this lesion," the question becomes "why did the robot decide to avoid this obstacle." The explainability methodology transfers directly; the sensing modality, real-time constraints, and embodiment do not, and that gap is what this project is designed to explore, directly aligned with research in robotic perception, autonomous decision-making, and human-robot interaction.

## System Overview

1. A TurtleBot3 navigates a Gazebo-simulated environment using obstacle-avoidance behavior.
2. A ROS2 perception node subscribes to the robot's camera feed and classifies each frame with a CNN.
3. Grad-CAM produces a saliency heatmap identifying which region of the frame drove the "obstacle ahead" decision.
4. The heatmap is published as a live ROS2 image topic (viewable in RViz), and each decision is logged with a timestamp and confidence score.
5. A LIDAR-based data collection pipeline auto-labels camera frames as "obstacle" or "clear" using the robot's own range sensor as ground truth, enabling a classifier to be fine-tuned on real simulation data rather than relying on an ImageNet-pretrained placeholder.

## Architecture

```
Camera (Gazebo) --> /camera/image_raw
                          |
                          v
              [explainable_nav perception_node]
                    |             |
                    v             v
        /explainable_nav/heatmap   logs/decisions.csv
              (RViz viewable)

LIDAR (Gazebo) --> /scan
                          |
                          v
              [data_collector_node] --> training/data/{obstacle,clear}/*.jpg
                          |
                          v
              training/train_classifier.py --> training/checkpoints/obstacle_classifier.pt
                          |
                          v
              (perception_node auto-loads this checkpoint if present)
```

## Setup

ROS2 and Gazebo are Linux-native and do not run natively on macOS, so the project runs inside a container. Two setups are supported:

### Option A: GitHub Codespaces (recommended)

Builds on GitHub's infrastructure, avoiding local disk and virtualization constraints. Gazebo and RViz require a display, which Codespaces does not provide by default; see the commented `desktop-lite` feature in `.devcontainer/devcontainer.json` to enable a browser-accessible VNC desktop if the visual simulator is needed.

1. Open the repository on GitHub.
2. **Code → Codespaces → Create codespace on main.**
3. Once the container finishes building, the commands below apply identically.

### Option B: Local Docker (macOS)

Requires XQuartz for the Gazebo/RViz GUI and roughly 10-15GB of free disk for a reliable build of the ROS2 desktop and Gazebo packages.

```bash
# One-time: install XQuartz
brew install --cask xquartz
# Log out and back in (or reboot) after first install, so XQuartz's
# XML preference changes take effect.

# Each session: start XQuartz and allow local Docker connections
./scripts/start_x11.sh

# Build and start the ROS2/Gazebo environment
docker compose build
docker compose up
```

### Running the Simulation

Inside the container (either option):

```bash
# Terminal 1: launch TurtleBot3 in Gazebo with obstacle-avoidance demo
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2: run the explainable perception node
ros2 run explainable_nav perception_node

# Terminal 3: view the heatmap overlay live
rviz2
# Add an Image display subscribed to /explainable_nav/heatmap
```

### Collecting Training Data and Fine-Tuning the Classifier

The perception node ships with an ImageNet-pretrained placeholder classifier, which produces heatmaps but not a meaningful obstacle/clear-path signal. To fine-tune a task-specific classifier:

```bash
# While driving/teleoperating the robot around the Gazebo world:
ros2 run explainable_nav data_collector_node

# Once a reasonable number of frames exist in training/data/{obstacle,clear}/:
python3 training/train_classifier.py --data-dir training/data --epochs 10

# The perception node automatically loads the resulting checkpoint at
# training/checkpoints/obstacle_classifier.pt on the next launch.
```

## Engineering Notes

Two implementation issues were identified and resolved during development, documented here for transparency:

1. The initial Dockerfile's `pip install torch` resolved to the full CUDA-enabled PyTorch build, pulling in several gigabytes of NVIDIA toolkit dependencies unnecessary for a container without GPU passthrough. Resolved by pinning the CPU-only PyTorch wheel index.
2. A `setuptools`/`packaging` version mismatch in the base ROS2 image caused `colcon build` to fail. Resolved by explicitly upgrading both packages prior to the build step.

## Research Direction

This project is an active, in-progress foundation rather than a finished result. Planned next steps include verifying the full perception pipeline against live simulation data, fine-tuning the obstacle classifier on collected frames, and extending the explainability framework toward uncertainty quantification (Monte Carlo Dropout) under simulated sensor degradation, mirroring the quality-aware approach used in my prior colonoscopy image segmentation work, applied here to robotic perception under degraded visual conditions.
