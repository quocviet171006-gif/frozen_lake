from collections import deque
from environment import Environment, Node, reconstruct

class UninformedSearch:
    @staticmethod
    def bfs(grid, start_state, goal_pos, *args):
        # BFS Type 2: Check goal BEFORE pushing to frontier
        if start_state == goal_pos: return [start_state], []
        node = Node(start_state)
        frontier, reached, visit_order = deque([node]), {start_state}, []
        while frontier:
            node = frontier.popleft()
            visit_order.append(node.state)
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                if nb_state not in reached:
                    child = Node(nb_state, node, action=action)
                    if child.state == goal_pos:
                        visit_order.append(child.state)
                        return reconstruct(child), visit_order
                    reached.add(child.state)
                    frontier.append(child)
        return [], visit_order

    @staticmethod
    def dfs(grid, start_state, goal_pos, *args):
        # DFS Type 2: Check goal BEFORE pushing to frontier
        if start_state == goal_pos: return [start_state], []
        node = Node(start_state)
        frontier, explored, visit_order = [node], set(), []
        while frontier:
            node = frontier.pop()
            explored.add(node.state)
            visit_order.append(node.state)
            
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                if nb_state not in explored:
                    child = Node(nb_state, node, action=action)
                    if child.state == goal_pos:
                        visit_order.append(child.state)
                        return reconstruct(child), visit_order
                    frontier.append(child)
        return [], visit_order

    @staticmethod
    def ucs(grid, start_state, goal_pos, *args):
        import heapq
        node = Node(start_state, cost=0)
        frontier = [(node.cost, id(node), node)]
        explored, dist, visit_order = set(), {start_state: 0}, []
        while frontier:
            _, _, node = heapq.heappop(frontier)
            if node.state in explored: continue
            explored.add(node.state)
            visit_order.append(node.state)
            if node.state == goal_pos: return reconstruct(node), visit_order
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                new_cost = node.cost + cost
                if n_state not in dist or new_cost < dist[n_state]:
                    dist[n_state] = new_cost
                    child = Node(n_state, node, cost=new_cost, action=action)
                    heapq.heappush(frontier, (new_cost, id(child), child))
        return [], visit_order
