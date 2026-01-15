apt-get update && apt-get install -y \
    cmake \
    libcairo2-dev \
    pkg-config \
    python3-dev \

pip3 install --user -e .[dev]

npm install -g changie