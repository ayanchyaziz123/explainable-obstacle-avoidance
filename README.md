# Explainable Obstacle Avoidance Robot

A ROS2 + Gazebo simulation project that pairs a TurtleBot3's obstacle-avoidance
navigation with a live Grad-CAM explainability overlay, showing not just *that*
the robot detected an obstacle, but *why* (which region of its camera view
drove the decision).

This project extends the explainable AI work from my medical imaging research
(PolyDetect, MultiParkNet) into robotic perception: the same Grad-CAM technique
used to explain lesion/segmentation decisions in colonoscopy images here
explains a robot's real-time navigation decisions.

## What it does

1. A TurtleBot3 navigates a Gazebo world using standard obstacle-avoidance behavior.
2. A custom ROS2 node subscribes to the robot's camera feed and runs each frame
   through a lightweight CNN classifier.
3. Grad-CAM generates a heatmap showing which part of the frame most influenced
   the "obstacle ahead" decision.
4. The heatmap-overlaid frame is published as a live ROS2 image topic (viewable
   in RViz), and each decision (confidence + timestamp) is logged to `logs/`.
5. A separate data collector node auto-labels frames as "obstacle" or "clear"
   using the robot's LIDAR as ground truth, so a real classifier can be
   fine-tuned instead of relying on the ImageNet-pretrained placeholder.

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

ROS2 and Gazebo are Linux-native and do not run natively on macOS, so this
project runs inside a container. Two ways to run it:

### Option A: GitHub Codespaces (recommended)

No local disk/Docker issues since the build runs on GitHub's infrastructure.
Gazebo/RViz GUIs are not available headlessly by default; see the note in
`.devcontainer/devcontainer.json` for the desktop-lite VNC option if you need
the visual simulator.

1. Push this repo to GitHub.
2. On the repo page: **Code → Codespaces → Create codespace on main**.
3. Once the container finishes building, everything below works the same way.

### Option B: Local Docker (macOS)

Requires XQuartz for the Gazebo/RViz GUI, and enough free disk (the base
ROS2 desktop image plus Gazebo packages need roughly 10-15GB of headroom to
build reliably).

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

### Running the simulation

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

### Collecting training data and fine-tuning the classifier

The perception node ships with an ImageNet-pretrained placeholder classifier,
which produces heatmaps but not a meaningful "obstacle vs. clear" signal.
To fine-tune a real one:

```bash
# While driving/teleoperating the robot around the Gazebo world:
ros2 run explainable_nav data_collector_node

# Once you have a reasonable number of frames in training/data/{obstacle,clear}/:
python3 training/train_classifier.py --data-dir training/data --epochs 10

# The perception node automatically picks up the resulting checkpoint at
# training/checkpoints/obstacle_classifier.pt on next launch.
```

## Project status

- [x] Docker + ROS2 + Gazebo environment builds successfully
- [ ] TurtleBot3 baseline navigation verified
- [ ] Grad-CAM perception node verified against live camera feed
- [ ] Training data collected and classifier fine-tuned
- [ ] Demo video recorded

## Why this project

Built as part of exploring a research pivot toward robotics, extending
uncertainty-aware and explainable AI (the focus of my published/under-review
work in medical imaging) into embodied, real-time robotic perception.
