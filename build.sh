#!/usr/bin/env bash
# Enable error reporting
set -o errexit
set -o nounset

# Update and install FFmpeg development libraries
apt-get update && \
apt-get install -y \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    pkg-config
