import heapq
from environment import Environment, Node, reconstruct

class InformedSearch:
    """
    Chứa các thuật toán Tìm kiếm có thông tin (Informed Search/Heuristic Search).
    Các thuật toán này sử dụng hàm heuristic h(n) để ước lượng chi phí đến đích,
    giúp hướng dẫn quá trình tìm kiếm hiệu quả hơn.
    """
    
    @staticmethod
    def greedy(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm tốt nhất đầu tiên tham lam (Greedy Best-First Search)
        Khám phá nút có vẻ gần đích nhất (h(n) thấp nhất).
        Hàng đợi ưu tiên (priority queue) chỉ được sắp xếp dựa trên giá trị heuristic.
        """
        node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        frontier = [(node.cost, id(node), node)]
        frontier_states = {start_state}              # Track states currently in FRONTIER
        
        reached = set()
        visit_order = []
        
        while frontier:
            # Pop the state n from FRONTIER with the lowest h(n)
            _, _, node = heapq.heappop(frontier)
            
            # Skip stale entries
            if node.state in reached:
                frontier_states.discard(node.state)
                continue
                
            # Goal check upon expansion
            if node.state == goal_pos:
                visit_order.append(node.state)
                return reconstruct(node), visit_order
                
            # Remove n from FRONTIER and add to REACHED
            frontier_states.discard(node.state)
            reached.add(node.state)
            visit_order.append(node.state)
            
            # Expand neighbors
            for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                # If neighbor is neither in FRONTIER nor REACHED -> add to FRONTIER
                if n_state not in frontier_states and n_state not in reached:
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    heapq.heappush(frontier, (child.cost, id(child), child))
                    frontier_states.add(n_state)
                    
        return [], visit_order

    @staticmethod
    def a_star(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm A* (A* Search)
        Khám phá các nút dựa trên hàm đánh giá f(n) = g(n) + h(n)
        Hàng đợi ưu tiên được sắp xếp theo tổng chi phí ước lượng f(n).
        """
        node = Node(start_state)
        node.g = 0
        node.h = Environment.heuristic(start_state, goal_pos)
        node.cost = node.g + node.h
        
        frontier = [(node.cost, id(node), node)]
        frontier_dict = {start_state: node.g}        # State -> g(state) for states in FRONTIER
        reached = {}                                 # State -> g(state) for expanded states
        visit_order = []
        
        while frontier:
            # Pop node with lowest f(n)
            _, _, node = heapq.heappop(frontier)
            
            # Skip stale entries (already expanded with a better cost)
            if node.state in reached:
                frontier_dict.pop(node.state, None)
                continue
                
            if node.state == goal_pos:
                visit_order.append(node.state)
                return reconstruct(node), visit_order
                
            # Remove from FRONTIER and add to REACHED
            frontier_dict.pop(node.state, None)
            reached[node.state] = node.g
            visit_order.append(node.state)
            
            # Expand neighbors
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                g_new = node.g + cost
                h_val = Environment.heuristic(n_state, goal_pos)
                
                # Case 1: Neighbor already expanded (in REACHED)
                if n_state in reached:
                    if g_new >= reached[n_state]:
                        continue # Found a worse path to an already expanded node
                    else:
                        # Found a better path to an already expanded node -> Move back to FRONTIER
                        del reached[n_state]
                        child = Node(n_state, node, action=action)
                        child.g = g_new
                        child.h = h_val
                        child.cost = child.g + child.h
                        frontier_dict[n_state] = g_new
                        heapq.heappush(frontier, (child.cost, id(child), child))
                        
                # Case 2: Neighbor already in FRONTIER
                elif n_state in frontier_dict:
                    if g_new < frontier_dict[n_state]:
                        # Found a better path -> Update g(n) and re-push
                        frontier_dict[n_state] = g_new
                        child = Node(n_state, node, action=action)
                        child.g = g_new
                        child.h = h_val
                        child.cost = child.g + child.h
                        heapq.heappush(frontier, (child.cost, id(child), child))
                        
                # Case 3: Neighbor not seen before
                else:
                    child = Node(n_state, node, action=action)
                    child.g = g_new
                    child.h = h_val
                    child.cost = child.g + child.h
                    frontier_dict[n_state] = g_new
                    heapq.heappush(frontier, (child.cost, id(child), child))
                    
        return [], visit_order

    @staticmethod
    @staticmethod
    def ida_star(grid, start_state, goal_pos, *args):
        visit_order = []
        root = Node(start_state)
        root.g = 0
        threshold = Environment.heuristic(start_state, goal_pos)

        while True:
            frontier = [(root, frozenset([start_state]))]  # (node, path_set)
            next_threshold = float('inf')

            while frontier:
                node, path_set = frontier.pop()

                if node.state == goal_pos:
                    visit_order.append(node.state)
                    return reconstruct(node), visit_order

                visit_order.append(node.state)

                for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                    if n_state in path_set:          # O(1) thay vì O(depth)
                        continue

                    child = Node(n_state, node, action=action)
                    child.g = node.g + cost
                    f = child.g + Environment.heuristic(n_state, goal_pos)
                    child.cost = f

                    if f <= threshold:
                        frontier.append((child, path_set | {n_state}))
                    else:
                        next_threshold = min(next_threshold, f)

            if next_threshold == float('inf'):
                return [], visit_order

            threshold = next_threshold