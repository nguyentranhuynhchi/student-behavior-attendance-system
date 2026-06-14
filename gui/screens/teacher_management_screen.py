# gui/screens/teacher_management_screen.py

import customtkinter as ctk
from tkinter import messagebox

from gui.components.card import CustomCard
from gui.controllers.teacher_management_controller import TeacherManagementController
from gui.theme import FONT_FAMILY, THEME_COLORS


class TeacherManagementScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.controller = TeacherManagementController()
        self.current_user = None
        self.teacher_rows = []
        self.stat_labels = {}
        self.search_entry = None
        self.table_frame = None
        self.init_ui()

    def set_current_user(self, user):
        self.current_user = user
        self.refresh_data()

    def init_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 15))

        ctk.CTkLabel(
            header,
            text="Quản lý Teacher",
            font=(FONT_FAMILY, 28, "bold"),
            text_color=THEME_COLORS["text_main"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Tạo, cập nhật, khóa/mở khóa và tìm kiếm tài khoản giáo viên",
            font=(FONT_FAMILY, 14),
            text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(5, 0))

        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=10)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")
        self._build_stats_cards()

        list_card = CustomCard(self)
        list_card.pack(fill="both", expand=True, padx=40, pady=(10, 30))

        toolbar = ctk.CTkFrame(list_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(18, 12))

        # Nút Tạo mới Teacher — pack bên PHẢI trước để luôn hiển thị
        ctk.CTkButton(
            toolbar,
            text="+ Tạo mới Teacher",
            width=150,
            height=38,
            fg_color=THEME_COLORS["success_text"],
            hover_color=THEME_COLORS["success_text"],
            font=(FONT_FAMILY, 13, "bold"),
            command=self.open_create_dialog,
        ).pack(side="right")

        ctk.CTkButton(
            toolbar,
            text="Làm mới",
            width=90,
            height=38,
            fg_color=THEME_COLORS["bg_dark"],
            text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            command=self.handle_refresh_click,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            toolbar,
            text="Tìm kiếm",
            width=100,
            height=38,
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=self.refresh_data,
        ).pack(side="right", padx=(0, 8))

        # Thanh tìm kiếm chiếm phần còn lại bên trái
        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Tìm theo username, display name hoặc email",
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            height=38,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_data())

        self.table_frame = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.refresh_data()

    def _build_stats_cards(self):
        stats = [
            ("total", "Tổng số Teacher", THEME_COLORS["text_main"]),
            ("active", "Teacher đang hoạt động", THEME_COLORS["success_text"]),
            ("inactive", "Teacher bị khóa / ngưng hoạt động", THEME_COLORS["danger"]),
            ("new_this_month", "Teacher mới tạo trong tháng này", THEME_COLORS["warning"]),
        ]

        for index, (key, title, color) in enumerate(stats):
            card = CustomCard(self.stats_frame)
            card.grid(row=0, column=index, padx=10, sticky="nsew")
            ctk.CTkLabel(
                card,
                text=title,
                font=(FONT_FAMILY, 12, "bold"),
                text_color=THEME_COLORS["text_muted"],
            ).pack(anchor="w", padx=18, pady=(14, 4))

            value_label = ctk.CTkLabel(
                card,
                text="0",
                font=(FONT_FAMILY, 30, "bold"),
                text_color=color,
            )
            value_label.pack(anchor="w", padx=18, pady=(0, 14))
            self.stat_labels[key] = value_label

    def refresh_data(self):
        self._load_stats()
        self._load_teacher_table()

    def handle_refresh_click(self):
        self.search_entry.delete(0, "end")
        self.refresh_data()

    def _load_stats(self):
        stats = self.controller.get_stats()
        for key, label in self.stat_labels.items():
            label.configure(text=str(stats.get(key, 0)))

    def _load_teacher_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        keyword = self.search_entry.get() if self.search_entry else ""
        self.teacher_rows = self.controller.search_teachers(keyword)
        self._render_table_header()

        if not self.teacher_rows:
            ctk.CTkLabel(
                self.table_frame,
                text="Không tìm thấy Teacher phù hợp.",
                font=(FONT_FAMILY, 13),
                text_color=THEME_COLORS["text_muted"],
            ).grid(row=1, column=0, columnspan=8, pady=24)
            return

        for row_index, teacher in enumerate(self.teacher_rows, start=1):
            self._render_teacher_row(row_index, teacher)

    def _render_table_header(self):
        headers = [
            ("ID", 55),
            ("Username", 120),
            ("Display Name", 170),
            ("Email", 190),
            ("Trạng thái", 110),
            ("Ngày tạo", 135),
            ("Lần đăng nhập cuối", 155),
            ("Hành động", 170),
        ]
        for column, (text, width) in enumerate(headers):
            ctk.CTkLabel(
                self.table_frame,
                text=text,
                width=width,
                anchor="w",
                font=(FONT_FAMILY, 12, "bold"),
                text_color=THEME_COLORS["text_muted"],
            ).grid(row=0, column=column, padx=5, pady=(8, 8), sticky="w")

    def _render_teacher_row(self, row_index, teacher):
        status_text = "Hoạt động" if teacher["is_active"] == 1 else "Bị khóa"
        status_color = THEME_COLORS["success_text"] if teacher["is_active"] == 1 else THEME_COLORS["danger"]
        values = [
            (teacher["user_id"], 55, THEME_COLORS["text_main"]),
            (teacher["username"], 120, THEME_COLORS["text_main"]),
            (teacher["display_name"], 170, THEME_COLORS["text_main"]),
            (teacher["email"] or "Chưa có email", 190, THEME_COLORS["text_muted"]),
            (status_text, 110, status_color),
            (self._format_datetime(teacher["created_at"]), 135, THEME_COLORS["text_muted"]),
            (self._format_datetime(teacher["last_login"]), 155, THEME_COLORS["text_muted"]),
        ]

        for column, (text, width, color) in enumerate(values):
            ctk.CTkLabel(
                self.table_frame,
                text=str(text),
                width=width,
                anchor="w",
                font=(FONT_FAMILY, 12),
                text_color=color,
            ).grid(row=row_index, column=column, padx=5, pady=6, sticky="w")

        action_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent", width=170)
        action_frame.grid(row=row_index, column=7, padx=5, pady=4, sticky="w")

        ctk.CTkButton(
            action_frame,
            text="Sửa",
            width=58,
            height=30,
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=lambda target=teacher: self.open_edit_dialog(target),
        ).pack(side="left", padx=(0, 6))

        target_active = teacher["is_active"] != 1
        ctk.CTkButton(
            action_frame,
            text="Mở" if target_active else "Khóa",
            width=58,
            height=30,
            fg_color=THEME_COLORS["success_text"] if target_active else THEME_COLORS["danger"],
            hover_color=THEME_COLORS["success_text"] if target_active else "#B91C1C",
            command=lambda target=teacher, active=target_active: self.handle_toggle_status(target, active),
        ).pack(side="left")

    def open_create_dialog(self):
        self._open_teacher_dialog(mode="create")

    def open_edit_dialog(self, teacher):
        self._open_teacher_dialog(mode="edit", teacher=teacher)

    def _open_teacher_dialog(self, mode, teacher=None):
        is_edit = mode == "edit"
        dialog = ctk.CTkToplevel(self)
        dialog.title("Cập nhật Teacher" if is_edit else "Tạo mới Teacher")
        dialog.geometry("480x660" if is_edit else "480x620")
        dialog.configure(fg_color=THEME_COLORS["bg_main"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: self._close_teacher_dialog(dialog))

        card = CustomCard(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Cập nhật thông tin Teacher" if is_edit else "Tạo mới Teacher",
            font=(FONT_FAMILY, 20, "bold"),
            text_color=THEME_COLORS["text_main"],
        ).pack(anchor="w", padx=20, pady=(18, 12))

        entries = {}
        self._add_dialog_entry(card, entries, "display_name", "Display Name", "VD: Nguyễn Văn A", teacher.get("display_name") if teacher else "")
        self._add_dialog_entry(card, entries, "username", "Username", "VD: teacher01", teacher.get("username") if teacher else "")
        self._add_dialog_entry(card, entries, "email", "Email", "VD: teacher01@hcmute.edu.vn", teacher.get("email") if teacher else "")

        password_label = "Mật khẩu mới" if is_edit else "Mật khẩu"
        confirm_label = "Nhập lại mật khẩu mới" if is_edit else "Nhập lại mật khẩu"
        self._add_dialog_entry(card, entries, "password", password_label, "Tối thiểu 6 ký tự", "", show="*")
        self._add_dialog_entry(card, entries, "confirm_password", confirm_label, "Nhập lại mật khẩu", "", show="*")

        if is_edit:
            ctk.CTkLabel(
                card,
                text="Để trống mật khẩu nếu không muốn thay đổi.",
                font=(FONT_FAMILY, 11),
                text_color=THEME_COLORS["text_muted"],
            ).pack(anchor="w", padx=20, pady=(0, 12))

        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(4, 18))

        ctk.CTkButton(
            button_frame,
            text="Hủy",
            width=100,
            fg_color=THEME_COLORS["bg_dark"],
            text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            command=lambda: self._close_teacher_dialog(dialog),
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            button_frame,
            text="Lưu thay đổi" if is_edit else "Tạo Teacher",
            width=130,
            fg_color=THEME_COLORS["primary"],
            hover_color=THEME_COLORS["primary_hover"],
            command=lambda: self._handle_dialog_submit(dialog, entries, mode, teacher),
        ).pack(side="right")

    def _add_dialog_entry(self, parent, entries, key, label, placeholder, value="", show=None):
        ctk.CTkLabel(
            parent,
            text=label,
            font=(FONT_FAMILY, 12),
            text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", padx=20)

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            show=show,
            fg_color=THEME_COLORS["bg_input"],
            border_color=THEME_COLORS["border"],
            height=38,
        )
        entry.pack(fill="x", padx=20, pady=(4, 12))
        if value:
            entry.insert(0, value)
        entries[key] = entry

    def _handle_dialog_submit(self, dialog, entries, mode, teacher=None):
        if mode == "create":
            result = self.controller.create_teacher(
                admin_user=self.current_user,
                username=entries["username"].get(),
                password=entries["password"].get(),
                confirm_password=entries["confirm_password"].get(),
                display_name=entries["display_name"].get(),
                email=entries["email"].get(),
            )
        else:
            result = self.controller.update_teacher(
                admin_user=self.current_user,
                teacher_id=teacher["user_id"],
                username=entries["username"].get(),
                display_name=entries["display_name"].get(),
                email=entries["email"].get(),
                new_password=entries["password"].get(),
                confirm_password=entries["confirm_password"].get(),
            )

        if result["status"] != "success":
            messagebox.showerror("Thao tác thất bại", result["message"], parent=dialog)
            return

        messagebox.showinfo("Thành công", result["message"], parent=dialog)
        self._close_teacher_dialog(dialog)
        self.refresh_data()

    @staticmethod
    def _close_teacher_dialog(dialog):
        try:
            dialog.grab_release()
        except Exception:
            pass
        dialog.destroy()


    def handle_toggle_status(self, teacher, is_active):
        result = self.controller.set_teacher_active(self.current_user, teacher["user_id"], is_active)
        if result["status"] != "success":
            messagebox.showerror("Cập nhật thất bại", result["message"])
            return
        self.refresh_data()

    @staticmethod
    def _format_datetime(value):
        if not value:
            return "-"
        return str(value).split(".")[0]
