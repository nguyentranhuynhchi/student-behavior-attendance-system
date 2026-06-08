# database/user_crud.py

from database.connection import BaseRepository


class UserRepository(BaseRepository):
    def create_user(self, username, password_hash, display_name, email=None, role="teacher", is_active=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO User (username, password_hash, display_name, email, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (username, password_hash, display_name, email, role, is_active),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_by_username(self, username):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT user_id, username, password_hash, display_name, email, role, is_active, last_login
                FROM User
                WHERE username = ?
                """,
                (username,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def get_by_email(self, email):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT user_id, username, password_hash, display_name, email, role, is_active, last_login
                FROM User
                WHERE email = ?
                """,
                (email,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def is_username_exists(self, username):
        return self.get_by_username(username) is not None

    def is_email_exists(self, email):
        if not email:
            return False
        return self.get_by_email(email) is not None

    def update_last_login(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE User
                SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_teacher_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN is_active != 1 THEN 1 ELSE 0 END) AS inactive,
                    SUM(CASE
                        WHEN strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
                        THEN 1 ELSE 0
                    END) AS new_this_month
                FROM User
                WHERE role = 'teacher'
                """
            )
            row = cursor.fetchone()
            return {
                "total": row["total"] or 0,
                "active": row["active"] or 0,
                "inactive": row["inactive"] or 0,
                "new_this_month": row["new_this_month"] or 0,
            }
        finally:
            conn.close()

    def search_teachers(self, keyword=""):
        keyword = (keyword or "").strip()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if keyword:
                like_keyword = f"%{keyword}%"
                cursor.execute(
                    """
                    SELECT user_id, username, display_name, email, role, is_active, created_at, last_login
                    FROM User
                    WHERE role = 'teacher'
                      AND (
                        username LIKE ?
                        OR display_name LIKE ?
                        OR email LIKE ?
                      )
                    ORDER BY user_id DESC
                    """,
                    (like_keyword, like_keyword, like_keyword),
                )
            else:
                cursor.execute(
                    """
                    SELECT user_id, username, display_name, email, role, is_active, created_at, last_login
                    FROM User
                    WHERE role = 'teacher'
                    ORDER BY user_id DESC
                    """
                )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_by_id(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT user_id, username, password_hash, display_name, email, role, is_active, created_at, last_login
                FROM User
                WHERE user_id = ?
                """,
                (user_id,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    def update_teacher(self, user_id, username, display_name, email=None, password_hash=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if password_hash:
                cursor.execute(
                    """
                    UPDATE User
                    SET username = ?, display_name = ?, email = ?, password_hash = ?
                    WHERE user_id = ? AND role = 'teacher'
                    """,
                    (username, display_name, email, password_hash, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE User
                    SET username = ?, display_name = ?, email = ?
                    WHERE user_id = ? AND role = 'teacher'
                    """,
                    (username, display_name, email, user_id),
                )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def set_active_status(self, user_id, is_active):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE User
                SET is_active = ?
                WHERE user_id = ?
                """,
                (1 if is_active else 0, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
