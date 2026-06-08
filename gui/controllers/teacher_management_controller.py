# gui/controllers/teacher_management_controller.py

import re

from db_helper import DatabaseHelper
from gui.controllers.auth_controller import AuthController


class TeacherManagementController:
    def __init__(self):
        self.db = DatabaseHelper()
        self.auth = AuthController(self.db.users)

    def get_stats(self):
        return self.db.users.get_teacher_stats()

    def search_teachers(self, keyword=""):
        return [self._row_to_teacher(row) for row in self.db.users.search_teachers(keyword)]

    def create_teacher(self, admin_user, username, password, confirm_password, display_name, email=None):
        if not admin_user or admin_user.get("role") != "admin":
            return {"status": "error", "message": "Chỉ quản trị viên mới được tạo Teacher."}

        username = (username or "").strip()
        display_name = (display_name or "").strip()
        email = (email or "").strip() or None

        if not username or not password or not confirm_password or not display_name:
            return {"status": "error", "message": "Vui lòng nhập đầy đủ họ tên, tên đăng nhập và mật khẩu."}

        if len(username) < 4:
            return {"status": "error", "message": "Tên đăng nhập phải có ít nhất 4 ký tự."}

        if not re.match(r"^[A-Za-z0-9_.-]+$", username):
            return {"status": "error", "message": "Tên đăng nhập chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang."}

        if len(password) < 6:
            return {"status": "error", "message": "Mật khẩu phải có ít nhất 6 ký tự."}

        if password != confirm_password:
            return {"status": "error", "message": "Mật khẩu nhập lại không khớp."}

        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return {"status": "error", "message": "Email không đúng định dạng."}

        if self.db.users.is_username_exists(username):
            return {"status": "error", "message": "Tên đăng nhập đã tồn tại."}

        if self.db.users.is_email_exists(email):
            return {"status": "error", "message": "Email đã được sử dụng."}

        try:
            user_id = self.db.users.create_user(
                username=username,
                password_hash=self.auth.hash_password(password),
                display_name=display_name,
                email=email,
                role="teacher",
                is_active=1,
            )
            return {"status": "success", "message": "Đã tạo Teacher.", "user_id": user_id}
        except Exception as e:
            return {"status": "error", "message": f"Không thể tạo Teacher: {e}"}

    def update_teacher(self, admin_user, teacher_id, username, display_name, email=None, new_password=None, confirm_password=None):
        if not admin_user or admin_user.get("role") != "admin":
            return {"status": "error", "message": "Chỉ quản trị viên mới được cập nhật Teacher."}

        username = (username or "").strip()
        display_name = (display_name or "").strip()
        email = (email or "").strip() or None
        new_password = new_password or ""
        confirm_password = confirm_password or ""

        if not username or not display_name:
            return {"status": "error", "message": "Vui lòng nhập tên đăng nhập và họ tên hiển thị."}

        if len(username) < 4:
            return {"status": "error", "message": "Tên đăng nhập phải có ít nhất 4 ký tự."}

        if not re.match(r"^[A-Za-z0-9_.-]+$", username):
            return {"status": "error", "message": "Tên đăng nhập chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang."}

        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return {"status": "error", "message": "Email không đúng định dạng."}

        teacher_row = self.db.users.get_by_id(teacher_id)
        if not teacher_row or teacher_row["role"] != "teacher":
            return {"status": "error", "message": "Không tìm thấy Teacher cần cập nhật."}

        existing_username = self.db.users.get_by_username(username)
        if existing_username and existing_username["user_id"] != teacher_id:
            return {"status": "error", "message": "Tên đăng nhập đã tồn tại."}

        if email:
            existing_email = self.db.users.get_by_email(email)
            if existing_email and existing_email["user_id"] != teacher_id:
                return {"status": "error", "message": "Email đã được sử dụng."}

        password_hash = None
        if new_password or confirm_password:
            if len(new_password) < 6:
                return {"status": "error", "message": "Mật khẩu mới phải có ít nhất 6 ký tự."}
            if new_password != confirm_password:
                return {"status": "error", "message": "Mật khẩu nhập lại không khớp."}
            password_hash = self.auth.hash_password(new_password)

        success = self.db.users.update_teacher(
            user_id=teacher_id,
            username=username,
            display_name=display_name,
            email=email,
            password_hash=password_hash,
        )

        if not success:
            return {"status": "error", "message": "Không thể cập nhật Teacher."}
        return {"status": "success", "message": "Đã cập nhật thông tin Teacher."}

    def set_teacher_active(self, admin_user, teacher_id, is_active):
        if not admin_user or admin_user.get("role") != "admin":
            return {"status": "error", "message": "Chỉ quản trị viên mới được khóa/mở khóa Teacher."}

        teacher_row = self.db.users.get_by_id(teacher_id)
        if not teacher_row or teacher_row["role"] != "teacher":
            return {"status": "error", "message": "Không tìm thấy Teacher cần cập nhật."}

        success = self.db.users.set_active_status(teacher_id, is_active)
        if not success:
            return {"status": "error", "message": "Không thể cập nhật trạng thái Teacher."}
        return {"status": "success", "message": "Đã cập nhật trạng thái Teacher."}

    @staticmethod
    def _row_to_teacher(row):
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "email": row["email"],
            "role": row["role"],
            "is_active": row["is_active"],
            "created_at": row["created_at"],
            "last_login": row["last_login"],
        }
