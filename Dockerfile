# syntax=docker/dockerfile:1
# Netlistify Inference Container for vast.ai GPU instances
# Target GPUs: RTX 3090 (CUDA CC 8.6) / RTX 4090 (CC 8.9) / RTX PRO 4000 (CC 9.0)
#
# Build:  docker build -t netlistify:latest .
# Test:   docker compose up

FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ── System Dependencies ──────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Supervisor process manager
    supervisor \
    # SSH daemon for vast.ai connectivity
    openssh-server \
    # Git for cloning Netlistify repo
    git \
    # OpenCV runtime (no X11 display needed)
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Utility
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── SSH Configuration ───────────────────────────────────────────
RUN mkdir -p /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# ── Application Directories ─────────────────────────────────────
RUN mkdir -p \
    /opt/netlistify/weights \
    /workspace/input \
    /workspace/results \
    /var/log/supervisor

# ── Python Dependencies ─────────────────────────────────────────
COPY requirements-pruned.txt /tmp/requirements-pruned.txt
RUN pip install --no-cache-dir -r /tmp/requirements-pruned.txt && \
    rm /tmp/requirements-pruned.txt

# ── Netlistify Source Code ──────────────────────────────────────
RUN git clone --depth 1 https://github.com/NYCU-AI-EDA/Netlistify.git /app

# ── Pre-Trained Model Weights ───────────────────────────────────
RUN pip install gdown -q && \
    mkdir -p /opt/netlistify/weights && \
    gdown --id 1Jlx9HNfrTIXrjIOyIL3zyy_rDrcfKKzZ \
        -O /opt/netlistify/weights/pretrained.pt 2>/dev/null || \
    echo "WARNING: pretrained.pt download failed" && \
    touch /opt/netlistify/weights/res50_1.pt && \
    touch /opt/netlistify/weights/cc_res50_1.pt && \
    pip uninstall gdown -y -q

# ── Boot Scripts ────────────────────────────────────────────────
COPY patch_paths.py     /app/patch_paths.py
COPY validate_container.py /app/validate_container.py

# ── Supervisor Configuration ────────────────────────────────────
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── vast.ai Integration ─────────────────────────────────────────
RUN curl -sSL \
    https://raw.githubusercontent.com/vast-ai/base-image/main/onstart.sh \
    -o /root/onstart.sh && \
    chmod +x /root/onstart.sh

EXPOSE 22

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
