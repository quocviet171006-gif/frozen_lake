from collections import deque
from config import GameConfig
from environment import Node, reconstruct_actions


# ═══════════════════════════════════════════════════════════════
# HELPER CHUNG 
# ═══════════════════════════════════════════════════════════════

ACTIONS   = ["Up", "Down", "Left", "Right"]
ACT_DELTA = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


def _in_bounds(r, c):
    return 0 <= r < GameConfig.GRID and 0 <= c < GameConfig.GRID


def _transition_belief(grid, r, c, action):
    """
    Mô hình chuyển đổi trạng thái (Transition model) cho tìm kiếm Không cảm biến (SENSORLESS)
    và Quan sát cục bộ (PARTIAL-OBS).
    - Ô tuyết (SNOW): Di chuyển chắc chắn đến ô đích (hoặc đứng yên nếu bị chặn bởi ranh giới/núi).
    - Ô hố (HOLE): Bị trượt ngẫu nhiên sang các ô lân cận hợp lệ (có thể lên tới 4 kết quả khác nhau).
    """
    if grid[r][c] == GameConfig.HOLE:
        results = set()
        for a in ACTIONS:
            dr2, dc2 = ACT_DELTA[a]
            nr, nc = r + dr2, c + dc2
            if _in_bounds(nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
                results.add((nr, nc))
            else:
                results.add((r, c))
        return list(results)
    else:
        dr, dc = ACT_DELTA[action]
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
            return [(nr, nc)]
        return [(r, c)]   # bị chặn → đứng yên


def _transition_andor(grid, r, c, action):
    """
    Mô hình chuyển đổi trạng thái (Transition model) cho tìm kiếm AND-OR.
    - Ô tuyết (SNOW): Hành động hợp lệ trả về 1 kết quả; nếu bị chặn trả về danh sách rỗng [] (bỏ qua hành động).
    - Ô hố (HOLE): Bị trượt ngẫu nhiên lên tới 4 kết quả khác nhau (Thực sự là một nút AND).
    """
    if grid[r][c] == GameConfig.HOLE:
        results = set()
        for a in ACTIONS:
            dr2, dc2 = ACT_DELTA[a]
            nr, nc = r + dr2, c + dc2
            if _in_bounds(nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
                results.add((nr, nc))
            else:
                results.add((r, c))
        return list(results)
    else:
        dr, dc = ACT_DELTA[action]
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and grid[nr][nc] != GameConfig.MOUNT:
            return [(nr, nc)]
        return []   # bị chặn → action không áp dụng (skip)



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
    def _is_goal(belief: frozenset, goal_pos: tuple) -> bool:
        """Belief state là goal khi chắc chắn Santa ở goal_pos."""
        return len(belief) == 1 and goal_pos in belief

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
        # Belief ban đầu = tất cả ô không phải núi (Santa có thể ở đâu cũng được)
        initial_belief = frozenset(
            (r, c)
            for r in range(GameConfig.GRID)
            for c in range(GameConfig.GRID)
            if grid[r][c] != GameConfig.MOUNT
        )

        if SensorlessSearch._is_goal(initial_belief, goal_pos):
            return [], [initial_belief]

        # BFS trên không gian belief state
        root = Node(initial_belief)
        frontier = deque([root])
        explored = {initial_belief}
        visited_beliefs = []

        while frontier:
            node = frontier.popleft()
            visited_beliefs.append(node.state)

            for action in ACTIONS:
                new_belief = SensorlessSearch._predict(grid, node.state, action)
                if not new_belief or new_belief in explored:
                    continue

                child = Node(new_belief, parent=node, action=action)

                if SensorlessSearch._is_goal(new_belief, goal_pos):
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
        # Belief ban đầu: tất cả ô không phải núi
        initial_belief = frozenset(
            (r, c)
            for r in range(GameConfig.GRID)
            for c in range(GameConfig.GRID)
            if grid[r][c] != GameConfig.MOUNT
        )

        # Lọc belief ban đầu theo observation tại start_state
        sr, sc = start_state
        init_obs = grid[sr][sc]
        filtered_init = frozenset(
            (r, c) for (r, c) in initial_belief
            if grid[r][c] == init_obs
        )
        if not filtered_init:
            filtered_init = initial_belief

        # Kiểm tra ngay
        if len(filtered_init) == 1 and goal_pos in filtered_init:
            return [], [filtered_init]

        # BFS trên filtered belief space
        root = Node(filtered_init)
        frontier = deque([root])
        explored = {filtered_init}
        visited_beliefs = []

        while frontier:
            node = frontier.popleft()
            visited_beliefs.append(node.state)

            for action in ACTIONS:
                # PREDICT: áp dụng action lên tất cả ô trong belief
                predicted = set()
                for (r, c) in node.state:
                    for (nr, nc) in _transition_belief(grid, r, c, action):
                        predicted.add((nr, nc))

                if not predicted:
                    continue

                # UPDATE: thử từng observation khả dĩ
                possible_obs = {grid[r][c] for (r, c) in predicted}

                for obs in possible_obs:
                    new_belief = frozenset(
                        (r, c) for (r, c) in predicted
                        if grid[r][c] == obs
                    )
                    if not new_belief or new_belief in explored:
                        continue

                    child = Node(new_belief, parent=node, action=action)

                    # Goal: belief thu gọn còn chỉ goal_pos
                    if len(new_belief) == 1 and goal_pos in new_belief:
                        visited_beliefs.append(new_belief)
                        return reconstruct_actions(child), visited_beliefs

                    # Hoặc: goal_pos nằm trong belief VÀ obs khớp tile của goal
                    if goal_pos in new_belief and grid[goal_pos[0]][goal_pos[1]] == obs:
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

        MAX_DEPTH     = GameConfig.GRID * GameConfig.GRID
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
