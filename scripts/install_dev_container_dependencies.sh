#!/usr/bin/env bash
set -e

apt-get update && apt-get install -y \
    cmake \
    libcairo2-dev \
    pkg-config \
    python3-dev

pip3 install --user -e .
pip3 install --user -r requirements-dev.txt -r requirements-docs.txt

npm install -g changie