# core/vision_engine.py
import cv2
import json
import time
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
from db_helper import DatabaseHelper

class VisionEngine:
    def __init__(self):
        # 1. Khởi tạo cơ sở dữ liệu và nạp mô hình AI
        self.db = DatabaseHelper()
        self.model_yolo = YOLO("yolo11n-pose.pt")
        self.is_running = False
        self.session_attendance = {}
        self.known_students = []
        self.track_mapping = {}
        self.db_ready_to_write = True
        self.load_known_embeddings()

    def load_known_embeddings(self):
        # 2. Tải danh sách vector khuôn mặt sinh viên từ DB lên RAM
        rows = self.db.get_all_valid_embeddings()
        self.known_students = []
        for row in rows:
            try:
                emb_list = json.loads(row['face_embedding'])
                self.known_students.append({
                    "student_id": row['student_id'],
                    "full_name": row['full_name'],
                    "avatar_path": row['avatar_path'],
                    "embedding": np.array(emb_list, dtype=np.float32)
                })
            except Exception as e:
                print(f"[X] Lỗi đọc Vector SV {row['student_id']}: {e}")

    def compute_cosine_distance(self, emb1, emb2):
        # 3. Tính toán khoảng cách hình học Cosine giữa hai Vector khuôn mặt
        dot_product = np.dot(emb1, emb2)
        norm_emb1 = np.linalg.norm(emb1)
        norm_emb2 = np.linalg.norm(emb2)
        return 1.0 - (dot_product / (norm_emb1 * norm_emb2))

    def stop_stream(self):
        # 4. Phát lệnh dừng luồng quét camera thời gian thực
        self.is_running = False

    def analyze_pose_behavior(self, keypoints, box_coords=None):
        # 5. Phân tích tọa độ khớp xương cơ thể để xác định trạng thái học tập và phát biểu
        if keypoints is None or len(keypoints.xy) == 0:
            return "Distracted", False

        pts = keypoints.xy[0].cpu().numpy()
        if len(pts) < 11:
            return "Distracted", False

        left_eye, right_eye = pts[1], pts[2]
        left_shoulder, right_shoulder = pts[5], pts[6]
        left_wrist, right_wrist = pts[9], pts[10]

        is_raising_hand = False

        # Nhánh quét hành vi Giơ tay (Cổ tay cao hơn mắt)
        if left_eye[1] > 0 and left_wrist[1] > 0 and left_wrist[1] < left_eye[1]:
            is_raising_hand = True
        if right_eye[1] > 0 and right_wrist[1] > 0 and right_wrist[1] < right_eye[1]:
            is_raising_hand = True

        # Nhánh quét hành vi Đứng lên (Dựa vào tỉ lệ tọa độ vai so với chiều cao khung hình bao)
        if box_coords is not None:
            bx1, by1, bx2, by2 = box_coords
            box_height = by2 - by1
            if box_height > 0:
                if left_shoulder[1] > 0 and (left_shoulder[1] - by1) / box_height < 0.28:
                    is_raising_hand = True
                elif right_shoulder[1] > 0 and (right_shoulder[1] - by1) / box_height < 0.28:
                    is_raising_hand = True

        behavior = "Focusing"
        
        # Nhánh quét độ tập trung dựa vào khoảng cách đứng giữa đầu và vai
        if left_eye[1] > 0 and left_shoulder[1] > 0:
            head_shoulder_dist = left_shoulder[1] - left_eye[1]
            if head_shoulder_dist < 45:
                behavior = "Distracted"
        elif right_eye[1] > 0 and right_shoulder[1] > 0:
            head_shoulder_dist = right_shoulder[1] - right_eye[1]
            if head_shoulder_dist < 45:
                behavior = "Distracted"

        return behavior, is_raising_hand
    
    def start_stream(self, session_id, ui_update_callback, student_detected_callback, session_end_callback, log_callback):
        # 6. Khởi chạy luồng xử lý video real-time và kiểm soát ghi nhận điểm danh
        self.is_running = True
        self.session_attendance = {}
        cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        log_callback("[HỆ THỐNG] Bắt đầu phiên điểm danh realtime...")
        start_time = time.time()
        self.last_deepface_time = 0

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                break

            elapsed_time = time.time() - start_time
            current_phase_status = "Có mặt" if elapsed_time <= 10.0 else "Đi trễ"
            results = self.model_yolo.track(frame, persist=True, verbose=False)
            
            for result in results:
                if not result.boxes or not hasattr(result, 'keypoints') or result.keypoints is None:
                    continue

                for i, box in enumerate(result.boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0].item())
                    cls = int(box.cls[0].item())
                    track_id = int(box.id[0].item()) if box.id is not None else -1

                    if cls == 0 and conf > 0.45:
                        keypoints_data = result.keypoints[i]
                        box_coords = (x1, y1, x2, y2)
                        behavior, is_raising_hand = self.analyze_pose_behavior(keypoints_data, box_coords)

                        color = (0, 255, 255)
                        label_text = "Scanning..."
                        student_id = None

                        # Nhánh xử lý sinh viên cũ đã định danh (Truy xuất từ RAM đệm)
                        if track_id != -1 and track_id in self.track_mapping:
                            student_id = self.track_mapping[track_id]
                            if student_id in self.session_attendance:
                                self.session_attendance[student_id]["behavior"] = behavior
                                self.session_attendance[student_id]["raising_hand"] = is_raising_hand
                                
                                name = self.session_attendance[student_id]["full_name"]
                                avatar = self.session_attendance[student_id]["avatar_path"]
                                
                                student_detected_callback(student_id, name, self.session_attendance[student_id]["attendance_status"], avatar)
                                color = (0, 255, 0) if self.session_attendance[student_id]["attendance_status"] == "Có mặt" else (0, 165, 255)
                                hand_status = " | REQ " if is_raising_hand else ""
                                label_text = f"{name} ({behavior}{hand_status})"

                        # Nhánh gọi DeepFace nhận diện khuôn mặt lần đầu (Chu kỳ trễ 5s)
                        elif time.time() - self.last_deepface_time >= 5.0:
                            h_f, w_f, _ = frame.shape
                            pad = 15
                            x1_p = max(0, x1 - pad)
                            y1_p = max(0, y1 - pad)
                            x2_p = min(w_f, x2 + pad)
                            y2_p = min(h_f, y2 + pad)

                            student_crop = frame[y1_p:y2_p, x1_p:x2_p]
                            if student_crop.size == 0:
                                continue

                            try:
                                emb_objs = DeepFace.represent(
                                    img_path=student_crop,
                                    model_name="Facenet",
                                    detector_backend="opencv",
                                    enforce_detection=False
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
                                    
                                    if min_dist < 0.55 and match_student:
                                        student_id = match_student["student_id"]
                                        name = match_student["full_name"]
                                        avatar = match_student["avatar_path"]
                                        
                                        if track_id != -1:
                                            self.track_mapping[track_id] = student_id
                                        
                                        if student_id not in self.session_attendance:
                                            init_hand_digit = 1 if is_raising_hand else 0
                                            self.db.insert_attendance(session_id, student_id, current_phase_status, behavior, init_hand_digit)
                                            
                                            self.session_attendance[student_id] = {
                                                "full_name": name,
                                                "attendance_status": current_phase_status,
                                                "behavior": behavior,
                                                "raising_hand": is_raising_hand,
                                                "avatar_path": avatar
                                            }
                                            log_callback(f"[GHI NHẬN] SV {name} - {current_phase_status}")
                                        
                                        student_detected_callback(student_id, name, current_phase_status, avatar)
                                        color = (0, 255, 0) if current_phase_status == "Có mặt" else (0, 165, 255)
                                        hand_status = " | REQ " if is_raising_hand else ""
                                        label_text = f"{name} ({behavior}{hand_status})"
                                    else:
                                        color = (0, 0, 255)
                                        label_text = "Unknown"
                                self.last_deepface_time = time.time()
                            except Exception as e:
                                pass

                        # 7. Kiểm soát khóa cổng chu kỳ 5 giây và đồng bộ ghi nhận đa biến số xuống DB
                        if int(elapsed_time) % 5 == 0:
                            if self.db_ready_to_write and student_id:
                                hand_digit = 1 if is_raising_hand else 0
                                self.db.insert_learning_status(session_id, student_id, behavior, hand_digit)
                                self.db_ready_to_write = False
                        else:
                            self.db_ready_to_write = True

                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            ui_update_callback(frame)
            time.sleep(0.01)

        cap.release()
        session_end_callback()