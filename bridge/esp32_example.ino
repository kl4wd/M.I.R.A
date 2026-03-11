/*
 * M.I.R.A — ESP32 : Récepteur de commandes UART
 * ================================================
 * 
 * Ce code reçoit les trames UART envoyées par le bridge Raspberry Pi
 * au format : <CMD:ACTION>\n
 * 
 * Actions supportées :
 *   FORWARD, BACKWARD, LEFT, RIGHT, STOP, AUTOPILOT, POSITION
 * 
 * Branchement UART (Raspberry Pi → ESP32) :
 *   - RPi TX  → ESP32 RX (GPIO16 par défaut sur Serial2)
 *   - RPi RX  → ESP32 TX (GPIO17 par défaut sur Serial2)
 *   - GND     → GND (masse commune obligatoire)
 * 
 * ⚠️  Si le RPi est en 3.3V et l'ESP32 aussi, pas besoin de level shifter.
 *     Si le RPi envoie en 5V, utiliser un diviseur de tension sur la ligne RX de l'ESP32.
 */

#define UART_BAUD 115200

// Buffer pour stocker la trame en cours de réception
String inputBuffer = "";
bool receiving = false;

void setup() {
    // Serial pour le debug (USB)
    Serial.begin(115200);
    Serial.println("[MIRA-ESP32] Démarrage...");

    // Serial2 pour la communication UART avec le Raspberry Pi
    // GPIO16 = RX, GPIO17 = TX (par défaut sur ESP32)
    Serial2.begin(UART_BAUD, SERIAL_8N1, 16, 17);
    Serial.println("[MIRA-ESP32] UART2 initialisé (RX=GPIO16, TX=GPIO17)");
    Serial.print("[MIRA-ESP32] Baud rate : ");
    Serial.println(UART_BAUD);
    Serial.println("[MIRA-ESP32] En attente de commandes...");
}

void loop() {
    // Lire les données disponibles sur Serial2 (venant du RPi)
    while (Serial2.available()) {
        char c = Serial2.read();

        if (c == '<') {
            // Début de trame détecté
            receiving = true;
            inputBuffer = "";
        } else if (c == '>') {
            // Fin de trame détectée — on traite la commande
            receiving = false;
            processCommand(inputBuffer);
            inputBuffer = "";
        } else if (receiving) {
            // Accumulation des caractères entre < et >
            inputBuffer += c;
        }
    }
}

/**
 * Traite une commande reçue au format "CMD:ACTION"
 * Exemple : "CMD:FORWARD" → appelle handleForward()
 */
void processCommand(String raw) {
    raw.trim();

    // Vérifier le préfixe "CMD:"
    if (!raw.startsWith("CMD:")) {
        Serial.print("[ERREUR] Format invalide : ");
        Serial.println(raw);
        // Envoyer un feedback d'erreur au bridge
        Serial2.println("<ERR:INVALID_FORMAT>");
        return;
    }

    // Extraire l'action après "CMD:"
    String action = raw.substring(4);
    action.trim();

    Serial.print("[CMD] Action reçue : ");
    Serial.println(action);

    // Dispatcher vers la bonne fonction
    if (action == "FORWARD") {
        handleForward();
    } else if (action == "BACKWARD") {
        handleBackward();
    } else if (action == "LEFT") {
        handleLeft();
    } else if (action == "RIGHT") {
        handleRight();
    } else if (action == "STOP") {
        handleStop();
    } else if (action == "AUTOPILOT") {
        handleAutopilot();
    } else if (action == "POSITION") {
        handlePosition();
    } else {
        Serial.print("[ERREUR] Action inconnue : ");
        Serial.println(action);
        Serial2.println("<ERR:UNKNOWN_ACTION>");
        return;
    }

    // Envoyer un accusé de réception au bridge
    String ack = "<ACK:" + action + ">";
    Serial2.println(ack);
}

// ── Fonctions moteur (à adapter à votre hardware) ───────────

void handleForward() {
    Serial.println("[MOTEUR] >>> AVANCER");
    // TODO: Votre code pour faire avancer le robot
    // Exemple :
    // digitalWrite(MOTOR_A_FWD, HIGH);
    // digitalWrite(MOTOR_B_FWD, HIGH);
}

void handleBackward() {
    Serial.println("[MOTEUR] >>> RECULER");
    // TODO: Votre code pour faire reculer le robot
}

void handleLeft() {
    Serial.println("[MOTEUR] >>> TOURNER À GAUCHE");
    // TODO: Votre code pour tourner à gauche
}

void handleRight() {
    Serial.println("[MOTEUR] >>> TOURNER À DROITE");
    // TODO: Votre code pour tourner à droite
}

void handleStop() {
    Serial.println("[MOTEUR] >>> STOP");
    // TODO: Votre code pour arrêter tous les moteurs
}

void handleAutopilot() {
    Serial.println("[MODE] >>> AUTOPILOT ACTIVÉ");
    // TODO: Activer le mode autopilote (évitement d'obstacles, etc.)
}

void handlePosition() {
    Serial.println("[INFO] >>> DEMANDE DE POSITION");
    // TODO: Lire les capteurs et renvoyer la position
    // Exemple : envoyer les coordonnées GPS ou IMU au bridge
    // Serial2.println("<POS:48.8566,2.3522>");
}
