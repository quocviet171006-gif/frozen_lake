from collections import deque
from environment import Environment, Node, reconstruct

class UninformedSearch:
    """
    Chứa các thuật toán Tìm kiếm Mù (Uninformed Search).
    Các thuật toán này không sử dụng thông tin heuristic để hướng dẫn tìm kiếm.
    """
    
    @staticmethod
    def bfs(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm theo chiều rộng (Breadth-First Search - BFS)
        Khám phá không gian tìm kiếm theo từng tầng, ưu tiên duyệt tất cả các nút
        cùng một độ sâu trước khi chuyển sang độ sâu tiếp theo.
        Đảm bảo tìm được đường đi ngắn nhất (ít số bước nhất).
        """
        node = Node(start_state)
        if start_state == goal_pos: 
            return [start_state], []
            
        frontier = deque([node])                    # FIFO queue
        reached = {start_state}                     # Track visited states
        visit_order = []
        
        while frontier:
            node = frontier.popleft()               # Pop shallowest node
            visit_order.append(node.state)
            
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(nb_state, node, action=action)
                s = child.state
                
                if s == goal_pos:
                    visit_order.append(s)
                    return reconstruct(child), visit_order
                    
                if s not in reached:
                    reached.add(s)
                    frontier.append(child)
                    
        return [], visit_order

    @staticmethod
    def dfs(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm theo chiều sâu (Depth-First Search - DFS)
        Khám phá không gian tìm kiếm bằng cách ưu tiên đi sâu vào các nhánh.
        Sử dụng ngăn xếp (LIFO stack) để lưu trữ các nút.
        """
        node = Node(start_state)
        if start_state == goal_pos: 
            return [start_state], []
            
        frontier = [node]                           # LIFO stack
        reached = {start_state}
        visit_order = []
        
        while frontier:
            node = frontier.pop()                   # Pop deepest node
            visit_order.append(node.state)
            
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(nb_state, node, action=action)
                s = child.state
                
                if s == goal_pos:
                    visit_order.append(s)
                    return reconstruct(child), visit_order
                    
                if s not in reached:
                    reached.add(s)
                    frontier.append(child)          # Push to stack
                    
        return [], visit_order

    @staticmethod
    def ucs(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm chi phí cực tiểu (Uniform Cost Search - UCS)
        Sử dụng hàng đợi ưu tiên (priority queue) để mở rộng các nút có chi phí đường đi
        hiện tại thấp nhất (g(n)).
        Trong môi trường lưới này, vì mọi bước đi đều có chi phí là 1, UCS hoạt động
        giống hệt BFS nhưng sử dụng hàng đợi ưu tiên.
        """
        import heapq
        node = Node(start_state, cost=0)
        
        # Priority queue ordered by path cost: (cost, id, node)
        frontier = [(node.cost, id(node), node)]
        frontier_dict = {start_state: node.cost}         
        explored = set()                                 
        visit_order = []
        
        while frontier:
            _, _, node = heapq.heappop(frontier)         # Pop lowest-cost node
            
            # Skip stale entries (from replaced nodes in the priority queue)
            if node.state in explored:
                continue
                
            if node.state == goal_pos:
                visit_order.append(node.state)
                return reconstruct(node), visit_order
                
            explored.add(node.state)
            frontier_dict.pop(node.state, None)
            visit_order.append(node.state)
            
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(n_state, node, cost=node.cost + cost, action=action)
                
                # Case 1: State not explored and not in frontier -> Insert
                if n_state not in explored and n_state not in frontier_dict:
                    frontier_dict[n_state] = child.cost
                    heapq.heappush(frontier, (child.cost, id(child), child))
                    
                # Case 2: State in frontier but child has lower cost -> Replace
                elif n_state in frontier_dict and child.cost < frontier_dict[n_state]:
                    frontier_dict[n_state] = child.cost  
                    heapq.heappush(frontier, (child.cost, id(child), child))
                    
        return [], visit_order