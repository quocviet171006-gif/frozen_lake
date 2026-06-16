from algorithms.uninformed import UninformedSearch
from algorithms.informed import InformedSearch
from algorithms.local import LocalSearch
from algorithms.sensorless import SensorlessSearch
from algorithms.nondeterministic import NondeterministicSearch
from algorithms.csp import CSPGenerator

ALGORITHMS = {
    1: {"BFS": UninformedSearch.bfs, "DFS": UninformedSearch.dfs, "UCS": UninformedSearch.ucs},
    2: {"Greedy": InformedSearch.greedy, "A*": InformedSearch.a_star, "IDA*": InformedSearch.ida_star},
    3: {"Simple HC": LocalSearch.simple_hc, "Beam": LocalSearch.beam_search, "Sim Ann": LocalSearch.simulated_annealing},
    4: {"S-BFS": SensorlessSearch.sensorless_bfs, "S-DFS": SensorlessSearch.sensorless_dfs},
    5: {"AND-OR Graph": NondeterministicSearch.and_or_graph_search},
    6: {"Backtracking": CSPGenerator.generate_map_backtracking, "Forward Check": CSPGenerator.generate_map_forward_checking}
}
