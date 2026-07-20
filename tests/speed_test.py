"""Quick speed/nodes check at fixed depth on a midgame position.

Usage:  python tests/speed_test.py <module_name> [depth]
Run once per module (separate processes; pybind types can't coexist).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEN = "r1bqk2r/pp2bppp/2n1pn2/2pp4/3P4/2NBPN2/PPP2PPP/R1BQ1RK1 w kq - 0 8"

modname = sys.argv[1] if len(sys.argv) > 1 else "chess_engine_cpp"
DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 9

mod = __import__(modname)
e = mod.ChessEngine(); e.load_fen(FEN)
ai = mod.AlphaBetaEngine(DEPTH, 3600.0); ai.verbose = False
t = time.perf_counter()
mv = ai.get_best_move(e)
dt = time.perf_counter() - t
nps = ai.nodes_searched / dt if dt else 0
print(f"{modname:>18}: depth {ai.completed_depth}  time {dt:6.3f}s  "
      f"nodes {ai.nodes_searched:>9}  {nps/1000:7.0f}k nps  move {mv}")
