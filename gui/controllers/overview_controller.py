# gui/controllers/overview_controller.py
from db_helper import DatabaseHelper

class OverviewController:
    def __init__(self):
        # Khởi tạo đối tượng kết nối Database
        self.db = DatabaseHelper()

    def get_stats_data(self):
        """Lấy dữ liệu thống kê tổng quan cho các thẻ Stats Cards"""
        try:
            # 1. Tổng số sinh viên trong hệ thống (Bảng Student)
            total_students = self.db.count_students()

            # 2. Số sinh viên có mặt trong buổi học gần nhất (Bảng Attendance)
            session_id = self.db.get_latest_session_id()
            
            present_students = 0
            if session_id:
                present_students = self.db.count_present_by_session(session_id)

            # Tính tỷ lệ chuyên cần chuyên sâu
            attendance_rate = "0%"
            if total_students > 0:
                attendance_rate = f"{int((present_students / total_students) * 100)}%"

            # 3. Thống kê cảnh báo AI (Số lượng sinh viên đang ngủ hoặc mất tập trung ở phiên gần nhất)
            ai_alerts = 0
            if session_id:
                ai_alerts = self.db.count_alert_students_by_session(session_id)

            return {
                "total": str(total_students),
                "present": str(present_students),
                "rate": attendance_rate,
                "alerts": str(ai_alerts)
            }
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu thống kê: {e}")
            return {"total": "0", "present": "0", "rate": "0%", "alerts": "0"}

    def load_all_students(self):
        """Tải toàn bộ danh sách sinh viên từ database"""
        try:
            return self.db.get_all_students_with_classroom()
        except Exception as e:
            print(f"Lỗi load_all_students: {e}")
            return []

    def load_all_sessions(self):
        """Tải danh sách các buổi học đã diễn ra"""
        try:
            sessions = self.db.get_all_sessions()
            return [
                (
                    session["session_id"],
                    session["course_name"],
                    session["lecture_date"],
                    self._format_session_time(session),
                )
                for session in sessions
            ]
        except Exception as e:
            print(f"Lỗi load_all_sessions: {e}")
            return []

    def get_session_attendance_details(self, session_id):
        """Lấy chi tiết điểm danh và trạng thái học tập AI của một buổi học cụ thể"""
        try:
            return self.db.get_session_attendance_details(session_id)
        except Exception as e:
            print(f"Lỗi get_session_attendance_details: {e}")
            return []

    @staticmethod
    def _format_session_time(session):
        start_time = session.get("start_time") or "--:--"
        end_time = session.get("end_time") or "--:--"
        return f"{start_time} - {end_time}"
