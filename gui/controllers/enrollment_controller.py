# gui/controllers/enrollment_controller.py
import os
import shutil
import json
from tkinter import messagebox
from db_helper import DatabaseHelper
from config import DATASET_ENROLLMENT_DIR

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

class EnrollmentController:
    def __init__(self):
        self.db = DatabaseHelper()

    def handle_save_student(self, student_id, full_name, class_name, email, phone, source_img_path, reset_form_callback):
        """
        Xử lý toàn bộ logic nghiệp vụ khi người dùng nhấn nút 'Save Student'.
        Bao gồm: Kiểm tra form -> Trích xuất Face Embedding -> Copy ảnh chuẩn hóa -> Lưu DB.
        """
        # 1. Ràng buộc 1: Kiểm tra các trường bắt buộc không được để trống
        if not student_id or not full_name or not class_name or not email:
            messagebox.showerror("Lỗi dữ liệu", "Vui lòng nhập đầy đủ các trường: MSSV, Họ và tên, Lớp và Email!")
            return

        # 2. Ràng buộc 2: Bắt buộc phải chọn ảnh chân dung gốc trước
        if not source_img_path or not os.path.exists(source_img_path):
            messagebox.showerror("Thiếu ảnh thẻ", "Vui lòng bấm 'Load Image' hoặc chọn ảnh thẻ hợp lệ của sinh viên để làm dữ liệu Face ID gốc!")
            return

        # 3. Ràng buộc 3: Kiểm tra trùng lặp khóa chính (MSSV)
        if self.db.check_exists("student_id", student_id):
            messagebox.showerror("Trùng lặp dữ liệu", f"Mã số sinh viên '{student_id}' đã tồn tại trong hệ thống!")
            return

        # 4. Ràng buộc 4: Kiểm tra trùng lặp Email liên lạc
        if self.db.check_exists("email", email):
            messagebox.showerror("Trùng lặp dữ liệu", f"Địa chỉ email '{email}' đã được đăng ký bởi một sinh viên khác!")
            return

        # 5. Ràng buộc 5: Kiểm tra trùng lặp Số điện thoại (nếu có nhập)
        if phone and self.db.check_exists("phone", phone):
            messagebox.showerror("Trùng lặp dữ liệu", f"Số điện thoại '{phone}' đã được sử dụng trong hệ thống!")
            return

        # --- XỬ LÝ TRÍCH XUẤT FACE EMBEDDING (VISION ENGINE CHI TIẾT) ---
        embedding_json = None
        if DeepFace is not None:
            try:
                # Trích xuất vector đặc trưng bằng model ArcFace (512 chiều)
                embedding_objs = DeepFace.represent(
                    img_path=source_img_path,
                    model_name="ArcFace",           # Đã đổi sang ArcFace đồng bộ hệ thống
                    detector_backend="retinaface",  # Đổi sang retinaface để align chuẩn
                    enforce_detection=True,         # BẮT BUỘC ĐỂ TRUE: Nếu không tìm thấy mặt sẽ ném ra lỗi lập tức
                    align=True                      # Xoay thẳng khuôn mặt hình học
                )
                
                if embedding_objs and len(embedding_objs) > 0:
                    embedding_vector = embedding_objs[0]["embedding"]
                    
                    # Kiểm tra nếu vector toàn số 0 (lỗi ma trận rỗng)
                    if all(v == 0 for v in embedding_vector):
                        messagebox.showerror("Ảnh không hợp lệ", "Không thể trích xuất đặc trưng! Vui lòng chọn ảnh khác rõ mặt và sắc nét hơn.")
                        return
                        
                    embedding_json = json.dumps(embedding_vector)
                else:
                    # Trường hợp danh sách trả về rỗng
                    messagebox.showerror("Ảnh không hợp lệ", "Không tìm thấy cấu trúc khuôn mặt hợp lệ trong bức ảnh này. Vui lòng chọn hoặc chụp lại ảnh chân dung khác!")
                    return
                    
            except Exception as e:
                # KHI DEEPFACE KHÔNG TÌM THẤY MẶT (ENFORCE_DETECTION TRẢ VỀ LỖI), KHỐI LỆNH NÀY SẼ BẮT LẠI
                messagebox.showerror(
                    "Ảnh không hợp lệ", 
                    "Hệ thống không nhận diện được khuôn mặt nào trong ảnh hồ sơ này!\n\n"
                    "Yêu cầu:\n"
                    "- Chọn ảnh chân dung rõ mặt, chính diện giống ảnh thẻ.\n"
                    "- Đảm bảo khuôn mặt không bị che khuất hoặc quá mờ.\n\n"
                    "Vui lòng bấm 'Tải Ảnh Lên' để chọn lại ảnh hợp lệ."
                )
                return # Chặn đứng tiến trình, không cho lưu thông tin xuống database
        else:
            print("[Warning] Thư viện 'deepface' chưa được cài đặt. Hệ thống sẽ tạm thời bỏ qua bước lưu embedding.")

        # --- TIẾN HÀNH SAO CHÉP VÀ LƯU TRỮ VẬT LÝ ---
        try:
            # 6. Quy trình chuẩn hóa và lưu trữ tệp ảnh vật lý vào thư mục dataset
            ext = os.path.splitext(source_img_path)[1].lower()
            if not ext:
                ext = ".jpg"
                
            # Đổi tên file ảnh tự động theo cấu trúc chuẩn hóa: [MSSV]_[Ho_Va_Ten].[ext]
            clean_name = full_name.strip().replace(" ", "_")
            target_filename = f"{student_id.strip()}_{clean_name}{ext}"
            target_file_path = os.path.join(DATASET_ENROLLMENT_DIR, target_filename)

            # Thực hiện copy tệp ảnh từ máy tính vào kho lưu trữ cục bộ của ứng dụng
            shutil.copy2(source_img_path, target_file_path)

            # 7. Ghi nhận dữ liệu và chuỗi embedding vào SQLite database thông qua db_helper
            success = self.db.insert_student(
                student_id=student_id.strip(),
                full_name=full_name.strip(),
                class_name=class_name.strip(),
                email=email.strip(),
                phone=phone.strip() if phone else None,
                avatar_path=target_file_path,
                face_embedding=embedding_json  
            )

            if success:
                messagebox.showinfo("Thành công", f"Đã đăng ký thành công sinh viên: {full_name.strip()} ({student_id.strip()}) và lưu cấu trúc Face ID thành công!")
                # Kích hoạt hàm callback ở giao diện để clear form nhập liệu
                reset_form_callback()
            else:
                messagebox.showerror("Lỗi hệ thống", "Đã xảy ra lỗi trong quá trình ghi nhận dữ liệu vào SQLite database.")

        except Exception as e:
            messagebox.showerror("Lỗi xử lý", f"Không thể sao chép ảnh thẻ hoặc lưu thông tin: {str(e)}")