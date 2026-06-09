# gui/screens/session_screen.py
import customtkinter as ctk
from datetime import datetime
from gui.theme import THEME_COLORS, FONT_FAMILY
from gui.components.card import CustomCard
from gui.controllers.session_controller import SessionController

class SessionScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.controller = SessionController()
        self.classroom_lookup = {}
        self.classroom_empty_text = "Chưa có lớp học trong DB"
        self.init_ui()
        
    def init_ui(self):
        from gui.constants import TEXT_ICONS

        # 1. TIÊU ĐỀ CHÍNH CỦA MÀN HÌNH (HEADER SCREEN)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 15))
        
        ctk.CTkLabel(
            header_frame, text="Cấu Hình & Thiết Lập Phiên Học", 
            font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame, text="Khởi tạo một phiên bài giảng mới, tải tài liệu học tập hướng dẫn và tùy chỉnh các tham số AI thời gian thực.", 
            font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]
        ).pack(anchor="w", pady=(5, 0))

        # THÀNH PHẦN HIỂN THỊ THÔNG BÁO TRẠNG THÁI (STATUS LABEL)
        self.lbl_status = ctk.CTkLabel(header_frame, text="", font=(FONT_FAMILY, 13, "bold"))
        self.lbl_status.pack(anchor="w", pady=(5, 0))

        # 2. KHU VỰC BỐ CỤC CHÍNH CHIA LÀM HAI BÊN (MAIN SPLIT GRID)
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=30, pady=10)
        content_grid.grid_columnconfigure(0, weight=55, uniform="session_layout") # Panel biểu mẫu thông tin bên trái
        content_grid.grid_columnconfigure(1, weight=45, uniform="session_layout") # Panel cấu hình AI nâng cao bên phải
        content_grid.grid_rowconfigure(0, weight=1)

        # PANEL BÊN TRÁI: FORM NHẬP THÔNG TIN BÀI GIẢNG
        left_panel = CustomCard(content_grid)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Khung chứa hỗ trợ cuộn chuột tự động chống tràn giao diện
        form_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            form_scroll, text="THÔNG TIN BÀI GIẢNG CHÍNH", 
            font=(FONT_FAMILY, 15, "bold"), text_color=THEME_COLORS["text_title"]
        ).pack(anchor="w", pady=(0, 15))

        # Trường số 0: Trường nhập Mã bài giảng / Mã môn học
        # ctk.CTkLabel(form_scroll, text="Mã Bài Giảng / Mã Môn Học", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        # self.ent_course_code = ctk.CTkEntry(form_scroll, placeholder_text="Ví dụ: AI001", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], height=42, font=(FONT_FAMILY, 13))
        # self.ent_course_code.pack(fill="x", pady=(0, 12))

        # Trường số 1: Nhập tên môn học / tên bài giảng
        ctk.CTkLabel(form_scroll, text="Tên Môn Học / Tên Bài Giảng", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        self.ent_course_name = ctk.CTkEntry(form_scroll, placeholder_text="Ví dụ: Chuyên đề Trí Tuệ Nhân Tạo & Học Máy", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], height=42, font=(FONT_FAMILY, 13))
        self.ent_course_name.pack(fill="x", pady=(0, 12))

        # Trường số 2: Chọn lớp học áp dụng cho phiên học
        classroom_values = self.load_classroom_options()
        self.selected_classroom = ctk.StringVar(value=classroom_values[0])

        ctk.CTkLabel(form_scroll, text="Lớp Học / Phòng Học", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        self.opt_classroom = ctk.CTkOptionMenu(
            form_scroll,
            values=classroom_values,
            variable=self.selected_classroom,
            fg_color=THEME_COLORS["bg_input"],
            button_color=THEME_COLORS["primary"],
            button_hover_color=THEME_COLORS["primary_hover"],
            text_color=THEME_COLORS["text_main"],
            dropdown_fg_color=THEME_COLORS["bg_card"],
            dropdown_text_color=THEME_COLORS["text_main"],
            height=42,
            font=(FONT_FAMILY, 13),
        )
        self.opt_classroom.pack(fill="x", pady=(0, 12))
        if not self.classroom_lookup:
            self.opt_classroom.configure(state="disabled")

        # Dòng thời gian tổ chức 1: Ngày và Giờ bắt đầu
        row_time_1 = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_time_1.pack(fill="x", pady=(0, 12))
        row_time_1.grid_columnconfigure((0, 1), weight=1, uniform="time_grid")

        # Trường số 2: Chọn hoặc nhập ngày học
        f_date = ctk.CTkFrame(row_time_1, fg_color="transparent")
        f_date.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_date, text="Ngày Diễn Ra", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        self.ent_date = ctk.CTkEntry(f_date, placeholder_text="DD/MM/YYYY", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], height=42, font=(FONT_FAMILY, 13))
        self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y")) # Định dạng chuẩn DD/MM/YYYY đồng bộ với LobbyScreen
        self.ent_date.pack(fill="x")

        # Trường số 3: Nhập thời gian bắt đầu tiết học
        f_start = ctk.CTkFrame(row_time_1, fg_color="transparent")
        f_start.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(f_start, text="Thời Gian Bắt Đầu", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        self.start_hour_var, self.start_minute_var = self.create_time_picker(f_start, "07", "00")

        # Dòng thời gian tổ chức 2: Giờ kết thúc và Nút upload tài liệu đính kèm
        row_time_2 = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_time_2.pack(fill="x", pady=(0, 12))
        row_time_2.grid_columnconfigure((0, 1), weight=1, uniform="time_grid")

        # Trường số 4: Nhập thời gian kết thúc tiết học
        f_end = ctk.CTkFrame(row_time_2, fg_color="transparent")
        f_end.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_end, text="Thời Gian Kết Thúc", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        self.end_hour_var, self.end_minute_var = self.create_time_picker(f_end, "08", "00")

        # Trường số 5: Tải tài liệu đề cương / giáo trình bài giảng (UI giả lập giữ nguyên)
        f_docs = ctk.CTkFrame(row_time_2, fg_color="transparent")
        f_docs.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(f_docs, text="Tài Liệu Bài Giảng", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))
        
        upload_btn_text = f"{TEXT_ICONS['file_attachment']} Đính Kèm Đề Cương / PDF"
        self.btn_upload_docs = ctk.CTkButton(
            f_docs, text=upload_btn_text, 
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=THEME_COLORS["btn_pdf_bg"], 
            border_color=THEME_COLORS["btn_pdf_border"], 
            border_width=1, 
            hover_color=THEME_COLORS["btn_pdf_hover"], 
            height=42,
            command=self.handle_mock_upload
        )
        self.btn_upload_docs.pack(fill="x")

        # Trường số 6: Nhập lưu ý thêm hoặc các ghi chú lớp học bổ sung (UI)
        ctk.CTkLabel(form_scroll, text="Lưu Ý Thêm / Ghi Chú Lớp Học", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        self.txt_notes = ctk.CTkTextbox(form_scroll, fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], border_width=1, height=100, font=(FONT_FAMILY, 13), corner_radius=8)
        self.txt_notes.pack(fill="x", pady=(0, 5))
        self.txt_notes.insert("0.0", "Nhập các hướng dẫn đặc biệt hoặc lưu ý nội quy phòng học tại đây...")

        # PANEL BÊN PHẢI: CẤU HÌNH CÁC THAM SỐ AI AGENT TRỰC TIẾP
        right_panel = CustomCard(content_grid)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ai_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        ai_container.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            ai_container, text="THAM SỐ GIÁM SÁT AI AGENT", 
            font=(FONT_FAMILY, 15, "bold"), text_color=THEME_COLORS["text_title"]
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            ai_container, text="Thiết lập các bộ kích hoạt thị giác máy tính động cho công cụ camera xử lý dữ liệu.", 
            font=(FONT_FAMILY, 11), text_color=THEME_COLORS["text_muted"]
        ).pack(anchor="w", pady=(0, 20))

        opts = [
            ("Kích hoạt nhận diện & quét điểm danh sinh viên", True), 
            ("Kích hoạt đánh giá mức độ tập trung & tương tác", True), 
            ("Kích hoạt phát hiện phát biểu & ghi nhật ký âm thanh", False)
        ]
        
        self.checkboxes = {}
        for text, state in opts:
            row_card = CustomCard(ai_container, corner_radius=8, fg_color=THEME_COLORS["bg_input"])
            row_card.pack(fill="x", pady=6)
            
            cb = ctk.CTkCheckBox(
                row_card, text=text, font=(FONT_FAMILY, 13, "bold"), 
                fg_color=THEME_COLORS["primary"], text_color=THEME_COLORS["text_main"],
                border_color=THEME_COLORS["border"]
            )
            if state: 
                cb.select()
            cb.pack(anchor="w", padx=20, pady=16)
            self.checkboxes[text] = cb

        # 3. THANH ĐIỀU KHIỂN CHỨC NĂNG DƯỚI CÙNG (FOOTER ACTION BAR)
        footer_bar = ctk.CTkFrame(self, fg_color="transparent")
        footer_bar.pack(fill="x", padx=40, pady=(10, 30))

        # Nút xác nhận lưu thông tin
        self.btn_confirm = ctk.CTkButton(
            footer_bar, text="Xác Nhận & Khởi Tạo Phiên Học", 
            font=(FONT_FAMILY, 14, "bold"), 
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=48,
            width=240,
            command=self.handle_confirm_session
        )
        self.btn_confirm.pack(side="right", padx=(15, 0))

        # Nút xóa trắng thông tin form 
        self.btn_clear = ctk.CTkButton(
            footer_bar, text="Đặt Lại Biểu Mẫu", 
            font=(FONT_FAMILY, 13), 
            fg_color="transparent", 
            border_color=THEME_COLORS["border"], 
            border_width=1, 
            text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            height=48,
            width=120,
            command=self.handle_reset_form
        )
        self.btn_clear.pack(side="right")

    def create_time_picker(self, parent, default_hour, default_minute):
        hour_values = [f"{hour:02d}" for hour in range(24)]
        minute_values = [f"{minute:02d}" for minute in range(60)]

        hour_var = ctk.StringVar(value=default_hour)
        minute_var = ctk.StringVar(value=default_minute)

        picker_frame = ctk.CTkFrame(
            parent,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=8,
            height=42,
        )
        picker_frame.pack(fill="x")
        picker_frame.pack_propagate(False)

        option_style = {
            "fg_color": THEME_COLORS["bg_input"],
            "button_color": THEME_COLORS["primary"],
            "button_hover_color": THEME_COLORS["primary_hover"],
            "text_color": THEME_COLORS["text_main"],
            "dropdown_fg_color": THEME_COLORS["bg_card"],
            "dropdown_text_color": THEME_COLORS["text_main"],
            "height": 32,
            "width": 78,
            "font": (FONT_FAMILY, 13, "bold"),
        }

        hour_menu = ctk.CTkOptionMenu(
            picker_frame,
            values=hour_values,
            variable=hour_var,
            dynamic_resizing=False,
            **option_style,
        )
        hour_menu.pack(side="left", padx=(8, 4), pady=5)

        ctk.CTkLabel(
            picker_frame,
            text=":",
            font=(FONT_FAMILY, 16, "bold"),
            text_color=THEME_COLORS["text_main"],
            width=12,
        ).pack(side="left")

        minute_menu = ctk.CTkOptionMenu(
            picker_frame,
            values=minute_values,
            variable=minute_var,
            dynamic_resizing=False,
            **option_style,
        )
        minute_menu.pack(side="left", padx=(4, 8), pady=5)

        ctk.CTkLabel(
            picker_frame,
            text="24h",
            font=(FONT_FAMILY, 11, "bold"),
            text_color=THEME_COLORS["text_muted"],
        ).pack(side="right", padx=(0, 12))

        return hour_var, minute_var

    @staticmethod
    def format_time_value(hour_var, minute_var):
        return f"{hour_var.get()}:{minute_var.get()}"

    def load_classroom_options(self):
        classrooms = self.controller.load_classrooms()
        self.classroom_lookup = {}

        values = []
        for classroom in classrooms:
            class_name = classroom.get("class_name") or "Lớp chưa đặt tên"
            class_code = classroom.get("class_code") or classroom.get("classroom_id")
            display_text = f"{class_name} ({class_code})"
            self.classroom_lookup[display_text] = classroom["classroom_id"]
            values.append(display_text)

        return values or [self.classroom_empty_text]

    def get_selected_classroom_id(self):
        selected_text = self.selected_classroom.get()
        return self.classroom_lookup.get(selected_text)

    def refresh_and_load_data(self):
        if not hasattr(self, "opt_classroom"):
            return

        current_selection = self.selected_classroom.get()
        classroom_values = self.load_classroom_options()
        next_selection = current_selection if current_selection in self.classroom_lookup else classroom_values[0]

        self.opt_classroom.configure(values=classroom_values)
        self.selected_classroom.set(next_selection)
        self.opt_classroom.configure(state="normal" if self.classroom_lookup else "disabled")

    def handle_mock_upload(self):
        """Xử lý hành động giả lập khi người dùng nhấn nút chọn file tài liệu"""
        from tkinter import filedialog
        from gui.constants import TEXT_ICONS
        import os

        file_path = filedialog.askopenfilename(
            title="Chọn Tài Liệu Hướng Dẫn Bài Giảng",
            filetypes=[("Document Files", "*.pdf *.txt *.docx *.pptx")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            success_text = f"{TEXT_ICONS['check_mark']} Đã tải: {filename}"
            self.btn_upload_docs.configure(
                text=success_text, 
                fg_color=THEME_COLORS["success_bg"], 
                text_color=THEME_COLORS["success_text"]
            )

    def handle_confirm_session(self):
        # Thu thập thông tin từ các Entry trên UI
        course_name = self.ent_course_name.get()
        lecture_date = self.ent_date.get()
        start_time = self.format_time_value(self.start_hour_var, self.start_minute_var)
        end_time = self.format_time_value(self.end_hour_var, self.end_minute_var)
        classroom_id = self.get_selected_classroom_id()

        # Gọi sang lớp Controller xử lý logic lưu dữ liệu bài giảng
        result = self.controller.save_lecture_session(
            course_name=course_name,
            lecture_date=lecture_date,
            start_time=start_time,
            end_time=end_time,
            classroom_id=classroom_id
        )

        # Cập nhật kết quả phản hồi lên giao diện chính
        if result["status"] == "success":
            self.lbl_status.configure(text=result["message"], text_color=THEME_COLORS["success_text"])
            self.handle_reset_form()
            from tkinter import messagebox
            messagebox.showinfo("Thành Công", result["message"])
        else:
            self.lbl_status.configure(text=result["message"], text_color="#FF3333")

    def handle_reset_form(self):
        """Xóa trắng toàn bộ dữ liệu nhập trong các ô và đưa nút đính kèm về trạng thái mặc định ban đầu"""
        from gui.constants import TEXT_ICONS
        
        self.ent_course_name.delete(0, 'end')
        self.start_hour_var.set("07")
        self.start_minute_var.set("00")
        self.end_hour_var.set("08")
        self.end_minute_var.set("00")
        
        self.ent_date.delete(0, 'end')
        self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y"))

        if self.classroom_lookup:
            first_classroom = next(iter(self.classroom_lookup))
            self.selected_classroom.set(first_classroom)
        
        self.txt_notes.delete("0.0", "end")
        self.txt_notes.insert("0.0", "Nhập các hướng dẫn đặc biệt hoặc lưu ý nội quy phòng học tại đây...")
        
        default_btn_text = f"{TEXT_ICONS['file_attachment']} Đính Kèm Đề Cương / PDF"
        self.btn_upload_docs.configure(
            text=default_btn_text, 
            fg_color=THEME_COLORS["btn_pdf_bg"],
            text_color=THEME_COLORS["text_main"]
        )
