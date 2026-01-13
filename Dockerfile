# Use NVIDIA CUDA base image (more reliable than runpod/base)
# This image includes CUDA 12.1 and Ubuntu 22.04
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /workspace

# Prevent python buffering issues
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# HF cache to volume (RunPod cached models + local cache)
ENV HF_HOME=/runpod-volume/huggingface-cache
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface-cache
ENV HF_HUB_CACHE=/runpod-volume/huggingface-cache/hub

# System deps (Python 3.10, pip, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-dev \
    ffmpeg \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --no-cache-dir --upgrade pip

# Install python deps (CUDA-aware torch install first)
COPY requirements.txt .

# Install CUDA PyTorch (CUDA 12.1)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1

# Then install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY handler.py .
COPY src ./src

CMD ["python", "-u", "handler.py"]
