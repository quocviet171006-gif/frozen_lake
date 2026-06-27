import pygame

class GameConfig:
    """
    Cấu hình cho trò chơi Frozen Lake.
    Chứa kích thước lưới, thiết lập giao diện UI, các loại gạch (tile), và bảng màu.
    """
    
    # --- Kích thước & Giao diện ---
    GRID = 8                        # Số lượng ô trên một hàng/cột của lưới
    CELL = 72                       # Kích thước của một ô (pixel)
    PANEL_W = 380                   # Chiều rộng của bảng điều khiển bên phải (pixel)
    W = GRID * CELL + PANEL_W       # Tổng chiều rộng cửa sổ
    H = GRID * CELL + 60            # Tổng chiều cao cửa sổ (bao gồm khoảng cách bên dưới)
    FPS = 60                        # Số khung hình trên giây
    
    # --- Các loại gạch (Tile) ---
    SNOW = 0                        # Đường tuyết đi được
    HOLE = 1                        # Hố nguy hiểm (phạt/thua)
    MOUNT = 2                       # Chướng ngại vật (núi - không thể đi qua)
    HOUSE = 4                       # Ngôi nhà (đích đến/chiến thắng)

    # --- Bảng màu ---
    C = {
        "bg":        (8,  18,  40),     # Màu nền tối
        "snow1":     (210,230,245),     # Màu tuyết sáng
        "snow2":     (190,215,235),     # Màu tuyết tối hơn
        "hole":      (90, 170,210),     # Màu cơ bản của hố
        "hole2":     (50, 130,180),     # Màu hố tối hơn
        "mount":     (120,100, 80),     # Màu cơ bản của núi
        "mount2":    (160,140,110),     # Màu sáng của núi
        "panel":     (15,  30,  65),    # Nền bảng UI
        "panel2":    (20,  40,  80),    # Điểm nhấn trên bảng UI
        "accent":    (80, 160,255),     # Màu nhấn chính (xanh lam)
        "accent2":   (40, 100,200),     # Màu nhấn tối hơn
        "gold":      (255,210, 60),     # Màu vàng (cho ngôi sao/chiến thắng)
        "red":       (220, 70, 70),     # Màu đỏ (cho lỗi/nguy hiểm)
        "green":     (70, 200,100),     # Màu xanh lá (cho thành công)
        "teal":      (60, 200,180),     # Xanh ngọc cho một số phần UI
        "text":      (220,235,255),     # Màu chữ chính (trắng ánh xanh)
        "text2":     (140,170,210),     # Màu chữ phụ (mờ hơn)
        "white":     (255,255,255),     # Màu trắng tinh
        "btn":       (25,  50, 100),    # Màu nút bấm cơ bản
        "btn_hover": (40,  80, 160),    # Màu nút bấm khi di chuột
        "btn_act":   (60, 120,220),     # Màu nút bấm khi đang chọn/hoạt động
    }

    # --- Màu sắc đặc trưng cho từng thuật toán ---
    # Dùng để phân biệt các thuật toán trên UI hoặc khi vẽ đường đi
    ALG_COLORS = {
        # Nhóm 1 - Tìm kiếm mù (Uninformed Search)
        "BFS": (100,200,255), "DFS": (255,140, 60), "UCS": (100,240,140), 
        
        # Nhóm 2 - Tìm kiếm có thông tin (Informed Search)
        "Greedy": (255,100,200), "A*": (255,215, 0), "IDA*":  (218,165, 32),
        
        # Nhóm 3 - Tìm kiếm cục bộ (Local Search)
        "Simple HC": (255,182,193), "Beam": (255,105,180), "Sim Ann": (255,69,0),
        
        # Nhóm 4 - Tìm kiếm trong môi trường phức tạp (Complex Search)
        "Sensorless":  (147, 112, 219),   # Tím vừa
        "Partial-Obs": (64,  224, 208),   # Xanh lơ
        "AND-OR":      (255, 140,  60),   # Cam ấm
        
        # Nhóm 5 - Bài toán thỏa mãn ràng buộc (CSP)
        "Forward Check": (255, 140, 60), "AC-3": (100, 200, 255), "Min-Conflicts": (255, 69, 0),
        
        # Nhóm 6 - Tìm kiếm đối kháng (Adversarial Search)
        "Minimax": (220, 50, 50), "Alpha-Beta": (180, 40, 100), "Expectimax": (50, 200, 100)
    }

# --- Khởi tạo Pygame & Font chữ ---
pygame.init()
font_lg  = pygame.font.SysFont("consolas", 28, bold=True)    # Font lớn cho tiêu đề
font_md  = pygame.font.SysFont("consolas", 18, bold=True)    # Font vừa cho nút bấm/tiêu đề phụ
font_sm  = pygame.font.SysFont("consolas", 13)               # Font nhỏ cho văn bản thường
font_xs  = pygame.font.SysFont("consolas", 12)               # Font siêu nhỏ cho chi tiết
