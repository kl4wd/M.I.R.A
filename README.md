# M.I.R.A STT Engine (C Version)

Ce répertoire contient le moteur de reconnaissance vocale optimisé pour le Raspberry Pi 5.

## Pré-requis

Sur votre Raspberry Pi 5 (ou Debian/Ubuntu) :

```bash
sudo apt-get update
sudo apt-get install gcc make libvosk-dev libportaudio2 portaudio19-dev libasound2-dev
```

**Note :** Si `libvosk-dev` n'est pas disponible dans les dépôts, vous devez télécharger le SDK Vosk C et le placer dans `./vosk-api`.

## Installation du Modèle

Téléchargez un modèle Vosk léger (ex: `vosk-model-small-fr-0.22`) ou large, et décompressez-le dans un dossier nommé `model` à la racine :

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
unzip vosk-model-small-fr-0.22.zip
mv vosk-model-small-fr-0.22 model
rm vosk-model-small-fr-0.22.zip
```

Structure attendue :

```
.
├── mira_stt.c
├── Makefile
└── model/
    ├── conf/
    ├── graph/
    └── ...
```

## Compilation

```bash
make
```

Cela génèrera l'exécutable `mira_stt`.

## Utilisation

```bash
./mira_stt
```

Le programme écoutera le microphone par défaut. Il n'utilisera le CPU pour la reconnaissance que si une voix est détectée (RMS > 350).

## Fonctionnalités

- **Faible Latence** : Traitement par blocs de 4000 frames.
- **VAD (Voice Activity Detection)** : Filtre le silence pour économiser le CPU.
- **Filtre Passe-Haut** : Coupe les fréquences < 200Hz (bruit de fond, ventilo).
- **Léger** : Pas de dépendances JSON lourdes, parsing manuel optimisé.
