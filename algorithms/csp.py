"""
csp.py — Bài toán thỏa mãn ràng buộc (CSP - AIMA Ch. 6)
======================================================
Cung cấp 3 thuật toán để tạo bản đồ cho mô phỏng Frozen Lake dựa trên CSP.

Mô hình chung tạo bản đồ CSP:
  - Biến (Variables): Tất cả các ô (r, c) trong lưới NxN
  - Miền giá trị (Domain): {FROZEN, HOLE, MOUNT, SANTA_HOUSE} (SANTA_HOUSE = Đích đến)
  
  Ràng buộc (Constraints):
    - Đúng 1 ô SANTA_HOUSE
    - Đúng 10 Hố (HOLE), đúng 6 Núi (MOUNT)
    - Các biến đặc biệt không được trùng nhau và phải đúng số lượng
    - Hố không được nằm kề SANTA_HOUSE (ràng buộc an toàn)
    - Phải có đường đi hợp lệ từ Santa đến Nhà (sau khi gán xong)

Mô phỏng (Theo phong cách Forward Checking):
  - Các vật phẩm (Hố, Núi, Nhà) xuất hiện dần trên bản đồ
  - Santa được đặt ở một ô riêng biệt với Nhà
  - Hàm Generator yield từng trạng thái gán để tạo hoạt ảnh

Các thuật toán đã triển khai:
  1. Quay lui (Backtracking) + Forward Checking (AIMA Fig. 6.5 + FC)
  2. AC-3 (AIMA Fig. 6.3) → tiền xử lý → sau đó quay lui
  3. Min-Conflicts (AIMA Fig. 6.8) → tìm kiếm cục bộ trực tiếp
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
    def _has_path(assignment):
        """Return True if Santa can reach the house without crossing holes or mounts."""
        santa_pos = next((c for c, v in assignment.items() if v == SANTA), None)
        house_pos = next((c for c, v in assignment.items() if v == SANTA_HOUSE), None)
        if santa_pos is None or house_pos is None:
            return False

        blocked = {HOLE, MOUNT}
        queue = deque([santa_pos])
        visited = {santa_pos}

        while queue:
            cell = queue.popleft()
            if cell == house_pos:
                return True

            for nb in CSPGenerator._get_neighbors(cell):
                if nb in visited:
                    continue
                if assignment.get(nb, FROZEN) in blocked:
                    continue
                visited.add(nb)
                queue.append(nb)

        return False

    @staticmethod
    def _holes_not_adjacent_house(assignment):
        house_pos = next((c for c, v in assignment.items() if v == SANTA_HOUSE), None)
        if house_pos is None:
            return True
        return all(assignment.get(nb) != HOLE for nb in CSPGenerator._get_neighbors(house_pos))

    @staticmethod
    def _values_for_step(values, assigned_count):
        """During obstacle placement, reserve Santa and House for the final step."""
        allowed = {FROZEN, HOLE, MOUNT}
        return [value for value in values if value in allowed]

    @staticmethod
    def _counts_feasible(assignment):
        """Prune branches that can no longer reach exact tile counts."""
        total = GameConfig.GRID * GameConfig.GRID
        remaining_slots = total - len(assignment)
        obstacle_slots_left = max(0, remaining_slots - 2)

        hole_count = sum(1 for value in assignment.values() if value == HOLE)
        mount_count = sum(1 for value in assignment.values() if value == MOUNT)
        santa_count = sum(1 for value in assignment.values() if value == SANTA)
        house_count = sum(1 for value in assignment.values() if value == SANTA_HOUSE)

        if hole_count > MAX_HOLES or mount_count > MAX_MOUNTS:
            return False
        if santa_count > 1 or house_count > 1:
            return False
        if hole_count + obstacle_slots_left < MAX_HOLES:
            return False
        if mount_count + obstacle_slots_left < MAX_MOUNTS:
            return False
        return True

    @staticmethod
    def _obstacles_complete(assignment):
        return (
            sum(1 for value in assignment.values() if value == HOLE) == MAX_HOLES
            and sum(1 for value in assignment.values() if value == MOUNT) == MAX_MOUNTS
            and sum(1 for value in assignment.values() if value == SANTA) == 0
            and sum(1 for value in assignment.values() if value == SANTA_HOUSE) == 0
        )

    @staticmethod
    def _finish_with_santa_house(assignment):
        """Place Santa penultimately and House last on reachable snow cells."""
        base = dict(assignment)
        for r in range(GameConfig.GRID):
            for c in range(GameConfig.GRID):
                base.setdefault((r, c), FROZEN)

        snow_cells = [cell for cell, value in base.items() if value == FROZEN]
        random.shuffle(snow_cells)

        for santa_cell in snow_cells:
            with_santa = dict(base)
            with_santa[santa_cell] = SANTA
            yield dict(with_santa)

            house_cells = [cell for cell in snow_cells if cell != santa_cell]
            random.shuffle(house_cells)
            for house_cell in house_cells:
                candidate = dict(with_santa)
                candidate[house_cell] = SANTA_HOUSE
                if not CSPGenerator._holes_not_adjacent_house(candidate):
                    continue
                if CSPGenerator._assignment_complete(candidate):
                    yield candidate
                    return

    @staticmethod
    def _is_consistent(cell, value, assignment):
        """
        Kiểm tra tính nhất quán khi gán value cho cell.
        - Đúng 1 SANTA_HOUSE (Ngôi nhà) trong toàn bộ grid
        - Đúng 1 SANTA (vị trí Santa) trong toàn bộ grid
        - Tối đa MAX_HOLES HOLE và MAX_MOUNTS MOUNT
        - Các giá trị đặc biệt không được xuất hiện quá số lượng cho phép.
        - HOLE không được kề SANTA_HOUSE.
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

        for nb in CSPGenerator._get_neighbors(cell):
            if nb not in assignment:
                continue
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
        hole_count        = sum(1 for v in assignment.values() if v == HOLE)
        mount_count       = sum(1 for v in assignment.values() if v == MOUNT)
        return (
            santa_house_count == 1
            and santa_count == 1
            and hole_count == MAX_HOLES
            and mount_count == MAX_MOUNTS
            and CSPGenerator._holes_not_adjacent_house(assignment)
            and CSPGenerator._has_path(assignment)
        )

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

        return result


    # ═══════════════════════════════════════════════════════════════════════════
    # 1. BACKTRACKING + FORWARD CHECKING  (AIMA Fig. 6.5 + FC)
    # ═══════════════════════════════════════════════════════════════════════════
    @staticmethod
    def generate_map_forward_checking():
        """
        Tìm kiếm quay lui (Backtracking Search) kết hợp Forward Checking.

        Forward Checking đảm bảo rằng sau khi gán var=value, chúng ta kiểm tra tất cả
        các ô lân cận chưa được gán và loại bỏ các giá trị vi phạm ràng buộc khỏi miền giá trị của chúng.
        Nếu bất kỳ miền giá trị nào trở nên rỗng, không gian tìm kiếm sẽ được cắt tỉa (prune) sớm.
        """
        variables, domains = CSPGenerator._build_csp()
        random.shuffle(variables)

        def fc_backtrack(assignment, doms):
            yield dict(assignment)   # visualise step

            if CSPGenerator._assignment_complete(assignment):
                yield dict(assignment)
                return

            if CSPGenerator._obstacles_complete(assignment):
                yield from CSPGenerator._finish_with_santa_house(assignment)
                return

            # SELECT-UNASSIGNED-VARIABLE (MRV)
            cell = CSPGenerator._select_unassigned_variable(variables, assignment, doms)
            if cell is None:
                return

            # ORDER-DOMAIN-VALUES (random order)
            vals = doms[cell][:]
            random.shuffle(vals)
            vals = CSPGenerator._values_for_step(vals, len(assignment))

            for value in vals:
                # Consistent check
                if not CSPGenerator._is_consistent(cell, value, assignment):
                    continue

                assignment[cell] = value
                if not CSPGenerator._counts_feasible(assignment):
                    del assignment[cell]
                    continue
                saved = {k: v[:] for k, v in doms.items()}   # save domains

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
        AC-3 (Arc Consistency 3) + Tìm kiếm quay lui (Backtracking).

        Bước 1: Chạy AC-3 để buộc tính nhất quán cung (arc consistency) và thu hẹp miền giá trị.
        Bước 2: Chạy quay lui trên các miền giá trị đã được thu hẹp.

        Ràng buộc chính: đúng số lượng, không trùng biến, hố không kề nhà, và map cuối có đường đi.
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

            if CSPGenerator._obstacles_complete(assignment):
                yield from CSPGenerator._finish_with_santa_house(assignment)
                return

            # SELECT-UNASSIGNED-VARIABLE (MRV)
            cell = CSPGenerator._select_unassigned_variable(variables, assignment, doms)
            if cell is None:
                return

            vals = doms[cell][:]
            random.shuffle(vals)
            vals = CSPGenerator._values_for_step(vals, len(assignment))

            for value in vals:
                if not CSPGenerator._is_consistent(cell, value, assignment):
                    continue

                assignment[cell] = value
                if not CSPGenerator._counts_feasible(assignment):
                    del assignment[cell]
                    continue
                saved = {k: v[:] for k, v in doms.items()}

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
        Tối thiểu xung đột (Min-Conflicts): Tìm kiếm cục bộ trực tiếp trên một phép gán hoàn chỉnh.

        Ứng dụng cho việc tạo bản đồ:
        - Phép gán ban đầu: gán ngẫu nhiên đủ số lượng gạch cho tất cả các ô.
          (1 SANTA_HOUSE, 10 HOLE, 6 MOUNT, còn lại là FROZEN).
        - Biến xung đột (Conflicted variable): một ô đang vi phạm ràng buộc.
        - CONFLICTS(var, v): đếm số lượng vi phạm ràng buộc khi gán v cho var.
        - Lặp lại cho đến khi không còn xung đột hoặc đạt đến max_steps.
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
            trial = dict(assignment)
            trial[cell] = value
            conflicts = 0

            if value == HOLE:
                conflicts += sum(1 for nb in CSPGenerator._get_neighbors(cell) if trial.get(nb) == SANTA_HOUSE)
            if value == SANTA_HOUSE:
                conflicts += sum(1 for nb in CSPGenerator._get_neighbors(cell) if trial.get(nb) == HOLE)

            # ✅ Sửa: check path cho TẤT CẢ các ô, không chỉ SANTA/SANTA_HOUSE
            if not CSPGenerator._has_path(trial):
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
            if sum(1 for v in assignment.values() if v == SANTA_HOUSE) != 1:
                return False
            if sum(1 for v in assignment.values() if v == SANTA) != 1:
                return False
            if sum(1 for v in assignment.values() if v == HOLE) != MAX_HOLES:
                return False
            if sum(1 for v in assignment.values() if v == MOUNT) != MAX_MOUNTS:
                return False
            if not CSPGenerator._holes_not_adjacent_house(assignment):
                return False
            # ✅ Chỉ cần check path một lần — không cần get_conflicted_cells
            return CSPGenerator._has_path(assignment)

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

            if not CSPGenerator._has_path(current):
                special = random.choice([SANTA, SANTA_HOUSE])
                old_cell = next((c for c, v in current.items() if v == special), None)
                free_cells = [c for c, v in current.items() if v == FROZEN]
                if old_cell is not None and free_cells:
                    new_cell = random.choice(free_cells)
                    current[old_cell] = FROZEN
                    current[new_cell] = special
                    yield dict(current)
                    continue

            # var ← randomly chosen CONFLICTED variable
            conflicted = get_conflicted_cells(current)
            if not conflicted:
                current = make_initial()
                yield dict(current)
                continue

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