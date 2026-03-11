FROM python:3.11-bookworm

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -qO - https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | apt-key add - \
    && echo "deb http://archive.raspberrypi.org/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list

# On installe picamera2 au niveau système
RUN apt-get update && apt-get install -y \
    python3-picamera2 \
    python3-numpy \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Crucial : On dit à Python d'inclure les dossiers système dans sa recherche
ENV PYTHONPATH="/usr/lib/python3/dist-packages"

RUN pip install --no-cache-dir paho-mqtt

COPY vision.py .

CMD ["python3", "vision.py"]