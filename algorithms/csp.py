import random
from collections import deque
from config import GameConfig

class CSPGenerator:
    @staticmethod
    def generate_map_backtracking():
        # Variables: 1 Santa, 1 House, 10 Holes, 6 Mounts = 18 items
        items = ["Santa", "House"] + ["Hole"]*10 + ["Mount"]*6
        domains = {i: list(range(64)) for i in range(len(items))}
        
        def constraint_check(assignment):
            if len(assignment) != len(items): return True
            s_idx, h_idx = 0, 1
            mount_indices = [i for i, x in enumerate(items) if x == "Mount"]
            s_pos = (assignment[s_idx]//GameConfig.GRID, assignment[s_idx]%GameConfig.GRID)
            h_pos = (assignment[h_idx]//GameConfig.GRID, assignment[h_idx]%GameConfig.GRID)
            m_poses = set((assignment[m]//GameConfig.GRID, assignment[m]%GameConfig.GRID) for m in mount_indices)
            
            q = deque([s_pos])
            visited = {s_pos}
            while q:
                r, c = q.popleft()
                if (r, c) == h_pos: return True
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0<=nr<GameConfig.GRID and 0<=nc<GameConfig.GRID and (nr,nc) not in m_poses and (nr,nc) not in visited:
                        visited.add((nr,nc))
                        q.append((nr,nc))
            return False

        def backtrack(assignment):
            yield assignment
            if len(assignment) == len(items):
                if constraint_check(assignment): yield assignment
                return
                
            var = len(assignment)
            random.shuffle(domains[var])
            for val in domains[var]:
                if val not in assignment.values():
                    assignment[var] = val
                    yield from backtrack(assignment)
                    # If we reached the end successfully
                    if len(assignment) == len(items) and constraint_check(assignment):
                        return
                    del assignment[var]

        yield from backtrack({})

    @staticmethod
    def generate_map_forward_checking():
        items = ["Santa", "House"] + ["Hole"]*10 + ["Mount"]*6
        domains = {i: list(range(64)) for i in range(len(items))}
        
        def constraint_check(assignment):
            if len(assignment) != len(items): return True
            s_idx, h_idx = 0, 1
            mount_indices = [i for i, x in enumerate(items) if x == "Mount"]
            s_pos = (assignment[s_idx]//GameConfig.GRID, assignment[s_idx]%GameConfig.GRID)
            h_pos = (assignment[h_idx]//GameConfig.GRID, assignment[h_idx]%GameConfig.GRID)
            m_poses = set((assignment[m]//GameConfig.GRID, assignment[m]%GameConfig.GRID) for m in mount_indices)
            q = deque([s_pos])
            visited = {s_pos}
            while q:
                r, c = q.popleft()
                if (r, c) == h_pos: return True
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0<=nr<GameConfig.GRID and 0<=nc<GameConfig.GRID and (nr,nc) not in m_poses and (nr,nc) not in visited:
                        visited.add((nr,nc))
                        q.append((nr,nc))
            return False

        def fc_search(assignment, doms):
            yield assignment
            if len(assignment) == len(items):
                if constraint_check(assignment): yield assignment
                return

            var = len(assignment)
            vals = doms[var][:]
            random.shuffle(vals)
            
            for val in vals:
                assignment[var] = val
                # Forward checking: remove val from other domains
                new_doms = {k: v[:] for k, v in doms.items()}
                valid = True
                for k in range(var+1, len(items)):
                    if val in new_doms[k]:
                        new_doms[k].remove(val)
                    if not new_doms[k]:
                        valid = False
                        break
                
                if valid:
                    yield from fc_search(assignment, new_doms)
                    if len(assignment) == len(items) and constraint_check(assignment): return
                
                del assignment[var]

        yield from fc_search({}, domains)
