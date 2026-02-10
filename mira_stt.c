/**
 * M.I.R.A - Moteur STT (Speech-to-Text) Optimisé pour Raspberry Pi 5
 * 
 * Dépendances : libvosk, portaudio, math
 * Compilation : gcc mira_stt.c -o mira_stt -lvosk -lportaudio -lm -O3 -march=native
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <signal.h>
#include <vosk_api.h>
#include <portaudio.h>

#define SAMPLE_RATE 16000
#define FRAMES_PER_BUFFER 4000
#define RMS_THRESHOLD 350.0 // Seuil VAD pour silence
#define FILTER_CUTOFF 200.0 // Fréquence de coupure du filtre passe-haut

// Variable globale pour la gestion des signaux (arrêt propre)
volatile sig_atomic_t running = 1;

// Structure pour le filtre passe-haut (RC filter)
typedef struct {
    float alpha;
    float prev_input;
    float prev_output;
} HighPassFilter;

/**
 * Gestionnaire de signal pour Ctrl+C
 */
void handle_signal(int signal) {
    if (signal == SIGINT) {
        printf("\n\n[M.I.R.A] Arrêt demandé. Fermeture en cours...\n");
        running = 0;
    }
}

/**
 * Initialise le filtre passe-haut simple
 */
void init_filter(HighPassFilter *f, float cutoff) {
    float dt = 1.0f / SAMPLE_RATE;
    float rc = 1.0f / (2.0f * M_PI * cutoff);
    f->alpha = rc / (rc + dt);
    f->prev_input = 0;
    f->prev_output = 0;
}

/**
 * Applique le filtre passe-haut sur un échantillon
 */
short apply_filter(HighPassFilter *f, short input) {
    float output = f->alpha * (f->prev_output + (float)input - f->prev_input);
    f->prev_input = (float)input;
    f->prev_output = output;
    return (short)output;
}

/**
 * Extraction simple de la valeur "text" du JSON de Vosk
 * Évite d'utiliser une lourde bibliothèque JSON pour juste une chaîne.
 * Recherche la clé "text" : " et extrait jusqu'au prochain guillemet.
 */
void extract_and_print_text(const char *json_result) {
    const char *key = "\"text\" : \"";
    char *pos = strstr(json_result, key);
    
    if (pos) {
        pos += strlen(key); // Avance après la clé
        char *end = strchr(pos, '"'); // Trouve la fin de la chaîne
        if (end && end > pos) {
            // Affiche seulement si la chaîne n'est pas vide
            // Le format Vosk met parfois "text" : "" pour rien
            // Calculer la longueur pour affichage propre
            int len = end - pos;
            if (len > 0) {
                printf("> %.*s\n", len, pos);
                fflush(stdout); // Force l'affichage immédiat
            }
        }
    }
}

int main() {
    // Configuration du gestionnaire de signal
    signal(SIGINT, handle_signal);

    printf("=== M.I.R.A STT ENGINE (Optimisé Pi 5) ===\n");
    printf("[INIT] Chargement du modèle 'model'...\n");

    // Chargement du modèle Vosk (doit être dans ./model)
    VoskModel *model = vosk_model_new("model");
    if (!model) {
        fprintf(stderr, "[ERREUR] Modèle introuvable dans le dossier './model'\n");
        return 1;
    }

    VoskRecognizer *recognizer = vosk_recognizer_new(model, SAMPLE_RATE);
    
    // Initialisation de PortAudio
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        fprintf(stderr, "[ERREUR] PortAudio init failed: %s\n", Pa_GetErrorText(err));
        vosk_recognizer_free(recognizer);
        vosk_model_free(model);
        return 1;
    }

    PaStream *stream;
    // Ouverture du flux audio : Mono, 16bit, 16000Hz
    err = Pa_OpenDefaultStream(&stream, 
                               1,          // 1 canal entrée (Mono)
                               0,          // 0 canal sortie
                               paInt16,    // Format 16 bits
                               SAMPLE_RATE,
                               FRAMES_PER_BUFFER,
                               NULL,       // Pas de callback (mode bloquant)
                               NULL);
    
    if (err != paNoError) {
        fprintf(stderr, "[ERREUR] PortAudio open failed: %s\n", Pa_GetErrorText(err));
        Pa_Terminate();
        vosk_recognizer_free(recognizer);
        vosk_model_free(model);
        return 1;
    }

    err = Pa_StartStream(stream);
    if (err != paNoError) {
        fprintf(stderr, "[ERREUR] PortAudio start failed: %s\n", Pa_GetErrorText(err));
        Pa_CloseStream(stream);
        Pa_Terminate();
        vosk_recognizer_free(recognizer);
        vosk_model_free(model);
        return 1;
    }

    // Initialisation du filtre
    HighPassFilter hpf;
    init_filter(&hpf, FILTER_CUTOFF);

    printf("[PRET] En attente de voix (VAD > %.0f RMS, Filtre > %.0f Hz)...\n", RMS_THRESHOLD, FILTER_CUTOFF);

    short buffer[FRAMES_PER_BUFFER];
    
    // Boucle principale
    while (running) {
        // Lecture audio (bloquante)
        err = Pa_ReadStream(stream, buffer, FRAMES_PER_BUFFER);
        if (err != paNoError && err != paInputOverflowed) {
             fprintf(stderr, "[WARN] Erreur lecture audio: %s\n", Pa_GetErrorText(err));
             // On continue malgré tout s'il s'agit d'un warning mineur
        }

        double sum_sq = 0;

        // Pré-traitement : Filtrage + Calcul RMS
        for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
            // 1. Filtrage passe-haut (supprime bruits sourds/graves/ventilo)
            buffer[i] = apply_filter(&hpf, buffer[i]);
            
            // 2. Accumulation pour RMS
            sum_sq += (double)buffer[i] * buffer[i];
        }

        double rms = sqrt(sum_sq / FRAMES_PER_BUFFER);

        // VAD (Voice Activity Detection) simple
        if (rms > RMS_THRESHOLD) {
            // Voix détectée -> On envoie à Vosk
            if (vosk_recognizer_accept_waveform_s(recognizer, buffer, FRAMES_PER_BUFFER)) {
                // Résultat final (phrase complète)
                const char *result = vosk_recognizer_result(recognizer);
                extract_and_print_text(result);
            } else {
                // Résultat partiel (en cours de reconnaissance)
                // On peut décommenter ceci si on veut voir le texte s'afficher en temps réel :
                // const char *partial = vosk_recognizer_partial_result(recognizer);
                // extract_and_print_text(partial); 
            }
        } else {
            // Silence -> On économise le CPU (pas d'appel à Vosk)
            // Optionnel : on pourrait sleep un peu ici, mais Pa_ReadStream bloque déjà
        }
    }

    // Nettoyage final
    printf("[ARRET] Libération des ressources...\n");
    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();
    vosk_recognizer_free(recognizer);
    vosk_model_free(model);

    printf("[FIN] M.I.R.A STT terminé.\n");
    return 0;
}
