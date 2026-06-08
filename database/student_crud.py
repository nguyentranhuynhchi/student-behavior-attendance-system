# database/student_crud.py

from database.classroom_crud import ClassroomRepository
from database.connection import BaseRepository


class StudentRepository(BaseRepository):
    ALLOWED_CHECK_FIELDS = {"student_id", "email", "phone"}

    def __init__(self, db_path=None, classroom_repo=None):
        super().__init__(db_path)
        self.classroom_repo = classroom_repo or ClassroomRepository(self.db_path)

    def check_exists(self, field_name, value):
        if field_name not in self.ALLOWED_CHECK_FIELDS:
            raise ValueError(f"Khong ho tro kiem tra trung lap truong: {field_name}")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT 1 FROM Student WHERE {field_name} = ?", (value,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def insert_student(self, student_id, full_name, class_name, email, phone, avatar_path, face_embedding=None):
        classroom_id = self.classroom_repo.get_or_create_classroom(class_name)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO Student
                    (student_id, full_name, classroom_id, email, phone, avatar_path, face_embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (student_id, full_name, classroom_id, email, phone, avatar_path, face_embedding),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert student: {e}")
            return False
        finally:
            conn.close()

    def get_all_valid_embeddings(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT student_id, full_name, face_embedding, avatar_path
                FROM Student
                WHERE face_embedding IS NOT NULL
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def get_all_students_with_classroom(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT s.student_id, s.full_name, c.class_name
                FROM Student s
                LEFT JOIN Classroom c ON s.classroom_id = c.classroom_id
                ORDER BY s.student_id ASC
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()
