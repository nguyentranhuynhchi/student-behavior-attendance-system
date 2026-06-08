# database/connection.py
# Quan ly ket noi SQLite va khoi tao schema co so du lieu.

import hashlib
import os
import sqlite3

from config import DATABASE_DIR, DB_PATH


class BaseRepository:
    """Lop cha cung cap ket noi SQLite dung chung cho tat ca repository."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH

    def get_connection(self):
        """Tao va tra ve mot ket noi SQLite moi voi row_factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _hash_default_password():
    try:
        import bcrypt

        return bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except ImportError:
        print("[Warning] bcrypt chua duoc cai. Dung SHA-256 tam thoi. Chay: pip install bcrypt")
        return hashlib.sha256("admin123".encode("utf-8")).hexdigest()


def init_all_tables(db_path=None):
    """Khoi tao toan bo schema co so du lieu."""
    os.makedirs(DATABASE_DIR, exist_ok=True)

    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            email TEXT UNIQUE,
            role TEXT NOT NULL DEFAULT 'teacher',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Classroom (
            classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_code TEXT UNIQUE NOT NULL,
            class_name TEXT NOT NULL,
            department TEXT,
            academic_year TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Student (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            classroom_id INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            face_embedding TEXT,
            avatar_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (classroom_id) REFERENCES Classroom(classroom_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS LectureSession (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            classroom_id INTEGER NOT NULL,
            created_by INTEGER,
            lecture_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (classroom_id) REFERENCES Classroom(classroom_id),
            FOREIGN KEY (created_by) REFERENCES User(user_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            attendance_status TEXT NOT NULL,
            initial_behavior TEXT NOT NULL DEFAULT 'Focusing',
            initial_is_raising_hand INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES LectureSession(session_id),
            FOREIGN KEY (student_id) REFERENCES Student(student_id),
            UNIQUE(session_id, student_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS LearningStatus (
            status_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            learning_behavior TEXT NOT NULL,
            is_raising_hand INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES LectureSession(session_id),
            FOREIGN KEY (student_id) REFERENCES Student(student_id)
        )
        """
    )

    cursor.execute("SELECT 1 FROM User WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO User (username, password_hash, display_name, email, role)
            VALUES ('admin', ?, 'Quan Tri Vien', 'admin@hcmute.edu.vn', 'admin')
            """,
            (_hash_default_password(),),
        )

    conn.commit()
    conn.close()
