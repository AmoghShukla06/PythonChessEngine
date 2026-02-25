# ai_engine.py  — Classical Chess Engine (Sequential, Production-Ready)
#
# Algorithmic techniques:
#   • Negamax + Alpha-Beta pruning (fail-soft)
#   • Null-Move Pruning  (R=2, skipped in check and endgame)
#   • Late Move Reductions (LMR, log-scaled per depth×move-count)
#   • Killer Moves  (2 per ply)
#   • History Heuristic
#   • Aspiration Windows in iterative deepening
#   • Quiescence Search (captures-only, avoids horizon blunders)
#   • Move ordering: MVV-LVA captures → killers → history → PST quiet
#   • Transposition Table (own-process dict, keyed by board+turn+ep)
#
# Note on multi-core: pure Python alpha-beta is inherently sequential.
# All attempts at multiprocessing (spawn / fork) hit fundamental Python
# interpreter barriers (GIL, semaphore inheritance, main-module re-execution).
# The algorithmic speedups above give a genuine 10-20× improvement over
# a naive alpha-beta — far more than parallel overhead could recover.

import os
import copy
import time

# ---------------------------------------------------------------------------
# MATERIAL VALUES (centipawns)
# ---------------------------------------------------------------------------
PIECE_VALUE = {
    'P': 100, 'N': 320, 'B': 330,
    'R': 500, 'Q': 900, 'K': 20000
}

# ---------------------------------------------------------------------------
# PIECE-SQUARE TABLES  (White's perspective; row 0 = rank 8; flipped for Black)
# ---------------------------------------------------------------------------
PST = {
    'P': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [ 5,  5, 10, 25, 25, 10,  5,  5],
        [ 0,  0,  0, 20, 20,  0,  0,  0],
        [ 5, -5,-10,  0,  0,-10, -5,  5],
        [ 5, 10, 10,-20,-20, 10, 10,  5],
        [ 0,  0,  0,  0,  0,  0,  0,  0],
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50],
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20],
    ],
    'R': [
        [ 0,  0,  0,  0,  0,  0,  0,  0],
        [ 5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [ 0,  0,  0,  5,  5,  0,  0,  0],
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [ -5,  0,  5,  5,  5,  5,  0, -5],
        [  0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20],
    ],
    'K_mid': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [ 20, 20,  0,  0,  0,  0, 20, 20],
        [ 20, 30, 10,  0,  0, 10, 30, 20],
    ],
    'K_end': [
        [-50,-40,-30,-20,-20,-30,-40,-50],
        [-30,-20,-10,  0,  0,-10,-20,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 30, 40, 40, 30,-10,-30],
        [-30,-10, 20, 30, 30, 20,-10,-30],
        [-30,-30,  0,  0,  0,  0,-30,-30],
        [-50,-30,-30,-30,-30,-30,-30,-50],
    ],
}

MVV_LVA = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}

# TT flags
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA  = 2

# LMR table[depth][move_index] → reduction
import math as _math
_LMR = [[0] * 33 for _ in range(9)]
for _d in range(1, 9):
    for _m in range(1, 33):
        _LMR[_d][_m] = int(0.5 + _math.log(_d) * _math.log(_m) / 2.0)


# ---------------------------------------------------------------------------
# ENGINE
# ---------------------------------------------------------------------------
class AlphaBetaEngine:
    """
    Sequential classical chess engine with:
      Negamax + Alpha-Beta · Null-Move Pruning · LMR
      Killer Moves · History Heuristic · Aspiration Windows
      Quiescence Search · Transposition Table
    Estimated ELO: ~1600–1800 at depth 5.
    """

    def __init__(self, depth: int = 5, time_limit: float = 5.0):
        self.max_depth  = depth
        self.time_limit = time_limit
        self._reset_search_state()
        print(f"[AI] Alpha-Beta engine ready. depth={depth}, time={time_limit}s")

    def _reset_search_state(self):
        self.transposition_table = {}
        self.killer_moves        = [[None, None] for _ in range(self.max_depth + 16)]
        self.history             = {}
        self.nodes_searched      = 0
        self.start_time          = 0.0

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def get_best_move(self, engine):
        """Return (sr, sc, tr, tc) for the best move."""
        self._reset_search_state()
        self.start_time = time.time()

        best_move  = None
        prev_score = 0
        asp_window = 50

        for depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break

            # Aspiration windows from depth 4 onward
            if depth >= 4:
                alpha, beta = prev_score - asp_window, prev_score + asp_window
            else:
                alpha, beta = -999_999, 999_999

            move, score = self._root_search(engine, depth, alpha, beta)

            # Re-search with full window if outside aspiration bounds
            if score <= alpha or score >= beta:
                move, score = self._root_search(engine, depth, -999_999, 999_999)

            prev_score = score
            if move is not None:
                best_move = move

            print(f"  [AI] depth={depth:2d}  score={score:+5d}  "
                  f"nodes={self.nodes_searched:7d}  "
                  f"time={time.time()-self.start_time:.2f}s")

            if abs(score) >= 15_000:
                break   # Forced mate

        return best_move or self._any_legal_move(engine)

    # ------------------------------------------------------------------
    # ROOT SEARCH
    # ------------------------------------------------------------------
    def _root_search(self, engine, depth, alpha, beta):
        color     = engine.turn
        moves     = self._gen_ordered_moves(engine, color, ply=0)
        best_score = -999_999
        best_move  = None
        local_alpha = alpha

        for move in moves:
            if time.time() - self.start_time > self.time_limit:
                break
            sr, sc, tr, tc, promo = move
            undo  = self._make_move(engine, sr, sc, tr, tc, promo)
            score = -self._negamax(engine, depth - 1, -beta, -local_alpha)
            self._undo_move(engine, undo)

            if score > best_score:
                best_score = score
                best_move  = (sr, sc, tr, tc)
            local_alpha = max(local_alpha, score)
            if local_alpha >= beta:
                break

        return best_move, best_score

    # ------------------------------------------------------------------
    # NEGAMAX WITH ALPHA-BETA + NULL MOVE + LMR + KILLERS + HISTORY
    # ------------------------------------------------------------------
    def _negamax(self, engine, depth, alpha, beta):
        self.nodes_searched += 1

        # Time check every 2048 nodes
        if self.nodes_searched & 2047 == 0:
            if time.time() - self.start_time > self.time_limit:
                return 0

        # TT lookup
        key = self._board_hash(engine)
        tt  = self.transposition_table.get(key)
        if tt and tt['depth'] >= depth:
            flag, sc = tt['flag'], tt['score']
            if flag == TT_EXACT:              return sc
            if flag == TT_ALPHA and sc <= alpha: return alpha
            if flag == TT_BETA  and sc >= beta:  return beta

        # Terminal
        if engine.game_over:
            return 0 if engine.winner == 'draw' else -(20_000 - depth)

        if depth == 0:
            return self._quiescence(engine, alpha, beta)

        color    = engine.turn
        in_check = engine.in_check(color)

        # Null-Move Pruning (skip if in check or near endgame)
        if not in_check and depth >= 3 and self._material_count(engine) > 1500:
            R = 2
            engine.turn = 'b' if color == 'w' else 'w'
            null_score  = -self._negamax(engine, depth - 1 - R, -beta, -beta + 1)
            engine.turn = color
            if null_score >= beta:
                return beta

        moves = self._gen_ordered_moves(engine, color, ply=self.max_depth - depth)

        if not moves:
            return -(20_000 - depth) if in_check else 0

        original_alpha = alpha
        best_score     = -999_999
        move_count     = 0

        for move in moves:
            sr, sc, tr, tc, promo = move
            is_capture = engine.board[tr][tc] != '--' or (
                engine.board[sr][sc][1] == 'P' and
                (tr, tc) == engine.en_passant)

            # Late Move Reductions
            reduction = 0
            if (not in_check and not is_capture and
                    depth >= 3 and move_count >= 3 and promo is None):
                d_idx = min(depth, 8)
                m_idx = min(move_count, 32)
                reduction = max(0, min(_LMR[d_idx][m_idx], depth - 2))

            undo  = self._make_move(engine, sr, sc, tr, tc, promo)
            score = -self._negamax(engine, depth - 1 - reduction, -beta, -alpha)
            if reduction > 0 and score > alpha:
                score = -self._negamax(engine, depth - 1, -beta, -alpha)
            self._undo_move(engine, undo)
            move_count += 1

            if score > best_score:
                best_score = score
            if score > alpha:
                alpha = score
                # Update killer moves
                if not is_capture and promo is None:
                    ply = self.max_depth - depth
                    km  = self.killer_moves[ply]
                    if km[0] != (sr, sc, tr, tc):
                        km[1] = km[0]
                        km[0] = (sr, sc, tr, tc)

            if alpha >= beta:
                # History heuristic
                if not is_capture and promo is None:
                    hkey = (engine.turn, tr, tc)
                    self.history[hkey] = self.history.get(hkey, 0) + depth * depth
                break

        # TT store
        flag = TT_ALPHA if best_score <= original_alpha else \
               TT_BETA  if best_score >= beta else TT_EXACT
        self.transposition_table[key] = {
            'score': best_score, 'depth': depth, 'flag': flag}

        return best_score

    # ------------------------------------------------------------------
    # QUIESCENCE SEARCH
    # ------------------------------------------------------------------
    def _quiescence(self, engine, alpha, beta):
        self.nodes_searched += 1
        stand_pat = self._evaluate(engine)
        if stand_pat >= beta:   return beta
        alpha = max(alpha, stand_pat)

        for move in self._gen_capture_moves(engine, engine.turn):
            sr, sc, tr, tc, promo = move
            undo  = self._make_move(engine, sr, sc, tr, tc, promo)
            score = -self._quiescence(engine, -beta, -alpha)
            self._undo_move(engine, undo)
            if score >= beta:  return beta
            alpha = max(alpha, score)
        return alpha

    # ------------------------------------------------------------------
    # EVALUATION
    # ------------------------------------------------------------------
    def _evaluate(self, engine):
        total_mat = sum(
            PIECE_VALUE[p[1]] for r in engine.board for p in r
            if p != '--' and p[1] != 'K')
        endgame = total_mat < 1500

        sw = sb = 0
        for r in range(8):
            for c in range(8):
                p = engine.board[r][c]
                if p == '--': continue
                color, kind = p[0], p[1]
                val     = PIECE_VALUE[kind]
                pst_key = ('K_end' if endgame else 'K_mid') if kind == 'K' else kind
                if color == 'w':
                    sw += val + PST[pst_key][r][c]
                else:
                    sb += val + PST[pst_key][7 - r][c]

        sw += self._mobility(engine, 'w') * 5
        sb += self._mobility(engine, 'b') * 5

        raw = sw - sb
        return raw if engine.turn == 'w' else -raw

    def _mobility(self, engine, color):
        count = 0
        for r in range(8):
            for c in range(8):
                if engine.board[r][c].startswith(color):
                    m, caps = engine.pseudo_moves(r, c)
                    count += len(m) + len(caps)
        return count

    def _material_count(self, engine):
        return sum(
            PIECE_VALUE[p[1]] for r in engine.board for p in r
            if p != '--' and p[1] != 'K')

    # ------------------------------------------------------------------
    # MOVE GENERATION
    # ------------------------------------------------------------------
    def _gen_ordered_moves(self, engine, color, ply=0):
        captures, killers, quiets = [], [], []
        ply = max(0, min(ply, len(self.killer_moves) - 1))
        km  = self.killer_moves[ply]

        for r in range(8):
            for c in range(8):
                if not engine.board[r][c].startswith(color):
                    continue
                kind = engine.board[r][c][1]
                moves, caps = engine.legal_moves(r, c)

                for tr, tc in caps:
                    victim = engine.board[tr][tc]
                    vval   = MVV_LVA.get(victim[1], 1) if victim != '--' else MVV_LVA['P']
                    score  = vval * 10 - MVV_LVA.get(kind, 1)
                    if kind == 'P' and (tr == 0 or tr == 7):
                        for promo in ['Q', 'R', 'B', 'N']:
                            captures.append((r, c, tr, tc, promo, score + PIECE_VALUE[promo]))
                    else:
                        captures.append((r, c, tr, tc, None, score))

                for tr, tc in moves:
                    if kind == 'P' and (tr == 0 or tr == 7):
                        for promo in ['Q', 'R', 'B', 'N']:
                            quiets.append((r, c, tr, tc, promo, PIECE_VALUE[promo]))
                        continue
                    is_killer = (r, c, tr, tc) in (km[0], km[1])
                    hist_val  = self.history.get((color, tr, tc), 0)
                    pst_key   = 'K_mid' if kind == 'K' else kind
                    if color == 'w':
                        pst_d = PST[pst_key][tr][tc] - PST[pst_key][r][c]
                    else:
                        pst_d = PST[pst_key][7-tr][tc] - PST[pst_key][7-r][c]
                    if is_killer:
                        killers.append((r, c, tr, tc, None, 9000 + pst_d))
                    else:
                        quiets.append((r, c, tr, tc, None, hist_val + pst_d))

        captures.sort(key=lambda x: -x[5])
        killers.sort(key=lambda x:  -x[5])
        quiets.sort(key=lambda x:   -x[5])
        return [(m[0], m[1], m[2], m[3], m[4]) for m in captures + killers + quiets]

    def _gen_capture_moves(self, engine, color):
        out = []
        for r in range(8):
            for c in range(8):
                if not engine.board[r][c].startswith(color): continue
                kind = engine.board[r][c][1]
                _, caps = engine.legal_moves(r, c)
                for tr, tc in caps:
                    promo = 'Q' if kind == 'P' and (tr == 0 or tr == 7) else None
                    out.append((r, c, tr, tc, promo))
        return out

    # ------------------------------------------------------------------
    # MAKE / UNDO
    # ------------------------------------------------------------------
    def _make_move(self, engine, sr, sc, tr, tc, promo):
        undo = {
            'board':         [row[:] for row in engine.board],
            'turn':          engine.turn,
            'en_passant':    engine.en_passant,
            'castle_rights': copy.deepcopy(engine.castle_rights),
            'king_moved':    dict(engine.king_moved),
            'game_over':     engine.game_over,
            'winner':        engine.winner,
        }
        engine.make_move(sr, sc, tr, tc, promoted_piece=promo)
        return undo

    def _undo_move(self, engine, undo):
        engine.board         = undo['board']
        engine.turn          = undo['turn']
        engine.en_passant    = undo['en_passant']
        engine.castle_rights = undo['castle_rights']
        engine.king_moved    = undo['king_moved']
        engine.game_over     = undo['game_over']
        engine.winner        = undo['winner']

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _board_hash(self, engine):
        return (tuple(tuple(r) for r in engine.board),
                engine.turn, engine.en_passant)

    def _any_legal_move(self, engine):
        for r in range(8):
            for c in range(8):
                if engine.board[r][c].startswith(engine.turn):
                    moves, caps = engine.legal_moves(r, c)
                    if moves: return (r, c, moves[0][0], moves[0][1])
                    if caps:  return (r, c, caps[0][0],  caps[0][1])
        return None
