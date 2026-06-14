"""Script tao icon PNG cho sidebar bang Pillow"""
from PIL import Image, ImageDraw, ImageFont
import os

ICON_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
os.makedirs(ICON_DIR, exist_ok=True)

SIZE = 64
BG = (0, 0, 0, 0)  # Transparent

def create_icon(filename, draw_func):
    img = Image.new("RGBA", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    draw_func(draw, SIZE)
    img.save(os.path.join(ICON_DIR, filename))
    print(f"  [OK] {filename}")

# --- dashboard.png: 4 o vuong (grid) ---
def draw_dashboard(draw, s):
    c = "#E0E7FF"
    gap = 6
    half = (s - gap) // 2
    draw.rounded_rectangle([4, 4, 4+half, 4+half], radius=5, fill=c)
    draw.rounded_rectangle([4+half+gap, 4, s-4, 4+half], radius=5, fill=c)
    draw.rounded_rectangle([4, 4+half+gap, 4+half, s-4], radius=5, fill=c)
    draw.rounded_rectangle([4+half+gap, 4+half+gap, s-4, s-4], radius=5, fill=c)

# --- enroll.png: nguoi + dau cong ---
def draw_enroll(draw, s):
    c = "#E0E7FF"
    cx, cy = s//2 - 6, s//2
    draw.ellipse([cx-10, cy-18, cx+10, cy-2], fill=c)  # head
    draw.ellipse([cx-16, cy+2, cx+16, cy+20], fill=c)   # body
    # dau cong
    px = cx + 20
    py = cy - 8
    draw.rectangle([px-1, py-7, px+1, py+7], fill="#818CF8")
    draw.rectangle([px-7, py-1, px+7, py+1], fill="#818CF8")

# --- session.png: clipboard ---
def draw_session(draw, s):
    c = "#E0E7FF"
    draw.rounded_rectangle([12, 8, s-12, s-6], radius=6, fill=c)
    draw.rounded_rectangle([22, 4, s-22, 12], radius=3, fill="#818CF8")  # clip
    for i in range(3):
        y = 22 + i * 10
        draw.rectangle([20, y, s-20, y+3], fill="#818CF8")

# --- lobby.png: door ---
def draw_lobby(draw, s):
    c = "#E0E7FF"
    draw.rounded_rectangle([14, 6, s-14, s-6], radius=8, fill=c)
    draw.ellipse([s//2+4, s//2-2, s//2+10, s//2+4], fill="#818CF8")  # knob

# --- play.png: play triangle ---
def draw_play(draw, s):
    c = "#818CF8"
    cx, cy = s//2, s//2
    draw.ellipse([6, 6, s-6, s-6], fill="#E0E7FF")
    points = [(cx-6, cy-12), (cx-6, cy+12), (cx+10, cy)]
    draw.polygon(points, fill=c)

# --- settings.png: gear ---
def draw_settings(draw, s):
    c = "#E0E7FF"
    cx, cy = s//2, s//2
    r_out = 22
    r_in = 12
    draw.ellipse([cx-r_out, cy-r_out, cx+r_out, cy+r_out], fill=c)
    draw.ellipse([cx-r_in, cy-r_in, cx+r_in, cy+r_in], fill=BG)
    # 4 teeth
    for angle in [0, 90, 45, 135]:
        import math
        rad = math.radians(angle)
        x1 = cx + int((r_out-2) * math.cos(rad))
        y1 = cy + int((r_out-2) * math.sin(rad))
        draw.ellipse([x1-4, y1-4, x1+4, y1+4], fill="#818CF8")

print("Dang tao icon PNG...")
create_icon("dashboard.png", draw_dashboard)
create_icon("enroll.png", draw_enroll)
create_icon("session.png", draw_session)
create_icon("lobby.png", draw_lobby)
create_icon("play.png", draw_play)
create_icon("settings.png", draw_settings)
print("Hoan tat!")
