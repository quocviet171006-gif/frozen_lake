import os
import pygame
from config import GameConfig, font_sm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES = {}

def get_image(filename):
    """
    Tải một hình ảnh từ thư mục assets. Lưu vào bộ nhớ đệm (cache) để tránh tải lại nhiều lần.
    Nếu không tìm thấy ảnh, tạo một hình vuông màu hồng để thay thế.
    """
    if filename not in IMAGES:
        path = os.path.join(BASE_DIR, "assets", filename)
        if os.path.exists(path):
            img = pygame.image.load(path)
            # Căn chỉnh kích thước ảnh cho vừa với một ô trong game
            IMAGES[filename] = pygame.transform.smoothscale(img, (GameConfig.CELL, GameConfig.CELL))
        else:
            # Hình vuông màu hồng thay thế nếu thiếu tài nguyên
            IMAGES[filename] = pygame.Surface((GameConfig.CELL, GameConfig.CELL))
            IMAGES[filename].fill((255, 0, 255))
    return IMAGES[filename]

def draw_rounded_rect(surf, color, rect, radius=10, alpha=255):
    """
    Vẽ một hình chữ nhật bo góc trên bề mặt (surface) được cho.
    Hỗ trợ độ trong suốt (alpha).
    """
    r = pygame.Rect(rect)
    shape_surf = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, (*color[:3], alpha), shape_surf.get_rect(), border_radius=radius)
    surf.blit(shape_surf, r.topleft)

def draw_snow_tile(surf, x, y, shade=0):
    """Vẽ một ô tuyết bình thường (có thể đi được)."""
    surf.blit(get_image("snow.jpg"), (x, y))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_hole_tile(surf, x, y):
    """Vẽ một hố (nguy hiểm/phạt). Vẽ chồng lên lớp tuyết."""
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("hole.png"), (x, y))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_mount_tile(surf, x, y):
    """Vẽ một ngọn núi (chướng ngại vật). Vẽ chồng lên lớp tuyết."""
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("mount.webp"), (x, y))

def draw_house_tile(surf, x, y):
    """Vẽ mục tiêu/ngôi nhà. Vẽ chồng lên lớp tuyết."""
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("house.png"), (x, y))

def draw_santa(surf, x, y):
    """Vẽ tác nhân (Santa) trên ô hiện tại."""
    surf.blit(get_image("santa.png"), (x, y))

def draw_satan(surf, x, y):
    """Vẽ đối thủ (Satan) trên ô hiện tại."""
    surf.blit(get_image("satan.png"), (x, y))

class Button:
    """
    Một nút bấm GUI đơn giản với trạng thái di chuột (hover) và trạng thái đang chọn (active).
    """
    def __init__(self, rect, label, color=None, active=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color or GameConfig.C["btn"]
        self.active = active
        self.hovered = False

    def draw(self, surf):
        """Vẽ nút bấm lên bề mặt được cho."""
        # Xác định màu sắc hiện tại dựa trên trạng thái (active > hovered > default)
        col = GameConfig.C["btn_act"] if self.active else (GameConfig.C["btn_hover"] if self.hovered else self.color)
        
        # Vẽ nền và viền
        draw_rounded_rect(surf, col, self.rect, 8)
        border_col = GameConfig.C["accent"] if self.active else GameConfig.C["panel2"]
        pygame.draw.rect(surf, border_col, self.rect, 2, border_radius=8)
        
        # Vẽ chữ ở giữa nút
        text_col = GameConfig.C["white"] if self.active else GameConfig.C["text"]
        txt = font_sm.render(self.label, True, text_col)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        """Cập nhật trạng thái hover nếu con trỏ chuột nằm trong vùng của nút."""
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos):
        """Trả về True nếu nút được nhấp chuột."""
        return self.rect.collidepoint(pos)