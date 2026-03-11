# On utilise Debian Bookworm classique
FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Ajout du dépot Raspberry Pi officiel pour avoir accès à python3-picamera2 et libcamera
# On installe gpg et wget pour vérifier la clé
RUN apt-get update && apt-get install -y wget gnupg && \
    wget -qO - https://archive.raspberrypi.com/debian/raspberrypi.gpg.key | apt-key add - && \
    echo "deb http://archive.raspberrypi.com/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list

# Maintenant on peut installer les paquets officiels Raspberry Pi
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-picamera2 \
    python3-libcamera \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des requirements.txt (les libs Python pures non liées au système)
COPY requirements.txt .

# Installation des dépendances via pip
# On utilise la configuration pour ignorer les règles system-wide PEP 668 de debian bookworm
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# Copie du script Python principal
COPY vision.py .

# Commande de démarrage
CMD ["python3", "vision.py"]
