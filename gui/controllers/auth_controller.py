# gui/controllers/auth_controller.py

import hashlib

from db_helper import DatabaseHelper

try:
    import bcrypt
except ImportError:
    bcrypt = None


class AuthController:
    def __init__(self, user_repo=None):
        self.user_repo = user_repo or DatabaseHelper().users
        self.current_user = None

    def login(self, username, password):
        username = (username or "").strip()

        if not username or not password:
            return {"status": "error", "message": "Vui lòng nhập tên đăng nhập và mật khẩu."}

        user_row = self.user_repo.get_by_username(username)
        if not user_row:
            return {"status": "error", "message": "Tên đăng nhập hoặc mật khẩu không đúng."}

        if user_row["is_active"] != 1:
            return {"status": "error", "message": "Tài khoản đã bị vô hiệu hóa."}

        if not self._verify_password(password, user_row["password_hash"]):
            return {"status": "error", "message": "Tên đăng nhập hoặc mật khẩu không đúng."}

        self.user_repo.update_last_login(user_row["user_id"])
        refreshed = self.user_repo.get_by_username(username)
        self.current_user = self._row_to_user(refreshed)
        return {"status": "success", "message": "Đăng nhập thành công.", "user": self.current_user}

    def logout(self):
        self.current_user = None
        return {"status": "success", "message": "Đã đăng xuất."}

    def get_current_user(self):
        return self.current_user

    def hash_password(self, password):
        return self._hash_password(password)

    def _hash_password(self, password):
        if bcrypt is not None:
            return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _verify_password(self, password, password_hash):
        if password_hash.startswith("$2"):
            if bcrypt is None:
                return False
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

        return hashlib.sha256(password.encode("utf-8")).hexdigest() == password_hash

    @staticmethod
    def _row_to_user(row):
        if not row:
            return None

        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "email": row["email"],
            "role": row["role"],
            "is_active": row["is_active"],
            "last_login": row["last_login"],
            "created_at": row["created_at"] if "created_at" in row.keys() else None,
        }
