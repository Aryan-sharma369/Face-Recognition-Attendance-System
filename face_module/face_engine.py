import cv2
import face_recognition
import os
import numpy as np
import time
from datetime import datetime
from utils.attendance_logger import mark_attendance

class FaceRecognitionSystemWeb:
    def __init__(self, app, folder_name="known_faces"):
        self.app = app
        self.image_folder = folder_name
        self.known_encodings = []
        self.known_names = []
        self.last_seen = {} # Cooldown tracker
        self.load_known_faces()

    def load_known_faces(self):
        self.known_encodings = []
        self.known_names = []
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
            
        for filename in os.listdir(self.image_folder):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                path = os.path.join(self.image_folder, filename)
                img = face_recognition.load_image_file(path)
                encs = face_recognition.face_encodings(img)
                if encs:
                    self.known_encodings.append(encs[0])
                    self.known_names.append(os.path.splitext(filename)[0].title())

    def generate_frames(self):
        video_capture = cv2.VideoCapture(0)
        while True:
            success, frame = video_capture.read()
            if not success: break

            # Process smaller frame for speed
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small)
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_names[first_match_index]
                    
                    # Log Attendance with Cooldown (10 minutes)
                    now = datetime.now()
                    if name not in self.last_seen or (now - self.last_seen[name]).total_seconds() > 600:
                        if mark_attendance(self.app, name):
                            self.last_seen[name] = now

                # UI Box
                top, right, bottom, left = [v * 4 for v in face_location]
                color = (79, 70, 229) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')