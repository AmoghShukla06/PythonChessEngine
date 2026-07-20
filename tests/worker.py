"""Engine worker for cross-process self-play matches.

Runs one engine module in its own process (so baseline and improved modules
never collide in a single interpreter). Protocol over stdin/stdout, one line
each:
    "newgame"          -> reset AI (clears transposition table); no reply
    "<FEN>"            -> reply "sr sc tr tc" (best move) or "none"
    "quit"             -> exit

Usage:  python worker.py <module_name> <depth>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    module_name = sys.argv[1]
    depth = int(sys.argv[2])
    mod = __import__(module_name)
    ai = mod.AlphaBetaEngine(depth, 3600.0)
    ai.verbose = False

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line == "quit":
            break
        if line == "newgame":
            ai = mod.AlphaBetaEngine(depth, 3600.0)
            ai.verbose = False
            continue
        eng = mod.ChessEngine()
        eng.load_fen(line)
        mv = ai.get_best_move(eng)
        if mv is None:
            sys.stdout.write("none\n")
        else:
            sys.stdout.write(f"{mv[0]} {mv[1]} {mv[2]} {mv[3]}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
