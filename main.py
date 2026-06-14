# main.py
import customtkinter as ctk
from gui.theme import THEME_COLORS
from gui.components.admin_sidebar import AdminSidebar
from gui.components.sidebar import Sidebar
from gui.screens.overview_screen import OverviewScreen
from gui.screens.enrollment_screen import EnrollmentScreen
from gui.screens.session_screen import SessionScreen
from gui.screens.lecture_screen import LectureScreen
from gui.screens.account_screen import AccountScreen
from gui.screens.lecture_lobby_screen import LectureLobbyScreen
from gui.screens.teacher_management_screen import TeacherManagementScreen
from gui.screens.student_management_screen import StudentManagementScreen
from gui.screens.classroom_management_screen import ClassroomManagementScreen
from gui.screens.session_history_screen import SessionHistoryScreen

class SmartClassroomApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.admin_screens = {"admin_overview", "teacher_management", "student_management", "classroom_management", "session_history", "account"}
        self.teacher_screens = {"overview", "enrollment", "session", "lecture_lobby", "lecture", "account"}
        self.protected_screens = self.admin_screens | self.teacher_screens
        
        self.title("Lớp học thông minh - Smart Classroom")
        self.geometry("1280x720")
        self.minsize(1280, 720)
        
        self.configure(fg_color=THEME_COLORS["bg_main"])
        ctk.set_appearance_mode("dark")
        
        try:
            self.state("zoomed")
        except:
            self.attributes("-zoomed", True)
            
        self.grid_columnconfigure(0, weight=0, minsize=260) 
        self.grid_columnconfigure(1, weight=1)              
        self.grid_rowconfigure(0, weight=1)
        
        self.current_screen = None
        self.screens = {}
        self.init_ui()

    def init_ui(self):
        # 1. Khởi tạo Sidebar điều hướng theo vai trò
        self.teacher_sidebar = Sidebar(self, on_menu_select=self.switch_screen, on_logout=self.handle_logout)
        self.admin_sidebar = AdminSidebar(self, on_menu_select=self.switch_screen, on_logout=self.handle_logout)
        self.teacher_sidebar.grid(row=0, column=0, sticky="nsew")
        self.admin_sidebar.grid(row=0, column=0, sticky="nsew")
        self.admin_sidebar.grid_remove()
        self.sidebar = self.teacher_sidebar
        
        # 2. Khung chứa nội dung chính (Content Frame)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 3. Khởi tạo và đăng ký các màn hình vào content_frame đúng chuẩn
        self.screens = {
            "overview": OverviewScreen(self.content_frame, mode="teacher"),
            "admin_overview": OverviewScreen(self.content_frame, mode="admin"),
            "enrollment": EnrollmentScreen(self.content_frame),
            "session": SessionScreen(self.content_frame),
            "account": AccountScreen(self.content_frame, on_auth_changed=self.handle_auth_changed),
            "lecture_lobby": LectureLobbyScreen(self.content_frame),
            "lecture": LectureScreen(self.content_frame),
            "teacher_management": TeacherManagementScreen(self.content_frame),
            "student_management": StudentManagementScreen(self.content_frame),
            "classroom_management": ClassroomManagementScreen(self.content_frame),
            "session_history": SessionHistoryScreen(self.content_frame),
        }
        
        self.switch_screen("account")

    def switch_screen(self, screen_id):
            if not self._can_access_screen(screen_id):
                screen_id = "account"

            target_screen = self.screens.get(screen_id)
            if target_screen:
                if self.current_screen and self.current_screen is not target_screen:
                    self.current_screen.pack_forget()

                if hasattr(self, "sidebar"):
                    self.sidebar.set_active(screen_id)

                if hasattr(target_screen, "set_current_user"):
                    target_screen.set_current_user(self.current_user)
                target_screen.pack(fill="both", expand=True)
                self.current_screen = target_screen

                if hasattr(target_screen, "refresh_and_load_data"):
                    target_screen.refresh_and_load_data()
                elif hasattr(target_screen, "load_data_from_db"):
                    target_screen.load_data_from_db()
            else:
                print(f"[Warning] Không tìm thấy màn hình với ID: {screen_id}")

    def handle_auth_changed(self, user):
            self.current_user = user
            self._show_sidebar_for_user(user)
            if user:
                if user.get("role") == "admin":
                    self.switch_screen("admin_overview")
                else:
                    self.switch_screen("overview")
            else:
                self.switch_screen("account")

    def handle_logout(self):
            self.current_user = None
            self._show_sidebar_for_user(None)
            account_screen = self.screens.get("account")
            if account_screen and hasattr(account_screen, "set_current_user"):
                account_screen.set_current_user(None)
            self.switch_screen("account")

    def _show_sidebar_for_user(self, user):
            if user and user.get("role") == "admin":
                self.teacher_sidebar.grid_remove()
                self.admin_sidebar.grid()
                self.sidebar = self.admin_sidebar
            else:
                self.admin_sidebar.grid_remove()
                self.teacher_sidebar.grid()
                self.sidebar = self.teacher_sidebar

            self.teacher_sidebar.update_user_info(user if user and user.get("role") != "admin" else None)
            self.admin_sidebar.update_user_info(user if user and user.get("role") == "admin" else None)

    def _can_access_screen(self, screen_id):
            if screen_id == "account":
                return True

            if self.current_user is None:
                return False

            role = self.current_user.get("role")
            if role == "admin":
                return screen_id in self.admin_screens
            if role == "teacher":
                return screen_id in self.teacher_screens
            return False
   
if __name__ == "__main__":
    app = SmartClassroomApp()
    app.mainloop()
