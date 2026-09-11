#!/bin/bash
# Starts XQuartz and allows local Docker containers to connect to it for
# Gazebo/RViz GUI display on macOS. Run this before `docker compose up`.

set -e

open /Applications/Utilities/XQuartz.app

# Give XQuartz a moment to start before configuring it.
sleep 3

# Allow connections from localhost (Docker Desktop's VM connects via
# host.docker.internal, which resolves to localhost from XQuartz's view).
# Full path + explicit DISPLAY used since /opt/X11/bin may not be on PATH
# and $DISPLAY may not be exported until next login.
export DISPLAY=:0
/opt/X11/bin/xhost + 127.0.0.1

echo "XQuartz is running and accepting local connections."
echo "You can now run: docker compose up"
