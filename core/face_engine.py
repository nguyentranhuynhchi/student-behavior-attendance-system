# core/face_recognizer.py
import numpy as np
import tensorflow as tf
from deepface import DeepFace

class FaceRecognizer:
    def __init__(self, known_students):
        self.known_students = known_students

    def compute_cosine_distance(self, emb1, emb2):
        """Tính toán khoảng cách hình học Cosine giữa hai Vector khuôn mặt"""
        dot_product = np.dot(emb1, emb2)
        norm_emb1 = np.linalg.norm(emb1)
        norm_emb2 = np.linalg.norm(emb2)
        return 1.0 - (dot_product / (norm_emb1 * norm_emb2))

    def recognize(self, student_crop):
        """Trích xuất ma trận khuôn mặt bằng GPU rời và thực hiện khớp danh tính"""
        try:
            with tf.device('/GPU:0'):
                emb_objs = DeepFace.represent(
                    img_path=student_crop,
                    model_name="ArcFace",
                    detector_backend="retinaface",
                    enforce_detection=True,
                    align=True,
                )
            
            if emb_objs and len(emb_objs) > 0:
                current_emb = np.array(emb_objs[0]["embedding"], dtype=np.float32)
                min_dist = 1.0
                match_student = None
                
                for student in self.known_students:
                    dist = self.compute_cosine_distance(current_emb, student["embedding"])
                    if dist < min_dist:
                        min_dist = dist
                        match_student = student
                
                if min_dist < 0.38 and match_student:
                    return match_student
            return None
        except Exception as e:
            print(f"[FaceRecognizer] Lỗi xử lý nhận diện: {e}")
            return None