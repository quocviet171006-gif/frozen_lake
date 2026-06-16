import random
from collections import deque
from config import GameConfig


class CSPGenerator:
    GRID = GameConfig.GRID  # 8

    # ── Constraint sớm: kiểm tra từng biến khi gán ───────────────────────
    @staticmethod
    def _partial_ok(var, val, assignment):
        """
        Kiểm tra constraint cục bộ ngay khi gán biến thứ 'var'.
        Trả về False nếu vi phạm để prune sớm, tăng tốc backtracking.
        """
        # Không trùng ô với bất kỳ biến nào đã gán
        if val in assignment.values():
            return False

        G = CSPGenerator.GRID
        v_r, v_c = val // G, val % G

        # Santa (var=0) và House (var=1): khoảng cách Manhattan tối thiểu 2
        if var == 0 and 1 in assignment:
            h_r, h_c = assignment[1] // G, assignment[1] % G
            if abs(v_r - h_r) + abs(v_c - h_c) < 2:
                return False
        if var == 1 and 0 in assignment:
            s_r, s_c = assignment[0] // G, assignment[0] % G
            if abs(v_r - s_r) + abs(v_c - s_c) < 2:
                return False

        return True

    # ── Kiểm tra kết nối đầy đủ (Santa → House không bị block) ──────────
    @staticmethod
    def _connectivity_ok(assignment):
        """BFS kiểm tra Santa có đường đi đến House không."""
        items = ["Santa", "House"] + ["Hole"] * 10 + ["Mount"] * 6
        if len(assignment) < len(items):
            return True  # chưa gán hết, bỏ qua
        G = CSPGenerator.GRID
        mount_cells = set(
            (assignment[i] // G, assignment[i] % G)
            for i, x in enumerate(items) if x == "Mount"
        )
        s_pos = (assignment[0] // G, assignment[0] % G)
        h_pos = (assignment[1] // G, assignment[1] % G)

        q = deque([s_pos])
        visited = {s_pos}
        while q:
            r, c = q.popleft()
            if (r, c) == h_pos:
                return True
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < G and 0 <= nc < G
                        and (nr, nc) not in mount_cells
                        and (nr, nc) not in visited):
                    visited.add((nr, nc))
                    q.append((nr, nc))
        return False

    # ── Backtracking với partial-constraint pruning ───────────────────────
    @staticmethod
    def generate_map_backtracking():
        """
        Sinh bản đồ bằng CSP Backtracking.
        Cải tiến: partial_ok() prune sớm từng bước thay vì chỉ check cuối.
        Yield từng snapshot để UI animate quá trình tìm kiếm.
        """
        items = ["Santa", "House"] + ["Hole"] * 10 + ["Mount"] * 6
        n = len(items)  # = 18
        all_cells = list(range(CSPGenerator.GRID * CSPGenerator.GRID))

        def backtrack(assignment):
            yield dict(assignment)  # snapshot cho UI
            if len(assignment) == n:
                if CSPGenerator._connectivity_ok(assignment):
                    yield dict(assignment)  # yield kết quả hợp lệ
                return

            var = len(assignment)
            vals = all_cells[:]
            random.shuffle(vals)

            for val in vals:
                if CSPGenerator._partial_ok(var, val, assignment):
                    assignment[var] = val
                    yield from backtrack(assignment)
                    # Dừng sớm nếu đã tìm được
                    if len(assignment) == n and CSPGenerator._connectivity_ok(assignment):
                        return
                    if var in assignment:
                        del assignment[var]

        yield from backtrack({})

    # ── Forward Checking với arc-consistency cơ bản ──────────────────────
    @staticmethod
    def generate_map_forward_checking():
        """
        CSP Forward Checking: khi gán biến, xóa giá trị đó khỏi domain
        của các biến chưa gán để phát hiện conflict sớm hơn.
        """
        items = ["Santa", "House"] + ["Hole"] * 10 + ["Mount"] * 6
        n = len(items)
        all_cells = list(range(CSPGenerator.GRID * CSPGenerator.GRID))
        init_doms = {i: all_cells[:] for i in range(n)}

        def fc_search(assignment, doms):
            yield dict(assignment)
            if len(assignment) == n:
                if CSPGenerator._connectivity_ok(assignment):
                    yield dict(assignment)
                return

            var = len(assignment)
            vals = doms[var][:]
            random.shuffle(vals)

            for val in vals:
                if not CSPGenerator._partial_ok(var, val, assignment):
                    continue

                assignment[var] = val
                # Forward check: loại val khỏi domain các biến chưa gán
                new_doms = {k: v[:] for k, v in doms.items()}
                valid = True
                for k in range(var + 1, n):
                    if val in new_doms[k]:
                        new_doms[k].remove(val)
                    if not new_doms[k]:  # domain rỗng → conflict
                        valid = False
                        break

                if valid:
                    yield from fc_search(assignment, new_doms)
                    if len(assignment) == n and CSPGenerator._connectivity_ok(assignment):
                        return  # tìm được → dừng sớm

                if var in assignment:
                    del assignment[var]

        yield from fc_search({}, init_doms)
