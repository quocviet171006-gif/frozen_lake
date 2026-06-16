from config import GameConfig
from environment import Environment

class NondeterministicSearch:
    @staticmethod
    def and_or_graph_search(grid, start_state, goal_pos, *args):
        start = start_state
        actions = ["Up", "Down", "Left", "Right"]
        act_map = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
        
        def results(state, a):
            r, c = state
            dr, dc = act_map[a]
            if grid[r][c] == GameConfig.HOLE: # slippery
                outcomes = set()
                for adr, adc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + adr, c + adc
                    if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                        if not Environment.ALLOW_HOLES and grid[nr][nc] == GameConfig.HOLE:
                            outcomes.add((r, c))
                        else:
                            outcomes.add((nr, nc))
                    else:
                        outcomes.add((r, c))
                return list(outcomes)
            else:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                    if not Environment.ALLOW_HOLES and grid[nr][nc] == GameConfig.HOLE:
                        return [(r, c)]
                    return [(nr, nc)]
                return [(r, c)]
                
        def or_search(state, path):
            if state == goal_pos: return {}
            if state in path: return None
            for a in actions:
                plan = and_search(results(state, a), path + [state])
                if plan is not None:
                    return {state: a, **plan}
            return None
            
        def and_search(states, path):
            plan = {}
            for s in states:
                p = or_search(s, path)
                if p is None: return None
                plan.update(p)
            return plan

        policy = or_search(start, [])
        if policy is None: return [], []
        return policy, list(policy.keys())
