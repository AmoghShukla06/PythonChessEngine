"""Lightweight opening book.

Built by replaying a set of well-known opening mainlines (in UCI coordinate
notation) from the start position and recording, for every position reached,
which move(s) the book plays next. During a game the AI consults the book by
position (a FEN key without move counters); if the current position is known it
plays a weighted-random book move instead of searching — giving fast, varied,
principled openings.

Positions are keyed by the first four FEN fields (placement, side, castling,
en-passant), so transpositions are handled automatically.
"""
import random

# Popular mainlines, each a space-separated sequence of UCI moves. Move weights
# come naturally from how often a move appears across lines from a position.
LINES = [
    # 1.e4 e5 openings
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 d7d6 c2c3 e8g8",  # Ruy Lopez
    "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3 g8f6 d2d3 d7d6",                                  # Italian
    "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3 f8c5 e1g1 d7d6",                                  # Italian (Nf6)
    "e2e4 e7e5 g1f3 g8f6 f3e5 d7d6 e5f3 f6e4 d2d4 d7d5",                                  # Petrov
    "e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f3d4 g8f6 b1c3 f8b4",                                  # Scotch
    # Sicilian
    "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6 f1e2 e7e5",                        # Najdorf
    "e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4 g8f6 b1c3 e7e5",                                  # Sveshnikov
    "e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4 b8c6 b1c3 d8c7",                                  # Taimanov
    "e2e4 c7c5 b1c3 b8c6 g2g3 g7g6 f1g2 f8g7",                                            # Closed Sicilian
    # Other 1.e4
    "e2e4 e7e6 d2d4 d7d5 b1c3 g8f6 e4e5 f6d7 f2f4 c7c5",                                  # French
    "e2e4 e7e6 d2d4 d7d5 b1d2 g8f6 e4e5 f6d7",                                            # French Tarrasch
    "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5 e4g3 f5g6",                                  # Caro-Kann
    "e2e4 c7c6 d2d4 d7d5 e4e5 c8f5 g1f3 e7e6",                                            # Caro Advance
    "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5 d2d4 g8f6 g1f3 c7c6",                                  # Scandinavian
    "e2e4 g8f6 e4e5 f6d5 d2d4 d7d6 g1f3 g7g6",                                            # Alekhine
    "e2e4 g7g6 d2d4 f8g7 b1c3 d7d6 f2f4 g8f6",                                            # Pirc
    # 1.d4 openings
    "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7 e2e3 e8g8",                                  # QGD
    "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 b1c3 d5c4 a2a4 c8f5",                                  # Slav
    "d2d4 d7d5 c2c4 d5c4 g1f3 g8f6 e2e3 e7e6 f1c4 c7c5",                                  # QGA
    "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6 g1f3 e8g8 f1e2 e7e5",                        # King's Indian
    "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 e2e3 e8g8 f1d3 d7d5",                                  # Nimzo-Indian
    "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6 g2g3 c8b7 f1g2 f8e7",                                  # Queen's Indian
    "d2d4 g8f6 c2c4 g7g6 b1c3 d7d5 c4d5 f6d5 e2e4 d5c3 b2c3 f8g7",                        # Grünfeld
    "d2d4 d7d5 g1f3 g8f6 c1f4 e7e6 e2e3 f8d6 f4d6 c7d6",                                  # London
    "d2d4 f7f5 g2g3 g8f6 f1g2 e7e6 g1f3 f8e7",                                            # Dutch
    # Flank
    "c2c4 e7e5 b1c3 g8f6 g1f3 b8c6 g2g3 d7d5 c4d5 f6d5",                                  # English
    "g1f3 d7d5 g2g3 g8f6 f1g2 e7e6 e1g1 f8e7",                                            # Réti
]

PROMO_RANKS = (0, 7)


def _uci_to_coords(uci):
    """'e2e4' -> (sr, sc, tr, tc) with row 0 = rank 8."""
    sc = ord(uci[0]) - ord("a")
    sr = 8 - int(uci[1])
    tc = ord(uci[2]) - ord("a")
    tr = 8 - int(uci[3])
    return sr, sc, tr, tc


def position_key(engine):
    """First four FEN fields (placement, side, castling, ep)."""
    return engine.get_fen().rsplit(" ", 2)[0]


class OpeningBook:
    def __init__(self, engine_factory, max_ply=20):
        self.book = {}  # position_key -> {(sr,sc,tr,tc): weight}
        self.max_ply = max_ply
        self._build(engine_factory)

    def _build(self, engine_factory):
        for line in LINES:
            engine = engine_factory()
            for uci in line.split():
                sr, sc, tr, tc = _uci_to_coords(uci)
                legal, caps = engine.legal_moves(sr, sc)
                if (tr, tc) not in legal and (tr, tc) not in caps:
                    # Bad move in a line (typo/illegal) — stop this line here.
                    break
                key = position_key(engine)
                slot = self.book.setdefault(key, {})
                mv = (sr, sc, tr, tc)
                slot[mv] = slot.get(mv, 0) + 1
                # Apply (book lines never promote; queen default is harmless).
                promo = "Q" if engine.board[sr][sc][1] == "P" and tr in PROMO_RANKS else None
                engine.make_move(sr, sc, tr, tc, promoted_piece=promo)

    def pick(self, engine, ply):
        """Return a (sr,sc,tr,tc) book move for the current position, or None."""
        if ply >= self.max_ply:
            return None
        slot = self.book.get(position_key(engine))
        if not slot:
            return None
        moves = list(slot.keys())
        weights = list(slot.values())
        return random.choices(moves, weights=weights, k=1)[0]

    def __len__(self):
        return len(self.book)
