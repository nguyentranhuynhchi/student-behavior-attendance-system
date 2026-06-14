# gui/screens/student_management_screen.py

import os
import customtkinter as ctk
from tkinter import messagebox, filedialog

from gui.components.card import CustomCard
from gui.controllers.overview_controller import OverviewController
from gui.theme import FONT_FAMILY, THEME_COLORS


class StudentManagementScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.controller = OverviewController()
        self.search_var = ""
        self.init_ui()

    def set_current_user(self, user):
        pass

    def init_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 15))

        ctk.CTkLabel(
            header, text="Quản lý Sinh Viên",
            font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Xem, chỉnh sửa và xóa thông tin sinh viên trong hệ thống",
            font=(FONT_FAMILY, 14), text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(5, 0))

        # Stats cards
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=10)
        self.stats_frame.grid_columnconfigure((0, 1), weight=1, uniform="st")
        self.stat_labels = {}
        for i, (key, title, color) in enumerate([
            ("total", "Tổng số Sinh Viên", THEME_COLORS["text_main"]),
            ("classes", "Số Lớp Học", THEME_COLORS["primary"]),
        ]):
            card = CustomCard(self.stats_frame)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"]).pack(anchor="w", padx=18, pady=(14, 4))
            lbl = ctk.CTkLabel(card, text="0", font=(FONT_FAMILY, 30, "bold"), text_color=color)
            lbl.pack(anchor="w", padx=18, pady=(0, 14))
            self.stat_labels[key] = lbl

        # Table card
        list_card = CustomCard(self)
        list_card.pack(fill="both", expand=True, padx=40, pady=(10, 30))

        toolbar = ctk.CTkFrame(list_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(18, 12))

        ctk.CTkButton(
            toolbar, text="Làm mới", width=90, height=38,
            fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"],
            command=self._handle_refresh,
        ).pack(side="right")

        ctk.CTkButton(
            toolbar, text="Tìm kiếm", width=100, height=38,
            fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
            command=self.refresh_and_load_data,
        ).pack(side="right", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Tìm theo MSSV, họ tên hoặc lớp...",
            fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"], height=38,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _: self.refresh_and_load_data())

        self.table_frame = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.refresh_and_load_data()

    def _handle_refresh(self):
        self.search_entry.delete(0, "end")
        self.refresh_and_load_data()

    def refresh_and_load_data(self):
        self._load_stats()
        self._load_table()

    def _load_stats(self):
        students = self.controller.load_all_students()
        self.stat_labels["total"].configure(text=str(len(students)))
        class_set = set()
        for row in students:
            class_set.add(row[2])
        self.stat_labels["classes"].configure(text=str(len(class_set)))

    def _load_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        keyword = (self.search_entry.get() if self.search_entry else "").strip().lower()
        students = self.controller.load_all_students()

        # Filter
        if keyword:
            students = [s for s in students if keyword in str(s[0]).lower() or keyword in str(s[1]).lower() or keyword in str(s[2]).lower()]

        # Header
        headers = [("MSSV", 100, 0), ("Họ và tên", 200, 1), ("Lớp", 120, 0), ("Hành động", 140, 0)]
        hdr = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(6, 8), padx=5)
        for idx, (title, w, weight) in enumerate(headers):
            hdr.grid_columnconfigure(idx, minsize=w, weight=weight)
            ctk.CTkLabel(hdr, text=title, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=idx, sticky="ew", padx=(0, 10))

        if not students:
            ctk.CTkLabel(self.table_frame, text="Không tìm thấy sinh viên nào.",
                         font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]).pack(pady=24)
            return

        for s in students:
            sid, name, cls = s[0], s[1], s[2]
            row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            row.grid_columnconfigure(0, minsize=100, weight=0)
            row.grid_columnconfigure(1, minsize=200, weight=1)
            row.grid_columnconfigure(2, minsize=120, weight=0)
            row.grid_columnconfigure(3, minsize=140, weight=0)

            ctk.CTkLabel(row, text=str(sid), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(row, text=str(name), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=1, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(row, text=str(cls), font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=2, sticky="ew", padx=(0, 10))

            af = ctk.CTkFrame(row, fg_color="transparent")
            af.grid(row=0, column=3, sticky="ew")
            ctk.CTkButton(af, text="Sửa", width=50, height=28, font=(FONT_FAMILY, 11),
                          fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                          command=lambda _sid=sid: self._open_edit_dialog(_sid)).pack(side="left", padx=(0, 5))
            ctk.CTkButton(af, text="Xóa", width=50, height=28, font=(FONT_FAMILY, 11),
                          fg_color=THEME_COLORS["danger"], hover_color="#B91C1C",
                          command=lambda _sid=sid, _name=name: self._handle_delete(_sid, _name)).pack(side="left")

    def _handle_delete(self, student_id, student_name):
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa sinh viên:\n\n"
            f"MSSV: {student_id}\nHọ tên: {student_name}\n\n"
            f"Toàn bộ dữ liệu điểm danh và trạng thái học tập\n"
            f"liên quan sẽ bị xóa vĩnh viễn!"
        )
        if not confirm:
            return
        result = self.controller.handle_delete_student(student_id)
        if result["status"] == "success":
            messagebox.showinfo("Thành công", result["message"])
            self.refresh_and_load_data()
        else:
            messagebox.showerror("Lỗi", result["message"])

    def _open_edit_dialog(self, student_id):
        student = self.controller.get_student_by_id(student_id)
        if not student:
            messagebox.showerror("Lỗi", f"Không tìm thấy sinh viên: {student_id}")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Chỉnh sửa: {student['full_name']}")
        dialog.geometry("500x620")
        dialog.configure(fg_color=THEME_COLORS["bg_main"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        card = CustomCard(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(card, text=f"Chỉnh Sửa Sinh Viên: {student_id}",
                     font=(FONT_FAMILY, 20, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=25, pady=(20, 15))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        entries = {}
        for key, label, value in [
            ("full_name", "Họ và Tên", student["full_name"]),
            ("class_name", "Lớp", student["class_name"] or ""),
            ("email", "Email", student["email"]),
            ("phone", "Số Điện Thoại", student["phone"] or ""),
        ]:
            ctk.CTkLabel(form, text=label, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(8, 3))
            entry = ctk.CTkEntry(form, fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"],
                                 text_color=THEME_COLORS["text_main"], height=42, font=(FONT_FAMILY, 14))
            entry.pack(fill="x")
            if value:
                entry.insert(0, value)
            entries[key] = entry

        new_image_path = {"value": None}
        img_frame = ctk.CTkFrame(form, fg_color="transparent")
        img_frame.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(img_frame, text="Ảnh chân dung (tùy chọn)", font=(FONT_FAMILY, 12, "bold"),
                     text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(0, 3))
        lbl_img = ctk.CTkLabel(img_frame, text="Giữ nguyên ảnh cũ", font=(FONT_FAMILY, 12),
                               text_color=THEME_COLORS["text_muted"])
        lbl_img.pack(side="left", padx=(0, 10))

        def browse():
            path = filedialog.askopenfilename(title="Chọn ảnh mới", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
            if path:
                new_image_path["value"] = path
                lbl_img.configure(text=os.path.basename(path), text_color=THEME_COLORS["success_text"])

        ctk.CTkButton(img_frame, text="Đổi ảnh", width=90, height=32, font=(FONT_FAMILY, 12),
                      fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
                      hover_color=THEME_COLORS["bg_card_hover"], command=browse).pack(side="right")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(15, 20))

        def submit():
            result = self.controller.handle_update_student(
                student_id=student_id, full_name=entries["full_name"].get(),
                class_name=entries["class_name"].get(), email=entries["email"].get(),
                phone=entries["phone"].get(), new_image_path=new_image_path["value"],
            )
            if result["status"] == "success":
                messagebox.showinfo("Thành công", result["message"], parent=dialog)
                dialog.grab_release()
                dialog.destroy()
                self.refresh_and_load_data()
            else:
                messagebox.showerror("Lỗi", result["message"], parent=dialog)

        ctk.CTkButton(btn_frame, text="Hủy", width=100, height=42, fg_color=THEME_COLORS["bg_dark"],
                      text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_card_hover"],
                      command=lambda: (dialog.grab_release(), dialog.destroy())).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Lưu thay đổi", width=140, height=42, font=(FONT_FAMILY, 14, "bold"),
                      fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                      command=submit).pack(side="right")
