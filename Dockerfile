FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-gazebo \
    ros-humble-turtlebot3-msgs \
    ros-humble-cv-bridge \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --upgrade setuptools packaging

RUN pip3 install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch \
    torchvision \
    && pip3 install --no-cache-dir \
    opencv-python-headless \
    numpy \
    grad-cam

ENV TURTLEBOT3_MODEL=waffle_pi

WORKDIR /ros2_ws
COPY ros2_ws /ros2_ws

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

CMD ["/bin/bash"]
