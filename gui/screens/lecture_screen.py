# gui/screens/lecture_screen.py
import customtkinter as ctk
import threading
import cv2
import os
from datetime import datetime
from PIL import Image
from gui.theme import THEME_COLORS, FONT_FAMILY
from gui.constants import TEXT_ICONS
from core.vision_engine import VisionEngine
from db_helper import DatabaseHelper

class LectureScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = DatabaseHelper()
        self.engine = VisionEngine()
        
        self.session_id = None
        self.classroom_id = None
        self.lecture_name = ""
        self.lecture_date_str = ""
        self.end_time_str = ""
        self.student_bars = {}  
        self.class_student_ids = set()  # Danh sách MSSV thuộc lớp hiện tại
        
        self.countdown_time = 20  
        self.countdown_job = None   
        self.polling_job = None     
        self.runtime_job = None     
        self._camera_image = None
        self.stream_thread = None
        self.is_screen_active = False

        self.init_ui()

    def init_ui(self):
        # 1. HEADER BAR 
        header_container = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        header_container.pack(fill="x", padx=35, pady=(25, 15))
        
        self.lbl_welcome = ctk.CTkLabel(
            header_container, 
            text="Chào mừng đến với bài giảng: (Đang chờ kích hoạt)", 
            font=(FONT_FAMILY, 15, "bold"), 
            text_color=THEME_COLORS["text_title"]
        )
        self.lbl_welcome.pack(side="left", padx=20, pady=15)

        self.status_label = ctk.CTkLabel(
            header_container, 
            text="Trạng thái: Hệ thống đang quét lịch trình...", 
            font=(FONT_FAMILY, 13, "bold"), 
            text_color=THEME_COLORS["warning"]
        )
        self.status_label.pack(side="right", padx=20)

        # 2. MAIN LAYOUT (Camera 70% trái, Danh sách SV 30% phải)
        main_grid = ctk.CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="both", expand=True, padx=35, pady=(0, 25))
        main_grid.grid_rowconfigure(0, weight=1)
        main_grid.grid_columnconfigure(0, weight=70, uniform="main_layout")
        main_grid.grid_columnconfigure(1, weight=30, uniform="main_layout")

        # CỘT TRÁI: CAMERA AI
        self.main_cam_panel = ctk.CTkFrame(main_grid, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        self.main_cam_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        self.lbl_cam_title = ctk.CTkLabel(
            self.main_cam_panel, 
            text=f"{TEXT_ICONS.get('lecture_fallback', '')} CAMERA GIAM SAT REALTIME TRACKING (HD STANDARD)", 
            font=(FONT_FAMILY, 12, "bold"), 
            text_color=THEME_COLORS["text_title"]
        )
        self.lbl_cam_title.pack(anchor="w", padx=20, pady=(15, 5))

        self.cam_view = ctk.CTkLabel(
            self.main_cam_panel, 
            text="[ Camera đang tắt - Chờ luồng đếm ngược chuẩn bị ]", 
            font=(FONT_FAMILY, 14), 
            fg_color=THEME_COLORS["bg_dark"],
            corner_radius=8
        )
        self.cam_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # CỘT PHẢI: DANH SÁCH SINH VIÊN GHI DANH
        self.attendance_list_panel = ctk.CTkFrame(main_grid, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        self.attendance_list_panel.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self.lbl_attendance_title = ctk.CTkLabel(
            self.attendance_list_panel, 
            text="DANH SÁCH SINH VIÊN TRONG LỚP", 
            font=(FONT_FAMILY, 12, "bold"), 
            text_color=THEME_COLORS["text_title"]
        )
        self.lbl_attendance_title.pack(anchor="w", padx=15, pady=(15, 5))

        self.student_bar_scroll = ctk.CTkScrollableFrame(self.attendance_list_panel, fg_color="transparent")
        self.student_bar_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bắt đầu vòng lặp quét tín hiệu bài giảng
        self.start_listening_lobby_signal()

    def refresh_and_load_data(self):
        self.is_screen_active = True
        if self.session_id is not None and self.engine.is_running:
            return
        if self.session_id is not None and not self.engine.is_running:
            self.session_id = None
            self.classroom_id = None
        self.start_listening_lobby_signal()

    def prepopulate_class_roster(self, classroom_id):
        """Tải trước danh sách SV của lớp lên panel phải, đánh dấu 'Chưa điểm danh'"""
        for widget in self.student_bar_scroll.winfo_children():
            widget.destroy()
        self.student_bars.clear()
        self.class_student_ids.clear()

        try:
            students = self.db.get_students_by_classroom(classroom_id)
            for row in students:
                sid = row["student_id"]
                name = row["full_name"]
                avatar = row["avatar_path"] if row["avatar_path"] else ""
                self.class_student_ids.add(sid)
                self._create_student_bar(sid, name, "Chưa điểm danh", is_waiting=True)
            
            self.lbl_attendance_title.configure(
                text=f"DANH SÁCH SINH VIÊN ({len(students)} SV)"
            )
        except Exception as e:
            print(f"[X] Lỗi tải danh sách SV lớp: {e}")

    def _create_student_bar(self, student_id, student_name, status_text, is_waiting=False):
        """Tạo thẻ sinh viên trên panel phải"""
        # Màu nền và border khác nhau tùy trạng thái
        if is_waiting:
            bar_bg = THEME_COLORS["bg_input"]
            border_color = THEME_COLORS["border"]
        else:
            bar_bg = THEME_COLORS["bg_input"]
            border_color = THEME_COLORS["primary"]

        bar_frame = ctk.CTkFrame(
            self.student_bar_scroll, fg_color=bar_bg, corner_radius=8,
            border_width=1, border_color=border_color, height=65
        )
        bar_frame.pack(fill="x", pady=5, padx=5)
        bar_frame.pack_propagate(False)

        lbl_avatar = ctk.CTkLabel(
            bar_frame, text=TEXT_ICONS.get("user_avatar", "[U]"),
            font=(FONT_FAMILY, 20), text_color=THEME_COLORS["text_title"], width=40
        )
        lbl_avatar.pack(side="left", padx=12, pady=5)

        info_block = ctk.CTkFrame(bar_frame, fg_color="transparent")
        info_block.pack(side="left", fill="both", expand=True, pady=6)
        ctk.CTkLabel(
            info_block, text=student_name,
            font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_main"], anchor="w"
        ).pack(fill="x")
        
        lbl_status = ctk.CTkLabel(
            info_block, text=f"MSSV: {student_id} | {status_text}",
            font=(FONT_FAMILY, 11), text_color=THEME_COLORS["text_muted"], anchor="w"
        )
        lbl_status.pack(fill="x")

        status_block = ctk.CTkFrame(bar_frame, fg_color="transparent")
        status_block.pack(side="right", padx=15, pady=6)
        
        if is_waiting:
            behavior_text = "⏳ Đang chờ..."
            behavior_color = THEME_COLORS["text_muted"]
        else:
            behavior_text = "Biểu hiện: Focusing"
            behavior_color = THEME_COLORS["success_text"]

        lbl_behavior = ctk.CTkLabel(
            status_block, text=behavior_text,
            font=(FONT_FAMILY, 11, "bold"), text_color=behavior_color
        )
        lbl_behavior.pack(anchor="e")
        
        lbl_hand = ctk.CTkLabel(
            status_block, text="",
            font=(FONT_FAMILY, 10, "bold"), text_color=THEME_COLORS["text_muted"]
        )
        lbl_hand.pack(anchor="e")

        self.student_bars[student_id] = {
            "bar_frame": bar_frame,
            "lbl_status": lbl_status,
            "lbl_behavior": lbl_behavior,
            "lbl_hand": lbl_hand,
        }

    def start_listening_lobby_signal(self):
        """Quét tìm bài giảng (đang diễn ra hoặc đã đến giờ) và khởi động vào lớp"""
        if not self.is_screen_active:
            return

        if self.polling_job:
            self.after_cancel(self.polling_job)
            self.polling_job = None
            
        try:
            if self.session_id is None:
                # 1. Tìm lớp đang học (nếu Lobby đã kích hoạt)
                active_session = self.db.get_session_by_status("ongoing")
                
                # 2. Nếu không có lớp đang học, tìm lớp sắp tới xem đã đến giờ chưa
                if not active_session:
                    upcoming = self.db.get_next_upcoming_session()
                    if upcoming:
                        now = datetime.now()
                        date_clean = upcoming['lecture_date'].strip()
                        start_time_clean = upcoming['start_time'].strip().split('.')[0]
                        end_time_clean = upcoming['end_time'].strip().split('.')[0]
                        
                        # Chuẩn hóa chuỗi thời gian nếu người dùng chỉ nhập HH:MM (thêm :00 giây)
                        if len(start_time_clean) == 5: start_time_clean += ":00"
                        if len(end_time_clean) == 5: end_time_clean += ":00"
                        
                        start_dt = datetime.strptime(f"{date_clean} {start_time_clean}", "%Y-%m-%d %H:%M:%S")
                        end_dt = datetime.strptime(f"{date_clean} {end_time_clean}", "%Y-%m-%d %H:%M:%S")
                        
                        # CHỈ kích hoạt tự động nếu thời gian hiện tại nằm TRONG khoảng thời gian học
                        if start_dt <= now <= end_dt:
                            self.db.update_lecture_session_status(upcoming["session_id"], "ongoing")
                            active_session = upcoming
                            active_session["status"] = "ongoing"

                # 3. Kích hoạt camera nếu có lớp hợp lệ
                if active_session:
                    self.session_id = active_session["session_id"]
                    self.classroom_id = active_session.get("classroom_id")
                    self.lecture_name = active_session["course_name"]
                    self.lecture_date_str = active_session["lecture_date"]
                    self.start_time_str = active_session["start_time"]
                    self.end_time_str = active_session["end_time"]
                    
                    self.lbl_welcome.configure(text=f"Chào mừng đến với bài giảng: {self.lecture_name}")
                    self.status_label.configure(text="Lớp học đang diễn ra", text_color=THEME_COLORS["primary_light"])
                    
                    # Pre-populate danh sách SV thuộc lớp trước khi bật camera
                    if self.classroom_id:
                        self.prepopulate_class_roster(self.classroom_id)
                    
                    self.start_vision_engine()
                    self.start_lecture_runtime_countdown()
                    
                    return 
                        
        except Exception as e:
            print(f"[*] Lỗi đồng bộ tín hiệu lớp học: {e}")

        # Thăm dò lại sau 2 giây nếu chưa tới giờ
        self.polling_job = self.after(2000, self.start_listening_lobby_signal)

    def start_lecture_runtime_countdown(self):
        """Đồng hồ đếm ngược thời gian thực của buổi học"""
        if self.runtime_job:
            self.after_cancel(self.runtime_job)
            self.runtime_job = None

        try:
            date_clean = self.lecture_date_str.strip()
            end_time_clean = self.end_time_str.strip().split('.')[0]
            
            # Chuẩn hóa giây
            if len(end_time_clean) == 5: end_time_clean += ":00"
            
            end_dt = datetime.strptime(f"{date_clean} {end_time_clean}", "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            if now < end_dt:
                remaining = int((end_dt - now).total_seconds())
                hours = remaining // 3600
                mins = (remaining % 3600) // 60
                secs = remaining % 60
                self.status_label.configure(text=f"Thời gian tiết học còn lại: {hours:02d}:{mins:02d}:{secs:02d}", text_color=THEME_COLORS["success_text"])
                
                self.runtime_job = self.after(1000, self.start_lecture_runtime_countdown)
            else:
                self.finish_lecture_session()
        except Exception as e:
            print(f"[X] Lỗi đồng hồ thời gian thực lớp học: {e}")
            self.runtime_job = self.after(1000, self.start_lecture_runtime_countdown)

    def start_vision_engine(self):
        """Bật camera quét sinh viên thông qua luồng phụ (KHÔNG xóa danh sách SV đã pre-populate)"""
        if self.engine.is_running:
            return

        self.engine.load_known_embeddings()
        self.stream_thread = threading.Thread(
            target=self.engine.start_stream,
            args=(self.session_id, self.update_camera_feed, self.update_student_card, self.lecture_session_end_callback, print),
            daemon=True
        )
        self.stream_thread.start()

    def finish_lecture_session(self):
        """Kết thúc bài giảng an toàn, đóng camera và đồng bộ hóa trạng thái"""
        if self.runtime_job:
            self.after_cancel(self.runtime_job)
            self.runtime_job = None
            
        self.engine.stop_stream()
        
        if self.session_id:
            self.db.update_lecture_session_status(self.session_id, "completed")
            
        self.status_label.configure(text="Bài giảng đã kết thúc hoàn tất", text_color=THEME_COLORS["text_muted"])
        self._set_camera_text("[ Hệ thống Camera Tắt - Phiên Học Đã Kết Thúc ]")
        
        # Đánh dấu SV chưa được quét là "Vắng mặt"
        for sid, bar_data in self.student_bars.items():
            if sid in self.class_student_ids:
                current_text = bar_data["lbl_behavior"].cget("text")
                if "Đang chờ" in current_text:
                    bar_data["lbl_behavior"].configure(text="Vắng mặt", text_color=THEME_COLORS["danger"])
                    bar_data["lbl_status"].configure(text=f"MSSV: {sid} | Vắng mặt")
        
        # Reset các tham số, quay lại trạng thái chờ bài giảng tiếp theo
        self.session_id = None
        self.classroom_id = None
        self.lecture_name = ""
        self.lbl_welcome.configure(text="Chào mừng đến với bài giảng: (Đang chờ lịch trình)")
        self.lbl_attendance_title.configure(text="DANH SÁCH SINH VIÊN TRONG LỚP")
        self.polling_job = self.after(5000, self.start_listening_lobby_signal)

    def update_camera_feed(self, cv_frame):
        """Nhận khung hình, giữ nguyên tỷ lệ HD 16:9 chuẩn từ camera phần cứng"""
        def _render():
            try:
                if not self.is_screen_active or not self.winfo_ismapped() or not self.engine.is_running:
                    return

                # Tính toán kích thước hiển thị dựa trên chiều rộng khung để ép cứng tỷ lệ 16:9
                render_w = self.main_cam_panel.winfo_width() - 40
                render_h = int(render_w * (9 / 16)) # Luôn giữ tỷ lệ 16:9 chuẩn HD
                
                # Giới hạn chiều cao nếu vượt quá khung chứa cho phép
                max_h = self.main_cam_panel.winfo_height() - 70
                if render_h > max_h:
                    render_h = max_h
                    render_w = int(render_h * (16 / 9))

                if render_w <= 0 or render_h <= 0:
                    return

                cv_frame_resized = cv2.resize(cv_frame, (render_w, render_h))
                cv_img = cv2.cvtColor(cv_frame_resized, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(cv_img)
                
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(render_w, render_h))
                self._camera_image = ctk_img
                self.cam_view.configure(image=ctk_img)
                self.cam_view.configure(text="")
            except Exception as e:
                print(f"[X] Render Cam Error: {e}")
        self.after(0, _render)

    def _set_camera_text(self, text):
        """Clear frame camera an toàn trước khi đổi text để tránh lỗi pyimage stale của Tk."""
        try:
            self.cam_view.configure(image=None)
        except Exception:
            try:
                self.cam_view._label.configure(image="")
            except Exception:
                pass

        self._camera_image = None

        try:
            self.cam_view.configure(text=text)
        except Exception:
            try:
                self.cam_view._label.configure(text=text)
            except Exception as e:
                print(f"[X] Clear Cam Error: {e}")

    def update_student_card(self, student_id, student_name, attendance_status, avatar_path):
        """Cập nhật hoặc thêm mới thông tin thẻ sinh viên"""
        def _render_student():
            current_behavior = self.engine.session_attendance.get(student_id, {}).get("behavior", "Focusing")
            is_raising_hand = self.engine.session_attendance.get(student_id, {}).get("raising_hand", False)
            hand_status_text = f"{TEXT_ICONS.get('hand_raising', '')} Giơ tay phát biểu" if is_raising_hand else "Không phát biểu"
            hand_status_color = THEME_COLORS["primary"] if is_raising_hand else THEME_COLORS["text_muted"]
            behavior_color = THEME_COLORS["success_text"] if current_behavior == "Focusing" else THEME_COLORS["warning"]

            if student_id in self.student_bars:
                # SV đã có thẻ (từ pre-populate hoặc lần quét trước) → cập nhật
                bar_data = self.student_bars[student_id]
                bar_data["bar_frame"].configure(border_color=THEME_COLORS["primary"])
                bar_data["lbl_status"].configure(text=f"MSSV: {student_id} | {attendance_status}")
                bar_data["lbl_behavior"].configure(text=f"Biểu hiện: {current_behavior}", text_color=behavior_color)
                bar_data["lbl_hand"].configure(text=hand_status_text, text_color=hand_status_color)
            else:
                # SV ngoài lớp (không có trong roster) → tạo thẻ mới, thêm vào cuối
                self._create_student_bar(student_id, student_name, f"{attendance_status}", is_waiting=False)
                bar_data = self.student_bars[student_id]
                bar_data["lbl_behavior"].configure(text=f"Biểu hiện: {current_behavior}", text_color=behavior_color)
                bar_data["lbl_hand"].configure(text=hand_status_text, text_color=hand_status_color)
        self.after(0, _render_student)

    def lecture_session_end_callback(self):
        pass

    def pack_forget(self):
        """Hủy toàn bộ luồng chạy ngầm khi người dùng chuyển tab để tránh rò rỉ bộ nhớ"""
        self.is_screen_active = False
        if self.polling_job: 
            self.after_cancel(self.polling_job)
            self.polling_job = None
        if self.countdown_job: 
            self.after_cancel(self.countdown_job)
            self.countdown_job = None
        if self.runtime_job: 
            self.after_cancel(self.runtime_job)
            self.runtime_job = None
        self.engine.stop_stream()
        self.session_id = None
        self.classroom_id = None
        self._set_camera_text("[ Camera đang tạm dừng - Chọn lại Phòng Học để tiếp tục ]")
        super().pack_forget()
