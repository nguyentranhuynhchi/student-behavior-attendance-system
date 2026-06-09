# db_helper.py
# Facade giu API cu, logic CRUD chi tiet nam trong package database/.

from database.attendance_crud import AttendanceRepository
from database.classroom_crud import ClassroomRepository
from database.connection import BaseRepository, init_all_tables
from database.learning_status_crud import LearningStatusRepository
from database.lecture_session_crud import LectureSessionRepository
from database.student_crud import StudentRepository
from database.user_crud import UserRepository


class DatabaseHelper:
    def __init__(self):
        init_all_tables()

        self.base_repo = BaseRepository()
        self.classrooms = ClassroomRepository()
        self.students = StudentRepository(classroom_repo=self.classrooms)
        self.lecture_sessions = LectureSessionRepository(classroom_repo=self.classrooms)
        self.attendance = AttendanceRepository()
        self.learning_status = LearningStatusRepository()
        self.users = UserRepository()

    def get_connection(self):
        return self.base_repo.get_connection()

    def init_db(self):
        init_all_tables()

    def create_new_lecture_session(
        self,
        course_name,
        lecture_date,
        start_time,
        end_time,
        classroom_id=None,
        created_by=None,
    ):
        return self.lecture_sessions.create_new_lecture_session(
            course_name,
            lecture_date,
            start_time,
            end_time,
            classroom_id=classroom_id,
            created_by=created_by,
        )

    def update_lecture_session_status(self, session_id, new_status):
        return self.lecture_sessions.update_lecture_session_status(session_id, new_status)

    def check_exists(self, field_name, value):
        return self.students.check_exists(field_name, value)

    def insert_student(self, student_id, full_name, class_name, email, phone, avatar_path, face_embedding=None):
        return self.students.insert_student(
            student_id=student_id,
            full_name=full_name,
            class_name=class_name,
            email=email,
            phone=phone,
            avatar_path=avatar_path,
            face_embedding=face_embedding,
        )

    def get_all_valid_embeddings(self):
        return self.students.get_all_valid_embeddings()

    def insert_attendance(self, session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand):
        return self.attendance.insert_attendance(
            session_id, student_id, attendance_status, initial_behavior, initial_is_raising_hand
        )

    def insert_learning_status(self, session_id, student_id, learning_behavior, is_raising_hand):
        return self.learning_status.insert_learning_status(session_id, student_id, learning_behavior, is_raising_hand)

    def get_next_upcoming_session(self):
        return self.lecture_sessions.get_next_upcoming_session()

    def get_session_by_status(self, status):
        return self.lecture_sessions.get_session_by_status(status)

    def get_lectures_by_date(self, lecture_date, classroom_id=None):
        return self.lecture_sessions.get_lectures_by_date(lecture_date, classroom_id=classroom_id)

    def get_scheduled_lectures(self):
        return self.lecture_sessions.get_scheduled_lectures()

    def get_all_sessions(self):
        return self.lecture_sessions.get_all_sessions()

    def get_latest_session_id(self):
        return self.lecture_sessions.get_latest_session_id()

    def get_all_students_with_classroom(self):
        return self.students.get_all_students_with_classroom()

    def count_students(self):
        return self.students.count_students()

    def count_present_by_session(self, session_id):
        return self.attendance.count_present_by_session(session_id)

    def count_alert_students_by_session(self, session_id):
        return self.learning_status.count_alert_students_by_session(session_id)

    def get_session_attendance_details(self, session_id):
        return self.attendance.get_session_attendance_details(session_id)
