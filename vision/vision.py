import time
import json
import os
import paho.mqtt.client as mqtt
from picamera2 import Picamera2

# ── Configuration ──────────────────────────────────────────────
MQTT_BROKER = os.getenv("MQTT_BROKER", "mira-mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC_VISION", "mira/vision/output")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", 30))

# ── Couleurs terminal ─────────────────────────────────────────
C_RESET  = "\033[0m"
C_GREEN  = "\033[1;32m"
C_CYAN   = "\033[0;36m"
C_YELLOW = "\033[1;33m"
C_RED    = "\033[1;31m"

last_publish_time = 0.0
mqtt_client = None

def on_mqtt_connect(client, userdata, flags, rc):
    print(f"{C_CYAN}[MQTT] Connecté avec le code {rc} au broker {MQTT_BROKER}{C_RESET}")

def init_mqtt():
    """Initialise de façon robuste la connexion MQTT."""
    global mqtt_client
    try:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except AttributeError:
        mqtt_client = mqtt.Client()

    mqtt_client.on_connect = on_mqtt_connect
    
    while True:
        try:
            print(f"{C_YELLOW}Tentative de connexion à {MQTT_BROKER}:{MQTT_PORT}...{C_RESET}")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            mqtt_client.loop_start()
            break
        except Exception as e:
            print(f"{C_RED}[ERREUR] MQTT non joignable : {e}. Nouvelle tentative dans 5s...{C_RESET}")
            time.sleep(5)

def format_detections(detections):
    """
    Formate la liste brute de détections.
    Format d'une détection (ex: IMX500 mobilenet) :
    {'category': 0, 'conf': 0.85, 'category_name': 'person', 'box': [0.1, 0.2, 0.5, 0.8]}
    """
    labels = []
    
    for det in detections:
        # Gérer différents formats de sortie de réseaux neuronaux de picamera2
        score = det.get('conf', 0.0)
        label = det.get('category_name', str(det.get('category', 'unknown')))
        
        if score >= CONFIDENCE_THRESHOLD:
            labels.append(label)
    
    if not labels:
        return None
        
    # Construire la phrase descriptive
    # Ex: "Je vois une personne et une chaise"
    
    unique_labels = list(set(labels)) # Enlever les doublons (ex: 3 personnes -> juste 'person')
    
    # Simple traduction française si ce sont les labels COCO (souvent par défaut)
    translations = {
        'person': 'une personne', 'bicycle': 'un vélo', 'car': 'une voiture',
        'motorcycle': 'une moto', 'airplane': 'un avion', 'bus': 'un bus',
        'train': 'un train', 'truck': 'un camion', 'boat': 'un bateau',
        'traffic light': 'un feu de signalisation', 'fire hydrant': 'une borne à incendie',
        'stop sign': 'un panneau stop', 'parking meter': 'un parcmètre', 'bench': 'un banc',
        'bird': 'un oiseau', 'cat': 'un chat', 'dog': 'un chien', 'horse': 'un cheval',
        'sheep': 'un mouton', 'cow': 'une vache', 'elephant': 'un éléphant', 'bear': 'un ours',
        'zebra': 'un zèbre', 'giraffe': 'une girafe', 'backpack': 'un sac à dos',
        'umbrella': 'un parapluie', 'handbag': 'un sac à main', 'tie': 'une cravate',
        'suitcase': 'une valise', 'frisbee': 'un frisbee', 'skis': 'des skis',
        'snowboard': 'un snowboard', 'sports ball': 'un ballon', 'kite': 'un cerf-volant',
        'baseball bat': 'une batte de baseball', 'baseball glove': 'un gant de baseball',
        'skateboard': 'un skateboard', 'surfboard': 'une planche de surf', 'tennis racket': 'une raquette',
        'bottle': 'une bouteille', 'wine glass': 'un verre', 'cup': 'une tasse',
        'fork': 'une fourchette', 'knife': 'un couteau', 'spoon': 'une cuillère', 'bowl': 'un bol',
        'banana': 'une banane', 'apple': 'une pomme', 'sandwich': 'un sandwich', 'orange': 'une orange',
        'broccoli': 'un brocoli', 'carrot': 'une carotte', 'hot dog': 'un hot dog', 'pizza': 'une pizza',
        'donut': 'un donut', 'cake': 'un gâteau', 'chair': 'une chaise', 'couch': 'un canapé',
        'potted plant': 'une plante', 'bed': 'un lit', 'dining table': 'une table',
        'toilet': 'des toilettes', 'tv': 'une télévision', 'laptop': 'un ordinateur portable',
        'mouse': 'une souris', 'remote': 'une télécommande', 'keyboard': 'un clavier',
        'cell phone': 'un smartphone', 'microwave': 'un micro-ondes', 'oven': 'un four',
        'toaster': 'un grille-pain', 'sink': 'un évier', 'refrigerator': 'un réfrigérateur',
        'book': 'un livre', 'clock': 'une horloge', 'vase': 'un vase', 'scissors': 'des ciseaux',
        'teddy bear': 'un ours en peluche', 'hair drier': 'un sèche-cheveux', 'toothbrush': 'une brosse à dents'
    }
    
    fr_labels = [translations.get(lbl, lbl) for lbl in unique_labels]
    
    if len(fr_labels) == 1:
        phrase = f"Je vois {fr_labels[0]}"
    else:
        last = fr_labels.pop()
        phrase = f"Je vois {', '.join(fr_labels)} et {last}"
        
    return phrase

def main():
    global last_publish_time
    
    init_mqtt()
    
    # ── Initialisation Caméra ──────────────────────────────────────
    print(f"{C_CYAN}[INIT] Initialisation de Picamera2...{C_RESET}")
    try:
        picam2 = Picamera2()
        
        # Le réglage pour charger le firmware IMX500 et le JSON post_processing
        # Cela s'appuie sur le framework PostProcessing de Picamera2 (imx500_mobilenet_ssd.json)
        # Note: La configuration exacte peut dépendre de la version de Libcamera,
        # mais on utilise ici l'approche classique par dictionnaire de config/tuning.
        config = picam2.create_preview_configuration(
            main={"size": (1920, 1080), "format": "BGR888"}
        )
        # On attache le réseau de tenseur à la chaîne de traitement (IMX500 gère cela en interne)
        # picamera2 supporte un module de détection natif si installé via rpi-libcamera
        picam2.configure(config)
        
        # Pour une caméra IMX500, la sortie d'inférence arrive dans les métadonnées de la frame
        picam2.start()
        print(f"{C_GREEN}[VISION] Caméra AI démarrée. En attente de détections...{C_RESET}")
        
    except Exception as e:
        print(f"{C_RED}[ERREUR] Impossible de démarrer la caméra : {e}{C_RESET}")
        return

    # ── Boucle de capture et d'inférence ───────────────────────────
    while True:
        try:
            # Récupère l'image et ses métadonnées (qui contiennent l'inférence IMX500)
            request = picam2.capture_request()
            metadata = request.metadata
            
            # Selon la version rpi-libcamera, ça s'appelle Imx500Inference ou ObjectDetections
            # On cherche une clé ressemblant à des détections.
            detections = None
            if 'Imx500Inference' in metadata:
                detections = metadata['Imx500Inference']
            elif 'PostProcessingResults' in metadata:
                results = metadata['PostProcessingResults']
                if 'object_detect' in results:
                     detections = results['object_detect']
                     
            if detections is None:
                # Fallback format brut ou vide
                detections = metadata.get('ObjectDetections', [])
                
            if not isinstance(detections, list):
                detections = []

            # ── Logique de filtrage et cooldown ────────────────────────
            current_time = time.time()
            
            # Formatage et filtrage par seuil de confiance
            phrase = format_detections(detections)
            
            if phrase:
                if (current_time - last_publish_time) >= COOLDOWN_SECONDS:
                    # Le cooldown de 30s est respecté, on publie
                    print(f"{C_CYAN}[VISION] Détection validée ({COOLDOWN_SECONDS}s écoulées) : {phrase}{C_RESET}")
                    mqtt_client.publish(MQTT_TOPIC, phrase)
                    last_publish_time = current_time
            
            # Relâche la requête pour éviter les fuites de mémoire
            request.release()
            
            # Petite pause pour ne pas surcharger le CPU
            time.sleep(0.05)
            
        except KeyboardInterrupt:
            print(f"{C_YELLOW}\n[VISION] Arrêt demandé...{C_RESET}")
            break
        except Exception as e:
            print(f"{C_RED}[ERREUR] Erreur dans la boucle de vision : {e}{C_RESET}")
            time.sleep(1)

    picam2.stop()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print(f"{C_GREEN}[VISION] Module arrêté proprement.{C_RESET}")

if __name__ == "__main__":
    main()
