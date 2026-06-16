import heapq
from environment import Environment, Node, reconstruct


class InformedSearch:

    @staticmethod
    def greedy(grid, start_state, goal_pos, *args):
        """
        Greedy Best-First Search: chỉ dùng heuristic h(n) để chọn node.
        Nhanh nhưng không đảm bảo optimal.
        Fix: dùng Manhattan distance thuần (không cost âm).
        """
        h0 = Environment.heuristic(start_state, goal_pos)
        node = Node(start_state, cost=h0)
        frontier = [(h0, id(node), node)]
        reached, visit_order = {start_state}, []

        while frontier:
            _, _, node = heapq.heappop(frontier)
            visit_order.append(node.state)
            if node.state == goal_pos:
                return reconstruct(node), visit_order
            for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                if n_state not in reached:
                    reached.add(n_state)
                    h = Environment.heuristic(n_state, goal_pos)
                    child = Node(n_state, node, cost=h, action=action)
                    heapq.heappush(frontier, (h, id(child), child))

        return [], visit_order

    @staticmethod
    def a_star(grid, start_state, goal_pos, *args):
        """
        A* Search: f(n) = g(n) + h(n).
        Fix: heuristic admissible (Manhattan), không dùng cost âm.
        """
        node = Node(start_state)
        node.g = 0
        node.h = Environment.heuristic(start_state, goal_pos)
        node.cost = node.g + node.h
        frontier = [(node.cost, id(node), node)]
        dist, visit_order = {start_state: 0}, []

        while frontier:
            _, _, node = heapq.heappop(frontier)
            # Skip nếu đã tìm thấy đường ngắn hơn
            if node.g > dist.get(node.state, float('inf')):
                continue
            visit_order.append(node.state)
            if node.state == goal_pos:
                return reconstruct(node), visit_order
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                tg = node.g + cost
                if n_state not in dist or tg < dist[n_state]:
                    dist[n_state] = tg
                    child = Node(n_state, node, action=action)
                    child.g = tg
                    child.h = Environment.heuristic(n_state, goal_pos)
                    child.cost = child.g + child.h
                    heapq.heappush(frontier, (child.cost, id(child), child))

        return [], visit_order

    @staticmethod
    def ida_star(grid, start_state, goal_pos, *args):
        """
        IDA* (Iterative Deepening A*): tìm theo DFS với giới hạn f = g + h.
        Fix:
          - Heuristic dương → bound ban đầu hợp lệ.
          - Thêm path_set tránh vòng lặp trong một nhánh DFS.
          - Giới hạn MAX_ITER để không loop vô hạn.
        """
        h0 = Environment.heuristic(start_state, goal_pos)
        bound = max(h0, 1)   # bound tối thiểu là 1
        visit_order = []

        def search(node, g, bound, path_set):
            f = g + Environment.heuristic(node.state, goal_pos)
            visit_order.append(node.state)
            if f > bound:
                return f, None
            if node.state == goal_pos:
                return "FOUND", node
            min_cost = float('inf')
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                if n_state in path_set:     # tránh vòng lặp trong path hiện tại
                    continue
                child = Node(n_state, node, action=action)
                path_set.add(n_state)
                t, result_node = search(child, g + cost, bound, path_set)
                path_set.discard(n_state)
                if t == "FOUND":
                    return "FOUND", result_node
                if t < min_cost:
                    min_cost = t
            return min_cost, None

        root = Node(start_state)
        MAX_ITER = 60   # giới hạn số vòng lặp ngoài

        for _ in range(MAX_ITER):
            path_set = {start_state}
            t, result_node = search(root, 0, bound, path_set)
            if t == "FOUND":
                return reconstruct(result_node), visit_order
            if t == float('inf'):
                return [], visit_order
            bound = t   # tăng bound lên mức nhỏ nhất vượt quá

        return [], visit_order
