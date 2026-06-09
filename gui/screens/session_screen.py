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

        # 2. KHU VỰC BỐ CỤC CHÍNH CHUYỂN VỀ 1 CỘT TRUNG TÂM
        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=40, pady=10)

        main_panel = CustomCard(content_grid)
        main_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_scroll = ctk.CTkScrollableFrame(main_panel, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=35, pady=25)
        
        ctk.CTkLabel(
            form_scroll, text="THÔNG TIN BÀI GIẢNG CHÍNH", 
            font=(FONT_FAMILY, 16, "bold"), text_color=THEME_COLORS["text_title"]
        ).pack(anchor="w", pady=(0, 20))

        # Trường số 1: Nhập tên môn học / tên bài giảng
        ctk.CTkLabel(form_scroll, text="Tên Môn Học / Tên Bài Giảng", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(5, 2))
        self.ent_course_name = ctk.CTkEntry(form_scroll, placeholder_text="Ví dụ: Chuyên đề Trí Tuệ Nhân Tạo & Học Máy", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], text_color=THEME_COLORS["text_main"], placeholder_text_color=THEME_COLORS["text_muted"], height=45, font=(FONT_FAMILY, 14))
        self.ent_course_name.pack(fill="x", pady=(0, 15))

        # Dòng chứa 3 cột song song: Ngày, Giờ Bắt Đầu, Giờ Kết Thúc
        row_time = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_time.pack(fill="x", pady=(0, 25))
        row_time.grid_columnconfigure((0, 1, 2), weight=1, uniform="time_grid")

        # Trường số 2: Chọn hoặc nhập ngày học
        f_date = ctk.CTkFrame(row_time, fg_color="transparent")
        f_date.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(f_date, text="Ngày Diễn Ra", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.ent_date = ctk.CTkEntry(f_date, placeholder_text="DD/MM/YYYY", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], text_color=THEME_COLORS["text_main"], placeholder_text_color=THEME_COLORS["text_muted"], height=45, font=(FONT_FAMILY, 14))
        self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_date.pack(fill="x")

        # Trường số 3: Nhập thời gian bắt đầu tiết học
        f_start = ctk.CTkFrame(row_time, fg_color="transparent")
        f_start.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        ctk.CTkLabel(f_start, text="Thời Gian Bắt Đầu", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.ent_start_time = ctk.CTkEntry(f_start, placeholder_text="HH:MM (Ví dụ: 07:30)", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], text_color=THEME_COLORS["text_main"], placeholder_text_color=THEME_COLORS["text_muted"], height=45, font=(FONT_FAMILY, 14))
        self.ent_start_time.pack(fill="x")

        # Trường số 4: Nhập thời gian kết thúc tiết học
        f_end = ctk.CTkFrame(row_time, fg_color="transparent")
        f_end.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(f_end, text="Thời Gian Kết Thúc", font=(FONT_FAMILY, 12, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))
        self.ent_end_time = ctk.CTkEntry(f_end, placeholder_text="HH:MM (Ví dụ: 11:30)", fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], text_color=THEME_COLORS["text_main"], placeholder_text_color=THEME_COLORS["text_muted"], height=45, font=(FONT_FAMILY, 14))
        self.ent_end_time.pack(fill="x")

        # 3. THANH ĐIỀU KHIỂN CHỨC NĂNG DƯỚI CÙNG (FOOTER ACTION BAR TRONG FORM_SCROLL)
        footer_bar = ctk.CTkFrame(form_scroll, fg_color="transparent")
        footer_bar.pack(fill="x", pady=(10, 0))

        self.btn_confirm = ctk.CTkButton(
            footer_bar, text="Xác Nhận & Khởi Tạo Phiên Học", 
            font=(FONT_FAMILY, 14, "bold"), 
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=48,
            command=self.handle_confirm_session
        )
        self.btn_confirm.pack(side="right", padx=(15, 0), fill="x", expand=True)

        self.btn_clear = ctk.CTkButton(
            footer_bar, text="Đặt Lại", 
            font=(FONT_FAMILY, 13), 
            fg_color="transparent", 
            border_color=THEME_COLORS["border"], 
            border_width=1, 
            text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            height=48,
            width=150,
            command=self.handle_reset_form
        )
        self.btn_clear.pack(side="left")

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

    def handle_confirm_session(self):
        course_name = self.ent_course_name.get()
        lecture_date = self.ent_date.get()
        start_time = self.ent_start_time.get()
        end_time = self.ent_end_time.get()

        result = self.controller.save_lecture_session(
            course_name=course_name,
            lecture_date=lecture_date,
            start_time=start_time,
            end_time=end_time
        )

        if result["status"] == "success":
            self.lbl_status.configure(text=result["message"], text_color=THEME_COLORS["success_text"])
            self.handle_reset_form()
            from tkinter import messagebox
            messagebox.showinfo("Thành Công", result["message"])
        else:
            self.lbl_status.configure(text=result["message"], text_color="#EF4444")

    def handle_reset_form(self):
        """Xóa trắng toàn bộ dữ liệu nhập trong các ô"""
        self.ent_course_name.delete(0, 'end')
        self.ent_start_time.delete(0, 'end')
        self.ent_end_time.delete(0, 'end')
        
        self.ent_date.delete(0, 'end')
        self.ent_date.insert(0, datetime.now().strftime("%d/%m/%Y"))