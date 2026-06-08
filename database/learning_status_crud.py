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
