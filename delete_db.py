# delete_db.py
import sqlite3
from config import DB_PATH
from db_helper import DatabaseHelper  

def clear_all_database_data():
    """Hàm xóa sạch toàn bộ dữ liệu trong tất cả các bảng của hệ thống"""
    DatabaseHelper()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Bật chế độ ràng buộc khóa ngoại để đảm bảo an toàn dữ liệu toàn vẹn
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        print("[*] Đang bắt đầu dọn dẹp dữ liệu trong Database...")
        
        # 1. Xóa các bảng chứa dữ liệu phụ/log chu kỳ trước để tránh lỗi Foreign Key Constraint
        cursor.execute("DELETE FROM LearningStatus;")
        cursor.execute("DELETE FROM Attendance;")
        
        # 2. Xóa các bảng chứa danh mục gốc sau
        cursor.execute("DELETE FROM LectureSession;")
        cursor.execute("DELETE FROM Student;")
        cursor.execute("DELETE FROM Classroom;")
        
        # 3. Reset bộ đếm ID tự tăng (AUTOINCREMENT) trong hệ thống SQLite về lại từ 0
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('LearningStatus', 'Attendance', 'LectureSession', 'Classroom');")
        
        conn.commit()
        print("[+] ĐÃ XÓA SẠCH TOÀN BỘ DỮ LIỆU TRONG DATABASE THÀNH CÔNG!")
        
        conn.close()
    except Exception as e:
        print(f"[X] Lỗi khi thao tác dọn dẹp Database: {e}")

if __name__ == "__main__":
    # Xác nhận lại một lần nữa bảo mật trước khi dọn dẹp sạch data
    confirm = input("Bạn có chắc chắn muốn XÓA TOÀN BỘ dữ liệu trong database không? (y/n): ")
    if confirm.lower() == 'y':
        clear_all_database_data()
    else:
        print("[-] Đã hủy thao tác xóa dữ liệu.")
