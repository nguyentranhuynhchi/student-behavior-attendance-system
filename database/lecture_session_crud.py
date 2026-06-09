# database/lecture_session_crud.py

from database.classroom_crud import ClassroomRepository
from database.connection import BaseRepository


class LectureSessionRepository(BaseRepository):
    VALID_STATUSES = {"scheduled", "ongoing", "completed"}

    def __init__(self, db_path=None, classroom_repo=None):
        super().__init__(db_path)
        self.classroom_repo = classroom_repo or ClassroomRepository(self.db_path)

    def create_new_lecture_session(
        self,
        course_name,
        lecture_date,
        start_time,
        end_time,
        classroom_id=None,
        created_by=None,
    ):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            classroom_id = classroom_id or self.classroom_repo.get_default_classroom_id()

            cursor.execute(
                """
                INSERT INTO LectureSession
                    (course_code, course_name, classroom_id, created_by, lecture_date, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')
                """,
                ("", course_name, classroom_id, created_by, lecture_date, start_time, end_time),
            )

            session_id = cursor.lastrowid
            auto_course_code = f"LEC{session_id:05d}"

            cursor.execute(
                """
                UPDATE LectureSession
                SET course_code = ?
                WHERE session_id = ?
                """,
                (auto_course_code, session_id),
            )

            conn.commit()
            return session_id
        except Exception as e:
            print(f"[Error] Failed to create lecture session: {e}")
            raise
        finally:
            conn.close()

    def update_lecture_session_status(self, session_id, new_status):
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Khong ho tro trang thai phien hoc: {new_status}")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE LectureSession
                SET status = ?
                WHERE session_id = ?
                """,
                (new_status, session_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to update lecture session status: {e}")
            return False
        finally:
            conn.close()

    def get_next_upcoming_session(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT session_id, course_name, lecture_date, start_time, end_time, status
                FROM LectureSession
                WHERE status = 'scheduled'
                ORDER BY lecture_date ASC, start_time ASC
                LIMIT 1
                """
            )
            return self._session_row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def get_latest_session_id(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT session_id FROM LectureSession ORDER BY session_id DESC LIMIT 1")
            row = cursor.fetchone()
            return row["session_id"] if row else None
        finally:
            conn.close()

    def get_session_by_status(self, status):
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Khong ho tro trang thai phien hoc: {status}")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT session_id, course_name, lecture_date, start_time, end_time, status
                FROM LectureSession
                WHERE status = ?
                ORDER BY session_id DESC
                LIMIT 1
                """,
                (status,),
            )
            return self._session_row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def get_lectures_by_date(self, lecture_date, classroom_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            params = [lecture_date]
            classroom_filter = ""
            if classroom_id is not None:
                classroom_filter = "AND classroom_id = ?"
                params.append(classroom_id)

            cursor.execute(
                f"""
                SELECT session_id, course_code, course_name, classroom_id,
                       lecture_date, start_time, end_time, status
                FROM LectureSession
                WHERE lecture_date = ? AND status != 'completed'
                {classroom_filter}
                ORDER BY start_time ASC
                """,
                tuple(params),
            )
            return [self._session_row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[Error] Failed to get lectures by date: {e}")
            return []
        finally:
            conn.close()

    def get_scheduled_lectures(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ls.session_id, ls.course_code, ls.course_name,
                       ls.classroom_id, c.class_name,
                       ls.lecture_date, ls.start_time, ls.end_time, ls.status
                FROM LectureSession ls
                LEFT JOIN Classroom c ON ls.classroom_id = c.classroom_id
                WHERE ls.status = 'scheduled'
                ORDER BY ls.lecture_date ASC, ls.start_time ASC
                """
            )
            return [self._lobby_row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[Error] Failed to get scheduled lectures: {e}")
            return []
        finally:
            conn.close()

    def get_all_sessions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ls.session_id, ls.course_code, ls.course_name,
                       ls.classroom_id, c.class_name,
                       ls.lecture_date, ls.start_time, ls.end_time, ls.status
                FROM LectureSession ls
                LEFT JOIN Classroom c ON ls.classroom_id = c.classroom_id
                ORDER BY ls.session_id DESC
                """
            )
            return [self._session_row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[Error] Failed to get all sessions: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def _session_row_to_dict(row):
        if not row:
            return None

        return {
            "session_id": row["session_id"],
            "course_code": row["course_code"] if "course_code" in row.keys() else None,
            "course_name": row["course_name"],
            "classroom_id": row["classroom_id"] if "classroom_id" in row.keys() else None,
            "class_name": row["class_name"] if "class_name" in row.keys() else None,
            "lecture_date": row["lecture_date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "status": row["status"],
        }

    @staticmethod
    def _lobby_row_to_dict(row):
        if not row:
            return None

        return {
            "id": row["session_id"],
            "code": row["course_code"],
            "name": row["course_name"],
            "classroom_id": row["classroom_id"],
            "class_name": row["class_name"],
            "date": row["lecture_date"],
            "start": row["start_time"],
            "end": row["end_time"],
            "status": row["status"],
        }
