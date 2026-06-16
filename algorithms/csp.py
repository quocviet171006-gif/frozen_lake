import random
from collections import deque
from config import GameConfig

# Tile type constants for CSP domains
FROZEN = GameConfig.SNOW    # 0
HOLE   = GameConfig.HOLE    # 1
MOUNT  = GameConfig.MOUNT   # 2
HOUSE  = GameConfig.HOUSE   # 4
SANTA  = 5                  # special: Santa marker (not a grid tile)
SANTA_HOUSE = 6             # Santa + House on same cell (goal state)

class CSPGenerator:
    """
    CSP-based map generator for Frozen Lake.
    
    Variables: all cells (i,j) in grid_size × grid_size grid
    Domain: {FROZEN, HOLE, MOUNT, SANTA, HOUSE}
    
    Constraints:
    - Exactly 1 SANTA (or SANTA_HOUSE), exactly 1 HOUSE (or SANTA_HOUSE)
    - HOLE, MOUNT cannot overlap with SANTA or HOUSE
    - Neighbors of HOLE cannot be SANTA or HOUSE (danger constraint)
    - Neighbors of SANTA/HOUSE cannot be HOLE (safety constraint)  
    - SANTA and HOUSE can share the same cell (SANTA_HOUSE = goal)
    - Only 1 SANTA and 1 HOUSE globally
    - Path must exist from SANTA to HOUSE (connectivity via BFS)
    - Target: ~10 HOLEs, ~6 MOUNTs
    """
    
    @staticmethod
    def _build_csp():
        """Build CSP variables, domains, and neighbor map."""
        size = GameConfig.GRID
        variables = [(r, c) for r in range(size) for c in range(size)]
        # DOMAIN[cell] ← {FROZEN, HOLE, MOUNT, SANTA_HOUSE}
        # SANTA_HOUSE = Santa + House cùng 1 ô (goal state)
        domains = {}
        for cell in variables:
            domains[cell] = [FROZEN, HOLE, MOUNT, SANTA_HOUSE]
        return variables, domains
    
    @staticmethod
    def _get_neighbors(cell):
        """Get 4-connected neighbors of a cell."""
        r, c = cell
        nbs = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID:
                nbs.append((nr, nc))
        return nbs
    
    @staticmethod
    def _is_consistent(cell, value, assignment):
        """Check if assigning value to cell is consistent with current assignment."""
        # Count existing assignments
        santa_house_count = sum(1 for v in assignment.values() if v == SANTA_HOUSE)
        hole_count = sum(1 for v in assignment.values() if v == HOLE)
        mount_count = sum(1 for v in assignment.values() if v == MOUNT)
        
        # Enforce max counts: exactly 1 SANTA_HOUSE, ~10 HOLEs, ~6 MOUNTs
        if value == SANTA_HOUSE and santa_house_count >= 1: return False
        if value == HOLE and hole_count >= 10: return False
        if value == MOUNT and mount_count >= 6: return False
        
        # Check neighbor constraints
        for nb in CSPGenerator._get_neighbors(cell):
            if nb in assignment:
                nb_val = assignment[nb]
                # HOLE cannot be adjacent to SANTA_HOUSE (and vice versa)
                if value == HOLE and nb_val == SANTA_HOUSE:
                    return False
                if value == SANTA_HOUSE and nb_val == HOLE:
                    return False
        
        return True
    
    @staticmethod
    def _assignment_complete(assignment):
        """Check if assignment covers all variables and meets item requirements."""
        if len(assignment) != GameConfig.GRID * GameConfig.GRID:
            return False
        santa_house_count = sum(1 for v in assignment.values() if v == SANTA_HOUSE)
        if santa_house_count != 1:
            return False
        # SANTA_HOUSE = Santa + House cùng ô → always at goal
        s_pos = h_pos = None
        m_poses = set()
        for cell, val in assignment.items():
            if val == SANTA_HOUSE: s_pos = h_pos = cell
            elif val == MOUNT: m_poses.add(cell)
        if s_pos is None or h_pos is None:
            return False
        if s_pos == h_pos:
            return True  # SANTA_HOUSE: already at goal
        # BFS connectivity check
        q = deque([s_pos])
        visited = {s_pos}
        while q:
            r, c = q.popleft()
            if (r, c) == h_pos:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and (nr, nc) not in m_poses and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return False
    
    @staticmethod
    def _select_unassigned_variable(variables, assignment, domains):
        """SELECT-UNASSIGNED-VARIABLE: pick cell with smallest domain (MRV heuristic)."""
        unassigned = [v for v in variables if v not in assignment]
        if not unassigned:
            return None
        # MRV: cell có miền nhỏ nhất
        return min(unassigned, key=lambda v: len(domains[v]))
    
    @staticmethod
    def _to_game_format(assignment):
        """Convert cell-based assignment to the item-based format game.py expects.
        
        Returns dict {index: flat_position} matching:
        items = ["Santa", "House"] + ["Hole"]*10 + ["Mount"]*6
        """
        result = {}
        s_pos = h_pos = None
        holes = []
        mounts = []
        
        for cell, val in assignment.items():
            r, c = cell
            flat = r * GameConfig.GRID + c
            if val == SANTA_HOUSE:
                s_pos = flat
                h_pos = flat  # Santa and House share the same cell
            elif val == HOLE:
                holes.append(flat)
            elif val == MOUNT:
                mounts.append(flat)
        
        if s_pos is None or h_pos is None:
            return None
        
        # Build items dict: 0=Santa, 1=House, 2-11=Holes, 12-17=Mounts
        result[0] = s_pos   # Santa
        result[1] = h_pos   # House
        for i, h in enumerate(holes[:10]):
            result[2 + i] = h
        for i, m in enumerate(mounts[:6]):
            result[12 + i] = m
        
        # Pad if fewer holes/mounts (fill with unused frozen cells)
        used = set(result.values())
        unused = [r * GameConfig.GRID + c for r in range(GameConfig.GRID) 
                  for c in range(GameConfig.GRID) if r * GameConfig.GRID + c not in used]
        random.shuffle(unused)
        
        idx = 0
        for i in range(2, 12):  # Holes
            if i not in result and unused:
                result[i] = unused[idx]; idx += 1
        for i in range(12, 18):  # Mounts
            if i not in result and idx < len(unused):
                result[i] = unused[idx]; idx += 1
                
        return result if len(result) >= 18 else None

    # ========================================================================
    # BACKTRACKING SEARCH (Pseudocode Image 1 - AIMA)
    # ========================================================================
    @staticmethod
    def generate_map_backtracking():
        """
        function BACKTRACKING-SEARCH(csp) returns a solution or failure
            return BACKTRACK(csp, {})
        """
        variables, domains = CSPGenerator._build_csp()
        random.shuffle(variables)  # Randomize variable order for variety
        
        def backtrack(assignment):
            """
            function BACKTRACK(csp, assignment) returns a solution or failure
            """
            yield dict(assignment)  # Yield current state for visualization
            
            # if assignment is complete then return assignment
            if len(assignment) == len(variables):
                if CSPGenerator._assignment_complete(assignment):
                    yield dict(assignment)
                return
            
            # var ← SELECT-UNASSIGNED-VARIABLE(csp, assignment)
            var = CSPGenerator._select_unassigned_variable(variables, assignment, domains)
            if var is None:
                return
            
            # for each value in ORDER-DOMAIN-VALUES(csp, var, assignment) do
            vals = domains[var][:]
            random.shuffle(vals)  # ORDER-DOMAIN-VALUES: random order for variety
            
            for value in vals:
                # if value is consistent with assignment then
                if CSPGenerator._is_consistent(var, value, assignment):
                    # add {var = value} to assignment
                    assignment[var] = value
                    
                    # result ← BACKTRACK(csp, assignment)
                    yield from backtrack(assignment)
                    
                    # if result ≠ failure then return result
                    if len(assignment) == len(variables) and CSPGenerator._assignment_complete(assignment):
                        return
                    
                    # remove {var = value} from assignment
                    del assignment[var]
            
            # return failure
        
        yield from backtrack({})

    # ========================================================================
    # FORWARD CHECKING (Pseudocode Image 2)
    # ========================================================================
    @staticmethod
    def generate_map_forward_checking():
        """
        function CSP_GENERATE_MAP(grid_size) returns a valid map or failure
            variables ← all cells (i,j)
            DOMAIN[cell] ← {FROZEN, HOLE, SANTA, HOUSE, MOUNT}
            return BACKTRACK(variables, {}, DOMAIN)
        """
        variables, domains = CSPGenerator._build_csp()
        random.shuffle(variables)
        
        def fc_backtrack(assignment, doms):
            """
            function BACKTRACK(variables, assignment, DOMAIN) returns a map or failure
            """
            yield dict(assignment)  # Visualization step
            
            # if assignment is complete then return assignment
            if len(assignment) == len(variables):
                if CSPGenerator._assignment_complete(assignment):
                    yield dict(assignment)
                return
            
            # cell ← ô chưa gán có miền nhỏ nhất (MRV)
            cell = CSPGenerator._select_unassigned_variable(variables, assignment, doms)
            if cell is None:
                return
            
            # for each value in DOMAIN[cell] do
            vals = doms[cell][:]
            random.shuffle(vals)
            
            for value in vals:
                # if value is consistent with assignment then
                if not CSPGenerator._is_consistent(cell, value, assignment):
                    continue
                
                # add {cell = value} to assignment
                assignment[cell] = value
                
                # saved_domains ← COPY(DOMAIN)
                saved_domains = {k: v[:] for k, v in doms.items()}
                
                # FC_OK ← true
                fc_ok = True
                
                # Forward Checking: prune neighbor domains
                # for each neighbor in GET_NEIGHBORS(cell) do
                for neighbor in CSPGenerator._get_neighbors(cell):
                    # if neighbor not in assignment then
                    if neighbor not in assignment:
                        # if value = HOLE then
                        #     DOMAIN[neighbor] ← DOMAIN[neighbor] \ {SANTA_HOUSE}
                        if value == HOLE:
                            doms[neighbor] = [v for v in doms[neighbor] 
                                             if v != SANTA_HOUSE]
                        # if value = SANTA_HOUSE then
                        #     DOMAIN[neighbor] ← DOMAIN[neighbor] \ {HOLE}
                        if value == SANTA_HOUSE:
                            doms[neighbor] = [v for v in doms[neighbor] if v != HOLE]
                        
                        # if DOMAIN[neighbor] = ∅ then FC_OK ← false; break
                        if not doms[neighbor]:
                            fc_ok = False
                            break
                
                # Global uniqueness: if value = SANTA_HOUSE
                # remove SANTA_HOUSE from ALL other unassigned cells
                if fc_ok and value == SANTA_HOUSE:
                    for other_cell in variables:
                        if other_cell not in assignment and other_cell != cell:
                            doms[other_cell] = [v for v in doms[other_cell] 
                                               if v != SANTA_HOUSE]
                            if not doms[other_cell]:
                                fc_ok = False
                                break
                
                # if FC_OK then
                if fc_ok:
                    # result ← BACKTRACK(variables, assignment, DOMAIN)
                    yield from fc_backtrack(assignment, doms)
                    # if result ≠ failure then return result
                    if len(assignment) == len(variables) and CSPGenerator._assignment_complete(assignment):
                        return
                
                # DOMAIN ← saved_domains (restore)
                for k in saved_domains:
                    doms[k] = saved_domains[k]
                
                # remove {cell = value} from assignment
                del assignment[cell]
            
            # return failure
        
        yield from fc_backtrack({}, domains)
