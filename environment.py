from config import GameConfig

class Node:
    def __init__(self, state, parent=None, cost=0, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost
        self.g = 0
        self.h = 0
    def __lt__(self, other):
        return self.cost < other.cost

def reconstruct(node):
    path = []
    while node:
        path.append(node.state)
        node = node.parent
    return path[::-1]

def reconstruct_actions(node):
    actions = []
    while node and node.parent:
        actions.append(node.action)
        node = node.parent
    return actions[::-1]

class Environment:
    ALLOW_HOLES = True

    @staticmethod
    def get_cost_transitions(grid, state, house_pos):
        r, c = state
        transitions = []
        for action, (dr, dc) in zip(["Up", "Down", "Left", "Right"], [(-1,0), (1,0), (0,-1), (0,1)]):
            nr, nc = r+dr, c+dc
            if 0<=nr<GameConfig.GRID and 0<=nc<GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                if not Environment.ALLOW_HOLES and grid[nr][nc] == GameConfig.HOLE:
                    continue
                cost = 1
                if grid[nr][nc] == GameConfig.HOLE: cost += 3
                if (nr, nc) == house_pos: cost -= 20
                transitions.append(((nr, nc), cost, action))
        return transitions

    @staticmethod
    def heuristic(state, house_pos):
        r, c = state
        dist = abs(r - house_pos[0]) + abs(c - house_pos[1])
        return dist - 20

    @staticmethod
    def get_initial_belief(grid):
        return frozenset((r, c) for r in range(GameConfig.GRID) for c in range(GameConfig.GRID) if grid[r][c] != GameConfig.MOUNT)

    @staticmethod
    def sensorless_transition(grid, b_state, action):
        act_map = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
        dr, dc = act_map[action]
        new_b = set()
        for r, c in b_state:
            if grid[r][c] == GameConfig.HOLE:
                for adr, adc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + adr, c + adc
                    if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                        if not Environment.ALLOW_HOLES and grid[nr][nc] == GameConfig.HOLE:
                            new_b.add((r, c))
                        else:
                            new_b.add((nr, nc))
                    else:
                        new_b.add((r, c))
            else:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                    if not Environment.ALLOW_HOLES and grid[nr][nc] == GameConfig.HOLE:
                        new_b.add((r, c))
                    else:
                        new_b.add((nr, nc))
                else:
                    new_b.add((r, c))
        return frozenset(new_b)
