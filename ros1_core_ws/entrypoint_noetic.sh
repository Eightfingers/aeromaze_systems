#!/bin/bash
# Ensure the script fails immediately if any command fails
set -e
source /opt/ros/noetic/setup.bash
source /workspace/devel/setup.bash

# Execute the given command, which will be passed as arguments to this script
exec "$@"

# Ensure the passed command is valid and execute it
if [ $# -eq 0 ]; then
    echo "No command provided. Starting an interactive shell..."
    exec /bin/bash
else
    echo "Running command: $@"
    exec "$@"
fi