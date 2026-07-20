"""Standard Algebraic Notation (SAN) + PGN helpers.

SAN is generated from the engine state *before* a move is applied (needed for
capture/disambiguation info); the check/checkmate suffix is added afterwards by
the caller from the post-move engine state.
"""
import datetime

FILES = "abcdefgh"


def _sq(r, c):
    return FILES[c] + str(8 - r)


def move_to_san(engine, sr, sc, tr, tc, promo=None):
    """Base SAN for a move, WITHOUT the +/# suffix. `engine` is pre-move."""
    piece = engine.board[sr][sc]
    if piece == "--":
        return _sq(sr, sc) + _sq(tr, tc)  # shouldn't happen
    ptype = piece[1]

    # Castling.
    if ptype == "K" and abs(tc - sc) == 2:
        return "O-O" if tc > sc else "O-O-O"

    target = engine.board[tr][tc]
    is_ep = ptype == "P" and sc != tc and target == "--"
    is_capture = (target != "--") or is_ep
    dest = _sq(tr, tc)

    if ptype == "P":
        san = (FILES[sc] + "x" if is_capture else "") + dest
        if promo:
            san += "=" + promo
        return san

    san = ptype
    # Disambiguation: other same-colour, same-type pieces that can also reach dest.
    color = piece[0]
    same_file = same_rank = need = False
    for r in range(8):
        for c in range(8):
            if (r, c) == (sr, sc):
                continue
            if engine.board[r][c] != piece:
                continue
            moves, caps = engine.legal_moves(r, c)
            if (tr, tc) in moves or (tr, tc) in caps:
                need = True
                if c == sc:
                    same_file = True
                if r == sr:
                    same_rank = True
    if need:
        if not same_file:
            san += FILES[sc]
        elif not same_rank:
            san += str(8 - sr)
        else:
            san += _sq(sr, sc)

    if is_capture:
        san += "x"
    san += dest
    return san


def build_pgn(san_moves, white_name, black_name, result="*"):
    """Assemble a PGN string from a flat list of SAN strings."""
    date = datetime.date.today().strftime("%Y.%m.%d")
    headers = [
        ('Event', 'Human vs AI'),
        ('Site', 'ChessEngine'),
        ('Date', date),
        ('White', white_name),
        ('Black', black_name),
        ('Result', result),
    ]
    lines = [f'[{k} "{v}"]' for k, v in headers]
    body = []
    for i, san in enumerate(san_moves):
        if i % 2 == 0:
            body.append(f"{i // 2 + 1}.")
        body.append(san)
    if result != "*":
        body.append(result)
    return "\n".join(lines) + "\n\n" + " ".join(body) + "\n"
