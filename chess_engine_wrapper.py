from chess_engine_cpp import ChessEngine as CppChessEngine, AlphaBetaEngine as CppAlphaBetaEngine
import time

class ChessEngine(CppChessEngine):
    def __init__(self):
        super().__init__()

class AlphaBetaEngine:
    def __init__(self, depth=5, time_limit=5.0):
        self._cpp_engine = CppAlphaBetaEngine(depth, time_limit)
        
    def record_move(self, move):
        self._cpp_engine.record_move(move)
        
    def get_best_move(self, engine):
        return self._cpp_engine.get_best_move(engine)
