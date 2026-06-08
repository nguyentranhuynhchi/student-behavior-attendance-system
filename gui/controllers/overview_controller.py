# gui/controllers/overview_controller.py
from db_helper import DatabaseHelper

class OverviewController:
    def __init__(self):
        # Khởi tạo đối tượng kết nối Database
        self.db = DatabaseHelper()

    def get_stats_data(self):
        """Lấy dữ liệu thống kê tổng quan cho các thẻ Stats Cards"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # 1. Tổng số sinh viên trong hệ thống (Bảng Student)
            cursor.execute("SELECT COUNT(*) FROM Student")
            total_students = cursor.fetchone()[0] or 0

            # 2. Số sinh viên có mặt trong buổi học gần nhất (Bảng Attendance)
            cursor.execute("SELECT session_id FROM LectureSession ORDER BY session_id DESC LIMIT 1")
            session_res = cursor.fetchone()
            
            present_students = 0
            if session_res:
                session_id = session_res["session_id"]
                cursor.execute(
                    "SELECT COUNT(*) FROM Attendance WHERE session_id = ? AND attendance_status = 'Có mặt'", 
                    (session_id,)
                )
                present_students = cursor.fetchone()[0] or 0

            # Tính tỷ lệ chuyên cần chuyên sâu
            attendance_rate = "0%"
            if total_students > 0:
                attendance_rate = f"{int((present_students / total_students) * 100)}%"

            # 3. Thống kê cảnh báo AI (Số lượng sinh viên đang ngủ hoặc mất tập trung ở phiên gần nhất)
            ai_alerts = 0
            if session_res:
                cursor.execute(
                    "SELECT COUNT(DISTINCT student_id) FROM LearningStatus WHERE session_id = ? AND learning_behavior IN ('Sleeping', 'Distracted')",
                    (session_id,)
                )
                ai_alerts = cursor.fetchone()[0] or 0

            return {
                "total": str(total_students),
                "present": str(present_students),
                "rate": attendance_rate,
                "alerts": str(ai_alerts)
            }
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu thống kê: {e}")
            return {"total": "0", "present": "0", "rate": "0%", "alerts": "0"}
        finally:
            conn.close()

    def load_all_students(self):
        """Tải toàn bộ danh sách sinh viên từ database"""
        try:
            return self.db.get_all_students_with_classroom()
        except Exception as e:
            print(f"Lỗi load_all_students: {e}")
            return []

    def load_all_sessions(self):
        """Tải danh sách các buổi học đã diễn ra"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT session_id, course_name, lecture_date, start_time FROM LectureSession ORDER BY session_id DESC")
            return cursor.fetchall()
        except Exception as e:
            print(f"Lỗi load_all_sessions: {e}")
            return []
        finally:
            conn.close()

    def get_session_attendance_details(self, session_id):
        """Lấy chi tiết điểm danh và trạng thái học tập AI của một buổi học cụ thể"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # Query kết hợp thông tin điểm danh và lấy trạng thái hành vi AI mới nhất (Latest Log) của từng SV
            query = """
                SELECT 
                    s.student_id, 
                    s.full_name, 
                    a.attendance_status,
                    (SELECT ls.learning_behavior 
                     FROM LearningStatus ls 
                     WHERE ls.student_id = s.student_id AND ls.session_id = ? 
                     ORDER BY ls.status_id DESC LIMIT 1) as latest_behavior
                FROM Student s
                LEFT JOIN Attendance a ON s.student_id = a.student_id AND a.session_id = ?
            """
            cursor.execute(query, (session_id, session_id))
            return cursor.fetchall()
        except Exception as e:
            print(f"Lỗi get_session_attendance_details: {e}")
            return []
        finally:
            conn.close()
