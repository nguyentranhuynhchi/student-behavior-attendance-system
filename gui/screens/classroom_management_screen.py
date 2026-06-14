# gui/screens/classroom_management_screen.py

import customtkinter as ctk
from tkinter import messagebox

from gui.components.card import CustomCard
from gui.theme import FONT_FAMILY, THEME_COLORS
from db_helper import DatabaseHelper


class ClassroomManagementScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = DatabaseHelper()
        self.init_ui()

    def set_current_user(self, user):
        pass

    def init_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 15))

        ctk.CTkLabel(
            header, text="Quản lý Lớp Học",
            font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Xem, chỉnh sửa và xóa lớp học trong hệ thống",
            font=(FONT_FAMILY, 14), text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(5, 0))

        # Stats
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=10)
        self.stats_frame.grid_columnconfigure((0, 1), weight=1, uniform="cls_st")
        self.stat_labels = {}
        for i, (key, title, color) in enumerate([
            ("total_classes", "Tổng số Lớp Học", THEME_COLORS["text_main"]),
            ("total_students", "Tổng số Sinh Viên", THEME_COLORS["primary"]),
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
            toolbar, text="Làm mới", width=100, height=38,
            fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"], command=self.refresh_and_load_data,
        ).pack(side="right")

        ctk.CTkLabel(
            toolbar, text="Lớp học được tạo tự động khi ghi danh sinh viên",
            font=(FONT_FAMILY, 12), text_color=THEME_COLORS["text_muted"],
        ).pack(side="left")

        self.table_frame = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.refresh_and_load_data()

    def refresh_and_load_data(self):
        self._load_table()

    def _load_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        classrooms = self.db.get_all_classrooms_with_stats()

        # Update stats
        total_students = sum(row["student_count"] for row in classrooms)
        self.stat_labels["total_classes"].configure(text=str(len(classrooms)))
        self.stat_labels["total_students"].configure(text=str(total_students))

        # Header
        headers = [("ID", 50, 0), ("Tên Lớp", 180, 1), ("Mã Lớp", 140, 0), ("Khoa", 150, 0), ("Số SV", 70, 0), ("Hành động", 140, 0)]
        hdr = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(6, 8), padx=5)
        for idx, (title, w, weight) in enumerate(headers):
            hdr.grid_columnconfigure(idx, minsize=w, weight=weight)
            ctk.CTkLabel(hdr, text=title, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=idx, sticky="ew", padx=(0, 10))

        if not classrooms:
            ctk.CTkLabel(self.table_frame, text="Chưa có lớp học nào trong hệ thống.",
                         font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]).pack(pady=24)
            return

        for c in classrooms:
            cid = c["classroom_id"]
            row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            for idx, (w, weight) in enumerate([(50, 0), (180, 1), (140, 0), (150, 0), (70, 0), (140, 0)]):
                row.grid_columnconfigure(idx, minsize=w, weight=weight)

            vals = [
                (str(cid), THEME_COLORS["text_main"]),
                (c["class_name"], THEME_COLORS["text_main"]),
                (c["class_code"], THEME_COLORS["text_muted"]),
                (c["department"] or "-", THEME_COLORS["text_muted"]),
                (str(c["student_count"]), THEME_COLORS["success_text"]),
            ]
            for idx, (text, color) in enumerate(vals):
                ctk.CTkLabel(row, text=text, font=(FONT_FAMILY, 13), text_color=color, anchor="w").grid(
                    row=0, column=idx, sticky="ew", padx=(0, 10))

            af = ctk.CTkFrame(row, fg_color="transparent")
            af.grid(row=0, column=5, sticky="ew")
            ctk.CTkButton(af, text="Sửa", width=50, height=28, font=(FONT_FAMILY, 11),
                          fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                          command=lambda _c=c: self._open_edit_dialog(_c)).pack(side="left", padx=(0, 5))
            ctk.CTkButton(af, text="Xóa", width=50, height=28, font=(FONT_FAMILY, 11),
                          fg_color=THEME_COLORS["danger"], hover_color="#B91C1C",
                          command=lambda _c=c: self._handle_delete(_c)).pack(side="left")

    def _handle_delete(self, classroom):
        count = classroom["student_count"]
        msg = (
            f"Bạn có chắc chắn muốn xóa lớp:\n\n"
            f"Tên lớp: {classroom['class_name']}\n"
            f"Số sinh viên: {count}\n\n"
        )
        if count > 0:
            msg += "Toàn bộ sinh viên và dữ liệu điểm danh\ntrong lớp này sẽ bị xóa vĩnh viễn!"
        else:
            msg += "Lớp học trống sẽ bị xóa khỏi hệ thống."

        if not messagebox.askyesno("Xác nhận xóa", msg):
            return

        success = self.db.delete_classroom(classroom["classroom_id"])
        if success:
            messagebox.showinfo("Thành công", f"Đã xóa lớp {classroom['class_name']} thành công.")
            self.refresh_and_load_data()
        else:
            messagebox.showerror("Lỗi", "Đã xảy ra lỗi khi xóa lớp học.")

    def _open_edit_dialog(self, classroom):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Chỉnh sửa lớp: {classroom['class_name']}")
        dialog.geometry("450x380")
        dialog.configure(fg_color=THEME_COLORS["bg_main"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        card = CustomCard(dialog)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(card, text=f"Chỉnh Sửa Lớp Học (ID: {classroom['classroom_id']})",
                     font=(FONT_FAMILY, 20, "bold"), text_color=THEME_COLORS["text_title"]).pack(anchor="w", padx=25, pady=(20, 15))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        entries = {}
        for key, label, value in [
            ("class_name", "Tên Lớp", classroom["class_name"]),
            ("department", "Khoa / Ngành", classroom["department"] or ""),
            ("academic_year", "Niên Khóa", classroom["academic_year"] or ""),
        ]:
            ctk.CTkLabel(form, text=label, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"]).pack(anchor="w", pady=(8, 3))
            entry = ctk.CTkEntry(form, fg_color=THEME_COLORS["bg_input"], border_color=THEME_COLORS["border"],
                                 text_color=THEME_COLORS["text_main"], height=42, font=(FONT_FAMILY, 14))
            entry.pack(fill="x")
            if value:
                entry.insert(0, value)
            entries[key] = entry

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(15, 20))

        def submit():
            name = entries["class_name"].get().strip()
            if not name:
                messagebox.showerror("Lỗi", "Tên lớp không được để trống!", parent=dialog)
                return
            success = self.db.update_classroom(
                classroom_id=classroom["classroom_id"],
                class_name=name,
                department=entries["department"].get().strip() or None,
                academic_year=entries["academic_year"].get().strip() or None,
            )
            if success:
                messagebox.showinfo("Thành công", f"Đã cập nhật lớp {name} thành công!", parent=dialog)
                dialog.grab_release()
                dialog.destroy()
                self.refresh_and_load_data()
            else:
                messagebox.showerror("Lỗi", "Đã xảy ra lỗi khi cập nhật lớp học.", parent=dialog)

        ctk.CTkButton(btn_frame, text="Hủy", width=100, height=42, fg_color=THEME_COLORS["bg_dark"],
                      text_color=THEME_COLORS["text_main"], hover_color=THEME_COLORS["bg_card_hover"],
                      command=lambda: (dialog.grab_release(), dialog.destroy())).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Lưu thay đổi", width=140, height=42, font=(FONT_FAMILY, 14, "bold"),
                      fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                      command=submit).pack(side="right")
