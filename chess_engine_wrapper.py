from chess_engine_cpp import ChessEngine as CppChessEngine, AlphaBetaEngine as CppAlphaBetaEngine
import time

class ChessEngine(CppChessEngine):
    def __init__(self):
        super().__init__()

class AlphaBetaEngine:
    def __init__(self, depth=5, time_limit=5.0, verbose=False):
        self._cpp_engine = CppAlphaBetaEngine(depth, time_limit)
        self._cpp_engine.verbose = verbose

    def record_move(self, move):
        self._cpp_engine.record_move(move)

    def get_best_move(self, engine):
        return self._cpp_engine.get_best_move(engine)

    def set_depth(self, depth):
        self._cpp_engine.max_depth = depth

    def set_time_limit(self, limit):
        self._cpp_engine.time_limit = limit

    # --- Search introspection (for the eval bar / status) ---
    @property
    def verbose(self):
        return self._cpp_engine.verbose

    @verbose.setter
    def verbose(self, value):
        self._cpp_engine.verbose = value

    @property
    def last_score(self):
        """Score of the last search, in centipawns, side-to-move POV."""
        return self._cpp_engine.last_score

    @property
    def completed_depth(self):
        return self._cpp_engine.completed_depth

    @property
    def nodes_searched(self):
        return self._cpp_engine.nodes_searched
