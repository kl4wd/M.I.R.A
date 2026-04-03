#!/usr/bin/env python3
"""
Agent Raspberry — présence MQTT + GPS (réel ou simulé) pour le dashboard M.I.R.A.
Uniquement des dépendances Python standard + paho-mqtt.

Variables d'environnement :
  MQTT_BROKER   hôte du broker (ex. IP du PC)
  MQTT_PORT     1883 par défaut
  ROBOT_ID      identifiant unique (défaut : hostname)
  MOCK_GPS      si "1", envoie une position fictive autour de Paris
  LAT, LON      position initiale si MOCK_GPS
  ROBOT_DOCKER_CONTAINERS   noms de conteneurs à surveiller sur la Pi (liste séparée par des virgules)
  DOCKER_REPORT_SEC         période entre deux rapports sur mira/robots/{id}/docker/status (défaut 30)
"""

import json
import os
import random
import socket
import subprocess
import time

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
PORT = int(os.getenv("MQTT_PORT", "1883"))
ROBOT_ID = os.getenv("ROBOT_ID", socket.gethostname())
MOCK_GPS = os.getenv("MOCK_GPS", "1") == "1"
LAT0 = float(os.getenv("LAT", "48.869867"))
LON0 = float(os.getenv("LON", "2.307077"))
INTERVAL = float(os.getenv("HEARTBEAT_SEC", "5"))
ROBOT_DOCKER_CONTAINERS = [
    x.strip()
    for x in os.getenv(
        "ROBOT_DOCKER_CONTAINERS",
        "mira-stt,mira-tts,mira-vision,mira-bridge",
    ).split(",")
    if x.strip()
]
DOCKER_REPORT_SEC = float(os.getenv("DOCKER_REPORT_SEC", "30"))


def collect_docker_status(names):
    """État Docker pour le dashboard (docker inspect sur la Pi)."""
    out = {"ts": time.time(), "services": []}
    try:
        for name in names:
            r = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", name],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if r.returncode != 0:
                out["services"].append(
                    {"name": name, "running": False, "status": "absent"}
                )
            else:
                st = (r.stdout or "").strip()
                out["services"].append(
                    {"name": name, "running": st == "running", "status": st}
                )
    except FileNotFoundError:
        out["error"] = "docker_cli_missing"
    except Exception as e:
        out["error"] = str(e)
    return out


def main():
    cid = f"mira-agent-{ROBOT_ID}"
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id=cid)

    will = json.dumps({"ts": time.time(), "online": False})
    client.will_set(f"mira/robots/{ROBOT_ID}/presence", will, qos=0, retain=True)

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    meta = {
        "hostname": socket.gethostname(),
        "version": "rpi-agent/1",
        "capabilities": ["telemetry", "gps", "bridge"],
        "streamUrl": os.getenv("STREAM_URL", ""),
    }
    client.publish(
        f"mira/robots/{ROBOT_ID}/meta",
        json.dumps(meta),
        qos=0,
        retain=True,
    )

    lat, lon = LAT0, LON0
    last_docker_report = 0.0
    try:
        while True:
            now = time.time()
            if ROBOT_DOCKER_CONTAINERS and (
                now - last_docker_report >= DOCKER_REPORT_SEC
            ):
                payload = collect_docker_status(ROBOT_DOCKER_CONTAINERS)
                client.publish(
                    f"mira/robots/{ROBOT_ID}/docker/status",
                    json.dumps(payload),
                    qos=0,
                    retain=False,
                )
                last_docker_report = now
            client.publish(
                f"mira/robots/{ROBOT_ID}/presence",
                json.dumps({"ts": now, "online": True}),
                qos=0,
                retain=False,
            )
            if MOCK_GPS:
                lat += random.uniform(-0.0003, 0.0003)
                lon += random.uniform(-0.0003, 0.0003)
            client.publish(
                f"mira/robots/{ROBOT_ID}/gps",
                json.dumps(
                    {"lat": lat, "lon": lon, "acc": 5.0, "ts": now},
                ),
                qos=0,
                retain=False,
            )
            client.publish(
                f"mira/robots/{ROBOT_ID}/telemetry",
                json.dumps(
                    {
                        "battery_pct": round(70 + random.uniform(-5, 5), 1),
                        "uptime_sec": int(now),
                        "mock": MOCK_GPS,
                    },
                ),
                qos=0,
                retain=False,
            )
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
