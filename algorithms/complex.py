from collections import deque
from config import GameConfig
from environment import Node, reconstruct_actions


# ═══════════════════════════════════════════════════════════════
# HELPER CHUNG 
# ═══════════════════════════════════════════════════════════════

ACTIONS   = ["Up", "Down", "Left", "Right"]
ACT_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


def _in_bounds(grid, r, c, nr, nc):
    if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])):
        return False
    if r // 4 != nr // 4 or c // 4 != nc // 4:
        return False
    return True


def _transition_belief(grid, r, c, action, block_holes=False):
    """
    Mô hình chuyển đổi trạng thái. 
    Nếu Santa đang ở House, thì dừng lại (không di chuyển nữa).
    """
    if grid[r][c] == GameConfig.HOUSE:
        return [(r, c)]
        
    if grid[r][c] == GameConfig.HOLE and not block_holes:
        results = set()
        for a in ACTIONS:
            dr2, dc2 = ACT_DELTA[a]
            nr, nc = r + dr2, c + dc2
            if _in_bounds(grid, r, c, nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
                results.add((nr, nc))
            else:
                results.add((r, c))
        return list(results)
    else:
        dr, dc = ACT_DELTA[action]
        nr, nc = r + dr, c + dc
        
        is_blocked = False
        if not _in_bounds(grid, r, c, nr, nc):
            is_blocked = True
        elif grid[nr][nc] == GameConfig.MOUNT:
            is_blocked = True
        elif block_holes and grid[nr][nc] == GameConfig.HOLE:
            is_blocked = True
            
        if not is_blocked:
            return [(nr, nc)]
        return [(r, c)]


def _transition_andor(grid, r, c, action):
    if grid[r][c] == GameConfig.HOUSE:
        return [(r, c)]
        
    if grid[r][c] == GameConfig.HOLE:
        results = set()
        for a in ACTIONS:
            dr2, dc2 = ACT_DELTA[a]
            nr, nc = r + dr2, c + dc2
            if _in_bounds(grid, r, c, nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
                results.add((nr, nc))
            else:
                results.add((r, c))
        return list(results)
    else:
        dr, dc = ACT_DELTA[action]
        nr, nc = r + dr, c + dc
        if _in_bounds(grid, r, c, nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
            return [(nr, nc)]
        return []



# ═══════════════════════════════════════════════════════════════
# 1. SENSORLESS SEARCH (Conformant BFS)
# ═══════════════════════════════════════════════════════════════

class SensorlessSearch:
    """
    Tìm kiếm không cảm biến (Sensorless / Conformant Planning).

    - Trạng thái niềm tin (Belief State): frozenset({(r,c), ...}) — tập hợp mọi vị trí mà Santa có thể đang đứng.
    - Đích đến (Goal): Trạng thái niềm tin được thu gọn lại chỉ còn đúng 1 ô là vị trí đích (goal_pos).

    - Quá trình chuyển đổi (Transition): Với mỗi vị trí (r,c) trong trạng thái niềm tin, áp dụng hành động 
      và hợp nhất (union) tất cả các kết quả khả thi lại. (Ví dụ: Đứng trên hố sẽ bị trượt ra 4 hướng; 
      đứng trên ô thường sẽ di chuyển chắc chắn).

    - Thuật toán: Tìm kiếm theo chiều rộng (BFS) trên không gian của trạng thái niềm tin (Belief State space - AIMA Fig 4.14).
    """

    @staticmethod
    def _is_goal(grid, belief: frozenset) -> bool:
        """Đạt đích khi TẤT CẢ các trạng thái trong belief đều là HOUSE."""
        if not belief: return False
        for r, c in belief:
            if grid[r][c] != GameConfig.HOUSE:
                return False
        return True

    @staticmethod
    def _predict(grid, belief: frozenset, action: str) -> frozenset:
        """Predict: áp dụng action lên toàn bộ belief state."""
        new_belief = set()
        for (r, c) in belief:
            for (nr, nc) in _transition_belief(grid, r, c, action):
                new_belief.add((nr, nc))
        return frozenset(new_belief)

    @staticmethod
    def sensorless_bfs(grid, start_state, goal_pos, *args):
        """
        BFS Không cảm biến: Tìm kiếm một chuỗi hành động đảm bảo đưa tác nhân đến đích
        bất kể tác nhân xuất phát từ ô nào trên bản đồ ban đầu.

        Trả về:
            (actions, visited_beliefs):
            - actions        : list[str]       — Danh sách các hành động cần thực thi
            - visited_beliefs: list[frozenset] — Lịch sử các trạng thái niềm tin đã duyệt qua
        """
        if isinstance(start_state, frozenset):
            initial_belief = start_state
        else:
            initial_belief = frozenset([start_state])

        if SensorlessSearch._is_goal(grid, initial_belief):
            return [], [initial_belief]

        # BFS trên không gian belief state
        root = Node(initial_belief)
        frontier = deque([root])
        explored = {initial_belief}
        visited_beliefs = []

        MAX_NODES = 5000
        while frontier:
            node = frontier.popleft()
            visited_beliefs.append(node.state)
            
            if len(explored) > MAX_NODES:
                break

            for action in ACTIONS:
                new_belief = SensorlessSearch._predict(grid, node.state, action)
                if not new_belief or new_belief in explored:
                    continue

                child = Node(new_belief, parent=node, action=action)

                if SensorlessSearch._is_goal(grid, new_belief):
                    visited_beliefs.append(new_belief)
                    return reconstruct_actions(child), visited_beliefs

                explored.add(new_belief)
                frontier.append(child)

        return [], visited_beliefs  # Không tìm thấy


# ═══════════════════════════════════════════════════════════════
# ███  2. PARTIAL OBSERVABLE SEARCH  ███
# ═══════════════════════════════════════════════════════════════

class PartialObservableSearch:
    """
    Tìm kiếm quan sát cục bộ (Partial Observable / Online Belief-State Search).

    Mô hình:
    - Tác nhân không biết chính xác vị trí của mình nhưng có một cảm biến hạn chế:
      Cảm biến (Observation) = Loại gạch (tile) của ô đang đứng (SNOW=0, HOLE=1, MOUNT=2, HOUSE=4).
    - Trạng thái niềm tin (Belief State) = frozenset gồm các ô nhất quán với tất cả các cảm biến đo được.

    Vòng lặp mỗi bước:
      - DỰ ĐOÁN (PREDICT): Áp dụng hành động lên trạng thái niềm tin hiện tại (dùng _transition).
      - CẬP NHẬT (UPDATE) : Lọc trạng thái niềm tin dựa trên cảm biến thực tế (chỉ giữ lại những ô có tile trùng khớp).

    Thuật toán: BFS trên không gian trạng thái niềm tin kết hợp với bộ lọc theo cảm biến (AIMA Fig 4.19).
    """

    @staticmethod
    def partial_obs_bfs(grid, start_state, goal_pos, *args):
        """
        BFS Quan sát cục bộ: Tìm kiếm chuỗi hành động có tính toán đến các thông tin thu được từ cảm biến (percept).

        Trả về:
            (actions, visited_beliefs):
            - actions        : list[str]       — Danh sách các hành động
            - visited_beliefs: list[frozenset] — Lịch sử các trạng thái niềm tin
        """
        if isinstance(start_state, frozenset):
            initial_belief = start_state
        else:
            initial_belief = frozenset([start_state])
            
        if SensorlessSearch._is_goal(grid, initial_belief):
            return [], [initial_belief]

        root = Node(initial_belief)
        frontier = deque([root])
        explored = {initial_belief}
        visited_beliefs = []

        MAX_NODES = 5000
        while frontier:
            node = frontier.popleft()
            visited_beliefs.append(node.state)
            
            if len(explored) > MAX_NODES:
                break

            for action in ACTIONS:
                predicted = set()
                for (r, c) in node.state:
                    for (nr, nc) in _transition_belief(grid, r, c, action, block_holes=True):
                        predicted.add((nr, nc))

                if not predicted:
                    continue

                new_belief = frozenset(predicted)
                if new_belief in explored:
                    continue

                child = Node(new_belief, parent=node, action=action)

                if SensorlessSearch._is_goal(grid, new_belief):
                    visited_beliefs.append(new_belief)
                    return reconstruct_actions(child), visited_beliefs

                explored.add(new_belief)
                frontier.append(child)

        return [], visited_beliefs


# ═══════════════════════════════════════════════════════════════
# 3. AND-OR GRAPH SEARCH  
# ═══════════════════════════════════════════════════════════════

class AndOrSearch:
    @staticmethod
    def and_or_graph_search(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm đồ thị AND-OR (AND-OR Graph Search) — Triển khai chính xác theo mã giả AIMA.

        - TÌM KIẾM OR (OR_SEARCH): Trả về một từ điển {state: action} (kế hoạch phẳng) hoặc None (nếu thất bại).
        - TÌM KIẾM AND (AND_SEARCH): Trả về một từ điển hợp nhất tất cả các kế hoạch hoặc None.

        Trả về:
            (policy, visited_states)
            - policy : dict{state: action_str} — Chính sách hành động hoặc {} nếu không tìm thấy.
            - visited: list[state]             — Danh sách các trạng thái đã duyệt.
        """
        import sys
        sys.setrecursionlimit(100000)

        MAX_DEPTH     = len(grid) * len(grid[0]) * 2
        failed_states = set()    # state chứng minh thất bại (safe to cache)
        success_cache = {}       # state → plan đã tìm được (safe to cache)

        visited_log = []

        # ── OR_SEARCH ──────────────────────────────────────────
        def or_search(state, path):
            """
            TÌM KIẾM OR (OR_SEARCH - Trạng thái, Bài toán, Đường đi):
              nếu trạng thái ∈ đích → trả về [] (thành công)
              nếu trạng thái ∈ đường đi → trả về thất bại (chu trình)
              với mỗi hành động khả thi:
                  các_trạng_thái_kết_quả = chuyển_đổi(trạng thái, hành động)
                  kế_hoạch = TÌM_KIẾM_AND(các_trạng_thái_kết_quả, đường đi + [trạng thái])
                  nếu kế_hoạch ≠ thất bại → trả về [hành động, kế_hoạch]
              trả về thất bại
            """
            if state == goal_pos:
                return {}

            # Cycle detection
            if state in path:
                return None

            # Depth limit
            if len(path) >= MAX_DEPTH:
                return None

            # Failure cache
            if state in failed_states:
                return None

            # Success cache — plan không phụ thuộc path (chỉ phụ thuộc grid+goal)
            if state in success_cache:
                return success_cache[state]

            if len(visited_log) < 5000:
                visited_log.append(state)

            new_path = path | {state}
            for action in ACTIONS:
                result_states = _transition_andor(grid, state[0], state[1], action)
                if not result_states:
                    continue

                plan = and_search(result_states, new_path)

                if plan is not None:
                    result = {state: action, **plan}
                    success_cache[state] = result   # cache thành công
                    return result

            failed_states.add(state)
            return None


        # ── AND_SEARCH ─────────────────────────────────────────
        def and_search(states, path):
            """
            TÌM KIẾM AND (AND_SEARCH - Các trạng thái, Bài toán, Đường đi):
              các_kế_hoạch = từ điển rỗng
              với mỗi trạng thái s trong các trạng thái:
                  kế_hoạch_s = TÌM_KIẾM_OR(s, bài toán, đường đi)
                  nếu kế_hoạch_s == thất bại → trả về thất bại
                  thêm kế_hoạch_s vào các_kế_hoạch
              trả về các_kế_hoạch

            Mở rộng: 
            Nếu trạng thái s đã nằm trong đường đi (tổ tiên) → phát hiện chu trình;
            Nhưng nếu s == nút cha ngay trước đó ở đầu đường đi (hành động không có tác dụng),
            coi như kế hoạch rỗng (đứng yên không sao, sẽ thử lại hành động ở bước tiếp theo).
            """
            plans = {}   # empty mapping
            for s in states:
                plan_s = or_search(s, path)
                if plan_s is None:   # if plan_s == failure
                    return None      # return failure
                plans.update(plan_s)   # plans[s] = plan_s
            return plans


        # ── Entry point ────────────────────────────────────────
        # AND_OR_GRAPH_SEARCH(problem):
        #     return OR_SEARCH(problem.initial_state, problem, [])
        policy = or_search(start_state, set())   # path = []  (set)

        if policy is None:
            return {}, visited_log

        return policy, visited_log



# ═══════════════════════════════════════════════════════════════
# ███  FACADE CLASS  ███
# ═══════════════════════════════════════════════════════════════

class ComplexSearch:
    """
    Lớp mặt tiền (Facade class) — Cung cấp giao diện thống nhất cho từ điển thuật toán ALGORITHMS.
    """

    @staticmethod
    def sensorless_bfs(grid, start_state, goal_pos, *args):
        """BFS Không cảm biến — Lên kế hoạch mù hoàn toàn, tin tưởng tuyệt đối vào kế hoạch hành động."""
        return SensorlessSearch.sensorless_bfs(grid, start_state, goal_pos)

    @staticmethod
    def partial_obs_bfs(grid, start_state, goal_pos, *args):
        """BFS Quan sát cục bộ — Nhận biết loại gạch qua cảm biến để thu hẹp dần không gian niềm tin."""
        return PartialObservableSearch.partial_obs_bfs(grid, start_state, goal_pos)

    @staticmethod
    def and_or_search(grid, start_state, goal_pos, *args):
        """Tìm kiếm Đồ thị AND-OR — Xây dựng kế hoạch có điều kiện (conditional plan) cho môi trường phi tất định."""
        return AndOrSearch.and_or_graph_search(grid, start_state, goal_pos)