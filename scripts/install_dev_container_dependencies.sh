#!/usr/bin/env bash
set -e

apt-get update && apt-get install -y \
    cmake \
    libcairo2-dev \
    pkg-config \
    python3-dev

sudo pip3 install -e .
pip3 install -r requirements-dev.txt -r requirements-docs.txt

npm install -g changie