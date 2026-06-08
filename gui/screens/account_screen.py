# gui/screens/account_screen.py

import customtkinter as ctk
from tkinter import messagebox

from gui.components.card import CustomCard
from gui.controllers.auth_controller import AuthController
from gui.theme import FONT_FAMILY, THEME_COLORS


class AccountScreen(ctk.CTkFrame):
    def __init__(self, parent, on_auth_changed=None):
        super().__init__(parent, fg_color="transparent")
        self.auth_controller = AuthController()
        self.on_auth_changed = on_auth_changed
        self.current_user = None
        self.entries = {}
        self.init_ui()

    def init_ui(self):
        self.card = CustomCard(self)
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        self.inner = ctk.CTkFrame(self.card, fg_color="transparent")
        self.inner.pack(padx=50, pady=45)

        self.title_label = ctk.CTkLabel(
            self.inner,
            text="Tài Khoản",
            font=(FONT_FAMILY, 24, "bold"),
            text_color=THEME_COLORS["text_main"],
        )
        self.title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            self.inner,
            text="Đăng nhập để sử dụng hệ thống lớp học thông minh",
            font=(FONT_FAMILY, 12),
            text_color=THEME_COLORS["text_muted"],
        )
        self.subtitle_label.pack(pady=(5, 24))

        self.body = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.body.pack(fill="x")
        self.show_login_form()

    def set_auth_changed_callback(self, callback):
        self.on_auth_changed = callback

    def set_current_user(self, user):
        self.current_user = user
        self.auth_controller.current_user = user
        if user:
            self.show_account_home()
        else:
            self.show_login_form()

    def show_login_form(self):
        self.entries = {}
        self._clear_body()
        self.title_label.configure(text="Tài Khoản")
        self.subtitle_label.configure(text="Tài khoản giáo viên do quản trị viên cấp")

        login_frame = ctk.CTkFrame(self.body, fg_color="transparent", width=420)
        login_frame.pack(fill="x")

        self._add_entry(login_frame, "username", "Tên Đăng Nhập", "Nhập tên đăng nhập")
        self._add_entry(login_frame, "password", "Mật Khẩu", "Nhập mật khẩu", show="*")

        ctk.CTkButton(
            login_frame,
            text="Đăng Nhập",
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            height=44,
            command=self.handle_login,
        ).pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            login_frame,
            text="Nếu chưa có tài khoản, vui lòng liên hệ quản trị viên.",
            font=(FONT_FAMILY, 11),
            text_color=THEME_COLORS["text_muted"],
        ).pack(pady=(14, 0))

    def show_account_home(self):
        user = self.current_user or self.auth_controller.get_current_user()
        if not user:
            self.show_login_form()
            return

        if user.get("role") == "admin":
            self.show_admin_profile()
        else:
            self.show_teacher_profile()

    def show_admin_profile(self):
        self._clear_body()
        self.title_label.configure(text="Tài Khoản Admin")
        self.subtitle_label.configure(text="Thông tin quản trị viên đang đăng nhập")
        self._render_profile_summary(self.body, self.current_user)
        self._render_logout_button(self.body)

    def show_teacher_profile(self):
        self._clear_body()
        self.title_label.configure(text="Hồ Sơ Giáo Viên")
        self.subtitle_label.configure(text="Thông tin tài khoản đang đăng nhập")
        self._render_profile_summary(self.body, self.current_user)
        self._render_logout_button(self.body)

    def handle_login(self):
        result = self.auth_controller.login(
            username=self.entries["username"].get(),
            password=self.entries["password"].get(),
        )

        if result["status"] != "success":
            messagebox.showerror("Đăng nhập thất bại", result["message"])
            return

        self.current_user = result["user"]
        if self.on_auth_changed:
            self.on_auth_changed(self.current_user)
        messagebox.showinfo("Thành công", result["message"])
        self.show_account_home()

    def handle_logout(self):
        self.auth_controller.logout()
        self.current_user = None
        if self.on_auth_changed:
            self.on_auth_changed(None)
        self.show_login_form()

    def _render_profile_summary(self, parent, user, compact=False):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=16 if compact else 0, pady=14 if compact else 0)

        ctk.CTkLabel(
            container,
            text=self._get_avatar_text(user),
            font=(FONT_FAMILY, 22, "bold"),
            text_color="#FFFFFF",
            fg_color=THEME_COLORS["primary"],
            width=72,
            height=72,
            corner_radius=36,
        ).pack(pady=(0, 14))

        ctk.CTkLabel(
            container,
            text=user["display_name"],
            font=(FONT_FAMILY, 20 if not compact else 17, "bold"),
            text_color=THEME_COLORS["text_main"],
        ).pack()

        ctk.CTkLabel(
            container,
            text=f"@{user['username']} | {user['role']}",
            font=(FONT_FAMILY, 12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(pady=(4, 16))

        info_frame = ctk.CTkFrame(container, fg_color=THEME_COLORS["bg_card"], corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 10))
        self._add_info_row(info_frame, "Email", user["email"] or "Chưa cập nhật")
        self._add_info_row(info_frame, "Lần đăng nhập gần nhất", user["last_login"] or "Vừa đăng nhập")

    def _render_logout_button(self, parent):
        ctk.CTkButton(
            parent,
            text="Đăng Xuất",
            font=(FONT_FAMILY, 14, "bold"),
            fg_color=THEME_COLORS["danger"],
            hover_color="#B91C1C",
            height=42,
            command=self.handle_logout,
        ).pack(fill="x", pady=(18, 0))

    def _add_entry(self, parent, key, label, placeholder, show=None):
        ctk.CTkLabel(
            parent,
            text=label,
            font=(FONT_FAMILY, 12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w")

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            show=show,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            height=38,
        )
        entry.pack(fill="x", pady=(4, 10))
        self.entries[key] = entry
        return entry

    def _add_info_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=7)
        ctk.CTkLabel(row, text=label, font=(FONT_FAMILY, 12), text_color=THEME_COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(row, text=value, font=(FONT_FAMILY, 13, "bold"), text_color=THEME_COLORS["text_main"]).pack(anchor="w")

    def _clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    @staticmethod
    def _get_avatar_text(user):
        display_name = user.get("display_name") or user.get("username") or "U"
        parts = [part for part in display_name.split() if part]
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return display_name[:2].upper()
