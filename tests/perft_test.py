"""Perft correctness check for the C++ move generator.

Validates legal-move generation + make/unmake against known node counts
for the standard starting position. Run after any move-gen change.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chess_engine_cpp as m

# (name, FEN, {depth: expected_nodes}). Standard perft positions that exercise
# castling, en passant, promotions, and pin edge cases.
POSITIONS = [
    ("startpos", None,
     {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609}),
    ("kiwipete",
     "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
     {1: 48, 2: 2039, 3: 97862, 4: 4085603}),
    ("position3",
     "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
     {1: 14, 2: 191, 3: 2812, 4: 43238, 5: 674624}),
    ("position4",
     "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
     {1: 6, 2: 264, 3: 9467, 4: 422333}),
    ("position5",
     "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
     {1: 44, 2: 1486, 3: 62379, 4: 2103487}),
]

def main():
    ok = True
    for name, fen, expected in POSITIONS:
        for depth, exp in expected.items():
            engine = m.ChessEngine()
            if fen is not None:
                if not engine.load_fen(fen):
                    print(f"{name}: FAILED to load FEN")
                    ok = False
                    continue
            got = engine.perft(depth)
            status = "OK" if got == exp else "FAIL"
            if got != exp:
                ok = False
            print(f"{name:>10} perft({depth}) = {got:>10}  expected {exp:>10}  {status}")
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
