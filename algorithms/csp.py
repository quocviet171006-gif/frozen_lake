"""
csp.py — Constraint Satisfaction Problem (AIMA Ch. 6)
======================================================
3 thuật toán sinh map cho Frozen Lake dựa trên CSP:

Mô hình chung (CSP Map Generation):
  Variables : tất cả ô (r,c) trong grid N×N
  Domain    : {FROZEN, HOLE, MOUNT, SANTA_HOUSE}
               SANTA_HOUSE = Santa + House cùng 1 ô (goal state)
  Constraints:
    - Đúng 1 ô SANTA_HOUSE
    - Tối đa 10 HOLE, tối đa 6 MOUNT
    - HOLE không kề SANTA_HOUSE (constraint an toàn)
    - Có đường đi từ Santa đến House (sau khi gán xong)

Ý tưởng hiển thị (giống Forward Checking):
  - Vật phẩm (Hole, Mount, House) xuất hiện dần trên bản đồ
  - Santa được đặt ở ô cuối trùng với ngôi nhà (SANTA_HOUSE)
  - Generator yield từng trạng thái gán để animation

Thuật toán:
  1. Backtracking + Forward Checking (AIMA Fig. 6.5 + FC)
  2. AC-3 (AIMA Fig. 6.3) → tiền xử lý → rồi backtrack
  3. Min-Conflicts (AIMA Fig. 6.8) → local search trực tiếp
"""

import random
from collections import deque
from config import GameConfig

# ── Tile constants ───────────────────────────────────────────────────────────
FROZEN     = GameConfig.SNOW   # 0
HOLE       = GameConfig.HOLE   # 1
MOUNT      = GameConfig.MOUNT  # 2
HOUSE      = GameConfig.HOUSE  # 4
SANTA      = 5                 # internal marker: vị trí Santa (chỉ dùng nội bộ CSP)
SANTA_HOUSE = 6                # marker: đây là Ngôi nhà (House/goal)

# ── Limits ───────────────────────────────────────────────────────────────────
MAX_HOLES  = 10
MAX_MOUNTS = 6


# ═══════════════════════════════════════════════════════════════════════════
class CSPGenerator:
    """
    CSP Map Generator — cung cấp 3 thuật toán sinh bản đồ.
    Mỗi hàm là một generator yield dict assignment từng bước (để animate).
    """

    # ── CSP helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_csp():
        """Xây dựng variables (list ô) và domains ban đầu."""
        size = GameConfig.GRID
        variables = [(r, c) for r in range(size) for c in range(size)]
        # Mỗi ô có thể là: Tuyết, Hố, Núi, Ngôi nhà, hoặc vị trí Santa
        domains   = {cell: [FROZEN, HOLE, MOUNT, SANTA_HOUSE, SANTA] for cell in variables}
        return variables, domains

    @staticmethod
    def _get_neighbors(cell):
        """4-connected neighbors của cell."""
        r, c = cell
        return [
            (r + dr, c + dc)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
            if 0 <= r+dr < GameConfig.GRID and 0 <= c+dc < GameConfig.GRID
        ]

    @staticmethod
    def _is_consistent(cell, value, assignment):
        """
        Kiểm tra tính nhất quán khi gán value cho cell.
        - Đúng 1 SANTA_HOUSE (Ngôi nhà) trong toàn bộ grid
        - Đúng 1 SANTA (vị trí Santa) trong toàn bộ grid
        - Tối đa MAX_HOLES HOLE và MAX_MOUNTS MOUNT
        - HOLE không kề SANTA_HOUSE
        - SANTA không đứng cùng ô SANTA_HOUSE, HOLE, MOUNT
        """
        santa_house_count = sum(1 for v in assignment.values() if v == SANTA_HOUSE)
        santa_count       = sum(1 for v in assignment.values() if v == SANTA)
        hole_count        = sum(1 for v in assignment.values() if v == HOLE)
        mount_count       = sum(1 for v in assignment.values() if v == MOUNT)

        if value == SANTA_HOUSE and santa_house_count >= 1:
            return False
        if value == SANTA and santa_count >= 1:
            return False
        if value == HOLE  and hole_count  >= MAX_HOLES:
            return False
        if value == MOUNT and mount_count >= MAX_MOUNTS:
            return False

        # Lấy vị trí hiện tại của các ô đặc biệt
        existing_santa_house = next((c for c, v in assignment.items() if v == SANTA_HOUSE), None)
        existing_santa       = next((c for c, v in assignment.items() if v == SANTA), None)

        # SANTA không được đứng trùng Ngôi nhà (cũng không được kề Hố để an toàn)
        if value == SANTA and existing_santa_house == cell:
            return False
        if value == SANTA_HOUSE and existing_santa == cell:
            return False

        for nb in CSPGenerator._get_neighbors(cell):
            if nb in assignment:
                nb_val = assignment[nb]
                if value == HOLE and nb_val == SANTA_HOUSE:
                    return False
                if value == SANTA_HOUSE and nb_val == HOLE:
                    return False

        return True

    @staticmethod
    def _assignment_complete(assignment):
        """
        Kiểm tra assignment hoàn chỉnh và hợp lệ:
        - Gán đủ tất cả ô
        - Đúng 1 SANTA_HOUSE (Ngôi nhà)
        - Đúng 1 SANTA (vị trí bắt đầu)
        """
        if len(assignment) != GameConfig.GRID * GameConfig.GRID:
            return False
        santa_house_count = sum(1 for v in assignment.values() if v == SANTA_HOUSE)
        santa_count       = sum(1 for v in assignment.values() if v == SANTA)
        return santa_house_count == 1 and santa_count == 1

    @staticmethod
    def _select_unassigned_variable(variables, assignment, domains):
        """MRV heuristic: chọn ô chưa gán có domain nhỏ nhất."""
        unassigned = [v for v in variables if v not in assignment]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: len(domains[v]))

    @staticmethod
    def _to_game_format(assignment):
        """
        Chuyển {(r,c): tile_type} → {index: flat_position} cho game.py.
        Format: index 0 = Santa, 1 = House, 2-11 = Holes, 12-17 = Mounts.
        Santa (SANTA) và House (SANTA_HOUSE) là 2 ô khác nhau do CSP quyết định.
        """
        if not assignment:
            return None

        s_pos = h_pos = None
        holes, mounts = [], []

        for cell, val in assignment.items():
            r, c = cell
            flat = r * GameConfig.GRID + c
            if val == SANTA:
                s_pos = flat
            elif val == SANTA_HOUSE:
                h_pos = flat
            elif val == HOLE:
                holes.append(flat)
            elif val == MOUNT:
                mounts.append(flat)

        if s_pos is None or h_pos is None:
            return None

        result = {0: s_pos, 1: h_pos}
        for i, h in enumerate(holes[:MAX_HOLES]):
            result[2 + i] = h
        for i, m in enumerate(mounts[:MAX_MOUNTS]):
            result[12 + i] = m

        # Pad thiếu hole / mount bằng ô FROZEN chưa dùng
        used   = set(result.values())
        unused = [
            r * GameConfig.GRID + c
            for r in range(GameConfig.GRID)
            for c in range(GameConfig.GRID)
            if r * GameConfig.GRID + c not in used
        ]
        random.shuffle(unused)
        idx = 0
        for i in range(2, 12):
            if i not in result and idx < len(unused):
                result[i] = unused[idx]; idx += 1
        for i in range(12, 18):
            if i not in result and idx < len(unused):
                result[i] = unused[idx]; idx += 1

        return result if len(result) >= 18 else None


    # ═══════════════════════════════════════════════════════════════════════════
    # 1. BACKTRACKING + FORWARD CHECKING  (AIMA Fig. 6.5 + FC)
    # ═══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def generate_map_forward_checking():
        """
        Backtracking Search kết hợp Forward Checking.

        Pseudocode:
          function BACKTRACK(csp, assignment) returns solution or failure
            if assignment is complete → return assignment
            var ← SELECT-UNASSIGNED-VARIABLE(csp, assignment)   // MRV
            for each value in ORDER-DOMAIN-VALUES(csp, var):
              if value is consistent:
                add {var = value} to assignment
                inferences ← FORWARD-CHECKING(csp, var, value, assignment)
                if inferences ≠ failure:
                  result ← BACKTRACK(csp, assignment ∪ inferences)
                  if result ≠ failure → return result
                remove {var = value} and inferences from assignment
            return failure

        Forward Checking: sau khi gán var=value, với mỗi ô kề chưa gán,
        xóa các giá trị vi phạm constraint khỏi domain.
        Nếu domain rỗng → prune ngay.
        """
        variables, domains = CSPGenerator._build_csp()
        random.shuffle(variables)

        def fc_backtrack(assignment, doms):
            yield dict(assignment)   # visualise step

            if CSPGenerator._assignment_complete(assignment):
                yield dict(assignment)
                return

            # SELECT-UNASSIGNED-VARIABLE (MRV)
            cell = CSPGenerator._select_unassigned_variable(variables, assignment, doms)
            if cell is None:
                return

            # ORDER-DOMAIN-VALUES (random order)
            vals = doms[cell][:]
            random.shuffle(vals)

            for value in vals:
                # Consistent check
                if not CSPGenerator._is_consistent(cell, value, assignment):
                    continue

                assignment[cell] = value
                saved = {k: v[:] for k, v in doms.items()}   # save domains

                # ── FORWARD CHECKING ──────────────────────────────
                fc_ok = True
                for nb in CSPGenerator._get_neighbors(cell):
                    if nb in assignment:
                        continue
                    # Xóa giá trị vi phạm constraint với (cell, value)
                    if value == HOLE:
                        doms[nb] = [v for v in doms[nb] if v != SANTA_HOUSE]
                    if value == SANTA_HOUSE:
                        doms[nb] = [v for v in doms[nb] if v != HOLE]
                    if not doms[nb]:   # domain rỗng → prune
                        fc_ok = False
                        break

                # Tính nhất quán toàn cục: SANTA_HOUSE chỉ xuất hiện 1 lần
                if fc_ok and value == SANTA_HOUSE:
                    for other in variables:
                        if other not in assignment and other != cell:
                            doms[other] = [v for v in doms[other] if v != SANTA_HOUSE]
                            if not doms[other]:
                                fc_ok = False
                                break

                if fc_ok:
                    yield from fc_backtrack(assignment, doms)
                    if CSPGenerator._assignment_complete(assignment):
                        return

                # Restore domains + remove assignment
                for k in saved:
                    doms[k] = saved[k]
                del assignment[cell]

        yield from fc_backtrack({}, domains)


    # ═══════════════════════════════════════════════════════════════════════════
    # 2. AC-3 (AIMA Fig. 6.3) → tiền xử lý domain → rồi Backtrack
    # ═══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def generate_map_ac3():
        """
        AC-3 (Arc Consistency 3) + Backtracking.

        Bước 1: Chạy AC-3 để thu hẹp domains trước khi tìm kiếm.
        Bước 2: Backtracking trên domains đã được thu hẹp.

        Pseudocode AC-3:
          function AC-3(csp) returns csp with reduced domains
            queue ← tất cả arcs (Xi, Xj) trong csp
            while queue not empty:
              (Xi, Xj) ← REMOVE-FIRST(queue)
              if RM-INCONSISTENT-VALUES(Xi, Xj):
                for each Xk in NEIGHBORS[Xi]:
                  add (Xk, Xi) to queue

          function RM-INCONSISTENT-VALUES(Xi, Xj):
            removed ← false
            for each x in DOMAIN[Xi]:
              if no y in DOMAIN[Xj] allows (x,y) to satisfy constraint(Xi,Xj):
                delete x from DOMAIN[Xi]; removed ← true
            return removed

        Constraint giữa các ô kề:
          (HOLE, SANTA_HOUSE) và (SANTA_HOUSE, HOLE) là bất nhất quán.
        """
        variables, domains = CSPGenerator._build_csp()
        random.shuffle(variables)

        # ── AC-3 tiền xử lý ──────────────────────────────────────────────────
        def constraint_ok(val_i, val_j):
            """Constraint giữa 2 ô kề nhau: trả về True nếu (val_i, val_j) hợp lệ."""
            if val_i == HOLE and val_j == SANTA_HOUSE:
                return False
            if val_i == SANTA_HOUSE and val_j == HOLE:
                return False
            return True

        def rm_inconsistent_values(xi, xj):
            """
            RM-INCONSISTENT-VALUES(Xi, Xj):
              removed ← false
              for each x in DOMAIN[Xi]:
                if no y in DOMAIN[Xj] allows (x,y) to satisfy constraint:
                  delete x from DOMAIN[Xi]; removed ← true
              return removed
            """
            removed = False
            new_domain = []
            for x in domains[xi]:
                # Tồn tại y trong DOMAIN[Xj] thỏa constraint(xi=x, xj=y)?
                if any(constraint_ok(x, y) for y in domains[xj]):
                    new_domain.append(x)
                else:
                    removed = True
            domains[xi] = new_domain
            return removed

        def run_ac3():
            """
            AC-3: thu hẹp domains bằng arc consistency.
            queue khởi đầu = tất cả arcs (Xi, Xj) là cặp ô kề nhau.
            """
            # queue ← tất cả arcs trong csp
            queue = deque()
            for cell in variables:
                for nb in CSPGenerator._get_neighbors(cell):
                    queue.append((cell, nb))
                    queue.append((nb, cell))

            while queue:
                xi, xj = queue.popleft()   # (Xi, Xj) ← REMOVE-FIRST(queue)
                if rm_inconsistent_values(xi, xj):
                    # for each Xk in NEIGHBORS[Xi]: add (Xk, Xi) to queue
                    for xk in CSPGenerator._get_neighbors(xi):
                        if xk != xj:
                            queue.append((xk, xi))
                    # Nếu domain rỗng → CSP vô nghiệm (không xảy ra với map này)
                    if not domains[xi]:
                        return False
            return True

        # Chạy AC-3 để thu hẹp domain
        ac3_ok = run_ac3()
        if not ac3_ok:
            return

        # Yield trạng thái sau AC-3 để visualise (hiện grid trống, domain đã thu gọn)
        yield {}

        # ── Backtracking trên domains đã thu hẹp ─────────────────────────────
        def backtrack(assignment, doms):
            yield dict(assignment)

            if CSPGenerator._assignment_complete(assignment):
                yield dict(assignment)
                return

            # SELECT-UNASSIGNED-VARIABLE (MRV)
            cell = CSPGenerator._select_unassigned_variable(variables, assignment, doms)
            if cell is None:
                return

            vals = doms[cell][:]
            random.shuffle(vals)

            for value in vals:
                if not CSPGenerator._is_consistent(cell, value, assignment):
                    continue

                assignment[cell] = value
                saved = {k: v[:] for k, v in doms.items()}

                # Forward Checking nhẹ (kế thừa tinh thần AC-3)
                fc_ok = True
                for nb in CSPGenerator._get_neighbors(cell):
                    if nb in assignment:
                        continue
                    if value == HOLE:
                        doms[nb] = [v for v in doms[nb] if v != SANTA_HOUSE]
                    if value == SANTA_HOUSE:
                        doms[nb] = [v for v in doms[nb] if v != HOLE]
                    if not doms[nb]:
                        fc_ok = False
                        break

                if fc_ok and value == SANTA_HOUSE:
                    for other in variables:
                        if other not in assignment and other != cell:
                            doms[other] = [v for v in doms[other] if v != SANTA_HOUSE]
                            if not doms[other]:
                                fc_ok = False
                                break

                if fc_ok:
                    yield from backtrack(assignment, doms)
                    if CSPGenerator._assignment_complete(assignment):
                        return

                for k in saved:
                    doms[k] = saved[k]
                del assignment[cell]

        yield from backtrack({}, domains)


    # ═══════════════════════════════════════════════════════════════════════════
    # 3. MIN-CONFLICTS  (AIMA Fig. 6.8)
    # ═══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def generate_map_min_conflicts(max_steps=2000):
        """
        Min-Conflicts: local search trực tiếp trên assignment hoàn chỉnh.

        Pseudocode (AIMA Fig. 6.8):
          function MIN-CONFLICTS(csp, max_steps) returns solution or failure
            current ← initial complete assignment for csp
            for i = 1 to max_steps:
              if current is a solution → return current
              var ← randomly chosen CONFLICTED variable from csp.VARIABLES
              value ← the value v for var that minimizes CONFLICTS(var,v,current,csp)
              set var = value in current
            return failure

        Áp dụng cho map generation:
        - Initial assignment: gán ngẫu nhiên đủ tile cho tất cả ô.
          Đảm bảo đúng số lượng: 1 SANTA_HOUSE, 10 HOLE, 6 MOUNT, còn lại FROZEN.
        - Conflicted variable: ô đang vi phạm constraint.
        - CONFLICTS(var, v): đếm số constraint bị vi phạm khi gán v cho var.
        - Lặp cho đến khi không còn conflict hoặc hết max_steps.
        """

        size = GameConfig.GRID
        N    = size * size

        # ── Tạo initial complete assignment ──────────────────────────────────
        def make_initial():
            """
            Tạo assignment hoàn chỉnh ngẫu nhiên:
            - 1 ô SANTA_HOUSE (Ngôi nhà)
            - 1 ô SANTA (vị trí bắt đầu của Santa, khác Ngôi nhà)
            - MAX_HOLES ô HOLE
            - MAX_MOUNTS ô MOUNT
            - Còn lại: FROZEN
            """
            cells = [(r, c) for r in range(size) for c in range(size)]
            random.shuffle(cells)
            assignment = {}
            assignment[cells[0]] = SANTA_HOUSE
            assignment[cells[1]] = SANTA
            for i in range(2, MAX_HOLES + 2):
                assignment[cells[i]] = HOLE
            for i in range(MAX_HOLES + 2, MAX_HOLES + MAX_MOUNTS + 2):
                assignment[cells[i]] = MOUNT
            for i in range(MAX_HOLES + MAX_MOUNTS + 2, N):
                assignment[cells[i]] = FROZEN
            return assignment

        def count_conflicts(cell, value, assignment):
            """
            CONFLICTS(var, value, current, csp):
            Đếm số constraint bị vi phạm khi gán value cho cell,
            với phần còn lại giữ nguyên assignment.
            """
            conflicts = 0
            for nb in CSPGenerator._get_neighbors(cell):
                nb_val = assignment.get(nb, FROZEN)
                if value == HOLE and nb_val == SANTA_HOUSE:
                    conflicts += 1
                if value == SANTA_HOUSE and nb_val == HOLE:
                    conflicts += 1
            # Santa không được đứng trùng Ngôi nhà
            if value == SANTA:
                house_pos = next((c for c, v in assignment.items() if v == SANTA_HOUSE and c != cell), None)
                if house_pos == cell:
                    conflicts += 1
            return conflicts

        def get_conflicted_cells(assignment):
            """Trả về danh sách các ô đang vi phạm ít nhất 1 constraint."""
            conflicted = []
            for cell, value in assignment.items():
                if count_conflicts(cell, value, assignment) > 0:
                    conflicted.append(cell)
            return conflicted

        def is_solution(assignment):
            """Kiểm tra assignment là solution hợp lệ."""
            # Đúng 1 SANTA_HOUSE và 1 SANTA
            if sum(1 for v in assignment.values() if v == SANTA_HOUSE) != 1:
                return False
            if sum(1 for v in assignment.values() if v == SANTA) != 1:
                return False
            # Không có conflict
            return len(get_conflicted_cells(assignment)) == 0

        # ── Khởi tạo ─────────────────────────────────────────────────────────
        current = make_initial()
        yield dict(current)   # visualise initial state

        # ── Vòng lặp chính Min-Conflicts ─────────────────────────────────────
        # for i = 1 to max_steps:
        for step in range(max_steps):
            # if current is a solution for csp → return current
            if is_solution(current):
                yield dict(current)
                return

            # var ← randomly chosen CONFLICTED variable
            conflicted = get_conflicted_cells(current)
            if not conflicted:
                yield dict(current)
                return

            var = random.choice(conflicted)

            # value ← value v that minimizes CONFLICTS(var, v, current, csp)
            # Lấy domain đầy đủ và tìm giá trị min-conflict
            santa_house_count = sum(1 for v in current.values() if v == SANTA_HOUSE)
            santa_count_ex    = sum(1 for k, v in current.items() if v == SANTA and k != var)
            hole_count  = sum(1 for k, v in current.items() if v == HOLE and k != var)
            mount_count = sum(1 for k, v in current.items() if v == MOUNT and k != var)

            # Xây domain hợp lệ cho var (tuân thủ ràng buộc đếm)
            candidate_values = [FROZEN]
            if hole_count  < MAX_HOLES:  candidate_values.append(HOLE)
            if mount_count < MAX_MOUNTS: candidate_values.append(MOUNT)
            # SANTA_HOUSE: chỉ được gán nếu hiện tại var đang giữ SANTA_HOUSE
            # hoặc chưa có SANTA_HOUSE nào
            if santa_house_count == 0 or current[var] == SANTA_HOUSE:
                candidate_values.append(SANTA_HOUSE)
            # SANTA: chỉ được gán nếu var đang giữ SANTA hoặc chưa có SANTA nào
            if santa_count_ex == 0 or current[var] == SANTA:
                candidate_values.append(SANTA)

            # Chọn value minimizes conflicts
            min_conf  = float('inf')
            best_vals = []
            for v in candidate_values:
                # Tạm thời gán để đếm conflict
                old = current[var]
                current[var] = v
                c = count_conflicts(var, v, current)
                current[var] = old
                if c < min_conf:
                    min_conf  = c
                    best_vals = [v]
                elif c == min_conf:
                    best_vals.append(v)

            # set var = value in current
            current[var] = random.choice(best_vals)

            # yield mỗi bước để animate hiển thị quá trình sửa lỗi
            yield dict(current)

        # return failure (hết max_steps)
        yield dict(current)


    # ── Alias giữ tương thích ngược ──────────────────────────────────────────
    @staticmethod
    def generate_map_backtracking():
        """Alias — dùng Forward Checking (thuật toán mạnh hơn backtracking thuần)."""
        yield from CSPGenerator.generate_map_forward_checking()
