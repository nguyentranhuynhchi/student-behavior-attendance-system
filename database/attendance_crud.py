# database/attendance_crud.py

from database.connection import BaseRepository


class AttendanceRepository(BaseRepository):
    def insert_attendance(self, session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO Attendance
                    (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to insert attendance: {e}")
            return False
        finally:
            conn.close()
