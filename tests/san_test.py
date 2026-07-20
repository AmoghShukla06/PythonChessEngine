"""Sanity-check SAN generation against a known move sequence."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import notation
from chess_engine_cpp import ChessEngine

# (sr,sc,tr,tc,promo) with expected SAN base (no +/# suffix checked here).
# Scholar's-mate-ish line + a castle + a disambiguation case.
MOVES = [
    (6, 4, 4, 4, None, "e4"),
    (1, 4, 3, 4, None, "e5"),
    (7, 5, 4, 2, None, "Bc4"),
    (0, 1, 2, 2, None, "Nc6"),
    (7, 3, 3, 7, None, "Qh5"),
    (0, 6, 2, 5, None, "Nf6"),
    (3, 7, 1, 5, None, "Qxf7"),   # capture + should be mate (#) in real game
]

def main():
    e = ChessEngine()
    ok = True
    for sr, sc, tr, tc, promo, expected in MOVES:
        san = notation.move_to_san(e, sr, sc, tr, tc, promo)
        promo_arg = promo
        e.make_move(sr, sc, tr, tc, promoted_piece=promo_arg)
        # append suffix like the app does
        if e.game_over and e.winner in ("w", "b"):
            san += "#"
        elif e.in_check(e.turn):
            san += "+"
        base = san.rstrip("+#")
        status = "OK" if base == expected else f"FAIL (got {base})"
        if base != expected:
            ok = False
        print(f"  {expected:>6} -> {san:<7} {status}")
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
