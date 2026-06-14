# gui/screens/session_history_screen.py

import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog

from gui.components.card import CustomCard
from gui.theme import FONT_FAMILY, THEME_COLORS
from db_helper import DatabaseHelper


class SessionHistoryScreen(ctk.CTkFrame):
    """Màn hình xem toàn bộ lịch sử buổi học cho Admin"""

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
            header, text="Lịch Sử Buổi Học",
            font=(FONT_FAMILY, 28, "bold"), text_color=THEME_COLORS["text_main"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Xem toàn bộ lịch sử buổi học và điểm danh trong hệ thống",
            font=(FONT_FAMILY, 14), text_color=THEME_COLORS["text_muted"],
        ).pack(anchor="w", pady=(5, 0))

        # Stats
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=10)
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="ss")
        self.stat_labels = {}
        for i, (key, title, color) in enumerate([
            ("total_sessions", "Tổng số Buổi Học", THEME_COLORS["text_main"]),
            ("completed", "Đã Hoàn Thành", THEME_COLORS["success_text"]),
            ("scheduled", "Đang Lên Lịch", THEME_COLORS["warning"]),
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
            toolbar, text="Xuất Tất Cả (CSV)", width=150, height=38,
            fg_color=THEME_COLORS["success_text"], hover_color=THEME_COLORS["success_text"],
            font=(FONT_FAMILY, 13, "bold"), command=self._export_all_csv,
        ).pack(side="right")

        ctk.CTkButton(
            toolbar, text="Làm mới", width=100, height=38,
            fg_color=THEME_COLORS["bg_dark"], text_color=THEME_COLORS["text_main"],
            hover_color=THEME_COLORS["bg_card_hover"], command=self.refresh_and_load_data,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkLabel(
            toolbar, text="Danh sách toàn bộ buổi học trong hệ thống",
            font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"],
        ).pack(side="left")

        self.table_frame = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.refresh_and_load_data()

    def refresh_and_load_data(self):
        self._load_table()

    def _load_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        sessions = self.db.get_all_sessions()

        # Stats
        total = len(sessions)
        completed = sum(1 for s in sessions if s.get("status") == "completed")
        scheduled = sum(1 for s in sessions if s.get("status") == "scheduled")
        self.stat_labels["total_sessions"].configure(text=str(total))
        self.stat_labels["completed"].configure(text=str(completed))
        self.stat_labels["scheduled"].configure(text=str(scheduled))

        # Header
        headers = [("ID", 50, 0), ("Tên buổi học", 200, 1), ("Lớp", 120, 0),
                   ("Ngày", 100, 0), ("Giờ", 110, 0), ("Trạng thái", 90, 0), ("Chi tiết", 70, 0)]
        hdr = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(6, 8), padx=5)
        for idx, (title, w, weight) in enumerate(headers):
            hdr.grid_columnconfigure(idx, minsize=w, weight=weight)
            ctk.CTkLabel(hdr, text=title, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=idx, sticky="ew", padx=(0, 10))

        if not sessions:
            ctk.CTkLabel(self.table_frame, text="Chưa có buổi học nào trong hệ thống.",
                         font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]).pack(pady=24)
            return

        for s in sessions:
            sid = s["session_id"]
            status = s.get("status", "")
            status_text = {"completed": "Hoàn thành", "scheduled": "Lên lịch", "ongoing": "Đang diễn ra"}.get(status, status)
            status_color = {"completed": THEME_COLORS["success_text"], "scheduled": THEME_COLORS["warning"],
                            "ongoing": THEME_COLORS["primary"]}.get(status, THEME_COLORS["text_muted"])

            row = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            for idx, (w, weight) in enumerate([(50, 0), (200, 1), (120, 0), (100, 0), (110, 0), (90, 0), (70, 0)]):
                row.grid_columnconfigure(idx, minsize=w, weight=weight)

            vals = [
                (str(sid), THEME_COLORS["text_main"]),
                (s.get("course_name", ""), THEME_COLORS["text_main"]),
                (s.get("class_name", "-") or "-", THEME_COLORS["text_muted"]),
                (s.get("lecture_date", ""), THEME_COLORS["text_muted"]),
                (f"{s.get('start_time', '')} - {s.get('end_time', '')}", THEME_COLORS["text_muted"]),
                (status_text, status_color),
            ]
            for idx, (text, color) in enumerate(vals):
                ctk.CTkLabel(row, text=text, font=(FONT_FAMILY, 13), text_color=color, anchor="w").grid(
                    row=0, column=idx, sticky="ew", padx=(0, 10))

            ctk.CTkButton(
                row, text="Xem", width=50, height=28, font=(FONT_FAMILY, 11),
                fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                command=lambda _s=s: self._show_detail(_s),
            ).grid(row=0, column=6, sticky="w")

    def _show_detail(self, session):
        """Mở cửa sổ chi tiết điểm danh của buổi học"""
        sid = session["session_id"]
        title = session.get("course_name", "")
        date = session.get("lecture_date", "")

        detail_window = ctk.CTkToplevel(self)
        detail_window.title(f"Chi tiết: {title}")
        detail_window.geometry("750x500")
        detail_window.configure(fg_color=THEME_COLORS["bg_main"])
        detail_window.transient(self.winfo_toplevel())
        detail_window.grab_set()
        detail_window.focus_set()

        # Header
        info_frame = CustomCard(detail_window)
        info_frame.pack(fill="x", padx=20, pady=15)

        info_header = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(info_header, text=f"Bài học: {title}", font=(FONT_FAMILY, 16, "bold"),
                     text_color=THEME_COLORS["text_title"]).pack(side="left")

        # Nút xuất CSV
        attendance_data = self.db.get_session_attendance_details(sid)

        def export_csv():
            file_path = filedialog.asksaveasfilename(
                title="Lưu báo cáo điểm danh", defaultextension=".csv",
                initialfile=f"DiemDanh_{sid}_{date}.csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if not file_path:
                return
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["MSSV", "Họ và tên", "Điểm danh", "Trạng thái AI"])
                    for mssv, name, status, ai_state in attendance_data:
                        writer.writerow([mssv, name, status or "Vắng mặt", ai_state or "Không có dữ liệu"])
                messagebox.showinfo("Thành công", f"Đã xuất báo cáo tại:\n{file_path}", parent=detail_window)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất:\n{e}", parent=detail_window)

        ctk.CTkButton(info_header, text="Xuất CSV", width=90, height=30, font=(FONT_FAMILY, 12, "bold"),
                      fg_color=THEME_COLORS["primary"], hover_color=THEME_COLORS["primary_hover"],
                      command=export_csv).pack(side="right")

        ctk.CTkLabel(info_frame, text=f"Thời gian: {date} | ID phiên học: {sid}",
                     font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 15))

        # Bảng điểm danh
        list_card = CustomCard(detail_window)
        list_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll = ctk.CTkScrollableFrame(list_card, fg_color=THEME_COLORS["bg_input"], corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Header bảng
        thdr = ctk.CTkFrame(scroll, fg_color="transparent")
        thdr.pack(fill="x", pady=(6, 8), padx=5)
        for idx, (t, w, wt) in enumerate([("MSSV", 95, 0), ("Họ và tên", 220, 1), ("Điểm danh", 100, 0), ("Trạng thái AI", 130, 0)]):
            thdr.grid_columnconfigure(idx, minsize=w, weight=wt)
            ctk.CTkLabel(thdr, text=t, font=(FONT_FAMILY, 12, "bold"),
                         text_color=THEME_COLORS["text_muted"], anchor="w").grid(row=0, column=idx, sticky="ew", padx=(0, 10))

        for mssv, name, status, ai_state in attendance_data:
            status = status if status else "Vắng mặt"
            ai_state = ai_state if ai_state else "Không có dữ liệu"
            status_color = THEME_COLORS["success_text"] if status == "Có mặt" else THEME_COLORS["danger"]

            if ai_state == "Tập trung":
                ai_color = THEME_COLORS["success_text"]
            elif "ngủ" in ai_state.lower() or "gục" in ai_state.lower():
                ai_color = THEME_COLORS["danger"]
            elif "mất tập trung" in ai_state.lower() or ai_state == "Distracted":
                ai_color = THEME_COLORS["warning"]
            else:
                ai_color = THEME_COLORS["text_muted"]

            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=4, padx=5)
            r.grid_columnconfigure(0, minsize=95, weight=0)
            r.grid_columnconfigure(1, minsize=220, weight=1)
            r.grid_columnconfigure(2, minsize=100, weight=0)
            r.grid_columnconfigure(3, minsize=130, weight=0)

            ctk.CTkLabel(r, text=mssv, font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(r, text=name, font=(FONT_FAMILY, 13), text_color=THEME_COLORS["text_main"], anchor="w").grid(row=0, column=1, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(r, text=status, font=(FONT_FAMILY, 13, "bold"), text_color=status_color, anchor="w").grid(row=0, column=2, sticky="ew", padx=(0, 10))
            ctk.CTkLabel(r, text=ai_state, font=(FONT_FAMILY, 13, "bold"), text_color=ai_color, anchor="w").grid(row=0, column=3, sticky="ew")

    def _export_all_csv(self):
        """Xuất toàn bộ dữ liệu điểm danh tất cả buổi học ra 1 file CSV"""
        sessions = self.db.get_all_sessions()
        if not sessions:
            messagebox.showinfo("Thông báo", "Chưa có dữ liệu buổi học nào để xuất.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Xuất toàn bộ dữ liệu điểm danh",
            defaultextension=".csv",
            initialfile="BaoCao_TatCaBuoiHoc.csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID Buổi học", "Tên buổi học", "Ngày", "MSSV", "Họ và tên", "Điểm danh", "Trạng thái AI"])

                for s in sessions:
                    sid = s["session_id"]
                    name = s.get("course_name", "")
                    date = s.get("lecture_date", "")
                    attendance = self.db.get_session_attendance_details(sid)
                    for mssv, sname, status, ai_state in attendance:
                        writer.writerow([
                            sid, name, date, mssv, sname,
                            status or "Vắng mặt", ai_state or "Không có dữ liệu"
                        ])

            messagebox.showinfo("Thành công", f"Đã xuất toàn bộ báo cáo tại:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo:\n{e}")
