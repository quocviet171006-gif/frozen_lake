"""
adversarial.py — Adversarial Search (AIMA Ch. 5)
================================================
Gồm 3 thuật toán: MINIMAX, ALPHA-BETA PRUNING, EXPECTIMAX

Mô hình Adversarial trong Frozen Lake:
- Santa (MAX) muốn đến đích nhanh nhất.
- Environment (MIN) điều khiển các ô HỐ (sàn trơn trượt).
- Tại ô bình thường: Santa đi đâu đến đó (tất định).
- Tại ô HỐ: 
  + Minimax: Môi trường ác ý sẽ đẩy Santa về ô xấu nhất (xa đích nhất).
  + Expectimax: Môi trường ngẫu nhiên đẩy Santa đi 4 hướng (trung bình).

Evaluation Function:
- eval(s) = 1000 - khoảng cách BFS từ s đến đích.
- Đến đích: +10000

Mỗi bước đi tốn cost = 1 để khuyến khích đường đi ngắn nhất.
"""

from collections import deque
from config import GameConfig

ACTIONS = ["Up", "Down", "Left", "Right"]
ACT_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

class AdversarialSearch:

    @staticmethod
    def _precompute_eval(grid, goal_pos):
        """Tính BFS distance từ mọi ô đến đích để làm hàm đánh giá."""
        dist = {}
        q = deque([(goal_pos, 0)])
        visited = {goal_pos}
        while q:
            curr, d = q.popleft()
            dist[curr] = d
            r, c = curr
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append(((nr, nc), d + 1))
        return dist

    @staticmethod
    def _run_adversarial(grid, start_state, goal_pos, alg_type):
        """
        Khung chạy chung cho cả 3 thuật toán.
        Sinh ra đường đi (path) bằng cách chạy depth-limited search ở mỗi bước.
        """
        dist = AdversarialSearch._precompute_eval(grid, goal_pos)
        
        def evaluate(s):
            if s == goal_pos: return 10000
            return 1000 - dist.get(s, 10000)

        visited_log = []

        def get_outcomes(s, a):
            r, c = s
            if grid[r][c] == GameConfig.HOLE:
                # Môi trường quyết định: có thể trượt sang bất kỳ ô kề nào
                results = set()
                for act in ACTIONS:
                    dr, dc = ACT_DELTA[act]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                        results.add((nr, nc))
                    else:
                        results.add((r, c))
                return list(results)
            else:
                # Tất định
                dr, dc = ACT_DELTA[a]
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                    return [(nr, nc)]
                return [(r, c)]

        # ==========================================
        # 1. MINIMAX
        # ==========================================
        def minimax_max(s, depth):
            if len(visited_log) < 5000: visited_log.append(s)
            if s == goal_pos: return 10000
            if depth == 0: return evaluate(s)
            
            best_val = -float('inf')
            for a in ACTIONS:
                val = minimax_min(s, a, depth)
                if val > best_val: best_val = val
            return best_val

        def minimax_min(s, a, depth):
            outcomes = get_outcomes(s, a)
            if grid[s[0]][s[1]] == GameConfig.HOLE:
                # MIN (Môi trường) chọn kết quả xấu nhất cho Santa
                return min(minimax_max(nxt, depth-1) for nxt in outcomes) - 1
            else:
                return minimax_max(outcomes[0], depth-1) - 1

        # ==========================================
        # 2. ALPHA-BETA PRUNING
        # ==========================================
        def ab_max(s, depth, alpha, beta):
            if len(visited_log) < 5000: visited_log.append(s)
            if s == goal_pos: return 10000
            if depth == 0: return evaluate(s)
            
            best_val = -float('inf')
            for a in ACTIONS:
                val = ab_min(s, a, depth, alpha, beta)
                if val > best_val: best_val = val
                if best_val >= beta: return best_val
                alpha = max(alpha, best_val)
            return best_val

        def ab_min(s, a, depth, alpha, beta):
            outcomes = get_outcomes(s, a)
            if grid[s[0]][s[1]] == GameConfig.HOLE:
                best_val = float('inf')
                for nxt in outcomes:
                    val = ab_max(nxt, depth-1, alpha, beta) - 1
                    if val < best_val: best_val = val
                    if best_val <= alpha: return best_val
                    beta = min(beta, best_val)
                return best_val
            else:
                return ab_max(outcomes[0], depth-1, alpha, beta) - 1

        # ==========================================
        # 3. EXPECTIMAX
        # ==========================================
        def exp_max(s, depth):
            if len(visited_log) < 5000: visited_log.append(s)
            if s == goal_pos: return 10000
            if depth == 0: return evaluate(s)
            
            best_val = -float('inf')
            for a in ACTIONS:
                val = exp_chance(s, a, depth)
                if val > best_val: best_val = val
            return best_val

        def exp_chance(s, a, depth):
            outcomes = get_outcomes(s, a)
            if grid[s[0]][s[1]] == GameConfig.HOLE:
                # CHANCE (Môi trường) lấy trung bình các khả năng
                avg = sum(exp_max(nxt, depth-1) for nxt in outcomes) / len(outcomes)
                return avg - 1
            else:
                return exp_max(outcomes[0], depth-1) - 1

        # ==========================================
        # XÂY DỰNG ĐƯỜNG ĐI (PATH RECONSTRUCTION)
        # ==========================================
        path = [start_state]
        curr = start_state
        MAX_DEPTH = 4  # Giới hạn độ sâu vừa đủ để chạy mượt realtime

        while curr != goal_pos and len(path) < 50:
            best_val = -float('inf')
            best_nxt = curr
            best_a = None
            
            for a in ACTIONS:
                if alg_type == "minimax":
                    val = minimax_min(curr, a, MAX_DEPTH)
                elif alg_type == "alphabeta":
                    val = ab_min(curr, a, MAX_DEPTH, -float('inf'), float('inf'))
                else:
                    val = exp_chance(curr, a, MAX_DEPTH)
                    
                if val > best_val:
                    best_val = val
                    best_a = a
            
            if best_a is None:
                break
                
            outcomes = get_outcomes(curr, best_a)
            if grid[curr[0]][curr[1]] == GameConfig.HOLE:
                if alg_type in ["minimax", "alphabeta"]:
                    # Môi trường ác ý -> ta dự đoán bị đẩy về ô xấu nhất
                    best_nxt = min(outcomes, key=lambda nxt: evaluate(nxt))
                else:
                    # Môi trường ngẫu nhiên -> Expectimax lạc quan hy vọng ô tốt nhất để vẽ đường
                    best_nxt = max(outcomes, key=lambda nxt: evaluate(nxt))
            else:
                best_nxt = outcomes[0]
                
            if best_nxt == curr:
                # Bị kẹt (ví dụ kẹt trong hố và môi trường đẩy ngược lại liên tục)
                break
                
            path.append(best_nxt)
            curr = best_nxt

        return path, visited_log

    @staticmethod
    def minimax(grid, start_state, goal_pos, *args):
        return AdversarialSearch._run_adversarial(grid, start_state, goal_pos, "minimax")

    @staticmethod
    def alpha_beta(grid, start_state, goal_pos, *args):
        return AdversarialSearch._run_adversarial(grid, start_state, goal_pos, "alphabeta")

    @staticmethod
    def expectimax(grid, start_state, goal_pos, *args):
        return AdversarialSearch._run_adversarial(grid, start_state, goal_pos, "expectimax")
