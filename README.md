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
```

## Setup

This runs inside Docker since ROS2 is Linux-native and this was developed on macOS.

```bash
docker compose build
docker compose up
```

Then, inside the container:

```bash
# Terminal 1: launch TurtleBot3 in Gazebo with obstacle-avoidance demo
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# Terminal 2: run the explainable perception node
ros2 run explainable_nav perception_node

# Terminal 3: view the heatmap overlay live
rviz2
# Add an Image display subscribed to /explainable_nav/heatmap
```

## Project status

- [ ] Docker + ROS2 + Gazebo environment verified
- [ ] TurtleBot3 baseline navigation working
- [ ] Grad-CAM perception node integrated
- [ ] Decision logging working
- [ ] Demo video recorded

## Why this project

Built as part of exploring a research pivot toward robotics, extending
uncertainty-aware and explainable AI (the focus of my published/under-review
work in medical imaging) into embodied, real-time robotic perception.
