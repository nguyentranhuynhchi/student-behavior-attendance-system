from datetime import datetime, timedelta
from db_helper import DatabaseHelper

class SessionController:
    def __init__(self):
        self.db = DatabaseHelper()

    def save_lecture_session(
        self,
        course_name,
        lecture_date,
        start_time,
        end_time,
        classroom_id=None,
        created_by=None,
    ):
        course_name = course_name.strip()
        lecture_date = lecture_date.strip()
        start_time = start_time.strip()
        end_time = end_time.strip()

        if not (course_name and lecture_date and start_time and end_time):
            return {"status": "error", "message": "Vui lòng nhập đầy đủ tất cả các trường thông tin!"}

        try:
            # 1. Kiểm tra định dạng ngày dữ liệu đầu vào
            try:
                parsed_date = datetime.strptime(lecture_date, "%d/%m/%Y")
                db_ready_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                return {"status": "error", "message": "Lỗi định dạng ngày! Yêu cầu: DD/MM/YYYY"}

            # 2. Kiểm tra định dạng giờ đầu vào (HH:MM) và tính hợp lệ của giá trị giờ số (ví dụ tránh 22:88)
            try:
                datetime.strptime(start_time, "%H:%M")
                datetime.strptime(end_time, "%H:%M")
            except ValueError:
                return {"status": "error", "message": "Lỗi định dạng hoặc giá trị giờ không hợp lệ! Yêu cầu định dạng 24h (Ví dụ: 07:30 hoặc 13:15)."}

            # 3. Tạo các đối tượng datetime để so sánh mốc tương lai và logic hình học
            now = datetime.now()
            start_datetime = datetime.strptime(f"{db_ready_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{db_ready_date} {end_time}", "%Y-%m-%d %H:%M")

            # Ràng buộc: Giờ kết thúc phải sau giờ bắt đầu
            if end_datetime <= start_datetime:
                return {"status": "error", "message": "Thời gian kết thúc phải diễn ra sau thời gian bắt đầu!"}

            # Ràng buộc: Ngày và giờ thiết lập phải thuộc về tương lai
            if start_datetime <= now:
                return {"status": "error", "message": "Thời gian bắt đầu bài giảng phải nằm ở tương lai (sau thời gian hiện tại của hệ thống)!"}

            # 4. Kiểm tra chống chồng chéo lịch học & Khoảng cách an toàn tối thiểu 5 phút
            # Lấy các bài giảng hiện có cùng ngày trong DB (loại trừ các bài đã completed)
            existing_lectures = self.db.get_lectures_by_date(db_ready_date, classroom_id=classroom_id)

            for row in existing_lectures:
                db_start_str = row["start_time"]
                db_end_str = row["end_time"]
                db_course_name = row["course_name"]

                # Parse thời gian của bài giảng trong DB thành đối tượng datetime
                db_start = datetime.strptime(f"{db_ready_date} {db_start_str}", "%Y-%m-%d %H:%M")
                db_end = datetime.strptime(f"{db_ready_date} {db_end_str}", "%Y-%m-%d %H:%M")

                # Áp dụng 2 ràng buộc biên an toàn 5 phút bằng cách nới rộng khoảng thời gian bị chiếm dụng
                # Bài mới phải cách bài cũ tối thiểu 5 phút (Bài mới bắt đầu sau bài cũ kết thúc 5p VÀ Bài mới kết thúc trước bài cũ bắt đầu 5p)
                # Logic xung đột xảy ra khi khoảng thời gian giao cắt nhau:
                if start_datetime < (db_end + timedelta(minutes=5)) and end_datetime > (db_start - timedelta(minutes=5)):
                    return {
                        "status": "error", 
                        "message": f"Xung đột lịch trình! Bài giảng mới vi phạm quy định khoảng cách an toàn 5 phút "
                                   f"hoặc chồng chéo với bài giảng môn [{db_course_name}] ({db_start_str} - {db_end_str}) đã có trên hệ thống."
                    }

            # 5. Lưu vào cơ sở dữ liệu nếu tất cả điều kiện được thỏa mãn
            session_id = self.db.create_new_lecture_session(
                course_name=course_name,
                lecture_date=db_ready_date, 
                start_time=start_time,
                end_time=end_time,
                classroom_id=classroom_id,
                created_by=created_by,
            )
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": f"Đăng ký thành công bài giảng [{course_name}] vào hệ thống!"
            }
        except Exception as e:
            return {"status": "error", "message": f"Lỗi không thể lưu bài giảng: {str(e)}"}
