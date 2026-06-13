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
        self.tracks_in_processing = set()
        self.track_cooldown = {} # QUẢN LÝ THỜI GIAN COOLDOWN CỦA TỪNG TRACK ID
        self.gpu_lock = threading.Lock()
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
        with self.gpu_lock:
            match_student = recognizer.recognize(student_crop)
        if match_student:
            student_id = match_student["student_id"]
            name = match_student["full_name"]
            avatar = match_student["avatar_path"]
            
            if student_id not in self.session_attendance:
                # 1. NẾU CHƯA ĐIỂM DANH: Ghi RAM đệm + Ghi Database điểm danh lần đầu
                if track_id != -1:
                    self.track_mapping[track_id] = student_id
                
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
            else:
                # 2. NẾU ĐÃ ĐIỂM DANH XONG: Chỉ gán lại Track ID mới cho MSSV đó để UI vẽ khung xanh, KHÔNG ghi thêm DB
                if track_id != -1:
                    self.track_mapping[track_id] = student_id
            
            print(f"[Worker Thread] Đã xử lý nhận diện xong cho SV: {name}")
        else:
            print("[Worker Thread] Khuôn mặt lạ (Unknown) hoặc không khớp hệ thống.")

        # KẾT THÚC LUỒNG: Ghi nhận thời gian hoàn thành (Cooldown) và GỠ track_id ra khỏi tracks_in_processing
        if track_id != -1:
            self.track_cooldown[track_id] = time.time()
            if track_id in self.tracks_in_processing:
                self.tracks_in_processing.remove(track_id)

    def start_stream(self, session_id, ui_update_callback, student_detected_callback, session_end_callback, log_callback):
        # 4. Khởi chạy luồng xử lý video real-time và kiểm soát ghi nhận điểm danh
        self.is_running = True
        self.session_attendance = {}
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        log_callback("[HỆ THỐNG] Bắt đầu phiên điểm danh realtime...")
        start_time = time.time()

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
                        # Nhánh gọi DeepFace độc lập hoàn toàn cho từng BB mới xuất hiện (Đưa Cooldown lên check trực tiếp)
                        elif track_id != -1 and track_id not in self.tracks_in_processing and not (track_id in self.track_cooldown and (time.time() - self.track_cooldown[track_id] < 2.0)):
                            # Trích xuất mảng keypoints từ YOLOv26-Pose để tính toán sải vai ảnh thẻ
                            kp = result.keypoints.xy[0].cpu().numpy()
                            x_left_shoulder = kp[5][0]
                            x_right_shoulder = kp[6][0]
                            h_f, w_f, _ = frame.shape
                            
                            if x_left_shoulder > 0 and x_right_shoulder > 0:
                                shoulder_width = abs(x_left_shoulder - x_right_shoulder)
                                center_x = int((x_left_shoulder + x_right_shoulder) / 2)
                            else:
                                shoulder_width = int((x2 - x1) * 0.5)
                                center_x = (x1 + x2) // 2
                                
                            crop_w = int(shoulder_width * 1.3)
                            crop_h = int(crop_w * 1.5)
                            crop_x1 = max(0, center_x - (crop_w // 2))
                            crop_x2 = min(w_f, crop_x1 + crop_w)
                            padding_top = int(shoulder_width * 0.15)
                            crop_y1 = max(0, y1 - padding_top)
                            crop_y2 = min(h_f, crop_y1 + crop_h)
                            
                            student_crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                            
                            if student_crop.size > 0:
                                # THÊM VÀO TRACKS_IN_PROCESSING ĐỂ KHÓA CỔNG, TRÁNH GỌI TRÙNG LUỒNG DEEPFACE
                                self.tracks_in_processing.add(track_id)

                                # Kích hoạt duy nhất 1 Thread phụ độc lập xử lý nhận diện cho riêng BB này
                                ai_worker_thread = threading.Thread(
                                    target=self.background_face_and_db_worker,
                                    args=(student_crop.copy(), session_id, current_phase_status, behavior, is_raising_hand, track_id, log_callback)
                                )
                                ai_worker_thread.daemon = True
                                ai_worker_thread.start()
                                
                                color = (0, 255, 255)
                                label_text = "Scanning..."
                                print(f"[Main Thread] Đã kích hoạt Thread độc lập quét DeepFace cho Track ID: {track_id}")
                        else:
                            # Nếu BB này đang nằm trong tracks_in_processing HOẶC đang trong thời gian nghỉ Cooldown 2 giây
                            color = (0, 255, 255)
                            label_text = "Scanning..."
                            
                        # GHI LOGIC TRẠNG THÁI HỌC TẬP CHU KỲ 5 GIÂY XUỐNG DATABASE CHUẨN CHỈ
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

                        # Tiến hành vẽ Bounding Box và nhãn chữ lên giao diện UI của Luồng chính
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            ui_update_callback(frame)
            time.sleep(0.01)

        cap.release()
        session_end_callback()