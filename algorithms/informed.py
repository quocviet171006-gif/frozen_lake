import heapq
from environment import Environment, Node, reconstruct

class InformedSearch:
    @staticmethod
    def greedy(grid, start_state, goal_pos, *args):
        node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        frontier = [(node.cost, id(node), node)]
        reached, visit_order = {start_state}, []
        while frontier:
            _, _, node = heapq.heappop(frontier)
            visit_order.append(node.state)
            if node.state == goal_pos: return reconstruct(node), visit_order
            for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                if n_state not in reached:
                    reached.add(n_state)
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    heapq.heappush(frontier, (child.cost, id(child), child))
        return [], visit_order

    @staticmethod
    def a_star(grid, start_state, goal_pos, *args):
        node = Node(start_state)
        node.g = 0
        node.h = Environment.heuristic(start_state, goal_pos)
        node.cost = node.g + node.h
        frontier = [(node.cost, id(node), node)]
        dist, visit_order = {start_state: 0}, []
        while frontier:
            _, _, node = heapq.heappop(frontier)
            visit_order.append(node.state)
            if node.state == goal_pos: return reconstruct(node), visit_order
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
        bound = Environment.heuristic(start_state, goal_pos)
        visit_order = []
        def search(node, g, bound):
            f = g + Environment.heuristic(node.state, goal_pos)
            visit_order.append(node.state)
            if f > bound: return f, None
            if node.state == goal_pos: return "FOUND", node
            min_cost = float('inf')
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(n_state, node, action=action)
                t, result_node = search(child, g + cost, bound)
                if t == "FOUND": return "FOUND", result_node
                if t < min_cost: min_cost = t
            return min_cost, None

        root = Node(start_state)
        while True:
            t, result_node = search(root, 0, bound)
            if t == "FOUND": return reconstruct(result_node), visit_order
            if t == float('inf'): return [], visit_order
            bound = t
