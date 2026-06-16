import pygame
import sys
import random
import time
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
        pygame.display.set_caption("Frozen Lake AI - 6 Algorithm Groups")
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
        self.path_log = []   # luu duong di toa do sau moi lan chay
        self.replan_count = 0
        self.log_scroll = 0  # so dong cuon tu cuoi len (0 = thay cuoi)

        # -- Thống kê --------------------------------------------------------
        self.stats = {
            "nodes_expanded": 0,
            "path_length":    0,
            "elapsed_ms":     0.0,
            "replan_count":   0,
        }

        self.csp_generator = None
        self.csp_assignment = {}

        self._build_ui()
        # Tạo map ngay lúc khởi động
        self._instant_map_gen()

    # -- Tạo bản đồ ----------------------------------------------------------
    def _instant_map_gen(self):
        """Tạo map ngay lập tức bằng CSP backtracking (không animate)."""
        gen = CSPGenerator.generate_map_backtracking()
        last_assignment = {}
        for a in gen:
            last_assignment = a
            # Dừng sớm khi đã có đủ 18 biến
            if len(last_assignment) == 18:
                break
        if self._apply_assignment(last_assignment):
            self.log = [f"[MAP] Map mới tạo xong! ({GameConfig.GRID}x{GameConfig.GRID})"]
        else:
            self.log = ["[ERR] Tạo map thất bại, thử lại!"]
        self._reset_run()

    def _apply_assignment(self, res):
        if not res or len(res) < 18:
            return False
        items = ["Santa", "House"] + ["Hole"] * 10 + ["Mount"] * 6
        grid = [[GameConfig.SNOW] * GameConfig.GRID for _ in range(GameConfig.GRID)]
        s_pos = h_pos = None

        for i, val in res.items():
            r, c = val // GameConfig.GRID, val % GameConfig.GRID
            if items[i] == "Santa":
                s_pos = (r, c)
            elif items[i] == "House":
                h_pos = (r, c)
                grid[r][c] = GameConfig.HOUSE
            elif items[i] == "Hole":
                grid[r][c] = GameConfig.HOLE
            elif items[i] == "Mount":
                grid[r][c] = GameConfig.MOUNT

        self.grid, self.santa_start, self.house_pos = grid, s_pos, h_pos
        return True

    # -- Xây UI --------------------------------------------------------------
    def _build_ui(self):
        px = GameConfig.GRID * GameConfig.CELL + 12
        self.tabs = {}
        tab_names = ["1.Uninf", "2.Infor", "3.Local", "4.Sensr", "5.N-Det", "6.CSP"]
        for i in range(6):
            col = i % 3
            row = i // 3
            self.tabs[i + 1] = Button((px + col * 115, 45 + row * 32, 110, 28), tab_names[i])

        self.btns_alg = {}
        self._update_alg_buttons()

        self.btn_run = Button((px, 200, 345, 36), "> Run Algorithm")
        self.btn_new_map = Button((px, 242, 345, 32), "[MAP] Generate New Map")

    def _update_alg_buttons(self):
        px = GameConfig.GRID * GameConfig.CELL + 12
        self.btns_alg.clear()
        algs = list(ALGORITHMS[self.group].keys())
        for i, a in enumerate(algs):
            col = i % 2
            row = i // 2
            self.btns_alg[a] = Button((px + col * 180, 120 + row * 36, 165, 30), a, active=(a == self.alg_name))
        if algs and self.alg_name not in algs:
            self.alg_name = algs[0]
            self.btns_alg[self.alg_name].active = True

    # -- Reset ----------------------------------------------------------------
    def _reset_run(self):
        self.state = GameState.IDLE
        self.santa_pos = self.santa_start
        self.full_path, self.visited_cells = [], []
        self.raw_path = []
        self.belief_state = None
        self.policy = None
        self.anim_idx = self.anim_timer = 0
        self.csp_generator = None
        self.replan_count = 0
        self.stats = {
            "nodes_expanded": 0,
            "path_length":    0,
            "elapsed_ms":     0.0,
            "replan_count":   0,
        }
        if self.log and "Map" not in self.log[-1]:
            self.log = ["Press > Run to start."]
        self.path_log = []

    # -- Helper tìm đường -----------------------------------------------------
    def _get_alg_result(self, alg_fn, initial_state):
        """Gọi algorithm, thử tránh hố trước, fallback cho phép hố."""
        Environment.ALLOW_HOLES = False
        res, vis = alg_fn(self.grid, initial_state, self.house_pos)
        if res:
            return res, vis
        self.log.append("Không thể né hố -> chấp nhận rủi ro!")
        Environment.ALLOW_HOLES = True
        return alg_fn(self.grid, initial_state, self.house_pos)

    @staticmethod
    def _pos_to_dir(p1, p2):
        """Chuyển 2 ô liên tiếp thành mũi tên kèm chữ hướng đi."""
        dr = p2[0] - p1[0]
        dc = p2[1] - p1[1]
        return {(-1, 0): "UP", (1, 0): "DOWN", (0, -1): "LEFT", (0, 1): "RIGHT"}.get((dr, dc), "?")

    def _log_path(self, path, alg_name):
        self.path_log = list(path)
        if not path:
            self.log.append("[ERR] Không có đường đi!")
            return

        n = len(path)
        s, e = path[0], path[-1]
        self.log.append(f"[OK] [{alg_name}]  {n-1} steps  ({s[0]},{s[1]}) -> ({e[0]},{e[1]})")

        # Tạo chuỗi hướng đi
        dirs = [self._pos_to_dir(path[i], path[i+1]) for i in range(n - 1)]

        # Chia thành chunk 5 hướng mỗi dòng (vì mỗi từ dài hơn)
        CHUNK = 5
        for start in range(0, len(dirs), CHUNK):
            chunk = dirs[start:start + CHUNK]
            line = " -> ".join(chunk)
            if start + CHUNK < len(dirs):
                line += " ->"
            self.log.append(line)

    def _do_replan(self):
        """
        Tính lại đường đi từ vị trí hiện tại của Santa.
        Có giới hạn MAX_REPLAN lần để tránh loop vô hạn.
        """
        MAX_REPLAN = 10
        if self.replan_count >= MAX_REPLAN:
            self.log.append(f"[STOP] Đã replan {MAX_REPLAN} lần — dừng lại!")
            self.state = GameState.DONE
            return False

        alg_fn = ALGORITHMS[self.group][self.alg_name]

        # Thử tránh hố trước
        Environment.ALLOW_HOLES = False
        raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)

        # Fallback: cho phép đi qua hố
        if not raw_path or len(raw_path) <= 1:
            Environment.ALLOW_HOLES = True
            raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)

        if raw_path and len(raw_path) > 1:
            self.full_path = [(s[0], s[1]) for s in raw_path]
            self.anim_idx = 0
            self.replan_count += 1
            self.stats["replan_count"] = self.replan_count
            self.log.append(f"[Replan #{self.replan_count}] {len(self.full_path)} bước")
            return True
        else:
            self.log.append("[DEAD] Kẹt! Không tìm thấy đường!")
            self.state = GameState.DONE
            return False

    # -- Chạy thuật toán ------------------------------------------------------
    def run_algorithm(self):
        if self.group == 6:
            self.state = GameState.CSP_GEN
            self.csp_generator = ALGORITHMS[self.group][self.alg_name]()
            self.log = [f"Generating map using {self.alg_name}"]
            return

        if self.grid is None:
            return
        self._reset_run()
        alg_fn = ALGORITHMS[self.group][self.alg_name]
        initial_state = (self.santa_start[0], self.santa_start[1])

        t0 = time.perf_counter()

        if self.group == 4:
            # Sensorless
            Environment.ALLOW_HOLES = True
            path_actions, visited_beliefs = alg_fn(self.grid, initial_state, self.house_pos)
            elapsed = (time.perf_counter() - t0) * 1000
            if path_actions:
                self.raw_path = path_actions
                self.visited_cells = visited_beliefs
                self.belief_state = Environment.get_initial_belief(self.grid)
                self.state = GameState.RUNNING
                self.stats.update({
                    "nodes_expanded": len(visited_beliefs),
                    "path_length":    len(path_actions),
                    "elapsed_ms":     elapsed,
                })
                self.log.append(
                    f"[{self.alg_name}] Plan:{len(path_actions)} | "
                    f"Nodes:{len(visited_beliefs)} | {elapsed:.1f}ms"
                )
                # Log actions dạng chữ - toàn bộ chuỗi bước
                ACT_DIR = {"Up": "UP", "Down": "DOWN", "Left": "LEFT", "Right": "RIGHT"}
                seq = [ACT_DIR.get(a, a) for a in path_actions]
                self.log.append(f"[OK] [{self.alg_name}]  {len(seq)} steps:")
                CHUNK = 5
                for st in range(0, len(seq), CHUNK):
                    chunk = seq[st:st+CHUNK]
                    line = " -> ".join(chunk)
                    if st + CHUNK < len(seq):
                        line += " ->"
                    self.log.append(line)
                self.path_log = list(path_actions)
            else:
                self.log.append("No plan found!")

        elif self.group == 5:
            # Non-deterministic
            Environment.ALLOW_HOLES = True
            policy, visited = alg_fn(self.grid, initial_state, self.house_pos)
            elapsed = (time.perf_counter() - t0) * 1000
            if policy:
                self.policy = policy
                self.visited_cells = visited
                self.state = GameState.RUNNING
                self.stats.update({
                    "nodes_expanded": len(visited),
                    "path_length":    len(policy),
                    "elapsed_ms":     elapsed,
                })
                self.log.append(
                    f"[{self.alg_name}] Policy:{len(policy)} states | "
                    f"Nodes:{len(visited)} | {elapsed:.1f}ms"
                )
                # Reconstruct chuỗi hướng đi từ policy (simulate từ start)
                ACT_DIR = {"Up": "UP", "Down": "DOWN", "Left": "LEFT", "Right": "RIGHT"}
                ACT_MAP = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
                seq, cur, seen = [], initial_state, {initial_state}
                while cur in policy and cur != self.house_pos and len(seq) < 30:
                    a = policy[cur]
                    seq.append(ACT_DIR.get(a, a))
                    dr2, dc2 = ACT_MAP[a]
                    cur = (cur[0]+dr2, cur[1]+dc2)
                    if cur in seen:
                        break
                    seen.add(cur)
                self.log.append(f"[OK] [{self.alg_name}]  {len(seq)} steps:")
                CHUNK = 5
                for st in range(0, len(seq), CHUNK):
                    chunk = seq[st:st+CHUNK]
                    line = " -> ".join(chunk)
                    if st + CHUNK < len(seq):
                        line += " ->"
                    self.log.append(line)
                self.path_log = []
            else:
                self.log.append("No policy found!")

        else:
            # Group 1, 2, 3
            if self.group == 3:
                Environment.ALLOW_HOLES = True
                raw_path, raw_visited = alg_fn(self.grid, initial_state, self.house_pos)
            else:
                raw_path, raw_visited = self._get_alg_result(alg_fn, initial_state)

            elapsed = (time.perf_counter() - t0) * 1000

            if raw_path:
                self.full_path = [(s[0], s[1]) for s in raw_path]
                self.visited_cells = [(s[0], s[1]) for s in raw_visited]
                self.state = GameState.RUNNING
                self.stats.update({
                    "nodes_expanded": len(raw_visited),
                    "path_length":    len(self.full_path),
                    "elapsed_ms":     elapsed,
                })
                self.log.append(
                    f"[{self.alg_name}] Path:{len(self.full_path)} | "
                    f"Nodes:{len(raw_visited)} | {elapsed:.1f}ms"
                )
                # Log đường đi tọa độ
                self._log_path(self.full_path, self.alg_name)
            else:
                self.log.append("No path found or stuck!")

    # -- Advance animation step ------------------------------------------------
    def _advance_step(self):
        # CSP generation mode
        if self.state == GameState.CSP_GEN:
            try:
                self.csp_assignment = next(self.csp_generator)
            except StopIteration:
                if self._apply_assignment(self.csp_assignment):
                    self.log.append("[OK] CSP Map Generated successfully.")
                else:
                    self.log.append("[ERR] CSP Map Gen Failed!")
                self._reset_run()
            return

        # Group 4: Sensorless
        if self.group == 4:
            if self.anim_idx >= len(self.raw_path):
                self._finish_game()
                return
            a = self.raw_path[self.anim_idx]
            self.belief_state = Environment.sensorless_transition(self.grid, self.belief_state, a)
            act_map = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
            dr, dc = act_map[a]
            r, c = self.santa_pos
            if self.grid[r][c] == GameConfig.HOLE:
                adr, adc = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            else:
                adr, adc = dr, dc
            nr, nc = r + adr, c + adc
            if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                self.santa_pos = (nr, nc)
            self.anim_idx += 1
            return

        # Group 5: Non-deterministic policy
        if self.group == 5:
            if self.santa_pos == self.house_pos:
                self._finish_game()
                return
            if self.santa_pos not in self.policy:
                self.log.append("Stuck! No policy for state.")
                self.state = GameState.DONE
                return
            a = self.policy[self.santa_pos]
            act_map = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
            dr, dc = act_map[a]
            r, c = self.santa_pos
            if self.grid[r][c] == GameConfig.HOLE:
                adr, adc = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
                nr, nc = r + adr, c + adc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                    self.santa_pos = (nr, nc)
                self.log.append(f"[~] Slip -> {a}")
            else:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and self.grid[nr][nc] != GameConfig.MOUNT:
                    self.santa_pos = (nr, nc)
                self.log.append(f"-> {a}")
            return

        # Group 1, 2, 3: Path-following với replanning
        if self.anim_idx >= len(self.full_path) - 1:
            self._finish_game()
            return

        curr_pos = self.santa_pos
        next_planned = self.full_path[self.anim_idx + 1]
        dr = max(-1, min(1, next_planned[0] - curr_pos[0]))
        dc = max(-1, min(1, next_planned[1] - curr_pos[1]))

        # Kiểm tra xem Santa có đang ở hố không (trượt ngẫu nhiên)
        if self.grid[curr_pos[0]][curr_pos[1]] == GameConfig.HOLE and (dr != 0 or dc != 0):
            adr, adc = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
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

        # Nếu lệch hướng -> replan
        if actual_next != next_planned:
            self.log.append("[~] Lệch hướng! Tính toán lại...")
            self.visited_cells.append(actual_next)

            if self.group == 3:
                # Local search: luôn allow holes
                Environment.ALLOW_HOLES = True
                alg_fn = ALGORITHMS[self.group][self.alg_name]
                raw_path, _ = alg_fn(self.grid, self.santa_pos, self.house_pos)
                if raw_path and len(raw_path) > 1:
                    self.full_path = [(s[0], s[1]) for s in raw_path]
                    self.anim_idx = 0
                    self.replan_count += 1
                    self.stats["replan_count"] = self.replan_count
                else:
                    self.state = GameState.DONE
            else:
                self._do_replan()
            return
        else:
            self.anim_idx += 1

        # Log nếu rơi hố
        pos = self.santa_pos
        if self.grid[pos[0]][pos[1]] == GameConfig.HOLE:
            self.log.append("[~] Rớt hố!")

        if pos == self.house_pos and (self.group == 5 or self.anim_idx == len(self.full_path) - 1):
            self._finish_game()

    def _finish_game(self):
        self.state = GameState.DONE
        self.log.append(
            f"[HOME] Hoàn thành! Path:{self.stats['path_length']} | "
            f"Nodes:{self.stats['nodes_expanded']} | "
            f"Replans:{self.stats['replan_count']}"
        )

    # -- Draw -----------------------------------------------------------------
    def draw(self):
        self.screen.fill(GameConfig.C["bg"])
        for r in range(GameConfig.GRID):
            for c in range(GameConfig.GRID):
                draw_snow_tile(self.screen, c * GameConfig.CELL, r * GameConfig.CELL, (r + c) % 2)

        if self.state == GameState.CSP_GEN:
            self._draw_csp()
        else:
            if self.group == 4 and self.belief_state:
                bsurf = pygame.Surface((GameConfig.CELL, GameConfig.CELL), pygame.SRCALPHA)
                pygame.draw.rect(bsurf, (147, 112, 219, 120), (0, 0, GameConfig.CELL, GameConfig.CELL))
                for (br, bc) in self.belief_state:
                    self.screen.blit(bsurf, (bc * GameConfig.CELL, br * GameConfig.CELL))
            elif self.group == 5 and self.policy:
                psurf = pygame.Surface(
                    (GameConfig.GRID * GameConfig.CELL, GameConfig.GRID * GameConfig.CELL), pygame.SRCALPHA
                )
                for (pr, pc), a in self.policy.items():
                    cx, cy = pc * GameConfig.CELL + 36, pr * GameConfig.CELL + 36
                    act_map = {"Up": (0, -16), "Down": (0, 16), "Left": (-16, 0), "Right": (16, 0)}
                    dx, dy = act_map[a]
                    pygame.draw.line(psurf, (255, 99, 71, 200), (cx, cy), (cx + dx, cy + dy), 4)
                    pygame.draw.circle(psurf, (255, 99, 71, 200), (cx + dx, cy + dy), 4)
                self.screen.blit(psurf, (0, 0))
            else:
                self._draw_paths()

            self._draw_tiles()
            self._draw_santa()

        self._draw_panel()
        self._draw_bottom_bar()
        pygame.display.flip()

    def _draw_csp(self):
        items = ["Santa", "House"] + ["Hole"] * 10 + ["Mount"] * 6
        for i, val in self.csp_assignment.items():
            r, c = val // GameConfig.GRID, val % GameConfig.GRID
            x, y = c * GameConfig.CELL, r * GameConfig.CELL
            if items[i] == "Santa":
                draw_santa(self.screen, x, y)
            elif items[i] == "House":
                draw_house_tile(self.screen, x, y)
            elif items[i] == "Hole":
                draw_hole_tile(self.screen, x, y)
            elif items[i] == "Mount":
                draw_mount_tile(self.screen, x, y)

    def _draw_paths(self):
        if not self.full_path:
            return
        path_surf = pygame.Surface(
            (GameConfig.GRID * GameConfig.CELL, GameConfig.GRID * GameConfig.CELL), pygame.SRCALPHA
        )
        pc = GameConfig.ALG_COLORS.get(self.alg_name, (255, 255, 255))
        for pos in self.visited_cells[:max(0, self.anim_idx * 3)]:
            pygame.draw.rect(
                path_surf, (*pc, 25),
                (pos[1] * GameConfig.CELL + 2, pos[0] * GameConfig.CELL + 2,
                 GameConfig.CELL - 4, GameConfig.CELL - 4),
                border_radius=4
            )
        for i in range(1, len(self.full_path)):
            r1, c1 = self.full_path[i - 1]
            r2, c2 = self.full_path[i]
            alpha = 60 if i > self.anim_idx else 200
            pygame.draw.line(
                path_surf, (*pc, alpha),
                (c1 * GameConfig.CELL + 36, r1 * GameConfig.CELL + 36),
                (c2 * GameConfig.CELL + 36, r2 * GameConfig.CELL + 36),
                4
            )
        self.screen.blit(path_surf, (0, 0))

    def _draw_tiles(self):
        if not self.grid:
            return
        for r in range(GameConfig.GRID):
            for c in range(GameConfig.GRID):
                t, x, y = self.grid[r][c], c * GameConfig.CELL, r * GameConfig.CELL
                if t == GameConfig.HOLE:
                    draw_hole_tile(self.screen, x, y)
                elif t == GameConfig.MOUNT:
                    draw_mount_tile(self.screen, x, y)
                elif t == GameConfig.HOUSE:
                    draw_house_tile(self.screen, x, y)

    def _draw_santa(self):
        if self.santa_pos:
            draw_santa(self.screen, self.santa_pos[1] * GameConfig.CELL, self.santa_pos[0] * GameConfig.CELL)

    # -- Helper chon mau dong log (xem _draw_panel moi ben duoi) ----------

    # -- Helper chon mau dong log --------------------------------------------
    @staticmethod
    def _log_color(line, C):
        """Tra ve mau RGB phu hop voi noi dung dong log."""
        if line.startswith("[OK]"):
            return C["gold"]
        if line.startswith(("[ERR]", "[STOP]", "[DEAD]")):
            return C["red"]
        if line.startswith("[~]") or "Replan" in line:
            return C["teal"]
        if line.startswith("[HOME]"):
            return C["green"]
        # dong huong di: bat dau bang UP/DOWN/LEFT/RIGHT
        if line and line.split()[0] in ("UP", "DOWN", "LEFT", "RIGHT"):
            return C["accent"]
        # dong toa do: bat dau bang '(' va co '->'
        if line and line[0] == "(" and "->" in line:
            return C["accent"]
        return C["text2"]

    def _draw_panel(self):
        px = GameConfig.GRID * GameConfig.CELL
        ox = px + 12
        draw_rounded_rect(self.screen, GameConfig.C["panel"], (px, 0, GameConfig.PANEL_W, GameConfig.H), 0)
        self.screen.blit(font_md.render("FROZEN LAKE", True, GameConfig.C["accent"]), (ox, 8))
        self.screen.blit(font_xs.render("ALGORITHM GROUPS", True, GameConfig.C["text2"]), (ox, 28))

        for g, btn in self.tabs.items():
            btn.active = (g == self.group)
            btn.draw(self.screen)

        for a, btn in self.btns_alg.items():
            btn.active = (a == self.alg_name)
            btn.draw(self.screen)

        self.btn_run.draw(self.screen)
        self.btn_new_map.draw(self.screen)

        # -- Stats section --------------------------------------------------
        y_stat = self.btn_new_map.rect.bottom + 14

        def stat_row(lbl, val, col):
            nonlocal y_stat
            self.screen.blit(font_xs.render(lbl, True, GameConfig.C["text2"]), (ox, y_stat))
            self.screen.blit(font_sm.render(str(val), True, col), (ox + 120, y_stat))
            y_stat += 20

        state_col = GameConfig.C["green"] if self.state == GameState.DONE else GameConfig.C["accent"]
        stat_row("State:",     self.state.value.upper(), state_col)
        stat_row("Nodes exp:", self.stats["nodes_expanded"], GameConfig.C["teal"])
        stat_row("Path len:",  self.stats["path_length"],    GameConfig.C["green"])
        stat_row("Time(ms):",  f"{self.stats['elapsed_ms']:.1f}", GameConfig.C["gold"])
        stat_row("Replans:",   self.stats["replan_count"],   GameConfig.C["red"])

        # -- Log section (scrollable) ----------------------------------------
        LINE_H   = 14          # chieu cao moi dong log (px)
        LOG_X    = ox          # cot ben trai log
        LOG_W    = GameConfig.PANEL_W - 24   # chieu rong vung log
        LOG_TOP  = y_stat + 8  # y bat dau vung log
        LOG_BOT  = GameConfig.H - 6          # y ket thuc vung log
        LOG_H    = LOG_BOT - LOG_TOP         # tong chieu cao kha dung
        VISIBLE  = max(1, LOG_H // LINE_H)   # so dong hien thi duoc

        # Ve tieu de LOG
        self.screen.blit(
            font_xs.render("-- LOG (scroll) --", True, GameConfig.C["text2"]),
            (LOG_X, LOG_TOP)
        )
        LOG_TOP += LINE_H + 2
        LOG_H    = LOG_BOT - LOG_TOP
        VISIBLE  = max(1, LOG_H // LINE_H)

        total = len(self.log)
        # Clamp scroll offset
        max_scroll = max(0, total - VISIBLE)
        self.log_scroll = max(0, min(self.log_scroll, max_scroll))

        # Index dong dau tien hien thi (tinh tu cuoi)
        # log_scroll=0 -> hien cuoi; log_scroll=N -> cuon len N dong
        first = max(0, total - VISIBLE - self.log_scroll)
        visible_lines = self.log[first: first + VISIBLE]

        # Clip vung log de khong tran ra ngoai
        clip_rect = pygame.Rect(LOG_X, LOG_TOP, LOG_W, LOG_H)
        old_clip  = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        for i, line in enumerate(visible_lines):
            col = FrozenLakeGame._log_color(line, GameConfig.C)
            self.screen.blit(
                font_xs.render(line, True, col),
                (LOG_X, LOG_TOP + i * LINE_H)
            )

        self.screen.set_clip(old_clip)

        # Ve scrollbar ben phai
        SB_W = 6
        SB_X = px + GameConfig.PANEL_W - SB_W - 4
        pygame.draw.rect(self.screen, GameConfig.C["panel2"],
                         (SB_X, LOG_TOP, SB_W, LOG_H), border_radius=3)
        if total > VISIBLE:
            thumb_h = max(20, LOG_H * VISIBLE // total)
            thumb_y = LOG_TOP + (LOG_H - thumb_h) * (max_scroll - self.log_scroll) // max(1, max_scroll)
            pygame.draw.rect(self.screen, GameConfig.C["accent"],
                             (SB_X, thumb_y, SB_W, thumb_h), border_radius=3)

    def _draw_bottom_bar(self):
        y = GameConfig.GRID * GameConfig.CELL
        pygame.draw.rect(self.screen, GameConfig.C["panel"],
                         (0, y, GameConfig.GRID * GameConfig.CELL, 60))
        self.screen.blit(font_lg.render("FROZEN LAKE", True, GameConfig.C["text"]), (12, y + 14))
        self.screen.blit(
            font_md.render(self.alg_name, True, GameConfig.ALG_COLORS.get(self.alg_name, GameConfig.C["white"])),
            (380, y + 16)
        )

    # -- Main loop ------------------------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(GameConfig.FPS)
            mouse = pygame.mouse.get_pos()

            all_btns = list(self.tabs.values()) + list(self.btns_alg.values()) + [self.btn_run, self.btn_new_map]
            for btn in all_btns:
                btn.check_hover(mouse)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for g, btn in self.tabs.items():
                        if btn.clicked(mouse):
                            self.group = g
                            self._update_alg_buttons()
                            self._reset_run()

                    for a, btn in self.btns_alg.items():
                        if btn.clicked(mouse):
                            self.alg_name = a
                            self._reset_run()

                    if self.btn_run.clicked(mouse):
                        self.run_algorithm()

                    if self.btn_new_map.clicked(mouse):
                        self._instant_map_gen()

                # Cuon chuot trong vung panel -> cuon log
                if e.type == pygame.MOUSEWHEEL:
                    px_panel = GameConfig.GRID * GameConfig.CELL
                    if mouse[0] >= px_panel:   # chuot o trong panel
                        # e.y > 0 = lan len (xem cu hon), < 0 = lan xuong (xem moi hon)
                        self.log_scroll = max(0, self.log_scroll - e.y * 2)

            if self.state in [GameState.RUNNING, GameState.CSP_GEN]:
                self.anim_timer += dt
                speed = 20 if self.state == GameState.CSP_GEN else self.anim_speed
                if self.anim_timer >= speed:
                    self.anim_timer = 0
                    self._advance_step()

            self.draw()