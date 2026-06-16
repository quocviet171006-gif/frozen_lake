import pygame

class GameConfig:
    GRID = 8
    CELL = 72
    PANEL_W = 380
    W = GRID * CELL + PANEL_W
    H = GRID * CELL + 60
    FPS = 60

    # Tile types
    SNOW = 0
    HOLE = 1
    MOUNT = 2
    HOUSE = 4

    # Colors & palette
    C = {
        "bg":        (8,  18,  40),
        "snow1":     (210,230,245),
        "snow2":     (190,215,235),
        "hole":      (90, 170,210),
        "hole2":     (50, 130,180),
        "mount":     (120,100, 80),
        "mount2":    (160,140,110),
        "panel":     (15,  30,  65),
        "panel2":    (20,  40,  80),
        "accent":    (80, 160,255),
        "accent2":   (40, 100,200),
        "gold":      (255,210, 60),
        "red":       (220, 70, 70),
        "green":     (70, 200,100),
        "teal":      (60, 200,180),
        "text":      (220,235,255),
        "text2":     (140,170,210),
        "white":     (255,255,255),
        "btn":       (25,  50, 100),
        "btn_hover": (40,  80, 160),
        "btn_act":   (60, 120,220),
    }

    ALG_COLORS = {
        "BFS": (100,200,255), "DFS": (255,140, 60), "UCS": (100,240,140), 
        "Greedy": (255,100,200), "A*": (255,215, 0), "IDA*":  (218,165, 32),
        "Simple HC": (255,182,193), "Beam": (255,105,180), "Sim Ann": (255,69,0),
        "S-BFS": (147,112,219), "S-DFS": (186,85,211),
        "AND-OR Graph": (255,99,71),
        "Backtracking": (100,200,255), "Forward Check": (255,140, 60)
    }

pygame.init()
font_lg  = pygame.font.SysFont("consolas", 28, bold=True)
font_md  = pygame.font.SysFont("consolas", 18, bold=True)
font_sm  = pygame.font.SysFont("consolas", 13)
font_xs  = pygame.font.SysFont("consolas", 12)
