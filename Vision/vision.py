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

from deepface import DeepFace
from ultralytics import YOLO
import cv2
import time
import threading
import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_POSE = "yolov8n-pose.pt"

class MiraRobot:
    def __init__(self):
        print("--- MIRA VISION : READY ---")
        self.model = YOLO(MODEL_POSE)
        self.current_response = "J'analyse..."
        self.is_processing_llm = False
        self.last_trigger = 0
        self.current_emotion = "neutre"

    def analyze_face(self, frame):
        try:
            analysis = DeepFace.analyze(
                frame, 
                actions=['emotion'], 
                enforce_detection=False, 
                detector_backend='opencv', 
                silent=True
            )
            if analysis:
                self.current_emotion = analysis[0]['dominant_emotion']
        except:
            pass

    def llm_worker(self, emotion, pose_desc):
        self.is_processing_llm = True
        try:
            payload = {
                "model": "ministral-3-3b-instruct-2512",
                "messages": [
                    {"role": "system", "content": "Tu es MIRA. Tu es sarcastique et brève."},
                    {"role": "user", "content": f"L'utilisateur est {emotion} et {pose_desc}. Commentaire court et piquant."}
                ],
                "temperature": 0.7,
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

            if results.boxes:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 255), 2)

            if results.keypoints is not None:
                for kpts in results.keypoints.xyn:
                    for i, (x, y) in enumerate(kpts):
                        if i >= 5:
                            px, py = int(x * frame.shape[1]), int(y * frame.shape[0])
                            if px > 0 and py > 0:
                                cv2.circle(annotated_frame, (px, py), 4, (0, 255, 0), -1)

            if time.time() - self.last_trigger > 4:
                self.last_trigger = time.time()
                threading.Thread(target=self.analyze_face, args=(frame.copy(),)).start()

                if not self.is_processing_llm:
                    pose = "immobile"
                    if results.keypoints is not None and len(results.keypoints.xyn) > 0:
                        if results.keypoints.xyn[0][9][1] < 0.5: 
                            pose = "bras levés / excité"
                    
                    threading.Thread(target=self.llm_worker, args=(self.current_emotion, pose)).start()

            cv2.rectangle(annotated_frame, (0, 0), (frame.shape[1], 80), (0, 0, 0), -1)
            cv2.putText(annotated_frame, f"MOOD: {self.current_emotion.upper()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(annotated_frame, f"MIRA: {self.current_response}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow("MIRA VISION", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    MiraRobot().run()