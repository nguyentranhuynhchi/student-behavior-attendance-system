# view_db.py
import sqlite3
import json
from config import DB_PATH
from db_helper import DatabaseHelper

try:
    from tabulate import tabulate
except ImportError:
    import os
    print("[*] Đang tự động cài đặt thư viện 'tabulate' để hiển thị bảng đẹp hơn...")
    os.system("pip install tabulate")
    from tabulate import tabulate

def check_database():
    DatabaseHelper() 
    
    print(f"[*] Đang kết nối tới DB tại đường dẫn: {DB_PATH}\n")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. BẢNG PHIÊN HỌC (LectureSession)
        print("=" * 40 + " 1. BẢNG BUỔI HỌC (LectureSession) " + "=" * 40)
        cursor.execute("SELECT * FROM LectureSession")
        session_rows = cursor.fetchall()
        if session_rows:
            headers = ["ID Buổi học", "Mã môn học", "Tên môn học", "Ngày học", "Bắt đầu", "Kết thúc", "Trạng thái"]
            data = [[
                r["session_id"], r["course_code"], r["course_name"], 
                r["lecture_date"], r["start_time"], r["end_time"], r["status"]
            ] for r in session_rows]
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print("[-] Chưa có dữ liệu buổi học nào.")
        print("\n")

        # 2. BẢNG SINH VIÊN (Student)
        print("=" * 40 + " 2. BẢNG SINH VIÊN (Student) " + "=" * 40)
        cursor.execute("SELECT * FROM Student")
        student_rows = cursor.fetchall()
        if student_rows:
            headers = ["MSSV", "Họ và tên", "Lớp", "Email", "Số ĐT", "Face Vector"]
            data = [] 
            for r in student_rows:
                emb_status = "Trống"
                if r["face_embedding"]:
                    try:
                        emb_list = json.loads(r["face_embedding"])
                        emb_status = f"Sẵn sàng ({len(emb_list)} dim)"
                    except:
                        emb_status = "Lỗi định dạng"
                
                data.append([r["student_id"], r["full_name"], r["class_name"], r["email"], r["phone"], emb_status])
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print("[-] Chưa có sinh viên nào trong hệ thống.")
        print("\n")

        # 3. BẢNG ĐIỂM DANH (Attendance)
        print("=" * 40 + " 3. BẢNG ĐIỂM DANH (Attendance) " + "=" * 40)
        cursor.execute('''
            SELECT att.attendance_id, att.session_id, att.student_id, std.full_name, 
                   att.check_in_time, att.attendance_status, att.initial_behavior, att.initial_is_raising_hand
            FROM Attendance att
            LEFT JOIN Student std ON att.student_id = std.student_id
        ''')
        attendance_rows = cursor.fetchall()
        if attendance_rows:
            headers = ["ID Giao dịch", "Mã buổi học", "MSSV", "Họ và tên", "Thời gian vào", "Trạng thái", "Hành vi đầu", "Phát biểu đầu"]
            data = []
            for r in attendance_rows:
                hand_status = "Có" if r["initial_is_raising_hand"] == 1 else "Không"
                data.append([
                    r["attendance_id"], r["session_id"], r["student_id"], r["full_name"], 
                    r["check_in_time"], r["attendance_status"], r["initial_behavior"], hand_status
                ])
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print("[-] Chưa có dữ liệu điểm danh thực tế.")
        print("\n")

        # 4. BẢNG TRẠNG THÁI HỌC TẬP (LearningStatus)
        print("=" * 40 + " 4. BẢNG TRẠNG THÁI HỌC TẬP (LearningStatus) " + "=" * 40)
        cursor.execute('''
            SELECT ls.status_id, ls.session_id, ls.student_id, std.full_name, ls.timestamp, ls.learning_behavior, ls.is_raising_hand
            FROM LearningStatus ls
            LEFT JOIN Student std ON ls.student_id = std.student_id
            ORDER BY ls.timestamp DESC
        ''')
        status_rows = cursor.fetchall()
        if status_rows:
            headers = ["ID Log", "Mã buổi học", "MSSV", "Họ và tên", "Thời gian ghi nhận", "Hành vi AI quét", "Giơ tay phát biểu"]
            data = []
            for r in status_rows:
                hand_icon = " Có giơ tay" if r["is_raising_hand"] == 1 else "Không"
                data.append([
                    r["status_id"], r["session_id"], r["student_id"], r["full_name"], 
                    r["timestamp"], r["learning_behavior"], hand_icon
                ])
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print("[-] Chưa có bản ghi log hành vi học tập nào.")
        print("=" * 125)

        conn.close()
    except Exception as e:
        print(f"[X] Lỗi nghiêm trọng khi truy vấn dữ liệu từ database: {e}")

if __name__ == "__main__":
    check_database()