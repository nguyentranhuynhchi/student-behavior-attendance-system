# # Đây là file test_db.py dùng để kiểm tra và hiển thị dữ liệu hiện có trong database một cách trực quan.
# # test_db.py
# import sqlite3
# import json
# from config import DB_PATH

# try:
#     from tabulate import tabulate
# except ImportError:
#     import os
#     print("[*] Đang tự động cài đặt thư viện 'tabulate' để hiển thị bảng đẹp hơn...")
#     os.system("pip install tabulate")
#     from tabulate import tabulate

# def check_database():
#     print(f"[*] Đang kết nối tới DB tại đường dẫn: {DB_PATH}\n")
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
        
#         # 1. BẢNG PHIÊN HỌC (LectureSession)
#         print("=" * 40 + " 1. BẢNG BUỔI HỌC (LectureSession) " + "=" * 40)
#         cursor.execute("SELECT * FROM LectureSession")
#         session_rows = cursor.fetchall()
#         if session_rows:
#             headers = ["ID Buổi học", "Tên môn học", "Thời gian bắt đầu"]
#             data = [[r["session_id"], r["course_name"], r["start_time"]] for r in session_rows]
#             print(tabulate(data, headers=headers, tablefmt="grid"))
#         else:
#             print("[-] Chưa có dữ liệu buổi học nào.")
#         print("\n")

#         # 2. BẢNG SINH VIÊN (Student)
#         print("=" * 40 + " 2. BẢNG SINH VIÊN (Student) " + "=" * 40)
#         cursor.execute("SELECT * FROM Student")
#         student_rows = cursor.fetchall()
#         if student_rows:
#             headers = ["MSSV", "Họ và tên", "Lớp", "Email", "Số ĐT", "Face Vector"]
#             data = [] 
#             for r in student_rows:
#                 emb_status = "Trống"
#                 if r["face_embedding"]:
#                     try:
#                         emb_list = json.loads(r["face_embedding"])
#                         emb_status = f"Sẵn sàng ({len(emb_list)} dim)"
#                     except:
#                         emb_status = "Lỗi định dạng"
                
#                 data.append([r["student_id"], r["full_name"], r["class_name"], r["email"], r["phone"], emb_status])
#             print(tabulate(data, headers=headers, tablefmt="grid"))
#         else:
#             print("[-] Chưa có sinh viên nào trong hệ thống.")
#         print("\n")

#         # 3. BẢNG ĐIỂM DANH (Attendance)
#         print("=" * 40 + " 3. BẢNG ĐIỂM DANH (Attendance) " + "=" * 40)
#         cursor.execute('''
#             SELECT att.attendance_id, att.session_id, att.student_id, std.full_name, att.check_in_time, att.attendance_status 
#             FROM Attendance att
#             LEFT JOIN Student std ON att.student_id = std.student_id
#         ''')
#         attendance_rows = cursor.fetchall()
#         if attendance_rows:
#             headers = ["ID Giao dịch", "Mã buổi học", "MSSV", "Họ và tên", "Thời gian vào", "Trạng thái"]
#             data = [[r["attendance_id"], r["session_id"], r["student_id"], r["full_name"], r["check_in_time"], r["attendance_status"]] for r in attendance_rows]
#             print(tabulate(data, headers=headers, tablefmt="grid"))
#         else:
#             print("[-] Chưa có dữ liệu điểm danh thực tế.")
#         print("\n")

#         # 4. BẢNG TRẠNG THÁI HỌC TẬP (LearningStatus)
#         print("=" * 40 + " 4. BẢNG TRẠNG THÁI HỌC TẬP (LearningStatus) " + "=" * 40)
#         cursor.execute('''
#             SELECT ls.status_id, ls.session_id, ls.student_id, std.full_name, ls.timestamp, ls.learning_behavior
#             FROM LearningStatus ls
#             LEFT JOIN Student std ON ls.student_id = std.student_id
#             ORDER BY ls.timestamp DESC
#         ''')
#         status_rows = cursor.fetchall()
#         if status_rows:
#             headers = ["ID Log", "Mã buổi học", "MSSV", "Họ và tên", "Thời gian ghi nhận", "Hành vi AI quét"]
#             data = [[r["status_id"], r["session_id"], r["student_id"], r["full_name"], r["timestamp"], r["learning_behavior"]] for r in status_rows]
#             print(tabulate(data, headers=headers, tablefmt="grid"))
#         else:
#             print("[-] Chưa có bản ghi log hành vi học tập nào.")
#         print("=" * 110)

#         conn.close()
#     except Exception as e:
#         print(f"[X] Lỗi nghiêm trọng khi truy vấn dữ liệu từ database: {e}")

# if __name__ == "__main__":
#     check_database()

# Dùng phần này để xóa toàn bộ dữ liệu trong database khi cần thiết, đặc biệt là trước khi chạy các bài test để đảm bảo môi trường sạch sẽ và không bị ảnh hưởng bởi dữ liệu cũ. Hãy cẩn thận khi sử dụng chức năng này vì nó sẽ xóa tất cả dữ liệu hiện có trong database!
import sqlite3
from config import DB_PATH

def clear_all_database_data():
    """Hàm xóa sạch toàn bộ dữ liệu trong tất cả các bảng của hệ thống"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Bật chế độ ràng buộc khóa ngoại để đảm bảo an toàn dữ liệu (nếu cần)
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        print("[*] Đang bắt đầu dọn dẹp Database...")
        
        # 1. Xóa các bảng chứa dữ liệu phụ/log trước để tránh lỗi Foreign Key Constraint
        cursor.execute("DELETE FROM LearningStatus;")
        cursor.execute("DELETE FROM Attendance;")
        
        # 2. Xóa các bảng chứa dữ liệu chính sau
        cursor.execute("DELETE FROM LectureSession;")
        cursor.execute("DELETE FROM Student;")
        cursor.execute("DELETE FROM Classroom;")
        
        # 3. Reset các tiến trình đếm ID tự động (AUTOINCREMENT) về lại 0
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('LearningStatus', 'Attendance', 'LectureSession', 'Classroom');")
        
        conn.commit()
        print("[+] ĐÃ XÓA SẠCH TOÀN BỘ DỮ LIỆU TRONG DATABASE THÀNH CÔNG!")
        
        conn.close()
    except Exception as e:
        print(f"[X] Lỗi khi thao tác dọn dẹp Database: {e}")

if __name__ == "__main__":
    # Xác nhận lại một lần nữa trước khi chạy code xóa sạch data
    confirm = input("Bạn có chắc chắn muốn XÓA TOÀN BỘ dữ liệu trong database không? (y/n): ")
    if confirm.lower() == 'y':
        clear_all_database_data()
    else:
        print("[-] Đã hủy thao tác xóa dữ liệu.")
