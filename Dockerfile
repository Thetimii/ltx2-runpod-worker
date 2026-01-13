FROM runpod/base:0.6.2-cuda12.1.1

WORKDIR /workspace

# Prevent python buffering issues
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# HF cache to volume (RunPod cached models + local cache)
ENV HF_HOME=/runpod-volume/huggingface-cache
ENV TRANSFORMERS_CACHE=/runpod-volume/huggingface-cache
ENV HF_HUB_CACHE=/runpod-volume/huggingface-cache/hub

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy code
COPY handler.py .
COPY src ./src

CMD ["python", "-u", "handler.py"]
