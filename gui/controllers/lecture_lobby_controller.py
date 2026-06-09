# gui/controllers/lecture_lobby_controller.py
from datetime import datetime
from db_helper import DatabaseHelper

class LectureLobbyController:
    def __init__(self):
        self.db = DatabaseHelper()
        self.scheduled_lectures = []

    def load_scheduled_lectures(self):
        """Load danh sách bài giảng CHƯA GIẢNG từ DB, chuẩn hóa thành dict và sắp xếp theo thời gian"""
        try:
            scheduled_lectures = self.db.get_scheduled_lectures()

            # Sắp xếp danh sách ưu tiên bài giảng nào sắp bắt đầu sớm nhất lên đầu
            def get_sort_key(x):
                try:
                    start_clean = x['start'].strip().split('.')[0] if x['start'] else ""
                    date_clean = x['date'].strip()
                    try:
                        return datetime.strptime(f"{date_clean} {start_clean}", "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        return datetime.strptime(f"{date_clean} {start_clean}", "%Y-%m-%d %H:%M")
                except Exception as e:
                    print(f"[LobbyController Sort Error] Sai định dạng thời gian cho {x['name']}: {e}")
                    return datetime.max

            scheduled_lectures.sort(key=get_sort_key)
            return scheduled_lectures
            
        except Exception as e:
            print(f"[LobbyController Error] Không thể load dữ liệu từ Database: {e}")
            return []
        
    def update_ticks(self):
        """Hàm cập nhật tick thời gian hệ thống và tự động đẩy phiên lên khi đến giờ G"""
        now = datetime.now()
        system_clock_str = now.strftime('%H:%M:%S')
        
        ui_updates = {}
        need_refresh_lobby = False

        for lec in self.scheduled_lectures:
            lec_id = lec["id"]
            try:
                start_clean = lec['start'].strip().split('.')[0] if lec['start'] else ""
                date_clean = lec['date'].strip()
                target_str = f"{date_clean} {start_clean}"
                try:
                    target_time = datetime.strptime(target_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    target_time = datetime.strptime(target_str, "%Y-%m-%d %H:%M")
                
                if now >= target_time:
                    ui_updates[lec_id] = {
                        "is_ready": True,
                        "time_string": "ĐÃ ĐẾN GIỜ"
                    }
                    self.db.update_lecture_session_status(lec_id, 'ongoing')
                    need_refresh_lobby = True
            except Exception as e:
                print(f"[Tick Error] Lỗi xử lý so sánh mốc giờ: {e}")

        return {
            "system_clock": system_clock_str,
            "ui_updates": ui_updates,
            "need_refresh_lobby": need_refresh_lobby
        }
