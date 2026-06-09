# database/learning_status_crud.py

from database.connection import BaseRepository


class LearningStatusRepository(BaseRepository):
    def insert_learning_status(self, session_id, student_id, learning_behavior, is_raising_hand):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO LearningStatus
                    (session_id, student_id, learning_behavior, is_raising_hand)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, student_id, learning_behavior, is_raising_hand),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert learning status: {e}")
            return False
        finally:
            conn.close()

    def count_alert_students_by_session(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(DISTINCT student_id)
                FROM LearningStatus
                WHERE session_id = ?
                  AND learning_behavior IN ('Sleeping', 'Distracted')
                """,
                (session_id,),
            )
            return cursor.fetchone()[0] or 0
        except Exception as e:
            print(f"[Error] Failed to count AI alert students: {e}")
            return 0
        finally:
            conn.close()
