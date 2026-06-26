from config import GameConfig

class Node:
    """
    Đại diện cho một nút trong cây tìm kiếm.
    Lưu trữ trạng thái (state), nút cha (parent), chi phí, giá trị heuristic, và hành động để đến trạng thái này.
    """
    def __init__(self, state, parent=None, cost=0, action=None):
        self.state = state          # Trạng thái hiện tại (ví dụ: tọa độ (row, col) hoặc tập hợp frozenset cho belief state)
        self.parent = parent        # Tham chiếu đến nút cha (dùng để truy vết đường đi)
        self.action = action        # Hành động đã thực hiện để đến được trạng thái này từ nút cha
        self.cost = cost            # Tổng chi phí từ trạng thái ban đầu đến trạng thái này
        self.g = 0                  # Chi phí g(n) từ điểm bắt đầu đến nút hiện tại (dùng cho A*/IDA*)
        self.h = 0                  # Ước lượng heuristic h(n) từ nút hiện tại đến đích (dùng cho A*/IDA*)
        
    def __lt__(self, other):
        """
        Định nghĩa toán tử nhỏ hơn để so sánh các nút dựa trên chi phí.
        Hữu ích cho các hàng đợi ưu tiên (priority queues) trong các thuật toán như UCS, Greedy, và A*.
        """
        return self.cost < other.cost

def reconstruct(node):
    """
    Truy vết lại đường đi (danh sách các trạng thái) từ nút ban đầu đến nút đích.
    Lần ngược theo các con trỏ parent và sau đó đảo ngược chuỗi để có đường đi đúng thứ tự.
    """
    path = []
    while node:
        path.append(node.state)
        node = node.parent
    return path[::-1] # Đảo ngược danh sách từ Start -> End

def reconstruct_actions(node):
    """
    Truy vết lại chuỗi hành động từ nút ban đầu đến nút đích.
    Lần ngược theo các con trỏ parent và sau đó đảo ngược chuỗi hành động.
    """
    actions = []
    while node and node.parent:
        actions.append(node.action)
        node = node.parent
    return actions[::-1] # Đảo ngược chuỗi hành động từ Start -> End

class Environment:
    """
    Cung cấp các hàm tiện ích cho môi trường Frozen Lake, bao gồm các hàm chuyển đổi trạng thái,
    hàm heuristic, và quản lý các trạng thái niềm tin (belief state) cho phần tìm kiếm phức tạp.
    """
    
    @staticmethod
    def get_cost_transitions(grid, state, house_pos):
        """
        Tạo ra các bước chuyển đổi hợp lệ từ trạng thái hiện tại.
        Trả về danh sách các tuple: ((row_kế_tiếp, col_kế_tiếp), step_cost, tên_hành_động)
        """
        r, c = state
        transitions = []
        # Các hành động có thể và tọa độ thay đổi tương ứng
        for action, (dr, dc) in zip(["Up", "Down", "Left", "Right"], [(-1,0),(1,0),(0,-1),(0,1)]):
            nr, nc = r + dr, c + dc
            # Kiểm tra xem trạng thái kế tiếp có nằm trong bản đồ và không phải chướng ngại vật/hố hay không
            if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] not in [GameConfig.MOUNT, GameConfig.HOLE]:
                transitions.append(((nr, nc), 1, action))
        return transitions

    @staticmethod
    def heuristic(state, house_pos):
        """
        Khoảng cách Manhattan — hàm heuristic admissible (luôn nhỏ hơn hoặc bằng h thực tế) cho A* và IDA*.
        KHÔNG trừ giá trị âm để đảm bảo tính admissible (h <= h*).
        Tính khoảng cách dạng lưới giữa trạng thái hiện tại và đích (ngôi nhà).
        """
        r, c = state
        return abs(r - house_pos[0]) + abs(c - house_pos[1])

    @staticmethod
    def get_initial_belief(grid):
        """
        Trả về tập hợp trạng thái niềm tin ban đầu (belief state) cho tìm kiếm Sensorless.
        Belief ban đầu chứa tất cả các ô có thể đi qua (không phải núi, không phải hố).
        """
        return frozenset(
            (r, c)
            for r in range(GameConfig.GRID)
            for c in range(GameConfig.GRID)
            if grid[r][c] not in [GameConfig.MOUNT, GameConfig.HOLE]
        )

    @staticmethod
    def sensorless_transition(grid, b_state, action):
        """
        Tính toán tập hợp trạng thái niềm tin (belief state) mới dựa trên belief hiện tại và hành động.
        Xử lý yếu tố bất định khi di chuyển, đặc biệt là khi trượt trên băng (hố).
        """
        act_map = {"Up": (-1,0), "Down": (1,0), "Left": (0,-1), "Right": (0,1)}
        dr, dc = act_map[action]
        new_b = set()
        
        for r, c in b_state:
            if grid[r][c] == GameConfig.HOLE:
                # Nếu đang ở trên hố, tác nhân sẽ bị trượt ngẫu nhiên về 4 hướng
                for adr, adc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + adr, c + adc
                    if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                        if not getattr(Environment, 'ALLOW_HOLES', False) and grid[nr][nc] == GameConfig.HOLE:
                            new_b.add((r, c)) # Đứng im nếu không cho phép đi vào hố
                        else:
                            new_b.add((nr, nc)) # Di chuyển tới ô kế
                    else:
                        new_b.add((r, c)) # Chạm biên/núi, đứng im
            else:
                # Di chuyển bình thường
                nr, nc = r + dr, c + dc
                if 0 <= nr < GameConfig.GRID and 0 <= nc < GameConfig.GRID and grid[nr][nc] != GameConfig.MOUNT:
                    if not getattr(Environment, 'ALLOW_HOLES', False) and grid[nr][nc] == GameConfig.HOLE:
                        new_b.add((r, c)) # Không được đi vào hố
                    else:
                        new_b.add((nr, nc)) # Di chuyển thành công
                else:
                    new_b.add((r, c)) # Chạm biên/núi, đứng im
                    
        return frozenset(new_b)
