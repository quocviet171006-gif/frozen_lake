import random
import math
from environment import Environment, Node, reconstruct

class LocalSearch:
    """
    Chứa các thuật toán Tìm kiếm cục bộ (Local Search).
    Các thuật toán này chỉ hoạt động trên một nút hiện tại (hoặc một tập hợp nhỏ) thay vì
    duy trì toàn bộ không gian tìm kiếm (frontier), giúp tiết kiệm bộ nhớ.
    """
    
    @staticmethod
    def simple_hc(grid, start_state, goal_pos, *args):
        """
        Leo đồi đơn giản (Simple Hill Climbing)
        Liên tục di chuyển đến trạng thái lân cận đầu tiên được tạo ra mà có giá trị heuristic tốt hơn.
        Dừng lại khi đạt đến cực đại cục bộ (local maximum - không có lân cận nào tốt hơn).
        """
        current = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        visit_order = [start_state]
        
        while True:
            if current.state == goal_pos:
                return reconstruct(current), visit_order
                
            nbs = Environment.get_cost_transitions(grid, current.state, goal_pos)
            if not nbs:
                break
                
            found_better = False
            for n_state, _, action in nbs:
                next_cost = Environment.heuristic(n_state, goal_pos)
                
                # Nếu lân cận tốt hơn thực sự (chi phí heuristic thấp hơn)
                if next_cost < current.cost:  
                    current = Node(n_state, current, cost=next_cost, action=action)
                    visit_order.append(current.state)
                    found_better = True
                    break # Simple HC: lấy lân cận đầu tiên tốt hơn tìm được
                    
            if not found_better:
                # Đã đạt cực đại cục bộ
                break
                
        return reconstruct(current), visit_order

    @staticmethod
    def beam_search(grid, start_state, goal_pos, *args):
        """
        Tìm kiếm chùm cục bộ (Local Beam Search)
        Duy trì k trạng thái trong bộ nhớ tại mọi thời điểm. Trong mỗi vòng lặp,
        nó tạo ra tất cả lân cận của tất cả k trạng thái, sau đó chọn k trạng thái
        tốt nhất tổng thể để tiếp tục.
        """
        k = 2
        initial_node = Node(start_state, cost=Environment.heuristic(start_state, goal_pos))
        
        if start_state == goal_pos:
            return [start_state], [start_state]
            
        initial_nbs = Environment.get_cost_transitions(grid, start_state, goal_pos)
        if not initial_nbs:
            return [], [start_state]
            
        initial_children = []
        for n_state, _, action in initial_nbs:
            child = Node(n_state, initial_node, cost=Environment.heuristic(n_state, goal_pos), action=action)
            initial_children.append(child)
            
        # Chọn k trạng thái khởi tạo tốt nhất
        initial_children.sort(key=lambda x: x.cost)
        current_state_set = initial_children[:k]
        
        visit_order = [start_state]
        for node in current_state_set:
            visit_order.append(node.state)
            
        while current_state_set:
            neighbor_states = []
            
            # Tạo tất cả lân cận cho toàn bộ k trạng thái hiện tại
            for node in current_state_set:
                for n_state, _, action in Environment.get_cost_transitions(grid, node.state, goal_pos):
                    child = Node(n_state, node, cost=Environment.heuristic(n_state, goal_pos), action=action)
                    neighbor_states.append(child)
                    
            if not neighbor_states:
                break
                
            # Kiểm tra đích đến
            for neighbor in neighbor_states:
                if neighbor.state == goal_pos:
                    visit_order.append(neighbor.state)
                    return reconstruct(neighbor), visit_order
                    
            # Chọn k trạng thái tốt nhất từ tất cả các lân cận được tạo ra
            neighbor_states.sort(key=lambda x: x.cost)
            current_state_set = neighbor_states[:k]
            
            for node in current_state_set:
                visit_order.append(node.state)
                
        return [], visit_order

    @staticmethod
    def simulated_annealing(grid, start_state, goal_pos, *args):
        """
        Tôi luyện mô phỏng (Simulated Annealing)
        Sử dụng cơ chế lịch trình nhiệt độ để thỉnh thoảng chấp nhận các bước đi tệ hơn
        ở giai đoạn đầu của quá trình tìm kiếm, giúp tránh kẹt ở cực đại cục bộ. Xác suất
        chấp nhận các bước đi tệ hơn sẽ giảm dần khi "nhiệt độ" giảm xuống.
        """
        current = start_state
        current_h = Environment.heuristic(start_state, goal_pos)
        
        # Các tham số cho tôi luyện
        T = 100.0       # Initial temperature
        Tmin = 1.0      # Minimum temperature to stop
        alpha = 0.95    # Cooling rate
        
        current_node = Node(start_state)
        visit_order = [start_state]
        
        while T > Tmin:
            if current == goal_pos:
                return reconstruct(current_node), visit_order
                
            nbs = Environment.get_cost_transitions(grid, current, goal_pos)
            if not nbs:
                break
                
            # Chọn ngẫu nhiên một lân cận
            n_state, _, action = random.choice(nbs)
            
            next_h = Environment.heuristic(n_state, goal_pos)
            delta = next_h - current_h # Negative means the next state is better (lower cost)
            
            # Nếu lân cận tốt hơn, luôn chấp nhận nó
            if delta < 0:
                current = n_state
                current_h = next_h
                current_node = Node(n_state, current_node, action=action)
                visit_order.append(current)
            else:
                # Nếu tệ hơn, chấp nhận với xác suất giảm dần theo thời gian
                p = math.exp(-delta / T) if T > 0 else 0
                if random.random() < p:
                    current = n_state
                    current_h = next_h
                    current_node = Node(n_state, current_node, action=action)
                    visit_order.append(current)
                    
            # Làm mát (giảm nhiệt độ)
            T *= alpha
            
        return reconstruct(current_node), visit_order