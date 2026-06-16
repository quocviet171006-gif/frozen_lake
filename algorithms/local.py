import random
import math
from environment import Environment, Node, reconstruct

class LocalSearch:
    @staticmethod
    def simple_hc(grid, start_state, goal_pos, *args):
        node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        visit_order = [start_state]
        while True:
            if node.state == goal_pos: break
            nbs = Environment.get_cost_transitions(grid, node.state, goal_pos)
            if not nbs: break
            better_found = False
            for n_state, _, action in nbs:
                child_cost = Environment.heuristic(n_state, goal_pos)
                if child_cost < node.cost:
                    node = Node(n_state, node, cost=child_cost, action=action)
                    if node.state not in visit_order: visit_order.append(node.state)
                    better_found = True
                    break
            if not better_found: break
        return reconstruct(node), visit_order

    @staticmethod
    def beam_search(grid, start_state, goal_pos, *args):
        k = 2
        beam = [Node(start_state, cost=Environment.heuristic(start_state, goal_pos))]
        visit_order = [start_state]
        while beam:
            next_states = []
            for node in beam:
                if node.state == goal_pos: return reconstruct(node), visit_order
                for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    next_states.append(child)
            if not next_states: break
            next_states.sort(key=lambda x: x.cost)
            beam = next_states[:k]
            for b in beam: visit_order.append(b.state)
        return [], visit_order

    @staticmethod
    def simulated_annealing(grid, start_state, goal_pos, *args):
        current = start_state
        current_cost = Environment.heuristic(start_state, goal_pos)
        # Track explicit path to avoid cycles in parent-chain reconstruction
        path = [start_state]
        path_set = {start_state}
        best_path = [start_state]
        best_cost = current_cost
        visit_order = [start_state]
        T, Tmin, alpha = 100, 1, 0.95
        while T > Tmin:
            if current == goal_pos: break
            nbs = Environment.get_cost_transitions(grid, current, goal_pos)
            if not nbs: break
            n_state, _, action = random.choice(nbs)
            child_cost = Environment.heuristic(n_state, goal_pos)
            delta = child_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / T):
                current = n_state
                current_cost = child_cost
                if current not in path_set:
                    path.append(current)
                    path_set.add(current)
                else:
                    # Cut path back to where we saw this state (avoid cycle)
                    idx = path.index(current)
                    path = path[:idx+1]
                    path_set = set(path)
                if current not in visit_order:
                    visit_order.append(current)
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_path = path[:]
            T *= alpha
        # If we reached goal, return actual path; else return best path found
        if current == goal_pos:
            return path, visit_order
        return best_path, visit_order
