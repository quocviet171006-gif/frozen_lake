import os
import pygame
from config import GameConfig, font_sm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES = {}

def get_image(filename):
    if filename not in IMAGES:
        path = os.path.join(BASE_DIR, "assets", filename)
        if os.path.exists(path):
            img = pygame.image.load(path)
            IMAGES[filename] = pygame.transform.scale(img, (GameConfig.CELL, GameConfig.CELL))
        else:
            IMAGES[filename] = pygame.Surface((GameConfig.CELL, GameConfig.CELL))
            IMAGES[filename].fill((255, 0, 255))
    return IMAGES[filename]

def draw_rounded_rect(surf, color, rect, radius=10, alpha=255):
    r = pygame.Rect(rect)
    shape_surf = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, (*color[:3], alpha), shape_surf.get_rect(), border_radius=radius)
    surf.blit(shape_surf, r.topleft)

def draw_snow_tile(surf, x, y, shade=0):
    surf.blit(get_image("snow.jpg"), (x, y))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_hole_tile(surf, x, y):
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("hole.png"), (x, y))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_mount_tile(surf, x, y):
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("mount.webp"), (x, y))

def draw_house_tile(surf, x, y):
    surf.blit(get_image("snow.jpg"), (x, y))
    surf.blit(get_image("house.png"), (x, y))

def draw_santa(surf, x, y):
    surf.blit(get_image("santa.png"), (x, y))

class Button:
    def __init__(self, rect, label, color=None, active=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color or GameConfig.C["btn"]
        self.active = active
        self.hovered = False

    def draw(self, surf):
        col = GameConfig.C["btn_act"] if self.active else (GameConfig.C["btn_hover"] if self.hovered else self.color)
        draw_rounded_rect(surf, col, self.rect, 8)
        pygame.draw.rect(surf, GameConfig.C["accent"] if self.active else GameConfig.C["panel2"], self.rect, 2, border_radius=8)
        txt = font_sm.render(self.label, True, GameConfig.C["white"] if self.active else GameConfig.C["text"])
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)
