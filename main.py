"""
Điểm bắt đầu (entry point) chính của Mô phỏng AI Frozen Lake.
Khởi tạo trò chơi và bắt đầu vòng lặp chính.
"""
from game import FrozenLakeGame

if __name__ == "__main__":
    game = FrozenLakeGame()
    game.run()
