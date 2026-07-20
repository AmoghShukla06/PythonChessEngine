"""Self-play match: baseline engine vs improved engine at equal fixed depth.

Objective strength gauge. Each engine runs in its own subprocess worker
(tests/worker.py) so the two pybind modules never collide. The orchestrator
holds the true board with chess_engine_cpp (move rules are perft-verified and
identical across builds) and asks the side-to-move's worker for each move.

Usage:  python tests/match.py [depth] [games]
"""
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import chess_engine_cpp as BOARD  # board bookkeeping only

OPENINGS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkb1r/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 3",
    "rnbqkb1r/pp2pppp/2p2n2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 0 4",
    "rnbqkbnr/pp2pppp/2p5/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3",
]
PROMO_RANKS = (0, 7)


class Worker:
    def __init__(self, module_name, depth):
        self.p = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "tests", "worker.py"),
             module_name, str(depth)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=ROOT)

    def newgame(self):
        self.p.stdin.write("newgame\n"); self.p.stdin.flush()

    def best_move(self, fen):
        self.p.stdin.write(fen + "\n"); self.p.stdin.flush()
        line = self.p.stdout.readline().strip()
        if line == "none" or not line:
            return None
        return tuple(int(x) for x in line.split())

    def close(self):
        try:
            self.p.stdin.write("quit\n"); self.p.stdin.flush()
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


def apply_move(board, sr, sc, tr, tc):
    piece = board.board[sr][sc]
    promo = "Q" if (piece and piece[1] == "P" and tr in PROMO_RANKS) else None
    target = board.board[tr][tc]
    reset = (target != "--") or (piece and piece[1] == "P")
    board.make_move(sr, sc, tr, tc, promoted_piece=promo)
    return reset


def play_game(white, black, start_fen):
    board = BOARD.ChessEngine()
    board.load_fen(start_fen)
    white.newgame(); black.newgame()
    seen = {}
    halfmove = 0
    for _ply in range(300):
        if board.check_game_over():
            return board.winner if board.winner != "draw" else "draw"
        worker = white if board.turn == "w" else black
        mv = worker.best_move(board.get_fen())
        if mv is None:
            return "b" if board.turn == "w" else "w"
        sr, sc, tr, tc = mv
        reset = apply_move(board, sr, sc, tr, tc)
        halfmove = 0 if reset else halfmove + 1
        if halfmove >= 100:
            return "draw"
        key = (board.get_fen().rsplit(" ", 2)[0],)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] >= 3:
            return "draw"
    return "draw"


def main():
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    games = int(sys.argv[2]) if len(sys.argv) > 2 else 16

    imp = Worker("chess_engine_cpp", depth)
    base = Worker("chess_engine_base", depth)

    imp_score = 0.0
    w = l = d = 0
    try:
        for i in range(games):
            fen = OPENINGS[i % len(OPENINGS)]
            imp_white = (i % 2 == 0)
            white, black = (imp, base) if imp_white else (base, imp)
            res = play_game(white, black, fen)  # 'w', 'b', or 'draw'
            if res == "draw":
                imp_score += 0.5; d += 1; tag = "draw"
            else:
                imp_won = (res == "w") == imp_white
                if imp_won:
                    imp_score += 1.0; w += 1; tag = "IMP wins"
                else:
                    l += 1; tag = "BASE wins"
            print(f"game {i+1:>2}/{games}  imp_white={imp_white}  -> {tag}", flush=True)
    finally:
        imp.close(); base.close()

    s = imp_score / games
    print(f"\nImproved vs Baseline @ depth {depth}: "
          f"{w}W {l}L {d}D  score {imp_score}/{games} ({100*s:.1f}%)")
    if 0 < s < 1:
        print(f"Approx Elo delta: {-400 * math.log10(1 / s - 1):+.0f}")


if __name__ == "__main__":
    main()
