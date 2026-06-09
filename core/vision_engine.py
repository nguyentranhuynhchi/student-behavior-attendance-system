# core/vision_engine.py
import cv2
import json
import time
import numpy as np
import threading
from ultralytics import YOLO
from db_helper import DatabaseHelper

# Import các Class từ 2 file linh kiện độc lập một cách chuẩn chỉnh
from core.pose_engine import PoseAnalyzer
from core.face_engine import FaceRecognizer

class VisionEngine:
    def __init__(self):
        # 1. Khởi tạo cơ sở dữ liệu và nạp mô hình AI
        self.db = DatabaseHelper()
        self.model_yolo = YOLO("yolo26n-pose.pt")
        self.model_yolo.to("cuda")
        self.is_running = False
        self.session_attendance = {}
        self.known_students = []
        self.track_mapping = {}
        self.db_ready_to_write = True
        
        # Khởi tạo instance của Class PoseAnalyzer để xài lâu dài
        self.pose_analyzer = PoseAnalyzer()
        
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

    def stop_stream(self):
        # 3. Phát lệnh dừng luồng quét camera thời gian thực
        self.is_running = False

    def background_face_and_db_worker(self, student_crop, session_id, current_phase_status, behavior, is_raising_hand, track_id, log_callback):
        """Hàm này xử lý trọn gói nhận diện khuôn mặt và ghi nhận DB trên Luồng Phụ ngầm"""
        # Khởi tạo Class FaceRecognizer và truyền data nền vào
        recognizer = FaceRecognizer(self.known_students)
        match_student = recognizer.recognize(student_crop)
        
        if match_student:
            student_id = match_student["student_id"]
            name = match_student["full_name"]
            avatar = match_student["avatar_path"]
            
            # Cập nhật mapping để luồng chính nhận diện ngay ở các khung hình sau
            if track_id != -1:
                self.track_mapping[track_id] = student_id
            
            if student_id not in self.session_attendance:
                init_hand_digit = 1 if is_raising_hand else 0
                # Ghi DB điểm danh lần đầu
                self.db.insert_attendance(session_id, student_id, current_phase_status, behavior, init_hand_digit)
                
                self.session_attendance[student_id] = {
                    "full_name": name,
                    "attendance_status": current_phase_status,
                    "behavior": behavior,
                    "raising_hand": is_raising_hand,
                    "avatar_path": avatar
                }
                log_callback(f"[GHI NHẬN] SV {name} - {current_phase_status}")
            
            print(f"[Worker Thread] Đã nhận diện thành công và cập nhật bộ nhớ đệm cho SV: {name}")
        else:
            print("[Worker Thread] Khuôn mặt lạ (Unknown) hoặc không khớp hệ thống.")

    def start_stream(self, session_id, ui_update_callback, student_detected_callback, session_end_callback, log_callback):
        # 4. Khởi chạy luồng xử lý video real-time và kiểm soát ghi nhận điểm danh
        self.is_running = True
        self.session_attendance = {}
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

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
                        
                        # Gọi hàm analyze_pose_behavior từ instance của Class PoseAnalyzer đã tạo ở __init__
                        behavior, is_raising_hand = self.pose_analyzer.analyze_pose_behavior(keypoints_data, box_coords)

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

                            # Đóng gói toàn bộ biến số cần thiết ném sang luồng phụ xử lý ngầm
                            ai_worker_thread = threading.Thread(
                                target=self.background_face_and_db_worker,
                                args=(
                                    student_crop.copy(), 
                                    session_id, 
                                    current_phase_status, 
                                    behavior, 
                                    is_raising_hand, 
                                    track_id, 
                                    log_callback
                                )
                            )
                            ai_worker_thread.daemon = True
                            ai_worker_thread.start()
                            
                            self.last_deepface_time = time.time()
                            print("[Main Thread] Đã chuyển tiếp ảnh khuôn mặt sang luồng phụ xử lý!")
                        else:
                            color = (0, 0, 255)
                            label_text = "Unknown"

                        # 5. Kiểm soát khóa cổng chu kỳ 5 giây và đồng bộ ghi nhận xuống DB
                        if int(elapsed_time) % 5 == 0:
                            if self.db_ready_to_write and student_id is not None:
                                hand_digit = 1 if is_raising_hand else 0
                                
                                db_thread = threading.Thread(
                                    target=self.db.insert_learning_status,
                                    args=(session_id, student_id, behavior, hand_digit)
                                )
                                db_thread.start()
                                
                                self.db_ready_to_write = False
                        else:
                            self.db_ready_to_write = True

                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            ui_update_callback(frame)
            time.sleep(0.01)

        cap.release()
        session_end_callback()