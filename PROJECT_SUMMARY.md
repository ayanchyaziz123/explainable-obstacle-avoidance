# Explainable Obstacle Avoidance Robot: Project Summary

**Author:** Azizur Rahman
**Repository:** https://github.com/ayanchyaziz123/explainable-obstacle-avoidance

## Motivation

My research background is in explainable, uncertainty-aware deep learning for medical imaging: CNN-Transformer hybrids for gastrointestinal endoscopy risk stratification (Beyond Binary, under review, Evolutionary Intelligence), polyp segmentation under image degradation (PolyDetect, under review, International Journal of Medical Informatics), and multimodal Parkinson's disease detection (MultiParkNet, accepted, Frontiers in Medicine). Across all of this work, the common thread is that a model's prediction is only useful if a clinician can see *why* the model made it, using techniques like Grad-CAM, SHAP, and Monte Carlo Dropout uncertainty quantification.

This project is a deliberate first step toward extending that research identity from medical imaging into robotics: instead of asking "why did the model flag this lesion," the question becomes "why did the robot decide to avoid this obstacle." The underlying explainability techniques transfer directly; the sensing domain and real-time constraints do not, which is exactly the gap I built this project to explore.

## What the project does

A TurtleBot3 robot navigates a Gazebo-simulated environment and performs standard obstacle-avoidance behavior. A custom ROS2 perception node subscribes to the robot's live camera feed, runs each frame through a CNN classifier, and generates a Grad-CAM saliency heatmap showing which region of the frame drove the "obstacle ahead" decision. The heatmap is published as a live ROS2 topic (viewable in RViz) and every decision is logged with a timestamp and confidence score.

A second component, the data collection pipeline, addresses a problem I consider central to doing this work honestly: an ImageNet-pretrained classifier produces a heatmap, but not a meaningful one, since it has no notion of "obstacle" as a category. To fix this, a LIDAR-based auto-labeling node uses the robot's own range sensor as ground truth (objects within 0.6m in the robot's forward arc are labeled "obstacle," otherwise "clear") while driving the robot through the simulated world, building a labeled dataset without manual annotation. A fine-tuning script then trains a MobileNetV3 classifier on this data, and the perception node automatically loads the fine-tuned checkpoint once it exists, falling back to the placeholder otherwise.

## Engineering notes

Getting this running was not trivial, and I think the debugging process is worth being upfront about rather than glossing over. ROS2 and Gazebo are Linux-native and do not run on macOS, so the project runs inside Docker. During development I encountered and fixed two real bugs:

1. The initial Dockerfile's `pip install torch` defaulted to the full CUDA-enabled build of PyTorch, pulling in several gigabytes of NVIDIA toolkit dependencies that are useless in a container with no GPU passthrough. Fixed by pinning the CPU-only PyTorch wheel index.
2. A `setuptools`/`packaging` version mismatch in the base ROS2 image caused `colcon build` to fail with a `TypeError` inside `canonicalize_version()`. Fixed by explicitly upgrading both packages before the build step.

The project also supports GitHub Codespaces (`.devcontainer/devcontainer.json`) as an alternative to local Docker, since local disk constraints on my machine made the macOS Docker path unreliable during development.

## Current status

- [x] Docker/Codespaces environment builds successfully end to end
- [ ] TurtleBot3 baseline navigation verified in simulation
- [ ] Grad-CAM perception node verified against a live camera feed
- [ ] Training data collected via the LIDAR auto-labeling pipeline and classifier fine-tuned
- [ ] Demo video recorded

I want to be direct about this: the environment builds and the code is written and reviewed, but I have not yet run the full simulation end to end or fine-tuned the classifier on real collected data. This is an active, in-progress project, not a finished result, and I am sharing it at this stage because it reflects the direction I want to take my research, not because it is complete.

## Why I'm sharing this

I recognize my background does not include prior hands-on robotics platform experience, and this project is my attempt to close that gap honestly rather than overstate unrelated experience. My intent is to keep building on this: fine-tuning the classifier on real collected data, verifying the full pipeline in simulation, and eventually extending the explainability approach toward uncertainty quantification (Monte Carlo Dropout) under simulated sensor degradation, mirroring the "quality-aware" framing of my PolyDetect work but applied to robotic perception instead of colonoscopy images.
