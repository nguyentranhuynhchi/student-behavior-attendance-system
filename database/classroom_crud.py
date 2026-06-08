# database/classroom_crud.py

from database.connection import BaseRepository


class ClassroomRepository(BaseRepository):
    def get_or_create_classroom(self, class_name, department=None, academic_year=None):
        clean_name = (class_name or "DEFAULT").strip() or "DEFAULT"
        class_code = clean_name.upper().replace(" ", "_")

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT classroom_id FROM Classroom WHERE class_code = ?", (class_code,))
            row = cursor.fetchone()
            if row:
                return row["classroom_id"]

            cursor.execute(
                """
                INSERT INTO Classroom (class_code, class_name, department, academic_year)
                VALUES (?, ?, ?, ?)
                """,
                (class_code, clean_name, department, academic_year),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_default_classroom_id(self):
        return self.get_or_create_classroom("DEFAULT")

    def get_all_classrooms(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT classroom_id, class_code, class_name, department, academic_year
                FROM Classroom
                ORDER BY class_name ASC
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()
