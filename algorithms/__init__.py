"""
Khởi tạo cho gói (package) thuật toán (algorithms).
Xuất ra tất cả các danh mục thuật toán tìm kiếm và nhóm chúng vào từ điển ALGORITHMS
để giao diện người dùng (UI) có thể truy cập động một cách dễ dàng.
"""
from algorithms.uninformed import UninformedSearch
from algorithms.informed import InformedSearch
from algorithms.local import LocalSearch
from algorithms.complex import ComplexSearch
from algorithms.csp import CSPGenerator
from algorithms.adversarial import AdversarialSearch

ALGORITHMS = {
    1: {"BFS": UninformedSearch.bfs, "DFS": UninformedSearch.dfs, "UCS": UninformedSearch.ucs},
    2: {"Greedy": InformedSearch.greedy, "A*": InformedSearch.a_star, "IDA*": InformedSearch.ida_star},
    3: {"Simple HC": LocalSearch.simple_hc, "Beam": LocalSearch.beam_search, "Sim Ann": LocalSearch.simulated_annealing},
    4: {
        "Sensorless":  ComplexSearch.sensorless_bfs,
        "Partial-Obs": ComplexSearch.partial_obs_bfs,
        "AND-OR":      ComplexSearch.and_or_search,
    },
    5: {
        "Forward Check": CSPGenerator.generate_map_forward_checking,
        "AC-3": CSPGenerator.generate_map_ac3,
        "Min-Conflicts": CSPGenerator.generate_map_min_conflicts
    },
    6: {
        "Minimax": AdversarialSearch.minimax,
        "Alpha-Beta": AdversarialSearch.alpha_beta,
        "Expectimax": AdversarialSearch.expectimax
    }
}