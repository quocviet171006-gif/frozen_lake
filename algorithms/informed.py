import heapq
from environment import Environment, Node, reconstruct

class InformedSearch:
    @staticmethod
    def greedy(grid, start_state, goal_pos, *args):
        # Greedy Search: priority queue by h(n), goal test on expansion
        # 1. FRONTIER = {Start}, h(Start)
        node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        frontier = [(node.cost, id(node), node)]
        frontier_states = {start_state}              # track states currently in FRONTIER
        # 2. REACHED = {}
        reached = set()
        visit_order = []
        # 3. WHILE (FRONTIER không rỗng)
        while frontier:
            # a. Chọn trạng thái n từ FRONTIER có h(n) nhỏ nhất
            _, _, node = heapq.heappop(frontier)
            # Skip stale entries
            if node.state in reached:
                frontier_states.discard(node.state)
                continue
            # b. NẾU n == Goal: TRẢ VỀ "Thành công"
            if node.state == goal_pos:
                visit_order.append(node.state)
                return reconstruct(node), visit_order
            # c. Loại bỏ n khỏi FRONTIER và thêm n vào REACHED
            frontier_states.discard(node.state)
            reached.add(node.state)
            visit_order.append(node.state)
            # d. Với mỗi trạng thái m kề với n
            for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                # i. NẾU m chưa có trong cả FRONTIER và REACHED → thêm m vào FRONTIER
                if n_state not in frontier_states and n_state not in reached:
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    heapq.heappush(frontier, (child.cost, id(child), child))
                    frontier_states.add(n_state)
                # ii. NẾU m đã có trong FRONTIER hoặc REACHED: Bỏ qua m
        # 4. TRẢ VỀ "Thất bại"
        return [], visit_order

    @staticmethod
    def a_star(grid, start_state, goal_pos, *args):
        # A*: priority queue by f(n) = g(n) + h(n), goal test on expansion
        # 1. FRONTIER = {Start} với f(Start) = g(Start) + h(Start) = 0 + h(Start)
        node = Node(start_state)
        node.g = 0
        node.h = Environment.heuristic(start_state, goal_pos)
        node.cost = node.g + node.h
        frontier = [(node.cost, id(node), node)]
        frontier_dict = {start_state: node.g}        # state → g(state) for states in FRONTIER
        # 2. REACHED = {}
        reached = {}                                 # state → g(state) for expanded states
        visit_order = []
        # 3. WHILE (FRONTIER không rỗng)
        while frontier:
            # a. Chọn trạng thái n từ FRONTIER có f(n) nhỏ nhất
            _, _, node = heapq.heappop(frontier)
            # Skip stale entries (already expanded with better cost)
            if node.state in reached:
                frontier_dict.pop(node.state, None)
                continue
            # b. NẾU n == Goal: TRẢ VỀ "Thành công"
            if node.state == goal_pos:
                visit_order.append(node.state)
                return reconstruct(node), visit_order
            # c. Loại bỏ n khỏi FRONTIER và thêm n vào REACHED
            frontier_dict.pop(node.state, None)
            reached[node.state] = node.g
            visit_order.append(node.state)
            # d. Với mỗi trạng thái m kề với n
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                # i. Tính toán chi phí thực tế mới: g_new(m) = g(n) + cost(n, m)
                g_new = node.g + cost
                h_val = Environment.heuristic(n_state, goal_pos)
                # ii. NẾU m đã nằm trong REACHED
                if n_state in reached:
                    if g_new >= reached[n_state]:
                        # g_new >= g(m) hiện tại: Bỏ qua (tệ hơn)
                        continue
                    else:
                        # NGƯỢC LẠI: Xóa m khỏi REACHED và cập nhật g(m) = g_new
                        del reached[n_state]
                        child = Node(n_state, node, action=action)
                        child.g = g_new
                        child.h = h_val
                        child.cost = child.g + child.h
                        frontier_dict[n_state] = g_new
                        heapq.heappush(frontier, (child.cost, id(child), child))
                # iii. NẾU m đã nằm trong FRONTIER
                elif n_state in frontier_dict:
                    if g_new < frontier_dict[n_state]:
                        # g_new < g(m) hiện tại: Cập nhật lại g(m) và f(m), đổi cha
                        frontier_dict[n_state] = g_new
                        child = Node(n_state, node, action=action)
                        child.g = g_new
                        child.h = h_val
                        child.cost = child.g + child.h
                        heapq.heappush(frontier, (child.cost, id(child), child))
                    # else: g_new >= g(m) hiện tại → bỏ qua
                # iv. NẾU m chưa có mặt trong FRONTIER và REACHED
                else:
                    child = Node(n_state, node, action=action)
                    child.g = g_new
                    child.h = h_val
                    child.cost = child.g + child.h
                    frontier_dict[n_state] = g_new
                    heapq.heappush(frontier, (child.cost, id(child), child))
        # 4. TRẢ VỀ "Thất bại"
        return [], visit_order

    @staticmethod
    def ida_star(grid, start_state, goal_pos, *args):
        # IDA*: iterative deepening with f-cost threshold, LIFO stack frontier
        visit_order = []
        # root ← NODE(problem.INITIAL)
        # threshold ← h(root)
        root = Node(start_state)
        root.g = 0
        threshold = Environment.heuristic(start_state, goal_pos)
        # loop do
        while True:
            # frontier ← {root}
            frontier = [root]
            # next_threshold ← ∞
            next_threshold = float('inf')
            # while frontier không rỗng do
            while frontier:
                # node ← POP(frontier)  /* LIFO - lấy node sâu nhất */
                node = frontier.pop()
                # if IS-GOAL(problem, node) then return SOLUTION(node)
                if node.state == goal_pos:
                    visit_order.append(node.state)
                    return reconstruct(node), visit_order
                visit_order.append(node.state)
                # for each child in EXPAND(problem, node) do
                for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                    child = Node(n_state, node, action=action)
                    child.g = node.g + cost
                    # f ← g(child) + h(child)
                    f = child.g + Environment.heuristic(n_state, goal_pos)
                    child.cost = f
                    # if f ≤ threshold then PUSH(child, frontier)
                    if f <= threshold:
                        frontier.append(child)
                    # else next_threshold ← MIN(next_threshold, f)
                    else:
                        next_threshold = min(next_threshold, f)
            # if next_threshold = ∞ then return failure
            if next_threshold == float('inf'):
                return [], visit_order
            # threshold ← next_threshold
            threshold = next_threshold
