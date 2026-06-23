# syntax=docker/dockerfile:1
# Netlistify Inference Container for vast.ai GPU instances
# Target GPU: RTX 4090 (sm_90, fully supported by PyTorch 2.4.1)

FROM pytorch/pytorch:2.4.1-cuda12.4-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ── System + Netlistify Source ───────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor openssh-server git libgl1-mesa-glx libglib2.0-0 \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/NYCU-AI-EDA/Netlistify.git /app

# ── SSH ─────────────────────────────────────────────────────────
RUN mkdir -p /var/run/sshd && echo 'root:root' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# ── Directories ─────────────────────────────────────────────────
RUN mkdir -p /opt/netlistify/weights /workspace/input /workspace/results /var/log/supervisor

# ── Python Dependencies ─────────────────────────────────────────
# torch + torchvision pre-installed. Install ALL Netlistify deps.
RUN cd /app && pip install --no-cache-dir \
    $(grep -vE '^torch==|^pyqt6|^pyside6|^pyqt6-webengine' requirements.txt | tr '\n' ' ') \
    && pip install --no-cache-dir --force-reinstall 'numpy>=1.24,<2.0'

# ── Model Weights ───────────────────────────────────────────────
COPY model/bubble_orientation/res50_1.pt /opt/netlistify/weights/res50_1.pt
COPY model/bubble_orientation/cc_res50_1.pt /opt/netlistify/weights/cc_res50_1.pt
COPY model/runs/FormalDatasetWindowedLinePair/0113_14-34-52/best_train.pth /opt/netlistify/weights/best_train.pth

# ── Boot Scripts + Config ───────────────────────────────────────
COPY patch_paths.py     /app/patch_paths.py
COPY validate_container.py /app/validate_container.py
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── vast.ai Integration ─────────────────────────────────────────
RUN curl -sSL https://raw.githubusercontent.com/vast-ai/base-image/main/onstart.sh \
    -o /root/onstart.sh && chmod +x /root/onstart.sh

EXPOSE 22
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
