import sys
import os

os.environ["TF_USE_LEGACY_KERAS"] = "1"

try:
    import tensorflow as tf
    import tf_keras
    sys.modules['keras'] = tf_keras
    sys.modules['tensorflow.keras'] = tf_keras
    sys.modules['tensorflow.keras.models'] = tf_keras.models
    sys.modules['tensorflow.keras.layers'] = tf_keras.layers
except ImportError:
    pass

from ultralytics import YOLO
import cv2
import time
import threading
import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
# Using standard YOLOv8n model for object detection instead of pose
MODEL_OBJ = "yolov8n.pt"

# List of dangerous objects to detect (COCO classes)
DANGEROUS_OBJECTS = {"knife", "scissors", "baseball bat"}

class MiraRobot:
    def __init__(self):
        print("MIRA VISION (SECURITY MODE) : READY")
        self.model = YOLO(MODEL_OBJ)
        self.current_response = "Scanne le périmètre..."
        self.is_processing_llm = False
        self.last_trigger = 0

    def llm_worker(self, objects):
        self.is_processing_llm = True
        try:
            detected_threats = [obj for obj in objects if obj in DANGEROUS_OBJECTS]
            has_threat = len(detected_threats) > 0
            
            object_str = ", ".join(objects) if objects else "rien de spécial"
            
            system_prompt = (
                "Tu es MIRA, une IA de sécurité sarcastique mais vigilante. "
                "Si tu vois une arme ou un danger (couteau, ciseaux, batte), tu dois alerter immédiatement et menacer l'intrus. "
                "Sinon, tu te moques gentiment de ce que tu vois."
            )

            user_prompt = f"Je vois : {object_str}. "
            if has_threat:
                user_prompt += f"ALERTE : J'ai détecté {', '.join(detected_threats)} ! Réagis de manière agressive pour dissuader."
            else:
                user_prompt += "Rien de dangereux pour l'instant. Fais un commentaire sur la situation."

            payload = {
                "model": "ministral-3-3b-instruct-2512",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.8,
                "stream": False
            }
            res = requests.post(LM_STUDIO_URL, json=payload, timeout=5)
            if res.status_code == 200:
                self.current_response = res.json()['choices'][0]['message']['content']
        except: pass
        finally: self.is_processing_llm = False

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            results = self.model(frame, verbose=False)[0]
            annotated_frame = frame.copy()
            
            current_detected_objects = []
            threat_detected = False

            if results.boxes:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls[0])
                    label = results.names[cls]
                    
                    # Filter: Only detect person and dangerous objects
                    if label != "person" and label not in DANGEROUS_OBJECTS:
                        continue
                    
                    current_detected_objects.append(label)
                    
                    # Determine color based on threat level
                    if label in DANGEROUS_OBJECTS:
                        color = (0, 0, 255) # RED for danger
                        label = f"DANGER: {label.upper()}"
                        threat_detected = True
                    else:
                        color = (0, 255, 0) # GREEN for safe (person)
                    
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Trigger LLM on threat or every 15s
            current_time = time.time()
            # Force trigger if threat detected and last trigger was > 5s ago (faster reaction for threats)
            force_trigger = threat_detected and (current_time - self.last_trigger > 5)
            # Regular trigger every 15s
            regular_trigger = (current_time - self.last_trigger > 15)

            if force_trigger or regular_trigger:
                self.last_trigger = current_time
                if not self.is_processing_llm:
                    threading.Thread(target=self.llm_worker, args=(current_detected_objects,)).start()

            # HUD Display
            overlay = annotated_frame.copy()
            header_color = (0, 0, 50) if not threat_detected else (0, 0, 100) # Red tint if threat
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 120), header_color, -1)
            annotated_frame = cv2.addWeighted(overlay, 0.6, annotated_frame, 0.4, 0)
            
            line_color = (0, 255, 255) if not threat_detected else (0, 0, 255)
            cv2.line(annotated_frame, (0, 120), (frame.shape[1], 120), line_color, 2)

            status_text = "SECURE" if not threat_detected else "THREAT DETECTED"
            status_color = (0, 255, 0) if not threat_detected else (0, 0, 255)
            
            cv2.putText(annotated_frame, f"STATUS: {status_text}", (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

            # MIRA Response Wrapping
            text = f"MIRA: {str(self.current_response)}"
            max_width = 80
            y0, dy = 70, 25
            
            lines = [text[i:i+max_width] for i in range(0, len(text), max_width)]
            for i, line_text in enumerate(lines):
                y_pos = y0 + i * dy
                if y_pos < frame.shape[0] - 10:
                    cv2.putText(annotated_frame, line_text, (20, y_pos), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow("MIRA VISION - SECURITY MODE", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    MiraRobot().run()