"""
adversarial.py — Adversarial Search (AIMA Ch. 5)
================================================
Turn-based game: Santa (MAX) vs Satan (MIN).

Evaluation Function (for MAX):
- Win (Santa at House): +1.0 + (depth * 0.01) (Win faster is better)
- Lose (Satan at Santa): -1.0 - (depth * 0.01) (Lose slower is better)
- Otherwise: distance heuristic using BFS to avoid obstacles.
- Visited penalty: Heavily penalize states Santa has already visited to prevent infinite loops.
"""

import math
import random
from collections import deque
from config import GameConfig

ACTIONS = ["Up", "Down", "Left", "Right"]
ACT_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

class AdversarialSearch:
    """
    Chứa các thuật toán Tìm kiếm đối kháng (Minimax, Alpha-Beta Pruning, Expectimax).
    Mô phỏng một trò chơi theo lượt giữa Santa (MAX) và Satan (MIN).
    """

    @staticmethod
    def get_valid_moves(grid, pos):
        """
        Trả về danh sách các ô kề hợp lệ có thể di chuyển tới.
        Tác nhân không thể di chuyển vào ô NÚI (MOUNT) hoặc HỐ (HOLE).
        Nếu bị kẹt, tác nhân có thể chọn đứng yên.
        """
        r, c = pos
        moves = []
        for act in ACTIONS:
            dr, dc = ACT_DELTA[act]
            nr, nc = r + dr, c + dc
            if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID:
                if grid[nr][nc] not in (GameConfig.MOUNT, GameConfig.HOLE):
                    moves.append((nr, nc))
        # If stuck, staying in place is the only valid move
        if not moves:
            moves.append(pos)
        return moves

    @staticmethod
    def get_bfs_distances(grid, goal_pos):
        """Tính khoảng cách BFS từ đích đến tất cả các ô hợp lệ."""
        dist = {}
        q = deque([(goal_pos, 0)])
        visited = {goal_pos}
        while q:
            curr, d = q.popleft()
            dist[curr] = d
            r, c = curr
            for act in ACTIONS:
                dr, dc = ACT_DELTA[act]
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID:
                    if grid[nr][nc] not in (GameConfig.MOUNT, GameConfig.HOLE):
                        if (nr, nc) not in visited:
                            visited.add((nr, nc))
                            q.append(((nr, nc), d + 1))
        return dist

    @staticmethod
    def evaluate(santa_pos, satan_pos, house_pos, d, bfs_dist, visited_cells):
        """
        Hàm đánh giá heuristic cho trạng thái trò chơi đối kháng.
        Điểm dương có lợi cho Santa (MAX), điểm âm có lợi cho Satan (MIN).
        Xem xét khoảng cách đến đích, khoảng cách đến Satan và phạt nếu lặp lại đường đi.
        """
        if santa_pos == house_pos:
            return 1.0 + (d * 0.01) # Thắng nhanh hơn thì tốt hơn
        if santa_pos == satan_pos:
            return -1.0 - (d * 0.01) # Thua chậm hơn thì tốt hơn
            
        # Khoảng cách BFS tới nhà; nếu không thể tới, coi như rất xa (1000)
        dist_to_house = bfs_dist.get(santa_pos, 1000)
        
        # Khoảng cách Manhattan tới Satan (Satan chỉ cần tránh né cục bộ, không cần BFS)
        dist_to_satan = abs(santa_pos[0] - satan_pos[0]) + abs(santa_pos[1] - satan_pos[1])
        
        # Phạt nếu đi lại các ô cũ (tránh lặp vô hạn)
        penalty = 0
        if visited_cells:
            count = visited_cells.count(santa_pos)
            penalty = count * 0.1  
            
        # Công thức: Gần nhà hơn thì tốt (-), xa Satan hơn thì tốt (+)
        # Trọng số ưu tiên việc di chuyển tới nhà hơn là chỉ chạy trốn
        eval_score = (dist_to_satan * 0.5 - dist_to_house * 2.0) / 100.0 - penalty
        
        # Giới hạn điểm trong khoảng (-1, 1) để không ghi đè lên giá trị Thắng/Thua tuyệt đối
        return max(-0.99, min(0.99, eval_score))

    @staticmethod
    def minimax(grid, santa_pos, goal_pos, satan_pos, is_santa_turn, visited_cells=None, depth=4):
        nodes_expanded = [0]
        bfs_dist = AdversarialSearch.get_bfs_distances(grid, goal_pos)

        def max_value(s_pos, m_pos, d):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            v = -math.inf
            for nxt in AdversarialSearch.get_valid_moves(grid, s_pos):
                v = max(v, min_value(nxt, m_pos, d - 1))
            return v

        def min_value(s_pos, m_pos, d):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            v = math.inf
            for nxt in AdversarialSearch.get_valid_moves(grid, m_pos):
                v = min(v, max_value(s_pos, nxt, d - 1))
            return v

        best_move = None
        if is_santa_turn:
            best_val = -math.inf
            moves = AdversarialSearch.get_valid_moves(grid, santa_pos)
            random.shuffle(moves) # Random tie-breaking
            for nxt in moves:
                val = min_value(nxt, satan_pos, depth - 1)
                if val > best_val:
                    best_val = val
                    best_move = nxt
        else:
            best_val = math.inf
            moves = AdversarialSearch.get_valid_moves(grid, satan_pos)
            random.shuffle(moves)
            for nxt in moves:
                val = max_value(santa_pos, nxt, depth - 1)
                if val < best_val:
                    best_val = val
                    best_move = nxt

        if not best_move:
            best_move = santa_pos if is_santa_turn else satan_pos
        return best_move, nodes_expanded[0]

    @staticmethod
    def alpha_beta(grid, santa_pos, goal_pos, satan_pos, is_santa_turn, visited_cells=None, depth=4):
        nodes_expanded = [0]
        bfs_dist = AdversarialSearch.get_bfs_distances(grid, goal_pos)

        def max_value(s_pos, m_pos, d, alpha, beta):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            v = -math.inf
            for nxt in AdversarialSearch.get_valid_moves(grid, s_pos):
                v = max(v, min_value(nxt, m_pos, d - 1, alpha, beta))
                if v >= beta: return v
                alpha = max(alpha, v)
            return v

        def min_value(s_pos, m_pos, d, alpha, beta):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            v = math.inf
            for nxt in AdversarialSearch.get_valid_moves(grid, m_pos):
                v = min(v, max_value(s_pos, nxt, d - 1, alpha, beta))
                if v <= alpha: return v
                beta = min(beta, v)
            return v

        best_move = None
        if is_santa_turn:
            best_val = -math.inf
            alpha = -math.inf
            beta = math.inf
            moves = AdversarialSearch.get_valid_moves(grid, santa_pos)
            random.shuffle(moves)
            for nxt in moves:
                val = min_value(nxt, satan_pos, depth - 1, alpha, beta)
                if val > best_val:
                    best_val = val
                    best_move = nxt
                alpha = max(alpha, best_val)
        else:
            best_val = math.inf
            alpha = -math.inf
            beta = math.inf
            moves = AdversarialSearch.get_valid_moves(grid, satan_pos)
            random.shuffle(moves)
            for nxt in moves:
                val = max_value(santa_pos, nxt, depth - 1, alpha, beta)
                if val < best_val:
                    best_val = val
                    best_move = nxt
                beta = min(beta, best_val)

        if not best_move:
            best_move = santa_pos if is_santa_turn else satan_pos
        return best_move, nodes_expanded[0]

    @staticmethod
    def expectimax(grid, santa_pos, goal_pos, satan_pos, is_santa_turn, visited_cells=None, depth=4):
        nodes_expanded = [0]
        bfs_dist = AdversarialSearch.get_bfs_distances(grid, goal_pos)

        def max_value(s_pos, m_pos, d):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            v = -math.inf
            for nxt in AdversarialSearch.get_valid_moves(grid, s_pos):
                v = max(v, chance_value(nxt, m_pos, d - 1))
            return v

        def chance_value(s_pos, m_pos, d):
            nodes_expanded[0] += 1
            if s_pos == goal_pos or s_pos == m_pos or d == 0: 
                return AdversarialSearch.evaluate(s_pos, m_pos, goal_pos, d, bfs_dist, visited_cells)

            moves = AdversarialSearch.get_valid_moves(grid, m_pos)
            if not moves:
                return max_value(s_pos, m_pos, d - 1)

            # Satan evaluates his optimal move
            best_val_for_satan = math.inf
            best_moves_for_satan = []
            
            evals = []
            for nxt in moves:
                val = max_value(s_pos, nxt, d - 1)
                evals.append((val, nxt))
                if val < best_val_for_satan:
                    best_val_for_satan = val
                    best_moves_for_satan = [nxt]
                elif val == best_val_for_satan:
                    best_moves_for_satan.append(nxt)

            optimal_move = random.choice(best_moves_for_satan) if best_moves_for_satan else moves[0]
            
            N = len(moves)
            expected_val = 0
            for val, nxt in evals:
                if nxt == optimal_move:
                    prob = 0.7 + (0.3 / N)
                else:
                    prob = 0.3 / N
                expected_val += prob * val
                
            return expected_val

        best_move = None
        if is_santa_turn:
            best_val = -math.inf
            moves = AdversarialSearch.get_valid_moves(grid, santa_pos)
            random.shuffle(moves)
            for nxt in moves:
                val = chance_value(nxt, satan_pos, depth - 1)
                if val > best_val:
                    best_val = val
                    best_move = nxt
        else:
            moves = AdversarialSearch.get_valid_moves(grid, satan_pos)
            random.shuffle(moves)
            if not moves:
                best_move = satan_pos
            else:
                best_val_for_satan = math.inf
                best_moves_for_satan = []
                for nxt in moves:
                    val = max_value(santa_pos, nxt, depth - 1)
                    if val < best_val_for_satan:
                        best_val_for_satan = val
                        best_moves_for_satan = [nxt]
                    elif val == best_val_for_satan:
                        best_moves_for_satan.append(nxt)
                
                if random.random() < 0.7 and best_moves_for_satan:
                    best_move = random.choice(best_moves_for_satan)
                else:
                    best_move = random.choice(moves)

        if not best_move:
            best_move = santa_pos if is_santa_turn else satan_pos
        return best_move, nodes_expanded[0]