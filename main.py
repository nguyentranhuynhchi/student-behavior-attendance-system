# main.py
import core
import customtkinter as ctk
from gui.theme import THEME_COLORS
from gui.components.sidebar import Sidebar
from gui.screens.overview_screen import OverviewScreen
from gui.screens.enrollment_screen import EnrollmentScreen
from gui.screens.session_screen import SessionScreen
from gui.screens.lecture_screen import LectureScreen
from gui.screens.account_screen import AccountScreen
from gui.screens.lecture_lobby_screen import LectureLobbyScreen

class SmartClassroomApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Lớp học thông minh - Smart Classroom")
        self.geometry("1280x720")
        self.minsize(1280, 720)
        
        self.configure(fg_color=THEME_COLORS["bg_main"])
        ctk.set_appearance_mode("light")
        
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
        # 1. Khởi tạo Sidebar điều hướng
        self.sidebar = Sidebar(self, on_menu_select=self.switch_screen)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Khung chứa nội dung chính (Content Frame)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 3. Khởi tạo và đăng ký các màn hình vào content_frame đúng chuẩn
        self.screens = {
            "overview": OverviewScreen(self.content_frame),
            "enrollment": EnrollmentScreen(self.content_frame),
            "session": SessionScreen(self.content_frame),
            "account": AccountScreen(self.content_frame),
            "lecture_lobby": LectureLobbyScreen(self.content_frame),
            "lecture": LectureScreen(self.content_frame) 
        }
        
        self.switch_screen("enrollment")

    def switch_screen(self, screen_id):
            if self.current_screen:
                self.current_screen.pack_forget()
            if screen_id == "lecture_lobby":
                if hasattr(self.screens["lecture_lobby"], "refresh_and_load_data"):
                    self.screens["lecture_lobby"].refresh_and_load_data()
            elif screen_id == "lecture":
                if hasattr(self.screens["lecture"], "refresh_and_load_data"):
                    self.screens["lecture"].refresh_and_load_data()
                    
            target_screen = self.screens.get(screen_id)
            if target_screen:
                target_screen.pack(fill="both", expand=True)
                self.current_screen = target_screen
            else:
                print(f"[Warning] Không tìm thấy màn hình với ID: {screen_id}")
   
if __name__ == "__main__":
    app = SmartClassroomApp()
    app.mainloop()