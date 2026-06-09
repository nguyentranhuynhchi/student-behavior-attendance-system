# gui/screens/enrollment_screen.py
import customtkinter as ctk
import os
from tkinter import filedialog  
from PIL import Image           
from gui.theme import THEME_COLORS, FONT_FAMILY
from gui.constants import TEXT_ICONS 
from gui.controllers.enrollment_controller import EnrollmentController

class EnrollmentScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        # Khởi tạo bộ điều phối và biến lưu đường dẫn ảnh
        self.controller = EnrollmentController()
        self.selected_image_path = None
        self.init_ui()

    def init_ui(self):
        # Khu vực Tiêu đề
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(header_frame, text="Ghi Danh Sinh Viên", font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"]).pack(side="left")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        content.grid_columnconfigure(0, weight=1, uniform="col")
        content.grid_columnconfigure(1, weight=1, uniform="col")

        # PANEL BÊN TRÁI (Ảnh & Camera)
        left_panel = ctk.CTkFrame(content, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10)
        
        ctk.CTkLabel(left_panel, text="Ảnh Sinh Viên", font=(FONT_FAMILY, 18, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=25, pady=(20, 10))
        
        # 1. Vùng Drag & Drop
        self.upload_box = ctk.CTkFrame(left_panel, fg_color=THEME_COLORS["bg_input"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border_dashed"], height=220)
        self.upload_box.pack(fill="x", padx=25, pady=(0, 15))
        self.upload_box.pack_propagate(False)
        
        self.cloud_icon = ctk.CTkLabel(self.upload_box, text=TEXT_ICONS["upload_cloud"], font=(FONT_FAMILY, 48), text_color=THEME_COLORS["primary"])
        self.cloud_icon.place(relx=0.5, rely=0.35, anchor="center")
        
        self.upload_text_main = ctk.CTkLabel(self.upload_box, text="Kéo thả ảnh vào đây", font=(FONT_FAMILY, 14, "bold"), text_color=THEME_COLORS["text_main"])
        self.upload_text_main.place(relx=0.5, rely=0.6, anchor="center")
        
        self.upload_text_sub = ctk.CTkLabel(self.upload_box, text="hoặc nhấp để duyệt tìm", font=(FONT_FAMILY, 12), text_color=THEME_COLORS["text_muted"])
        self.upload_text_sub.place(relx=0.5, rely=0.75, anchor="center")

        # 3. Nút tải ảnh lên
        self.btn_load_image = ctk.CTkButton(
            left_panel, 
            text="Tải Ảnh Lên", 
            font=(FONT_FAMILY, 14, "bold"), 
            fg_color=THEME_COLORS["primary"],        
            hover_color=THEME_COLORS["primary_hover"], 
            corner_radius=8,
            command=self.handle_browse_image        
        )
        self.btn_load_image.pack(fill="x", padx=25, pady=(0, 20))

        # PANEL BÊN PHẢI (Form Thông Tin)
        right_panel = ctk.CTkFrame(content, fg_color=THEME_COLORS["bg_card"], corner_radius=12, border_width=1, border_color=THEME_COLORS["border"])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=10)

        ctk.CTkLabel(right_panel, text="Hồ Sơ Sinh Viên", font=(FONT_FAMILY, 16, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=30, pady=(25, 10))

        form_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=30)

        # Quản lý các ô nhập liệu (Key tiếng Anh, Label & Placeholder tiếng Việt)
        self.entries = {}
        fields = [
            ("student_id", "Mã Sinh Viên", "VD: 23110136"), 
            ("full_name", "Họ và Tên", "VD: Trần Huỳnh Chí Nguyên"), 
            ("class_name", "Lớp", "VD: 23T1"), 
            ("email", "Email", "sinhvien@hcmute.edu.vn"), 
            ("phone", "Số Điện Thoại", "09xx xxx xxx")
        ]
        
        for key, label, placeholder in fields:
            ctk.CTkLabel(form_container, text=label, font=(FONT_FAMILY, 13, "bold"), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(10, 5))
            
            entry = ctk.CTkEntry(
                form_container, 
                placeholder_text=placeholder, 
                fg_color=THEME_COLORS["bg_input"], 
                border_color=THEME_COLORS["border"], 
                text_color=THEME_COLORS["text_main"], # Fix lỗi: Chữ nhập vào trắng sáng rõ ràng
                placeholder_text_color=THEME_COLORS["text_muted"], # Fix lỗi: Chữ gợi ý mờ tinh tế
                height=45, 
                font=(FONT_FAMILY, 14)
            )
            entry.pack(fill="x")
            self.entries[key] = entry
            
        # Khu vực Nút bấm
        btn_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_container.pack(fill="x", padx=30, pady=25)

        self.btn_save = ctk.CTkButton(
            btn_container, 
            text="Lưu Sinh Viên", 
            font=(FONT_FAMILY, 15, "bold"), 
            fg_color=THEME_COLORS["primary"], 
            hover_color=THEME_COLORS["primary_hover"], 
            height=50, 
            corner_radius=8,
            command=self.dispatch_save_event  
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 15))

        self.btn_reset = ctk.CTkButton(
            btn_container, 
            text="Làm Mới", 
            font=(FONT_FAMILY, 14), 
            fg_color="transparent", 
            border_color=THEME_COLORS["border"], 
            border_width=1, 
            text_color=THEME_COLORS["text_main"], 
            hover_color=THEME_COLORS["bg_input"], 
            height=50, 
            width=120, 
            corner_radius=8,
            command=self.handle_reset_form  
        )
        self.btn_reset.pack(side="right")

# --- CÁC HÀM XỬ LÝ SỰ KIỆN ---
    def handle_browse_image(self):
        """Mở hộp thoại hệ thống cho phép người dùng chọn tệp ảnh sinh viên"""
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh thẻ sinh viên",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            try:
                pil_img = Image.open(file_path)
                
                # Tính tỷ lệ scale ảnh tự động theo chiều cao khung box
                w, h = pil_img.size
                aspect_ratio = w / h
                new_h = 130
                new_w = int(new_h * aspect_ratio)
                
                ctk_img = ctk.CTkImage(light_image=pil_img, size=(new_w, new_h))
                
                # Cấu hình lại Label: Thay thế icon bằng ảnh preview
                self.cloud_icon.configure(image=ctk_img, text="")
                self.upload_text_main.configure(text=os.path.basename(file_path))
                self.upload_text_sub.configure(text="Ảnh đã được chọn thành công")
            except Exception as e:
                self.upload_text_main.configure(text="Lỗi hiển thị hình ảnh")
                print(f"[Error] Không hiển thị được ảnh preview: {e}")    
    
    def dispatch_save_event(self):
        """Thu thập dữ liệu thô từ các ô nhập liệu trên UI và đẩy sang Controller xử lý"""
        self.controller.handle_save_student(
            student_id=self.entries["student_id"].get(),
            full_name=self.entries["full_name"].get(),
            class_name=self.entries["class_name"].get(),
            email=self.entries["email"].get(),
            phone=self.entries["phone"].get(),
            source_img_path=self.selected_image_path,
            reset_form_callback=self.handle_reset_form  
        )
    
    def handle_reset_form(self):
        """Xóa toàn bộ ký tự trong Form nhập liệu và đưa vùng chọn ảnh về mặc định"""
        for entry in self.entries.values():
            entry.delete(0, 'end')
            
        self.selected_image_path = None
        
        self.cloud_icon.configure(image=None, text=TEXT_ICONS["upload_cloud"])
        self.upload_text_main.configure(text="Kéo thả ảnh vào đây")
        self.upload_text_sub.configure(text="hoặc nhấp để duyệt tìm")   