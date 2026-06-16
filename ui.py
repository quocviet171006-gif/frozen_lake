import pygame
from config import GameConfig, font_sm

def draw_rounded_rect(surf, color, rect, radius=10, alpha=255):
    r = pygame.Rect(rect)
    shape_surf = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, (*color[:3], alpha), shape_surf.get_rect(), border_radius=radius)
    surf.blit(shape_surf, r.topleft)

def draw_snow_tile(surf, x, y, shade=0):
    base = GameConfig.C["snow1"] if shade == 0 else GameConfig.C["snow2"]
    pygame.draw.rect(surf, base, (x,y,GameConfig.CELL,GameConfig.CELL))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_hole_tile(surf, x, y):
    pygame.draw.rect(surf, GameConfig.C["snow1"], (x,y,GameConfig.CELL,GameConfig.CELL))
    margin = 8
    pygame.draw.ellipse(surf, GameConfig.C["hole2"], (x+margin,y+margin,GameConfig.CELL-margin*2,GameConfig.CELL-margin*2))
    pygame.draw.ellipse(surf, GameConfig.C["hole"],  (x+margin+4,y+margin+4,GameConfig.CELL-margin*2-8,GameConfig.CELL-margin*2-8))
    pygame.draw.rect(surf, (180,205,225), (x,y,GameConfig.CELL,GameConfig.CELL), 1)

def draw_mount_tile(surf, x, y):
    pygame.draw.rect(surf, GameConfig.C["snow1"], (x,y,GameConfig.CELL,GameConfig.CELL))
    cx, cy = x+GameConfig.CELL//2, y+GameConfig.CELL//2
    pygame.draw.polygon(surf, GameConfig.C["mount2"], [(cx, cy-26), (cx-22, cy+20), (cx+22, cy+20)])
    pygame.draw.polygon(surf, GameConfig.C["mount"], [(cx+8, cy-8), (cx-14, cy+20), (cx+22, cy+20)])
    pygame.draw.polygon(surf, (240,250,255), [(cx, cy-26), (cx-8, cy-10), (cx+8, cy-10)])

def draw_house_tile(surf, x, y):
    draw_snow_tile(surf, x, y)
    cx,cy = x+GameConfig.CELL//2, y+GameConfig.CELL//2+4
    pygame.draw.rect(surf, (210,150,80), (cx-16,cy-6,32,20), border_radius=2)
    pygame.draw.polygon(surf, (180,60,60), [(cx,cy-22),(cx-20,cy-6),(cx+20,cy-6)])
    pygame.draw.rect(surf, (100,60,30), (cx-5,cy+2,10,12))

def draw_santa(surf, x, y):
    cx,cy = x+GameConfig.CELL//2, y+GameConfig.CELL//2
    pygame.draw.circle(surf, (200,40,40), (cx,cy+6), 12)
    pygame.draw.circle(surf, (255,200,160), (cx,cy-7), 10)
    pygame.draw.polygon(surf, (200,40,40), [(cx,cy-28),(cx-7,cy-16),(cx+7,cy-16)])
    pygame.draw.ellipse(surf, (240,240,240), (cx-8,cy-4,16,10))

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
