from collections import deque
from environment import Environment, Node, reconstruct

class UninformedSearch:
    @staticmethod
    def bfs(grid, start_state, goal_pos, *args):
        # BFS (AIMA 4th ed.): FIFO queue + reached set, goal test on child generation
        node = Node(start_state)
        if start_state == goal_pos: return [start_state], []
        frontier = deque([node])                    # frontier ← a FIFO queue
        reached = {start_state}                     # reached ← {problem.INITIAL}
        visit_order = []
        while frontier:                             # while not IS-EMPTY(frontier)
            node = frontier.popleft()               #   node ← POP(frontier)
            visit_order.append(node.state)
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(nb_state, node, action=action)  # for each child in EXPAND
                s = child.state                              # s ← child.STATE
                if s == goal_pos:                             # if problem.IS-GOAL(s) then return child
                    visit_order.append(s)
                    return reconstruct(child), visit_order
                if s not in reached:                         # if s is not in reached then
                    reached.add(s)                           #   add s to reached
                    frontier.append(child)                   #   add child to frontier
        return [], visit_order

    @staticmethod
    def dfs(grid, start_state, goal_pos, *args):
        # DFS: Same pattern as BFS but with LIFO stack
        node = Node(start_state)
        if start_state == goal_pos: return [start_state], []
        frontier = [node]                           # frontier ← a LIFO stack
        reached = {start_state}                     # reached ← {problem.INITIAL}
        visit_order = []
        while frontier:                             # while not IS-EMPTY(frontier)
            node = frontier.pop()                   #   node ← POP(frontier) /* deepest node */
            visit_order.append(node.state)
            for nb_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(nb_state, node, action=action)  # for each child in EXPAND
                s = child.state                              # s ← child.STATE
                if s == goal_pos:                             # if problem.IS-GOAL(s) then return child
                    visit_order.append(s)
                    return reconstruct(child), visit_order
                if s not in reached:                         # if s is not in reached then
                    reached.add(s)                           #   add s to reached
                    frontier.append(child)                   #   add child to frontier (PUSH)
        return [], visit_order

    @staticmethod
    def ucs(grid, start_state, goal_pos, *args):
        # UCS (AIMA): priority queue by PATH-COST, goal test on expansion
        import heapq
        node = Node(start_state, cost=0)
        frontier = [(node.cost, id(node), node)]        # priority queue ordered by PATH-COST
        frontier_dict = {start_state: node.cost}         # track states in frontier + their cost
        explored = set()                                 # explored ← an empty set
        visit_order = []
        while frontier:                                  # loop do
            _, _, node = heapq.heappop(frontier)         #   node ← POP(frontier) /* lowest-cost */
            # Skip stale entries (from replaced nodes)
            if node.state in explored:
                continue
            if node.state == goal_pos:                   #   if problem.GOAL-TEST(node.STATE)
                visit_order.append(node.state)
                return reconstruct(node), visit_order    #     then return SOLUTION(node)
            explored.add(node.state)                     #   add node.STATE to explored
            frontier_dict.pop(node.state, None)
            visit_order.append(node.state)
            for n_state, cost, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                child = Node(n_state, node, cost=node.cost + cost, action=action)
                # Case 1: child.STATE not in explored or frontier → INSERT
                if n_state not in explored and n_state not in frontier_dict:
                    frontier_dict[n_state] = child.cost
                    heapq.heappush(frontier, (child.cost, id(child), child))
                # Case 2: child.STATE in frontier with higher PATH-COST → REPLACE
                elif n_state in frontier_dict and child.cost < frontier_dict[n_state]:
                    frontier_dict[n_state] = child.cost  #   replace that frontier node with child
                    heapq.heappush(frontier, (child.cost, id(child), child))
        return [], visit_order
