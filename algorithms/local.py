import random
import math
from environment import Environment, Node, reconstruct

class LocalSearch:
    @staticmethod
    def simple_hc(grid, start_state, goal_pos, *args):
        # Simple Hill Climbing: tìm neighbor đầu tiên tốt hơn, dừng ở cực đại cục bộ
        # 1. Current_State = Start
        current = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        visit_order = [start_state]
        # 2. TRONG KHI (đúng):
        while True:
            # Nếu Current_State == Goal: TRẢ VỀ Current_State
            if current.state == goal_pos:
                return reconstruct(current), visit_order
            # Sinh các trạng thái lân cận của Current_State
            nbs = Environment.get_cost_transitions(grid, current.state, goal_pos)
            if not nbs:
                break
            # Tìm thấy Next_State đầu tiên có Value(Next_State) > Value(Current_State)
            # (h thấp hơn = tốt hơn trong bài toán tìm đường)
            found_better = False
            for n_state, _, action in nbs:
                next_cost = Environment.heuristic(n_state, goal_pos)
                if next_cost < current.cost:  # Value(Next) > Value(Current) ↔ h(Next) < h(Current)
                    # Current_State = Next_State
                    current = Node(n_state, current, cost=next_cost, action=action)
                    visit_order.append(current.state)
                    found_better = True
                    # Tiếp tục vòng lặp (Quay lại bước 2)
                    break
            # Nếu ĐÃ DUYỆT HẾT lân cận mà không có ai tốt hơn:
            if not found_better:
                # TRẢ VỀ Current_State (Dừng vì đạt cực đại cục bộ)
                break
        return reconstruct(current), visit_order

    @staticmethod
    def beam_search(grid, start_state, goal_pos, *args):
        # Local Beam Search: duy trì k trạng thái song song
        k = 2
        # 1. Khởi tạo: Current_State_set = {Sinh ngẫu nhiên k trạng thái từ Start}
        # Trong game pathfinding: bắt đầu từ start, sinh k neighbors làm beam ban đầu
        initial_node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        # Kiểm tra start có phải goal không
        if start_state == goal_pos:
            return [start_state], [start_state]
        # Sinh neighbors từ start để tạo k trạng thái ban đầu
        initial_nbs = Environment.get_cost_transitions(grid, start_state, goal_pos)
        if not initial_nbs:
            return [], [start_state]
        initial_children = []
        for n_state, _, action in initial_nbs:
            child = Node(n_state, initial_node, cost=Environment.heuristic(n_state, goal_pos), action=action)
            initial_children.append(child)
        # Sắp xếp và lấy k tốt nhất
        initial_children.sort(key=lambda x: x.cost)
        current_state_set = initial_children[:k]
        visit_order = [start_state]
        for node in current_state_set:
            visit_order.append(node.state)
        # 2. TRONG KHI (đúng):
        while current_state_set:
            # Neighbor_States = rỗng
            neighbor_states = []
            # 2.1. SINH TRẠNG THÁI LÂN CẬN
            for node in current_state_set:
                # VỚI MỖI State trong Current_State_set:
                #   Sinh tất cả các trạng thái lân cận của State
                for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    neighbor_states.append(child)
            if not neighbor_states:
                break
            # 2.2. KIỂM TRA ĐÍCH
            for neighbor in neighbor_states:
                # VỚI MỖI Neighbor trong Neighbor_States:
                #   NẾU Neighbor == Goal: TRẢ VỀ Neighbor
                if neighbor.state == goal_pos:
                    visit_order.append(neighbor.state)
                    return reconstruct(neighbor), visit_order
            # 2.3. LỰA CHỌN CHÙM (NẾU CHƯA TÌM THẤY ĐÍCH)
            # Sắp xếp Neighbor_States theo thứ tự giá trị hàm mục tiêu h tốt dần
            neighbor_states.sort(key=lambda x: x.cost)
            # Current_State_set = Lấy k trạng thái tốt nhất
            current_state_set = neighbor_states[:k]
            for node in current_state_set:
                visit_order.append(node.state)
        # 4. TRẢ VỀ "Thất bại"
        return [], visit_order

    @staticmethod
    def simulated_annealing(grid, start_state, goal_pos, *args):
        # Simulated Annealing: chấp nhận bước đi tệ hơn với xác suất giảm dần
        # current_state = start
        current = start_state
        current_h = Environment.heuristic(start_state, goal_pos)
        # T = T0
        T = 100.0
        Tmin = 1.0
        alpha = 0.95  # α: cooling rate
        # Track path bằng Node chain để reconstruct
        current_node = Node(start_state)
        visit_order = [start_state]
        # while T > Tmin:
        while T > Tmin:
            # if current_state == goal: return current_state
            if current == goal_pos:
                return reconstruct(current_node), visit_order
            # next_state = RandomNeighbor(current_state)
            nbs = Environment.get_cost_transitions(grid, current, goal_pos)
            if not nbs:
                break
            n_state, _, action = random.choice(nbs)
            # Δ = h(next_state) - h(current_state)
            next_h = Environment.heuristic(n_state, goal_pos)
            delta = next_h - current_h
            # if Δ < 0: current_state = next_state (tốt hơn → chấp nhận)
            if delta < 0:
                current = n_state
                current_h = next_h
                current_node = Node(n_state, current_node, action=action)
                visit_order.append(current)
            # else: p = exp(-Δ / T); if Random(0,1) < p: current_state = next_state
            else:
                p = math.exp(-delta / T) if T > 0 else 0
                if random.random() < p:
                    current = n_state
                    current_h = next_h
                    current_node = Node(n_state, current_node, action=action)
                    visit_order.append(current)
            # T = α * T
            T *= alpha
        # return current_state (trả về trạng thái cuối cùng)
        return reconstruct(current_node), visit_order
