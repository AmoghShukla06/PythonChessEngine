# engine.py
# PURE CHESS ENGINE — NO GUI, NO TURTLE

class ChessEngine:
    def __init__(self):
        self.board = [
            ["bR","bN","bB","bQ","bK","bB","bN","bR"],
            ["bP","bP","bP","bP","bP","bP","bP","bP"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["--","--","--","--","--","--","--","--"],
            ["wP","wP","wP","wP","wP","wP","wP","wP"],
            ["wR","wN","wB","wQ","wK","wB","wN","wR"]
        ]
        self.turn = "w"
        self.en_passant = None
        self.castle_rights = {
            "w": {"kingside": True, "queenside": True},
            "b": {"kingside": True, "queenside": True}
        }
        self.king_moved = {"w": False, "b": False}
        self.game_over = False
        self.winner = None

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def enemy(self, color):
        return "b" if color == "w" else "w"

    # --- MOVEMENT GENERATION METHODS (Same as before) ---
    def pawn_moves(self, r, c):
        moves, caps = [], []
        color = self.board[r][c][0]
        d = -1 if color == "w" else 1
        start = 6 if color == "w" else 1

        if self.in_bounds(r+d, c) and self.board[r+d][c] == "--":
            moves.append((r+d, c))
            if r == start and self.board[r+2*d][c] == "--":
                moves.append((r+2*d, c))

        for dc in (-1, 1):
            nr, nc = r+d, c+dc
            if self.in_bounds(nr, nc):
                if self.board[nr][nc] != "--" and self.board[nr][nc][0] != color:
                    caps.append((nr, nc))

        if self.en_passant:
            er, ec = self.en_passant
            if er == r+d and abs(ec-c) == 1:
                caps.append((er, ec))
        return moves, caps

    def knight_moves(self, r, c):
        moves, caps = [], []
        color = self.board[r][c][0]
        for dr, dc in [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]:
            nr, nc = r+dr, c+dc
            if self.in_bounds(nr, nc):
                if self.board[nr][nc] == "--":
                    moves.append((nr, nc))
                elif self.board[nr][nc][0] != color:
                    caps.append((nr, nc))
        return moves, caps

    def slide_moves(self, r, c, directions):
        moves, caps = [], []
        color = self.board[r][c][0]
        for dr, dc in directions:
            nr, nc = r+dr, c+dc
            while self.in_bounds(nr, nc):
                if self.board[nr][nc] == "--":
                    moves.append((nr, nc))
                else:
                    if self.board[nr][nc][0] != color:
                        caps.append((nr, nc))
                    break
                nr += dr
                nc += dc
        return moves, caps

    def king_moves(self, r, c):
        moves, caps = [], []
        color = self.board[r][c][0]
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == dc == 0: continue
                nr, nc = r+dr, c+dc
                if self.in_bounds(nr, nc):
                    if self.board[nr][nc] == "--":
                        moves.append((nr, nc))
                    elif self.board[nr][nc][0] != color:
                        caps.append((nr, nc))
        return moves, caps

    def pseudo_moves(self, r, c):
        piece = self.board[r][c]
        if piece == "--": return [], []
        kind = piece[1]
        if kind == "P": return self.pawn_moves(r,c)
        if kind == "N": return self.knight_moves(r,c)
        if kind == "B": return self.slide_moves(r,c,[(1,1),(1,-1),(-1,1),(-1,-1)])
        if kind == "R": return self.slide_moves(r,c,[(1,0),(-1,0),(0,1),(0,-1)])
        if kind == "Q": return self.slide_moves(r,c,[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)])
        if kind == "K": return self.king_moves(r,c)
        return [], []

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == color+"K":
                    return r, c

    def square_attacked(self, r, c, by_color):
        for i in range(8):
            for j in range(8):
                if self.board[i][j].startswith(by_color):
                    m, caps = self.pseudo_moves(i,j)
                    if (r,c) in m or (r,c) in caps:
                        return True
        return False

    def in_check(self, color):
        kr, kc = self.find_king(color)
        return self.square_attacked(kr, kc, self.enemy(color))

    def legal_moves(self, r, c):
        color = self.board[r][c][0]
        piece = self.board[r][c]
        moves, caps = self.pseudo_moves(r,c)
        lm, lc = [], []

        if piece[1] == "K" and not self.king_moved[color] and not self.in_check(color):
            if self.castle_rights[color]["kingside"]:
                if (self.board[r][c+1] == "--" and self.board[r][c+2] == "--" and
                    not self.square_attacked(r, c+1, self.enemy(color)) and
                    not self.square_attacked(r, c+2, self.enemy(color))):
                    moves.append((r, c+2))
            if self.castle_rights[color]["queenside"]:
                if (self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and 
                    self.board[r][c-3] == "--" and
                    not self.square_attacked(r, c-1, self.enemy(color)) and
                    not self.square_attacked(r, c-2, self.enemy(color))):
                    moves.append((r, c-2))

        for tr, tc in moves + caps:
            captured = self.board[tr][tc]
            self.board[tr][tc] = self.board[r][c]
            self.board[r][c] = "--"
            if not self.in_check(color):
                (lm if (tr,tc) in moves else lc).append((tr,tc))
            self.board[r][c] = self.board[tr][tc]
            self.board[tr][tc] = captured
        return lm, lc

    def has_legal_moves(self, color):
        for r in range(8):
            for c in range(8):
                if self.board[r][c].startswith(color):
                    moves, caps = self.legal_moves(r, c)
                    if moves or caps:
                        return True
        return False

    def check_game_over(self):
        if not self.has_legal_moves(self.turn):
            self.game_over = True
            if self.in_check(self.turn):
                self.winner = self.enemy(self.turn)
            else:
                self.winner = "draw"
            return True
        return False

    def make_move(self, sr, sc, tr, tc, promoted_piece=None):
        """
        Executes the move on the board.
        If promoted_piece is passed (e.g. 'Q', 'N'), the moving pawn becomes that piece.
        """
        piece = self.board[sr][sc]
        color = piece[0]
        target = self.board[tr][tc]

        # FIX: If opponent rook is captured, remove their castling rights
        if target != "--" and target[1] == "R":
            if tr == 0 and tc == 0: self.castle_rights["b"]["queenside"] = False
            if tr == 0 and tc == 7: self.castle_rights["b"]["kingside"] = False
            if tr == 7 and tc == 0: self.castle_rights["w"]["queenside"] = False
            if tr == 7 and tc == 7: self.castle_rights["w"]["kingside"] = False

        # Castling Move
        if piece[1] == "K" and abs(tc - sc) == 2:
            self.board[tr][tc] = piece
            self.board[sr][sc] = "--"
            if tc > sc: # Kingside
                self.board[tr][5] = self.board[tr][7]
                self.board[tr][7] = "--"
            else: # Queenside
                self.board[tr][3] = self.board[tr][0]
                self.board[tr][0] = "--"
            self.king_moved[color] = True
            self.castle_rights[color]["kingside"] = False
            self.castle_rights[color]["queenside"] = False
        
        else:
            # En Passant Capture
            if piece[1] == "P" and (tr,tc) == self.en_passant:
                self.board[sr][tc] = "--"
            
            # Move piece (or Promote)
            if promoted_piece:
                self.board[tr][tc] = color + promoted_piece
            else:
                self.board[tr][tc] = piece
            
            self.board[sr][sc] = "--"

            # Update Castling Rights for Mover
            if piece[1] == "K":
                self.king_moved[color] = True
                self.castle_rights[color]["kingside"] = False
                self.castle_rights[color]["queenside"] = False
            elif piece[1] == "R":
                if sr == 7 and sc == 7: self.castle_rights["w"]["kingside"] = False
                elif sr == 7 and sc == 0: self.castle_rights["w"]["queenside"] = False
                elif sr == 0 and sc == 7: self.castle_rights["b"]["kingside"] = False
                elif sr == 0 and sc == 0: self.castle_rights["b"]["queenside"] = False

        # Update En Passant Target
        self.en_passant = None
        if piece[1] == "P" and abs(tr-sr) == 2:
            self.en_passant = ((tr+sr)//2, sc)
        
        self.turn = self.enemy(self.turn)
        self.check_game_over()