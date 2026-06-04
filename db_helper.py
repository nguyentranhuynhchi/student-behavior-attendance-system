# db_helper.py
import sqlite3
from config import DB_PATH

class DatabaseHelper:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Bảng Student (Quản lý thông tin sinh viên)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Student (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE,
                face_embedding TEXT,
                avatar_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Bảng LectureSession (Quản lý các phiên/buổi học)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LectureSession (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                lecture_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled' -- 'scheduled', 'ongoing', 'completed'
            )
        ''')
        
        # 3. Bảng Attendance (Nâng cấp bổ sung cột hành vi và phát biểu ban đầu lúc điểm danh)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attendance_status TEXT NOT NULL,          -- 'Có mặt' hoặc 'Đi trễ'
                initial_behavior TEXT NOT NULL,           -- 'Focusing' hoặc 'Distracted' lúc điểm danh
                initial_is_raising_hand INTEGER DEFAULT 0, -- 1: Có giơ tay, 0: Không giơ tay lúc điểm danh
                FOREIGN KEY (session_id) REFERENCES LectureSession(session_id),
                FOREIGN KEY (student_id) REFERENCES Student(student_id),
                UNIQUE(session_id, student_id) 
            )
        ''')

        # 4. Bảng LearningStatus (Nâng cấp bổ sung cột theo dõi trạng thái giơ tay chu kỳ)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LearningStatus (
                status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                learning_behavior TEXT NOT NULL,     -- 'Focusing', 'Distracted'
                is_raising_hand INTEGER DEFAULT 0,   -- 1: Có giơ tay, 0: Không giơ tay tại chu kỳ quét
                FOREIGN KEY (session_id) REFERENCES LectureSession(session_id),
                FOREIGN KEY (student_id) REFERENCES Student(student_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_new_lecture_session(self, course_name, lecture_date, start_time, end_time):
        """Khởi tạo một phiên học mới, tự động sinh mã bài giảng và trả về session_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Bước 1: Chèn dữ liệu với course_code tạm thời là trống hoặc mặc định
            cursor.execute('''
                INSERT INTO LectureSession (course_code, course_name, lecture_date, start_time, end_time, status) 
                VALUES (?, ?, ?, ?, ?, 'scheduled')
            ''', ("", course_name, lecture_date, start_time, end_time))
            
            session_id = cursor.lastrowid
            
            # Bước 2: Tự động sinh mã môn học dựa trên session_id (Ví dụ: LEC00001, LEC00002)
            auto_course_code = f"LEC{session_id:05d}"
            
            # Bước 3: Cập nhật lại mã môn học vừa sinh vào DB
            cursor.execute('''
                UPDATE LectureSession 
                SET course_code = ? 
                WHERE session_id = ?
            ''', (auto_course_code, session_id))
            
            conn.commit()
            return session_id
        except Exception as e:
            print(f"[Error] Failed to create lecture session: {e}")
            raise e
        finally:
            conn.close()

    def update_lecture_session_status(self, session_id, new_status):
        """Cập nhật trạng thái mới cho bài giảng (ví dụ: chuyển sang 'ongoing' hoặc 'completed')"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE LectureSession 
                SET status = ? 
                WHERE session_id = ?
            ''', (new_status, session_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to update lecture session status: {e}")
            return False
        finally:
            conn.close()
            
    def check_exists(self, field_name, value):
        """Kiểm tra sự tồn tại của trường dữ liệu trong bảng Student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = f"SELECT 1 FROM Student WHERE {field_name} = ?"
        cursor.execute(query, (value,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def insert_student(self, student_id, full_name, class_name, email, phone, avatar_path, face_embedding=None):
        """Thêm mới một tài khoản sinh viên vào cơ sở dữ liệu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Student (student_id, full_name, class_name, email, phone, avatar_path, face_embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, full_name, class_name, email, phone, avatar_path, face_embedding))
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert student: {e}")
            return False
        finally:
            conn.close()

    def get_all_valid_embeddings(self):
        """Lấy danh sách tất cả các sinh viên đã được cấu hình Face Vector thành công"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, full_name, face_embedding, avatar_path FROM Student WHERE face_embedding IS NOT NULL")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def insert_attendance(self, session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand):
        """Ghi nhận log giao dịch điểm danh kèm hành vi trạng thái ban đầu của sinh viên"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO Attendance (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[Error] Failed to insert attendance: {e}")
            return False
        finally:
            conn.close()

    def insert_learning_status(self, session_id, student_id, learning_behavior, is_raising_hand):
        """Ghi nhận đồng thời trạng thái hành vi học tập và biến phát biểu số nguyên (1/0) vào DB theo chu kỳ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO LearningStatus (session_id, student_id, learning_behavior, is_raising_hand)
                VALUES (?, ?, ?, ?)
            ''', (session_id, student_id, learning_behavior, is_raising_hand))
            conn.commit()
            return True
        except Exception as e:
            print(f"[Error] Failed to insert learning status: {e}")
            return False
        finally:
            conn.close()
    
    def get_next_upcoming_session(self):
        """Lấy buổi học trạng thái chưa giảng ('scheduled') sắp bắt đầu sớm nhất"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, course_name, lecture_date, start_time, end_time, status 
            FROM LectureSession 
            WHERE status = 'scheduled' 
            ORDER BY lecture_date ASC, start_time ASC LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "session_id": row["session_id"], 
                "course_name": row["course_name"], 
                "lecture_date": row["lecture_date"],
                "start_time": row["start_time"], 
                "end_time": row["end_time"], 
                "status": row["status"]
            }
        return None

    def get_session_by_status(self, status):
        """Lấy thông tin buổi học theo trạng thái chính xác ('scheduled', 'ongoing', 'completed')"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, course_name, lecture_date, start_time, end_time, status 
            FROM LectureSession 
            WHERE status = ? 
            ORDER BY session_id DESC LIMIT 1
        ''', (status,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "session_id": row["session_id"], 
                "course_name": row["course_name"], 
                "lecture_date": row["lecture_date"],
                "start_time": row["start_time"], 
                "end_time": row["end_time"], 
                "status": row["status"]
            }
        return None
    
    def get_lectures_by_date(self, lecture_date):
        """Lấy tất cả các bài giảng trong một ngày cụ thể (chỉ lấy trạng thái chưa giảng hoặc đang giảng)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT session_id, course_name, start_time, end_time, status 
                FROM LectureSession 
                WHERE lecture_date = ? AND status != 'completed'
            ''', (lecture_date,))
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[Error] Failed to get lectures by date: {e}")
            return []
        finally:
            conn.close()