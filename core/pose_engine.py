# core/pose_analyzer.py
import cv2

class PoseAnalyzer:
    def __init__(self):
        pass

    def analyze_pose_behavior(self, keypoints, box_coords=None):
        """Phân tích tọa độ khớp xương cơ thể để xác định trạng thái học tập và phát biểu"""
        if keypoints is None or len(keypoints.xy) == 0:
            return "Distracted", False

        pts = keypoints.xy[0].cpu().numpy()
        if len(pts) < 11:
            return "Distracted", False

        left_eye, right_eye = pts[1], pts[2]
        left_shoulder, right_shoulder = pts[5], pts[6]
        left_wrist, right_wrist = pts[9], pts[10]

        is_raising_hand = False

        # Nhánh quét hành vi Giơ tay (Cổ tay cao hơn mắt)
        if left_eye[1] > 0 and left_wrist[1] > 0 and left_wrist[1] < left_eye[1]:
            is_raising_hand = True
        if right_eye[1] > 0 and right_wrist[1] > 0 and right_wrist[1] < right_eye[1]:
            is_raising_hand = True

        # Nhánh quét hành vi Đứng lên (Dựa vào tỉ lệ tọa độ vai so với chiều cao khung hình bao)
        if box_coords is not None:
            bx1, by1, bx2, by2 = box_coords
            box_height = by2 - by1
            if box_height > 0:
                if left_shoulder[1] > 0 and (left_shoulder[1] - by1) / box_height < 0.28:
                    is_raising_hand = True
                elif right_shoulder[1] > 0 and (right_shoulder[1] - by1) / box_height < 0.28:
                    is_raising_hand = True

        behavior = "Focusing"
        
        # Nhánh quét độ tập trung dựa vào khoảng cách đứng giữa đầu và vai
        if left_eye[1] > 0 and left_shoulder[1] > 0:
            head_shoulder_dist = left_shoulder[1] - left_eye[1]
            if head_shoulder_dist < 45:
                behavior = "Distracted"
        elif right_eye[1] > 0 and right_shoulder[1] > 0:
            head_shoulder_dist = right_shoulder[1] - right_eye[1]
            if head_shoulder_dist < 45:
                behavior = "Distracted"

        return behavior, is_raising_hand