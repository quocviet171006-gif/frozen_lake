from collections import deque
from environment import Environment, Node, reconstruct_actions

class SensorlessSearch:
    @staticmethod
    def is_goal(b_state, house_pos):
        return len(b_state) > 0 and b_state.issubset({house_pos})

    @staticmethod
    def sensorless_bfs(grid, start_state, goal_pos, *args):
        initial_b = Environment.get_initial_belief(grid)
        node = Node(initial_b)
        if SensorlessSearch.is_goal(initial_b, goal_pos): return reconstruct_actions(node), [initial_b]
        
        frontier = deque([node])
        explored = {initial_b}
        visit_order = []
        
        actions = ["Up", "Down", "Left", "Right"]
        while frontier:
            node = frontier.popleft()
            visit_order.append(node.state)
            for a in actions:
                new_b = Environment.sensorless_transition(grid, node.state, a)
                if new_b not in explored:
                    child = Node(new_b, node, action=a)
                    if SensorlessSearch.is_goal(new_b, goal_pos):
                        visit_order.append(new_b)
                        return reconstruct_actions(child), visit_order
                    explored.add(new_b)
                    frontier.append(child)
        return [], visit_order

    @staticmethod
    def sensorless_dfs(grid, start_state, goal_pos, *args):
        initial_b = Environment.get_initial_belief(grid)
        node = Node(initial_b)
        frontier, explored, visit_order = [node], set(), []
        
        actions = ["Up", "Down", "Left", "Right"]
        while frontier:
            node = frontier.pop()
            explored.add(node.state)
            visit_order.append(node.state)
            if SensorlessSearch.is_goal(node.state, goal_pos): return reconstruct_actions(node), visit_order
            for a in actions:
                new_b = Environment.sensorless_transition(grid, node.state, a)
                if new_b not in explored:
                    frontier.append(Node(new_b, node, action=a))
        return [], visit_order
