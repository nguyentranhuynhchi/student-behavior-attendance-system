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

    def get_all_classrooms_with_stats(self):
        """Lấy danh sách lớp kèm số lượng sinh viên mỗi lớp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT c.classroom_id, c.class_code, c.class_name, c.department, c.academic_year,
                       COUNT(s.student_id) AS student_count
                FROM Classroom c
                LEFT JOIN Student s ON c.classroom_id = s.classroom_id
                GROUP BY c.classroom_id
                ORDER BY c.class_name ASC
                """
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def update_classroom(self, classroom_id, class_name, department=None, academic_year=None):
        """Cập nhật thông tin lớp học"""
        class_code = (class_name or "DEFAULT").strip().upper().replace(" ", "_")
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE Classroom
                SET class_name = ?, class_code = ?, department = ?, academic_year = ?
                WHERE classroom_id = ?
                """,
                (class_name.strip(), class_code, department, academic_year, classroom_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to update classroom: {e}")
            return False
        finally:
            conn.close()

    def delete_classroom(self, classroom_id):
        """Xóa lớp học và toàn bộ sinh viên + dữ liệu liên quan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Lấy danh sách student_id trong lớp này
            cursor.execute("SELECT student_id FROM Student WHERE classroom_id = ?", (classroom_id,))
            student_ids = [row[0] for row in cursor.fetchall()]

            for sid in student_ids:
                cursor.execute("DELETE FROM LearningStatus WHERE student_id = ?", (sid,))
                cursor.execute("DELETE FROM Attendance WHERE student_id = ?", (sid,))

            cursor.execute("DELETE FROM Student WHERE classroom_id = ?", (classroom_id,))
            cursor.execute("DELETE FROM LectureSession WHERE classroom_id = ?", (classroom_id,))
            cursor.execute("DELETE FROM Classroom WHERE classroom_id = ?", (classroom_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to delete classroom: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
