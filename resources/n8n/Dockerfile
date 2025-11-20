FROM n8nio/n8n:1.114.4

USER root

RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    portaudio-dev \
    musl-dev \
    g++ \
    pkgconfig


COPY requirements.txt ./requirements.txt

COPY n8n-task-runners.json /etc/n8n-task-runners.json

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/python3 -m ensurepip && \
    /opt/venv/bin/pip3 install --no-cache --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir --no-deps -r requirements.txt
USER node