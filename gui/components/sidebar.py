# gui/components/sidebar.py
import os
import customtkinter as ctk
from PIL import Image
from gui.theme import THEME_COLORS, FONT_FAMILY
from gui.constants import TEXT_ICONS, IMAGE_ASSETS 

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_menu_select, on_logout=None):
        super().__init__(
            parent, 
            fg_color=THEME_COLORS["bg_sidebar"], 
            border_color=THEME_COLORS["border"],
            border_width=1,
            corner_radius=0
        )
        self.on_menu_select = on_menu_select
        self.on_logout = on_logout
        self.buttons = {}
        self.current_active = None
        self.init_ui()

    def _load_icon(self, filename, fallback_text):
        """Hàm tải icon, nếu lỗi sẽ dùng text fallback"""
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons", filename)
            return ctk.CTkImage(light_image=Image.open(path), size=(20, 20)), ""
        except:
            return None, f"{fallback_text}  "

    def init_ui(self):
        # Khu vực Logo
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=(30, 25), padx=20, fill="x")
        
        ctk.CTkLabel(
            logo_frame, text="Lớp Học Thông Minh", 
            font=(FONT_FAMILY, 18, "bold"), text_color=THEME_COLORS["text_main"], justify="left"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            logo_frame, text="version v1.0", 
            font=(FONT_FAMILY, 12), text_color=THEME_COLORS["primary"], justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # Danh sách các mục Menu 
        menu_items = [
            ("overview", "Tổng Quan", IMAGE_ASSETS["icon_dashboard"], TEXT_ICONS["dashboard_fallback"]),
            ("enrollment", "Ghi Danh Sinh Viên", IMAGE_ASSETS["icon_enrollment"], TEXT_ICONS["enrollment_fallback"]),
            ("session", "Thiết Lập Phiên", IMAGE_ASSETS["icon_session"], TEXT_ICONS["session_fallback"]),
            ("lecture_lobby", "Sảnh Chờ", IMAGE_ASSETS["icon_lecture_lobby"], TEXT_ICONS["lecture_lobby_fallback"]),
            ("lecture", "Phòng Học", IMAGE_ASSETS["icon_lecture"], TEXT_ICONS["lecture_fallback"]),
            ("account", "Tài Khoản", IMAGE_ASSETS["icon_account"], TEXT_ICONS["account_fallback"])
        ]

        # Tạo các nút điều hướng
        for screen_id, text, icon_file, fallback in menu_items:
            img, prefix = self._load_icon(icon_file, fallback)
            btn = ctk.CTkButton(
                self, text=f"{prefix}{text}", image=img, font=(FONT_FAMILY, 14), anchor="w", height=45,
                fg_color="transparent", text_color=THEME_COLORS["text_muted"],
                hover_color=THEME_COLORS["bg_card_hover"], corner_radius=8,
                command=lambda sid=screen_id: self.handle_click(sid)
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.buttons[screen_id] = btn

        # Khu vực Hồ sơ người dùng ở cuối Sidebar
        self.footer_frame = ctk.CTkFrame(self, fg_color=THEME_COLORS["bg_card"], corner_radius=12)
        self.footer_frame.pack(side="bottom", fill="x", pady=25, padx=15)

        profile_row = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        profile_row.pack(fill="x")
        
        self.user_avatar = ctk.CTkLabel(
            profile_row, text="--", font=(FONT_FAMILY, 14, "bold"),
            text_color="#FFFFFF", fg_color=THEME_COLORS["primary"], 
            width=38, height=38, corner_radius=19
        )
        self.user_avatar.pack(side="left", padx=12, pady=12)
        
        self.info_text = ctk.CTkLabel(
            profile_row, text="Chưa đăng nhập\nVui lòng đăng nhập",
            font=(FONT_FAMILY, 11), text_color=THEME_COLORS["text_muted"], justify="left"
        )
        self.info_text.pack(side="left", pady=12)

        self.logout_button = ctk.CTkButton(
            self.footer_frame,
            text="Đăng Xuất",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=THEME_COLORS["danger"],
            hover_color="#B91C1C",
            height=34,
            command=self.handle_logout_click,
        )

    def handle_click(self, screen_id):
        """Xử lý sự kiện khi click vào một mục menu"""
        if self.current_active == screen_id:
            return

        self.set_active(screen_id)
        self.on_menu_select(screen_id)

    def set_active(self, screen_id):
        self.current_active = screen_id
        for sid, btn in self.buttons.items():
            if sid == screen_id:
                btn.configure(fg_color=THEME_COLORS["bg_card_hover"], text_color=THEME_COLORS["text_main"])
            else:
                btn.configure(fg_color="transparent", text_color=THEME_COLORS["text_muted"])

    def update_user_info(self, user):
        """Cập nhật thông tin tài khoản hiển thị ở cuối sidebar"""
        if not user:
            self.user_avatar.configure(text="--")
            self.info_text.configure(text="Chưa đăng nhập\nVui lòng đăng nhập")
            self.logout_button.pack_forget()
            return

        display_name = user.get("display_name") or user.get("username") or "User"
        role = user.get("role") or ""
        email = user.get("email") or "Chưa có email"
        parts = [part for part in display_name.split() if part]
        initials = f"{parts[0][0]}{parts[-1][0]}".upper() if len(parts) >= 2 else display_name[:2].upper()
        self.user_avatar.configure(text=initials)
        self.info_text.configure(text=f"{display_name} ({role})\n{email}")
        self.logout_button.pack(fill="x", padx=12, pady=(0, 12))

    def handle_logout_click(self):
        if self.on_logout:
            self.on_logout()
