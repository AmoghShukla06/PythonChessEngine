import random

# ---------------------------------------------------------------------------
# Move aliases (White perspective)
# ---------------------------------------------------------------------------
# Pawns
e4   = (6,4,4,4);  e3   = (6,4,5,4);  e5w  = (6,4,3,4)  # white e-pawn
d4   = (6,3,4,3);  d3   = (6,3,5,3)
c4   = (6,2,4,2);  c3   = (6,2,5,2)
f4   = (6,5,4,5);  f3   = (6,5,5,5)
b4   = (6,1,4,1);  b3   = (6,1,5,1)
a3   = (6,0,5,0);  a4   = (6,0,4,0)
g3   = (6,6,5,6);  g4   = (6,6,4,6)
h3   = (6,7,5,7)

# White minor pieces
Nf3  = (7,6,5,5);  Ne2  = (7,6,6,4);  Ng5  = (5,5,3,6)
Nc3  = (7,1,5,2);  Nd2  = (7,1,6,3)
Bc4  = (7,5,4,2);  Bb5  = (7,5,4,1);  Be2  = (7,5,6,4)
Bg5  = (7,2,3,6);  Bf4  = (7,2,4,5);  Be3  = (7,2,5,4)

# White castles / rook / queen
OO_w = (7,4,7,6)   # kingside castling white
d5w  = (6,3,3,3)   # d2-d5 (not standard but alias for clarity)

# ---------------------------------------------------------------------------
# Black move aliases
# ---------------------------------------------------------------------------
e5b  = (1,4,3,4);  e6b  = (1,4,2,4)
d5b  = (1,3,3,3);  d6b  = (1,3,2,3)
c5b  = (1,2,3,2);  c6b  = (1,2,2,2)
f5b  = (1,5,3,5)
b6b  = (1,1,2,1);  b5b  = (1,1,3,1)
g6b  = (1,6,2,6);  g5b  = (1,6,3,6);  h6b  = (1,7,2,7)

Nf6b = (0,6,2,5);  Ng4b = (2,5,3,6);  Ne4b = (2,5,4,4)
Nc6b = (0,1,2,2);  Nd7b = (0,1,2,3)
Nf6b2= (0,6,2,5)   # same as Nf6b, alias

Bc5b = (0,5,3,2);  Bb4b = (0,5,3,1);  Be7b = (0,5,1,4)
Bg4b = (0,2,3,6);  Bf5b = (0,2,2,5)
OO_b = (0,4,0,6)   # kingside castling black
OOO_b= (0,4,0,2)   # queenside castling black

# ---------------------------------------------------------------------------
# BOOK
# Key: tuple of (sr,sc,tr,tc) tuples — the moves played so far
# Val: list of candidate responses to pick randomly from
# ---------------------------------------------------------------------------
BOOK = {}

def _add(line, responses):
    """Register all prefixes of `line` + `responses` into BOOK."""
    key = tuple(line)
    if key not in BOOK:
        BOOK[key] = []
    for r in responses:
        if r not in BOOK[key]:
            BOOK[key].append(r)

# ============================================================
# WHITE'S FIRST MOVE  (empty position)
# ============================================================
_add([], [e4, d4, Nf3, c4])

# ============================================================
# 1. e4 ...
# ============================================================
_add([e4], [e5b, c5b, e6b, c6b, d5b, Nf6b, d6b])

# --- 1...e5 (Open Game) ---
# White can choose from 7 distinct openings — selected randomly each game
_add([e4,e5b], [Nf3, Bc4, f4, Nc3])

# ---- OPENING 1: Ruy Lopez (1.e4 e5 2.Nf3 Nc6 3.Bb5) ----
_add([e4,e5b,Nf3], [Nc6b, Nf6b, d6b])
_add([e4,e5b,Nf3,Nc6b], [Bb5, Bc4, d4, Nc3])
a6b = (1,0,2,0)
Ba4w = (4,1,3,1)
_add([e4,e5b,Nf3,Nc6b,Bb5], [a6b, Nf6b, d6b])
_add([e4,e5b,Nf3,Nc6b,Bb5,a6b], [Ba4w])
_add([e4,e5b,Nf3,Nc6b,Bb5,a6b,Ba4w], [Nf6b])
_add([e4,e5b,Nf3,Nc6b,Bb5,a6b,Ba4w,Nf6b], [OO_w])
_add([e4,e5b,Nf3,Nc6b,Bb5,a6b,Ba4w,Nf6b,OO_w], [Be7b, (1,1,3,1)])  # ...Be7 or b5

# ---- OPENING 2: Italian / Giuoco Piano (1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.c3) ----
_add([e4,e5b,Nf3,Nc6b,Bc4], [Bc5b, Nf6b, Be7b])
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b], [c3, Nc3, d3])
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,c3], [Nf6b, d6b, (0,3,2,3)])   # Nf6/d6/Qe7
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,c3,Nf6b], [d4])                 # d4 central break
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,c3,Nf6b,d4], [(3,4,4,3)])       # exd4
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,c3,Nf6b,d4,(3,4,4,3)], [(5,2,4,3)])  # cxd4

# ---- OPENING 3: Evans Gambit (1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.b4) ----
b4_evans = (6,1,4,1)
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,b4_evans], [Bc5b, (3,2,4,1)])   # ...Bxb4 accept
Bxb4b = (3,2,4,1)
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,b4_evans,Bxb4b], [c3])          # 5.c3 gambit line
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,b4_evans,Bxb4b,c3], [(4,1,3,2)])# ...Bc5
_add([e4,e5b,Nf3,Nc6b,Bc4,Bc5b,b4_evans,Bxb4b,c3,(4,1,3,2)], [d4])

# ---- OPENING 4: Scotch Game (1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Nxd4) ----
exd4b = (3,4,4,3)
Nxd4w_scotch = (5,5,4,3)
_add([e4,e5b,Nf3,Nc6b,d4], [exd4b])
_add([e4,e5b,Nf3,Nc6b,d4,exd4b], [Nxd4w_scotch])
_add([e4,e5b,Nf3,Nc6b,d4,exd4b,Nxd4w_scotch], [Bc5b, Nf6b, (0,3,2,3)])  # Bc5/Nf6/Qh4
_add([e4,e5b,Nf3,Nc6b,d4,exd4b,Nxd4w_scotch,Bc5b], [Be3, Nc3, c3])
_add([e4,e5b,Nf3,Nc6b,d4,exd4b,Nxd4w_scotch,Nf6b], [Nc3, (4,3,3,5), Bc4])

# ---- OPENING 5: King's Gambit (1.e4 e5 2.f4) ----
f4_kg = (6,5,4,5)
fxe5b = (3,4,4,5)   # exf4 — black accepts
_add([e4,e5b,f4_kg], [fxe5b, d5b, Bc5b])     # accept/decline/Bc5
_add([e4,e5b,f4_kg,fxe5b], [Nf3, Bc4, (6,6,5,6)])  # 3.Nf3 / Bc4 / g3
_add([e4,e5b,f4_kg,fxe5b,Nf3], [(1,6,2,6), d6b, (1,6,3,6)])     # g6/d6/g5
_add([e4,e5b,f4_kg,fxe5b,Bc4], [(0,3,2,3), d5b, (1,6,3,6)])     # Qh4+ possibility
# King's Gambit Declined
_add([e4,e5b,f4_kg,Bc5b], [Nf3, c3])
_add([e4,e5b,f4_kg,d5b], [(4,4,3,3), Nc3])

# ---- OPENING 6: Bishop's Opening (1.e4 e5 2.Bc4) ----
_add([e4,e5b,Bc4], [Nf6b, Bc5b, Nc6b, d6b])
_add([e4,e5b,Bc4,Nf6b], [d3, Nc3, Nf3])
_add([e4,e5b,Bc4,Bc5b], [Nf3, d3, c3])
_add([e4,e5b,Bc4,Nc6b], [Nf3, d3, (6,6,5,6)])

# ---- OPENING 7: Vienna Game (1.e4 e5 2.Nc3) ----
_add([e4,e5b,Nc3], [Nc6b, Nf6b, Bc5b])
_add([e4,e5b,Nc3,Nc6b], [Bc4, f4, g3])      # Vienna Gambit or Bc4
_add([e4,e5b,Nc3,Nf6b], [f4, Bc4, g3])
_add([e4,e5b,Nc3,Bc5b], [Bc4, Nf3, f4])
_add([e4,e5b,Nc3,Nc6b,f4], [exd4b, d6b])    # Vienna Gambit accepted
_add([e4,e5b,Nc3,Nc6b,Bc4], [Bc5b, Nf6b])

# ---- OPENING 8: Four Knights (1.e4 e5 2.Nf3 Nc6 3.Nc3 Nf6) ----
Nf6b_4k = (0,6,2,5)
_add([e4,e5b,Nf3,Nc6b,Nc3], [Nf6b_4k, Bc5b, d6b])
_add([e4,e5b,Nf3,Nc6b,Nc3,Nf6b_4k], [Bb5, Bc4, d4])   # Spanish/Italian 4-Knights
_add([e4,e5b,Nf3,Nc6b,Nc3,Nf6b_4k,Bb5], [Bb4b, Nd4b:=(2,5,4,3), (1,3,2,3)])
_add([e4,e5b,Nf3,Nc6b,Nc3,Nf6b_4k,Bc4], [Bc5b, Nxe4b:=(2,5,4,4), (1,3,2,3)])

# ---- Petrov Defense (1.e4 e5 2.Nf3 Nf6) — Black plays symmetrically ----
_add([e4,e5b,Nf3,Nf6b], [(4,4,3,4), d4, Nc3])   # e5 push / d4 / Nc3
_add([e4,e5b,Nf3,Nf6b,(4,4,3,4)], [(2,5,4,4), d6b])    # Nxe5 or d6

# --- 1...c5 (Sicilian) ---
_add([e4,c5b], [Nf3, Nc3, c3])

#   2.Nf3 ...
_add([e4,c5b,Nf3], [d6b, Nc6b, e6b])

#     2...d6 3.d4 cxd4 4.Nxd4 (Open Sicilian)
_add([e4,c5b,Nf3,d6b], [d4])
_add([e4,c5b,Nf3,d6b,d4], [(3,2,4,3)])   # cxd4
cxd4b = (3,2,4,3)
_add([e4,c5b,Nf3,d6b,d4,cxd4b], [(5,5,4,3)])  # Nxd4
Nxd4w = (5,5,4,3)
_add([e4,c5b,Nf3,d6b,d4,cxd4b,Nxd4w], [Nf6b, (0,1,2,2)])    # Nf6 or Nc6 → Najdorf/Classical

#     2...Nc6 3.d4
_add([e4,c5b,Nf3,Nc6b], [d4, Bb5])
_add([e4,c5b,Nf3,Nc6b,d4], [(3,2,4,3)])  # cxd4
_add([e4,c5b,Nf3,Nc6b,d4,cxd4b], [(5,5,4,3)])  # Nxd4

#     2...e6 3.d4
_add([e4,c5b,Nf3,e6b], [d4, Nc3])
_add([e4,c5b,Nf3,e6b,d4], [(3,2,4,3)])  # cxd4

# --- 1...e6 (French Defence) ---
_add([e4,e6b], [d4])
_add([e4,e6b,d4], [d5b])
_add([e4,e6b,d4,d5b], [Nc3, Nd2, e3, (4,4,3,4)])  # Nc3/Nd2/e3/e5
e5push = (4,4,3,4)
_add([e4,e6b,d4,d5b,Nc3], [Nf6b, Bb4b, (1,3,2,3)])  # classical / Winawer
_add([e4,e6b,d4,d5b,Nc3,Bb4b], [(4,4,3,4), Nf3,(6,4,5,4)])  # e5/Nf3/e3 vs Winawer
_add([e4,e6b,d4,d5b,Nd2], [Nf6b, c5b])
_add([e4,e6b,d4,d5b,e5push], [c5b, Nd7b])          # French Advance

# --- 1...c6 (Caro-Kann) ---
_add([e4,c6b], [d4, Nc3, (6,3,5,3)])
_add([e4,c6b,d4], [d5b])
_add([e4,c6b,d4,d5b], [Nc3, Nd2, (4,4,3,4)])
_add([e4,c6b,d4,d5b,Nc3], [(3,3,4,4)])   # dxe4
dxe4b = (3,3,4,4)
_add([e4,c6b,d4,d5b,Nc3,dxe4b], [(5,2,4,4)])       # Nxe4

# --- 1...Nf6 (Alekhine/Pirc) ---
_add([e4,Nf6b], [(4,4,3,4), Nc3])  # e5 push or Nc3
_add([e4,Nf6b,(4,4,3,4)], [d5b, Nd7b])  # 2...d5 Scandinavian-ish / Nd7

# --- 1...d5 (Scandinavian) ---
_add([e4,d5b], [(4,4,3,3)])   # exd5
exd5w = (4,4,3,3)
_add([e4,d5b,exd5w], [(0,3,3,3),(0,3,2,3)])   # Qxd5 or Nf6
Qxd5b = (0,3,3,3)
_add([e4,d5b,exd5w,Qxd5b], [Nc3])             # 3.Nc3 chasing queen
_add([e4,d5b,exd5w,Nf6b], [c4, Nf3])

# --- 1...d6 (Pirc) ---
_add([e4,d6b], [d4, Nf3])
_add([e4,d6b,d4], [Nf6b, g6b])
_add([e4,d6b,d4,Nf6b], [Nc3])
_add([e4,d6b,d4,g6b],  [Nc3, Nf3])

# ============================================================
# 1. d4 ...
# ============================================================
_add([d4], [d5b, Nf6b, f5b, e6b, c5b])

# --- 1...d5  ---
_add([d4,d5b], [c4, Nf3, (6,2,5,2)])   # c4 = QG, Nf3, c3

#   2.c4 (Queen's Gambit)
_add([d4,d5b,c4], [e6b, c6b, (4,3,4,2)])   # QGD / Slav / QGA
dxc4b = (4,3,4,2)    # dxc4 = QGA

#     2...e6 3.Nc3 (QGD)
_add([d4,d5b,c4,e6b], [Nc3, Nf3])
_add([d4,d5b,c4,e6b,Nc3], [Nf6b, Bb4b])   # classical QGD or Nimzo-like
_add([d4,d5b,c4,e6b,Nc3,Nf6b], [Bg5, Nf3, (6,2,5,2)])
_add([d4,d5b,c4,e6b,Nc3,Nf6b,Bg5], [Be7b, (1,1,3,1)])   # classical / Tartakower

#     2...c6 3.Nc3 (Slav)
_add([d4,d5b,c4,c6b], [Nc3, Nf3, (6,4,5,4)])
_add([d4,d5b,c4,c6b,Nc3], [Nf6b, dxc4b])
_add([d4,d5b,c4,c6b,Nc3,Nf6b], [Nf3, (6,4,5,4)])

#     2...dxc4 (QGA)
_add([d4,d5b,c4,dxc4b], [Nf3, e3, Nc3])

# --- 1...Nf6 (Indian Systems) ---
_add([d4,Nf6b], [c4, Nf3, (6,2,5,2)])

#   2.c4 ...
_add([d4,Nf6b,c4], [g6b, e6b, c5b, (1,3,2,3)])   # KID / Nimzo / Benoni

#     2...g6 3.Nc3 (King's Indian Defence)
_add([d4,Nf6b,c4,g6b], [Nc3, (6,6,5,6)])
_add([d4,Nf6b,c4,g6b,Nc3], [(1,3,2,3), (0,5,2,3)])   # d6 / Bg7
Bg7b = (0,5,2,3)    # Bg7 for black (f8 to g7)
d6KID = (1,3,2,3)
_add([d4,Nf6b,c4,g6b,Nc3,d6KID], [e4, Nf3])
_add([d4,Nf6b,c4,g6b,Nc3,d6KID,e4], [Bg7b])
_add([d4,Nf6b,c4,g6b,Nc3,d6KID,e4,Bg7b], [Nf3, Be2, f3])

#     2...e6 3.Nc3 Bb4 (Nimzo-Indian)
_add([d4,Nf6b,c4,e6b], [Nc3, Nf3, g3])
_add([d4,Nf6b,c4,e6b,Nc3], [Bb4b, d5b])   # Nimzo or QGD transpose
_add([d4,Nf6b,c4,e6b,Nc3,Bb4b], [(6,3,5,3), (6,4,5,4), (6,3,4,3)])   # e3/e3/d4 stay

#     2...c5 (Benoni)
_add([d4,Nf6b,c4,c5b], [d5w2:=(4,3,3,3)])  # d5
d5push = (4,3,3,3)
_add([d4,Nf6b,c4,c5b,d5push], [e6b, g6b])

# --- 1...f5 (Dutch Defence) ---
_add([d4,f5b], [(6,2,5,2), Nf3, g3])

# --- 1...c5 (Benoni via 1.d4 c5) ---
_add([d4,c5b], [d5push, (6,4,5,4)])

# ============================================================
# 1. Nf3 (Réti / KIA)
# ============================================================
_add([Nf3], [d5b, Nf6b, c5b, g6b])
_add([Nf3,d5b], [c4, g3, (6,3,5,3)])
_add([Nf3,d5b,c4], [c6b, e6b, dxc4b, d4])
_add([Nf3,Nf6b], [c4, g3, d4])
_add([Nf3,Nf6b,c4], [g6b, e6b, c5b])

# ============================================================
# 1. c4 (English Opening)
# ============================================================
_add([c4], [e5b, Nf6b, c5b, g6b, e6b])
_add([c4,e5b], [Nc3, Nf3, g3])
_add([c4,e5b,Nc3], [Nf6b, Nc6b, Bb4b])
_add([c4,Nf6b], [Nc3, Nf3, g3])
_add([c4,Nf6b,Nc3], [e5b, g6b, e6b, c5b])

# ============================================================
# PUBLIC API
# ============================================================
def get_book_move(move_history: list) -> tuple | None:
    """
    Given the list of moves played so far (each a (sr,sc,tr,tc) tuple),
    return a random candidate book move, or None if position is not in book.
    """
    key = tuple(tuple(m) for m in move_history)
    candidates = BOOK.get(key)
    if candidates:
        return random.choice(candidates)
    return None
