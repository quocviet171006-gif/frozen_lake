import random
from config import GameConfig
from algorithms.complex import SensorlessSearch
from environment import Environment

grid = [[GameConfig.SNOW] * 8 for _ in range(8)]
santa_pos_list = []
for qr in range(2):
    for qc in range(2):
        ro, co = qr * 4, qc * 4
        cells = [(r, c) for r in range(4) for c in range(4)]
        random.shuffle(cells)
        sr, sc = cells.pop()
        santa_pos_list.append((ro + sr, co + sc))
        hr, hc = cells.pop()
        grid[ro+hr][co+hc] = GameConfig.HOUSE
        if qr == 0 and qc == 0:
            house_pos = (ro+hr, co+hc)
        mr, mc = cells.pop()
        grid[ro+mr][co+mc] = GameConfig.MOUNT
        hor, hoc = cells.pop()
        grid[ro+hor][co+hoc] = GameConfig.HOLE

print("Starting SensorlessSearch...")
actions, beliefs = SensorlessSearch.sensorless_bfs(grid, frozenset(santa_pos_list), house_pos)
print("Result:", actions)
print("Visited:", len(beliefs))
