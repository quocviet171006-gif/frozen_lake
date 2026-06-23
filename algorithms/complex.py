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
    Transition model cho SENSORLESS & PARTIAL-OBS.
    - Ô SNOW: di chuyển tất định (hoặc đứng yên nếu bị chặn).
    - Ô HỐ: trượt sang các ô kề hợp lệ (lên đến 4 outcomes).
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
    Transition model cho AND-OR SEARCH.
    - Ô SNOW: action hợp lệ → 1 outcome; action bị chặn → [] (skip action).
    - Ô HỐ: trượt lên đến 4 outcomes (AND node thực sự).
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

    Belief State = frozenset({(r,c), ...}) — tập mọi vị trí Santa có thể đang ở.
    Goal         = belief state thu gọn còn đúng 1 ô = goal_pos.

    Transition: với mỗi (r,c) trong belief, áp dụng action → union các outcomes.
    (Hố → trượt 4 hướng; ô thường → di chuyển tất định)

    Thuật toán: BFS trên không gian belief state (AIMA Fig. 4.14).
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
        Sensorless BFS: tìm chuỗi hành động đảm bảo đến goal
        bất kể Santa xuất phát từ ô nào trên bản đồ.

        Returns:
            (actions, visited_beliefs):
            - actions        : list[str]       — chuỗi action thực thi
            - visited_beliefs: list[frozenset] — lịch sử belief state
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
    - Agent không biết chính xác vị trí nhưng có cảm biến hạn chế:
      Observation = loại tile ô hiện tại (SNOW=0, HOLE=1, MOUNT=2, HOUSE=4).
    - Belief State = frozenset các ô nhất quán với tất cả observations.

    Vòng lặp mỗi bước:
      PREDICT  → áp dụng action lên belief (dùng _transition)
      UPDATE   → lọc belief theo observation: chỉ giữ ô có tile == obs

    Thuật toán: BFS trên belief space với filter theo percept (AIMA Fig. 4.19).
    """

    @staticmethod
    def partial_obs_bfs(grid, start_state, goal_pos, *args):
        """
        Partial Observable BFS: tìm chuỗi hành động có tính đến percept.

        Returns:
            (actions, visited_beliefs):
            - actions        : list[str]
            - visited_beliefs: list[frozenset]
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
        AND-OR Graph Search — implement đúng pseudocode AIMA.

        OR_SEARCH:  trả về dict{state→action} (plan phẳng) hoặc None (failure).
        AND_SEARCH: trả về dict hợp nhất tất cả plans hoặc None.

        Returns:
            (policy, visited_states)
            policy : dict{state: action_str} hoặc {} nếu không tìm thấy
            visited: list[state]
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
            OR_SEARCH(state, problem, path):
              if state ∈ goal_test → return []
              if state ∈ path      → return failure
              for each action:
                  result_states = results(state, action)
                  plan = AND_SEARCH(result_states, path + [state])
                  if plan ≠ failure → return [action, plan]
              return failure
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
            AND_SEARCH(states, problem, path):
              plans = empty mapping
              for each s in states:
                  plan_s = OR_SEARCH(s, problem, path)
                  if plan_s == failure → return failure
                  plans[s] = plan_s
              return plans

            Extension: nếu s đã nằm trong path (ancestor) → cycle;
            nhưng nếu s == parent ở đầu path (noop outcome của action),
            coi như plan rỗng (đứng yên là ok, sẽ retry action ở bước sau).
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
    Facade class — giao diện thống nhất cho ALGORITHMS dict.
    """

    @staticmethod
    def sensorless_bfs(grid, start_state, goal_pos, *args):
        """Sensorless BFS — không cần cảm biến, tin tưởng vào plan."""
        return SensorlessSearch.sensorless_bfs(grid, start_state, goal_pos)

    @staticmethod
    def partial_obs_bfs(grid, start_state, goal_pos, *args):
        """Partial Observable BFS — cảm biến tile type, thu hẹp belief dần."""
        return PartialObservableSearch.partial_obs_bfs(grid, start_state, goal_pos)

    @staticmethod
    def and_or_search(grid, start_state, goal_pos, *args):
        """AND-OR Graph Search — conditional plan cho môi trường phi tất định."""
        return AndOrSearch.and_or_graph_search(grid, start_state, goal_pos)
