import pygame
import sys
import random
from enum import Enum
from config import GameConfig, font_lg, font_md, font_sm, font_xs
from ui import Button, draw_snow_tile, draw_hole_tile, draw_mount_tile, draw_house_tile, draw_santa, draw_rounded_rect
from environment import Environment
from algorithms import ALGORITHMS
from algorithms.csp import CSPGenerator

class GameState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    CSP_GEN = "csp_gen"

class FrozenLakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((GameConfig.W, GameConfig.H))
        pygame.display.set_caption("❄️ Frozen Lake AI – 6 Algorithm Groups")
        self.clock = pygame.time.Clock()

        self.grid = self.santa_start = self.house_pos = None
        
        self.group = 1
        self.alg_name = "BFS"
        self.state = GameState.IDLE

        self.anim_idx = self.anim_timer = 0
        self.anim_speed = 120
        self.santa_pos = None
        
        self.raw_path = [] 
        self.full_path = [] 
        self.visited_cells = []
        self.belief_state = None
        self.policy = None 
        
        self.log = []

        self.csp_generator = None
        self.csp_assignment = {}

        self._build_ui()
        # Fallback instant map gen
        self._instant_map_gen()

    def _instant_map_gen(self):
        gen = CSPGenerator.generate_map_backtracking()
        last_assignment = None
        for a in gen:
            last_assignment = a
            if len(last_assignment) == 18:
                break
        self._apply_assignment(last_assignment)
        self._reset_run()

    def _apply_assignment(self, res):
        if not res or len(res) < 18: return False
        items = ["Santa", "House"] + ["Hole"]*10 + ["Mount"]*6
        grid = [[GameConfig.SNOW]*GameConfig.GRID for _ in range(GameConfig.GRID)]
        s_pos = h_pos = None
        
        for i, val in res.items():
            r, c = val//GameConfig.GRID, val%GameConfig.GRID
            if items[i] == "Santa": s_pos = (r, c)
            elif items[i] == "House": 
                h_pos = (r, c)
                grid[r][c] = GameConfig.HOUSE
            elif items[i] == "Hole": 
                grid[r][c] = GameConfig.HOLE
            elif items[i] == "Mount": 
                grid[r][c] = GameConfig.MOUNT
            
        self.grid, self.santa_start, self.house_pos = grid, s_pos, h_pos
        return True

    def _build_ui(self):
        px = GameConfig.GRID*GameConfig.CELL + 12
        self.tabs = {}
        tab_names = ["1.Uninf", "2.Infor", "3.Local", "4.Sensr", "5.N-Det", "6.CSP"]
        for i in range(6):
            # Fit 3 in a row
            col = i % 3
            row = i // 3
            self.tabs[i+1] = Button((px + col*115, 45 + row*32, 110, 28), tab_names[i])
            
        self.btns_alg = {}
        self._update_alg_buttons()
        self.btn_run = Button((px, 200, 345, 36), "▶ Run Algorithm")

    def _update_alg_buttons(self):
        px = GameConfig.GRID*GameConfig.CELL + 12
        self.btns_alg.clear()
        algs = list(ALGORITHMS[self.group].keys())
        for i, a in enumerate(algs):
            col = i % 2; row = i // 2
            self.btns_alg[a] = Button((px + col * 180, 120 + row * 36, 165, 30), a, active=(a==self.alg_name))
        if algs and self.alg_name not in algs:
            self.alg_name = algs[0]
            self.btns_alg[self.alg_name].active = True

    def _reset_run(self):
        self.state = GameState.IDLE
        self.santa_pos = self.santa_start
        self.full_path, self.visited_cells = [], []
        self.raw_path = []
        self.belief_state = None
        self.policy = None
        self.anim_idx = self.anim_timer = 0
        self.csp_generator = None
        if "Map" not in self.log[-1] if self.log else True:
            self.log = ["Press ▶ Run to start."]

    def _get_alg_result(self, alg_fn, initial_state):
        Environment.ALLOW_HOLES = False
        res, vis = alg_fn(self.grid, initial_state, self.house_pos)
        if res:
            return res, vis
        self.log.append("Không thể né hố. Chấp nhận rủi ro!")
        Environment.ALLOW_HOLES = True
        return alg_fn(self.grid, initial_state, self.house_pos)

    def run_algorithm(self):
        if self.group == 6:
            self.state = GameState.CSP_GEN
            self.csp_generator = ALGORITHMS[self.group][self.alg_name]()
            self.log = [f"Generating map using {self.alg_name}"]
            return

        if self.grid is None: return
        self._reset_run()
        alg_fn = ALGORITHMS[self.group][self.alg_name]
        initial_state = (self.santa_start[0], self.santa_start[1])
        
        if self.group == 4:
            Environment.ALLOW_HOLES = True
            path_actions, visited_beliefs = alg_fn(self.grid, initial_state, self.house_pos)
            if path_actions:
                self.raw_path = path_actions
                self.visited_cells = visited_beliefs
                self.belief_state = Environment.get_initial_belief(self.grid)
                self.state = GameState.RUNNING
                self.log.append(f"[{self.alg_name}] Plan: {len(path_actions)} steps")
            else:
                self.log.append("No plan found!")
        elif self.group == 5:
            Environment.ALLOW_HOLES = True
            policy, visited = alg_fn(self.grid, initial_state, self.house_pos)
            if policy:
                self.policy = policy
                self.visited_cells = visited
                self.state = GameState.RUNNING
                self.log.append(f"[{self.alg_name}] Policy generated")
            else:
                self.log.append("No policy found!")
        else:
            if self.group == 3:
                Environment.ALLOW_HOLES = True
                raw_path, raw_visited = alg_fn(self.grid, initial_state, self.house_pos)
            else:
                raw_path, raw_visited = self._get_alg_result(alg_fn, initial_state)
                
            if raw_path:
                self.full_path = [(s[0], s[1]) for s in raw_path]
                self.visited_cells = [(s[0], s[1]) for s in raw_visited]
                self.state = GameState.RUNNING
                self.log.append(f"[{self.alg_name}] Path: {len(self.full_path)} steps")
            else:
                self.log.append("No path found or stuck!")

    def _advance_step(self):
        if self.state == GameState.CSP_GEN:
            try:
                self.csp_assignment = next(self.csp_generator)
            except StopIteration:
                if self._apply_assignment(self.csp_assignment):
                    self.log.append("CSP Map Generated successfully.")
                else:
                    self.log.append("CSP Map Gen Failed!")
                self._reset_run()
            return

        if self.group == 4:
            if self.anim_idx >= len(self.raw_path):
                self._finish_game()
                return
            a = self.raw_path[self.anim_idx]
            self.belief_state = Environment.sensorless_transition(self.grid, self.belief_state, a)
            
            act_map = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
            dr, dc = act_map[a]
            r, c = self.santa_pos
            if self.grid[r][c] == GameConfig.HOLE:
                adr, adc = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
            else:
                adr, adc = dr, dc
                
            nr, nc = r + adr, c + adc
            if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                self.santa_pos = (nr, nc)
                
            self.anim_idx += 1
            return

        if self.group == 5:
            if self.santa_pos == self.house_pos:
                self._finish_game()
                return
            if self.santa_pos not in self.policy:
                self.log.append("Stuck! No policy for state.")
                self.state = GameState.DONE
                return
            
            a = self.policy[self.santa_pos]
            act_map = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
            dr, dc = act_map[a]
            r, c = self.santa_pos
            
            if self.grid[r][c] == GameConfig.HOLE:
                adr, adc = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
                nr, nc = r + adr, c + adc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                    self.santa_pos = (nr, nc)
                self.log.append(f"Slip Action: {a}")
            else:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                    self.santa_pos = (nr, nc)
                self.log.append(f"Action: {a}")
        else:
            if self.anim_idx >= len(self.full_path) - 1:
                self._finish_game()
                return
            
            curr_pos = self.santa_pos
            next_planned = self.full_path[self.anim_idx + 1]
            dr = max(-1, min(1, next_planned[0] - curr_pos[0]))
            dc = max(-1, min(1, next_planned[1] - curr_pos[1]))
            
            if self.grid[curr_pos[0]][curr_pos[1]] == GameConfig.HOLE and (dr != 0 or dc != 0):
                adr, adc = random.choice([(-1,0), (1,0), (0,-1), (0,1)])
                
                nr, nc = curr_pos[0] + adr, curr_pos[1] + adc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                    actual_next = (nr, nc)
                else:
                    actual_next = curr_pos
            else:
                actual_next = next_planned

            self.santa_pos = actual_next
            
            if self.santa_pos == self.house_pos:
                self._finish_game()
                return
            
            if actual_next != next_planned:
                self.log.append("💧 Lệch hướng! Tính toán lại...")
                alg_fn = ALGORITHMS[self.group][self.alg_name]
                
                if self.group == 3:
                    Environment.ALLOW_HOLES = True
                    raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)
                else:
                    Environment.ALLOW_HOLES = False
                    raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)
                    if not raw_path or len(raw_path) <= 1:
                        Environment.ALLOW_HOLES = True
                        raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)

                if raw_path and len(raw_path) > 1:
                    self.full_path = [(s[0], s[1]) for s in raw_path]
                    self.anim_idx = 0
                    self.visited_cells.append(actual_next)
                    self.log.append(f"[{self.alg_name}] Path mới: {len(self.full_path)} bước")
                else:
                    self.log.append("Kẹt! Không tìm thấy đường!")
                    self.state = GameState.DONE
                return
            else:
                self.anim_idx += 1

        # Calculate events
        pos = self.santa_pos
        tile = self.grid[pos[0]][pos[1]]
        
        if tile == GameConfig.HOLE:
            self.log.append(f"💧 Rớt hố!")

        if pos == self.house_pos and (self.group == 5 or self.anim_idx == len(self.full_path)-1):
            self._finish_game()

    def _finish_game(self):
        self.state = GameState.DONE
        self.log.append(f"🏠 Home! (Hoàn thành)")

    def draw(self):
        self.screen.fill(GameConfig.C["bg"])
        for r in range(GameConfig.GRID):
            for c in range(GameConfig.GRID):
                draw_snow_tile(self.screen, c*GameConfig.CELL, r*GameConfig.CELL, (r+c) % 2)

        if self.state == GameState.CSP_GEN:
            self._draw_csp()
        else:
            if self.group == 4 and self.belief_state:
                bsurf = pygame.Surface((GameConfig.CELL, GameConfig.CELL), pygame.SRCALPHA)
                pygame.draw.rect(bsurf, (147,112,219, 120), (0,0,GameConfig.CELL,GameConfig.CELL))
                for (br, bc) in self.belief_state:
                    self.screen.blit(bsurf, (bc*GameConfig.CELL, br*GameConfig.CELL))
            elif self.group == 5 and self.policy:
                psurf = pygame.Surface((GameConfig.GRID*GameConfig.CELL, GameConfig.GRID*GameConfig.CELL), pygame.SRCALPHA)
                for (pr, pc), a in self.policy.items():
                    cx, cy = pc*GameConfig.CELL+36, pr*GameConfig.CELL+36
                    act_map = {"Up": (0,-16), "Down": (0,16), "Left": (-16,0), "Right": (16,0)}
                    dx, dy = act_map[a]
                    pygame.draw.line(psurf, (255,99,71, 200), (cx, cy), (cx+dx, cy+dy), 4)
                    pygame.draw.circle(psurf, (255,99,71, 200), (cx+dx, cy+dy), 4)
                self.screen.blit(psurf, (0,0))
            else:
                self._draw_paths()
                
            self._draw_tiles()
            self._draw_santa()
                
        self._draw_panel()
        self._draw_bottom_bar()
        pygame.display.flip()

    def _draw_csp(self):
        items = ["Santa", "House"] + ["Hole"]*10 + ["Mount"]*6
        for i, val in self.csp_assignment.items():
            r, c = val//GameConfig.GRID, val%GameConfig.GRID
            x, y = c*GameConfig.CELL, r*GameConfig.CELL
            if items[i] == "Santa": draw_santa(self.screen, x, y)
            elif items[i] == "House": draw_house_tile(self.screen, x, y)
            elif items[i] == "Hole": draw_hole_tile(self.screen, x, y)
            elif items[i] == "Mount": draw_mount_tile(self.screen, x, y)

    def _draw_paths(self):
        if not self.full_path: return
        path_surf = pygame.Surface((GameConfig.GRID*GameConfig.CELL, GameConfig.GRID*GameConfig.CELL), pygame.SRCALPHA)
        pc = GameConfig.ALG_COLORS.get(self.alg_name, (255,255,255))
        for pos in self.visited_cells[:max(0, self.anim_idx*3)]:
            pygame.draw.rect(path_surf, (*pc, 25), (pos[1]*GameConfig.CELL+2,pos[0]*GameConfig.CELL+2,GameConfig.CELL-4,GameConfig.CELL-4), border_radius=4)
        for i in range(1, len(self.full_path)):
            r1,c1 = self.full_path[i-1]; r2,c2 = self.full_path[i]
            alpha = 60 if i > self.anim_idx else 200
            pygame.draw.line(path_surf, (*pc, alpha), (c1*GameConfig.CELL+36, r1*GameConfig.CELL+36),(c2*GameConfig.CELL+36, r2*GameConfig.CELL+36), 4)
        self.screen.blit(path_surf, (0,0))

    def _draw_tiles(self):
        if not self.grid: return
        for r in range(GameConfig.GRID):
            for c in range(GameConfig.GRID):
                t, x, y = self.grid[r][c], c*GameConfig.CELL, r*GameConfig.CELL
                if t == GameConfig.HOLE: draw_hole_tile(self.screen, x, y)
                elif t == GameConfig.MOUNT: draw_mount_tile(self.screen, x, y)
                elif t == GameConfig.HOUSE: draw_house_tile(self.screen, x, y)

    def _draw_santa(self):
        if self.santa_pos: draw_santa(self.screen, self.santa_pos[1]*GameConfig.CELL, self.santa_pos[0]*GameConfig.CELL)

    def _draw_panel(self):
        px, ox = GameConfig.GRID*GameConfig.CELL, GameConfig.GRID*GameConfig.CELL + 12
        draw_rounded_rect(self.screen, GameConfig.C["panel"], (px,0,GameConfig.PANEL_W,GameConfig.H), 0)
        self.screen.blit(font_md.render("FROZEN LAKE", True, GameConfig.C["accent"]), (ox, 8))
        self.screen.blit(font_xs.render("ALGORITHM GROUPS", True, GameConfig.C["text2"]), (ox, 28))

        for g, btn in self.tabs.items():
            btn.active = (g == self.group); btn.draw(self.screen)
            
        for a, btn in self.btns_alg.items():
            btn.active = (a == self.alg_name); btn.draw(self.screen)
            
        self.btn_run.draw(self.screen)

        y_stat = self.btn_run.rect.bottom + 20
        def stat_row(lbl, val, col):
            nonlocal y_stat
            self.screen.blit(font_xs.render(lbl, True, GameConfig.C["text2"]), (ox, y_stat))
            self.screen.blit(font_sm.render(str(val), True, col), (ox+120, y_stat))
            y_stat += 22
        stat_row("State:", self.state.value.upper(), GameConfig.C["green"] if self.state==GameState.DONE else GameConfig.C["accent"])

        y_log = y_stat + 10
        self.screen.blit(font_xs.render("LOG", True, GameConfig.C["text2"]), (ox, y_log))
        y_log += 16
        for line in self.log[-10:]:
            self.screen.blit(font_xs.render(line, True, GameConfig.C["text2"]), (ox, y_log))
            y_log += 15

    def _draw_bottom_bar(self):
        y = GameConfig.GRID*GameConfig.CELL
        pygame.draw.rect(self.screen, GameConfig.C["panel"], (0,y,GameConfig.GRID*GameConfig.CELL,60))
        self.screen.blit(font_lg.render("FROZEN LAKE", True, GameConfig.C["text"]), (12, y+14))
        self.screen.blit(font_md.render(self.alg_name, True, GameConfig.ALG_COLORS.get(self.alg_name, GameConfig.C["white"])), (380, y+16))

    def run(self):
        while True:
            dt = self.clock.tick(GameConfig.FPS)
            mouse = pygame.mouse.get_pos()
            for btn in list(self.tabs.values()) + list(self.btns_alg.values()) + [self.btn_run]: 
                btn.check_hover(mouse)

            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for g, btn in self.tabs.items():
                        if btn.clicked(mouse): 
                            self.group = g
                            self._update_alg_buttons()
                            self._reset_run()
                    for a, btn in self.btns_alg.items():
                        if btn.clicked(mouse): 
                            self.alg_name = a; self._reset_run()
                    if self.btn_run.clicked(mouse): self.run_algorithm()

            if self.state in [GameState.RUNNING, GameState.CSP_GEN]:
                self.anim_timer += dt
                # Faster animation for CSP
                speed = 20 if self.state == GameState.CSP_GEN else self.anim_speed
                if self.anim_timer >= speed:
                    self.anim_timer = 0
                    self._advance_step()
            self.draw()
