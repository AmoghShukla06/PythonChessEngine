#ifndef AI_ENGINE_H
#define AI_ENGINE_H

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <tuple>
#include <unordered_map>
#include <vector>

namespace py = pybind11;
using namespace std;

// Piece values
static const int PIECE_VALUE[6] = {100, 320, 330, 500, 900, 20000};

// --- Piece-Square Tables ---
const int PST_P[64] = {0,   0,  0,  0,   0,  0,  0,   0,  50, 50, 50, 50, 50,
                       50,  50, 50, 10,  10, 20, 30,  30, 20, 10, 10, 5,  5,
                       10,  25, 25, 10,  5,  5,  0,   0,  0,  20, 20, 0,  0,
                       0,   5,  -5, -10, 0,  0,  -10, -5, 5,  5,  10, 10, -20,
                       -20, 10, 10, 5,   0,  0,  0,   0,  0,  0,  0,  0};

const int PST_N[64] = {-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0,
                       0,   0,   0,   -20, -40, -30, 0,   10,  15,  15,  10,
                       0,   -30, -30, 5,   15,  20,  20,  15,  5,   -30, -30,
                       0,   15,  20,  20,  15,  0,   -30, -30, 5,   10,  15,
                       15,  10,  5,   -30, -40, -20, 0,   5,   5,   0,   -20,
                       -40, -50, -40, -30, -30, -30, -30, -40, -50};

const int PST_B[64] = {-20, -10, -10, -10, -10, -10, -10, -20, -10, 0,   0,
                       0,   0,   0,   0,   -10, -10, 0,   5,   10,  10,  5,
                       0,   -10, -10, 5,   5,   10,  10,  5,   5,   -10, -10,
                       0,   10,  10,  10,  10,  0,   -10, -10, 10,  10,  10,
                       10,  10,  10,  -10, -10, 5,   0,   0,   0,   0,   5,
                       -10, -20, -10, -10, -10, -10, -10, -10, -20};

const int PST_R[64] = {0,  0, 0, 0, 0, 0, 0, 0,  5,  10, 10, 10, 10, 10, 10, 5,
                       -5, 0, 0, 0, 0, 0, 0, -5, -5, 0,  0,  0,  0,  0,  0,  -5,
                       -5, 0, 0, 0, 0, 0, 0, -5, -5, 0,  0,  0,  0,  0,  0,  -5,
                       0,  0, 0, 5, 5, 0, 0, 0,  0,  5,  5,  0,  0,  5,  5,  0};

const int PST_Q[64] = {
    -20, -10, -10, -5, -5, -10, -10, -20, -10, 0,   0,   0,  0,  0,   0,   -10,
    -10, 0,   5,   5,  5,  5,   0,   -10, -5,  0,   5,   5,  5,  5,   0,   -5,
    0,   0,   5,   5,  5,  5,   0,   -5,  -10, 5,   5,   5,  5,  5,   0,   -10,
    -10, 0,   5,   0,  0,  0,   0,   -10, -20, -10, -10, -5, -5, -10, -10, -20};

const int PST_K_mid[64] = {
    -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50,
    -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40,
    -40, -50, -50, -40, -40, -30, -20, -30, -30, -40, -40, -30, -30,
    -20, -10, -20, -20, -20, -20, -20, -20, -10, 20,  20,  0,   0,
    0,   0,   20,  20,  20,  30,  10,  0,   0,   10,  30,  20};

const int PST_K_end[64] = {
    -50, -40, -30, -20, -20, -30, -40, -50, -30, -20, -10, 0,   0,
    -10, -20, -30, -30, -10, 20,  30,  30,  20,  -10, -30, -30, -10,
    30,  40,  40,  30,  -10, -30, -30, -10, 30,  40,  40,  30,  -10,
    -30, -30, -10, 20,  30,  30,  20,  -10, -30, -30, -30, 0,   0,
    0,   0,   -30, -30, -50, -30, -30, -30, -30, -30, -30, -50};

static unordered_map<int, int> MVV_LVA = {{P, 1}, {N, 2}, {B, 3},
                                          {R, 4}, {Q, 5}, {K, 6}};

static const int TT_EXACT = 0;
static const int TT_ALPHA = 1;
static const int TT_BETA = 2;

struct TTEntry {
  U64 full_key; // full Zobrist key for collision detection
  int score;
  int depth;
  int flag;
  int sr, sc, tr, tc;
  char promo;
  uint8_t gen; // search generation for aging-based replacement
};

// --- Passed pawn bonuses by rank (from White's perspective) ---
static const int PASSED_PAWN_BONUS[8] = {0, 10, 20, 30, 50, 70, 90, 0};

class AlphaBetaEngine {
public:
  int max_depth;
  double time_limit;
  vector<tuple<int, int, int, int>> move_history;

  vector<TTEntry> tt;    // fixed-size, bucket-indexed transposition table
  U64 tt_mask;           // (tt.size() - 1), tt.size() is a power of two
  uint8_t tt_gen;        // current search generation
  vector<pair<MoveFull, MoveFull>> killer_moves;
  unordered_map<U64, int> history;
  int nodes_searched;
  double start_time;
  vector<vector<int>> LMR_table;

  // Search introspection (read from Python for eval bar / tests / logging).
  bool verbose = false;  // print per-depth search info to stdout
  int last_score = 0;    // score (centipawns, side-to-move POV) of last search
  int completed_depth = 0; // deepest fully-searched depth in last search

  AlphaBetaEngine(int depth = 5, double time_limit = 5.0) {
    max_depth = depth;
    this->time_limit = time_limit;
    size_t tt_size = 1u << 21; // ~2M entries
    tt.assign(tt_size, TTEntry{0, 0, -1, 0, -1, -1, -1, -1, 0, 0});
    tt_mask = tt_size - 1;
    tt_gen = 0;
    history.reserve(1 << 18);

    LMR_table.assign(9, vector<int>(33, 0));
    for (int d = 1; d < 9; d++) {
      for (int m = 1; m < 33; m++) {
        LMR_table[d][m] = (int)(0.5 + log(d) * log(m) / 2.0);
      }
    }
    _reset_search_state();
  }

  void record_move(py::tuple move) {
    move_history.push_back({move[0].cast<int>(), move[1].cast<int>(),
                            move[2].cast<int>(), move[3].cast<int>()});
  }

  void _reset_search_state() {
    killer_moves.assign(max_depth + 16, {MoveFull{-1, -1, -1, -1, ""},
                                         MoveFull{-1, -1, -1, -1, ""}});
    for (auto &kv : history) {
      kv.second >>= 1;
    }
    if (history.size() > 250000) {
      history.clear();
    }
    nodes_searched = 0;
    start_time = 0.0;
  }

  bool _is_same_move(const MoveFull &m, const TTEntry &tt) const {
    if (tt.sr < 0)
      return false;
    if (get<0>(m) != tt.sr || get<1>(m) != tt.sc || get<2>(m) != tt.tr ||
        get<3>(m) != tt.tc) {
      return false;
    }
    const string &promo = get<4>(m);
    if (promo.empty())
      return tt.promo == 0;
    return promo[0] == tt.promo;
  }

  U64 _history_key(const MoveFull &m) const {
    return (U64)get<0>(m) ^ ((U64)get<1>(m) << 8) ^ ((U64)get<2>(m) << 16) ^
           ((U64)get<3>(m) << 24);
  }

  double get_time() {
    return chrono::duration_cast<chrono::duration<double>>(
               chrono::steady_clock::now().time_since_epoch())
        .count();
  }

  // --- Transposition table access ---
  const TTEntry *_tt_probe(U64 key) const {
    const TTEntry &e = tt[key & tt_mask];
    if (e.depth >= 0 && e.full_key == key)
      return &e;
    return nullptr;
  }

  void _tt_store(U64 key, int score, int depth, int flag, const MoveFull &m) {
    TTEntry &e = tt[key & tt_mask];
    // Keep a deeper entry from the current search on a bucket collision;
    // otherwise (empty, stale generation, or same position) overwrite.
    if (e.depth >= 0 && e.gen == tt_gen && e.full_key != key && e.depth > depth)
      return;
    char promo = get<4>(m).empty() ? 0 : get<4>(m)[0];
    e = {key,        score,      depth,      flag, get<0>(m),
         get<1>(m),  get<2>(m),  get<3>(m),  promo, tt_gen};
  }

  // =============================================
  // 1. ZOBRIST HASHING
  // =============================================
  U64 _get_hash(const ChessEngine &engine) {
    U64 h = 0;
    for (int color = 0; color < 2; color++) {
      for (int piece = 0; piece < 6; piece++) {
        U64 bb = engine.pieces[color][piece];
        while (bb) {
          int sq = bb_ctzll(bb);
          h ^= zobrist_pieces[color][piece][sq];
          bb &= bb - 1;
        }
      }
    }
    if (engine.turn_col == BLACK)
      h ^= zobrist_side;
    if (engine.ep_square >= 0 && engine.ep_square < 64)
      h ^= zobrist_ep[engine.ep_square];
    h ^= zobrist_castling[engine.castling & 0xF];
    return h;
  }

  // =============================================
  // ITERATIVE DEEPENING
  // =============================================
  py::object get_best_move(ChessEngine &engine) {
    _reset_search_state();
    tt_gen++; // new search generation for TT aging
    start_time = get_time();

    MoveFull best_move = {-1, -1, -1, -1, ""};
    bool has_best = false;
    int prev_score = 0;
    int asp_window = 50;
    MoveFull pv_hint = {-1, -1, -1, -1, ""};

    for (int depth = 1; depth <= max_depth; depth++) {
      if (get_time() - start_time > time_limit)
        break;

      int alpha = (depth >= 4) ? prev_score - asp_window : -999999;
      int beta = (depth >= 4) ? prev_score + asp_window : 999999;

      auto res = _root_search(engine, depth, alpha, beta, &pv_hint);
      MoveFull move = res.first;
      int score = res.second;

      if (score <= alpha || score >= beta) {
        res = _root_search(engine, depth, -999999, 999999, &pv_hint);
        move = res.first;
        score = res.second;
      }

      prev_score = score;
      if (get<0>(move) != -1) {
        best_move = move;
        has_best = true;
        pv_hint = move;
        last_score = score;
        completed_depth = depth;
      }

      if (verbose) {
        cout << "  [AI-BB] depth=" << depth << "  score=" << score
             << "  nodes=" << nodes_searched
             << "  time=" << (get_time() - start_time) << "s\n";
      }

      if (abs(score) >= 15000)
        break;
    }

    if (has_best) {
      return py::make_tuple(get<0>(best_move), get<1>(best_move),
                            get<2>(best_move), get<3>(best_move));
    } else {
      // fallback legal move
      auto pms = engine.get_pseudo_moves(engine.turn_col);
      for (auto &m : pms) {
        auto st = engine.save_state();
        int tc = engine.turn_col;
        engine.make_move_fast(get<0>(m), get<1>(m), get<2>(m), get<3>(m),
                              get<4>(m));
        U64 king_bb = engine.pieces[tc][K];
        bool in_chk =
            !king_bb || engine.is_attacked(bb_ctzll(king_bb), engine.enemy_col(tc));
        engine.restore_state(st, tc);
        if (!in_chk) {
          return py::make_tuple(get<0>(m), get<1>(m), get<2>(m), get<3>(m));
        }
      }
    }
    return py::none();
  }

  // =============================================
  // 4. PVS — ROOT SEARCH
  // =============================================
  pair<MoveFull, int> _root_search(ChessEngine &engine, int depth, int alpha,
                                   int beta,
                                   const MoveFull *preferred_move = nullptr) {
    int color = engine.turn_col;
    U64 key = _get_hash(engine);
    const TTEntry *tt_ptr = _tt_probe(key);
    auto moves = _gen_ordered_moves(engine, color, 0, false, tt_ptr,
                                    preferred_move);
    int best_score = -999999;
    MoveFull best_move = {-1, -1, -1, -1, ""};
    bool first_move = true;

    for (auto &move : moves) {
      if (get_time() - start_time > time_limit)
        break;

      auto st = engine.save_state();
      int tc = engine.turn_col;

      engine.make_move_fast(get<0>(move), get<1>(move), get<2>(move),
                            get<3>(move), get<4>(move));

      // Validate move
      U64 king_bb = engine.pieces[color][K];
      if (!king_bb ||
          engine.is_attacked(bb_ctzll(king_bb), engine.enemy_col(color))) {
        engine.restore_state(st, tc);
        continue;
      }

      int score;
      if (first_move) {
        // PVS: full window for first move
        score = -_negamax(engine, depth - 1, -beta, -alpha, 1);
        first_move = false;
      } else {
        // PVS: zero-window search
        score = -_negamax(engine, depth - 1, -alpha - 1, -alpha, 1);
        if (score > alpha && score < beta) {
          // Re-search with full window
          score = -_negamax(engine, depth - 1, -beta, -alpha, 1);
        }
      }
      engine.restore_state(st, tc);

      if (score > best_score) {
        best_score = score;
        best_move = move;
      }
      alpha = max(alpha, score);
      if (alpha >= beta)
        break;
    }
    return {best_move, best_score};
  }

  // =============================================
  // 4. PVS — NEGAMAX with PVS
  // =============================================
  int _negamax(ChessEngine &engine, int depth, int alpha, int beta, int ply) {
    nodes_searched++;

    if ((nodes_searched & 2047) == 0) {
      if (get_time() - start_time > time_limit)
        return 0;
    }

    bool is_pv = (beta - alpha) > 1;

    auto key = _get_hash(engine);
    const TTEntry *tt_ptr = _tt_probe(key);
    if (tt_ptr) {
      const TTEntry &e = *tt_ptr;
      if (e.depth >= depth && !is_pv) {
        if (e.flag == TT_EXACT)
          return e.score;
        if (e.flag == TT_ALPHA && e.score <= alpha)
          return alpha;
        if (e.flag == TT_BETA && e.score >= beta)
          return beta;
      }
    }

    int color = engine.turn_col;
    bool in_check = engine.in_check_col(color);

    // Check extension: search one ply deeper when in check (bounded so
    // perpetual checks can't explode the tree or overrun killer arrays).
    if (in_check && ply < 2 * max_depth + 8)
      depth++;

    if (depth <= 0)
      return _quiescence(engine, alpha, beta);

    bool non_mate_window = (abs(beta) < 15000 && abs(alpha) < 15000);

    // Lazy static eval (used by reverse-futility and futility pruning).
    int static_eval = 0;
    bool have_static = false;
    auto get_static = [&]() {
      if (!have_static) {
        static_eval = _evaluate(engine);
        have_static = true;
      }
      return static_eval;
    };

    // Reverse futility pruning (static null move): if a big margin below the
    // static eval still beats beta, assume the node fails high.
    if (!in_check && !is_pv && depth <= 6 && non_mate_window) {
      int margin = 85 * depth;
      if (get_static() - margin >= beta)
        return get_static() - margin;
    }

    // Null move pruning (adaptive R).
    if (!in_check && !is_pv && depth >= 3 && non_mate_window) {
      int total_mat = 0;
      for (int i = 0; i < 5; i++) {
        total_mat += count_bits(engine.pieces[WHITE][i]) * PIECE_VALUE[i];
        total_mat += count_bits(engine.pieces[BLACK][i]) * PIECE_VALUE[i];
      }
      if (total_mat > 1500) {
        int R = 2 + depth / 6;
        auto nm_st = engine.save_state();
        int nm_tc = engine.turn_col;
        engine.turn_col = engine.enemy_col(color);
        engine.ep_square = -1; // clear en-passant square during null move
        int null_score =
            -_negamax(engine, depth - 1 - R, -beta, -beta + 1, ply + 1);
        engine.restore_state(nm_st, nm_tc);
        if (null_score >= beta)
          return beta;
      }
    }

    auto moves = _gen_ordered_moves(engine, color, ply, false, tt_ptr, nullptr);

    // Late-move-pruning thresholds by depth (number of quiet moves to try
    // before skipping the rest at shallow depths).
    static const int LMP[4] = {0, 6, 10, 16};

    int original_alpha = alpha;
    int best_score = -999999;
    MoveFull best_move = {-1, -1, -1, -1, ""};
    int move_count = 0;
    int quiet_count = 0;
    bool has_legal = false;
    bool pv_search_done = false;

    for (auto &move : moves) {
      int tr = get<2>(move);
      int tc_sq = get<3>(move);
      string promo = get<4>(move);
      bool is_capture = (engine.occupied & (1ULL << (tr * 8 + tc_sq))) != 0;
      bool is_quiet = !is_capture && promo.empty();

      // Move-count based pruning of late quiet moves (only once we already have
      // a searched legal move, so we never wrongly report checkmate/stalemate).
      if (has_legal && is_quiet && !in_check && non_mate_window) {
        if (depth <= 3 && quiet_count >= LMP[depth]) {
          quiet_count++;
          continue;
        }
        // Futility pruning near the frontier.
        if (depth <= 2) {
          int fmargin = 100 + 150 * depth;
          if (get_static() + fmargin <= alpha) {
            quiet_count++;
            continue;
          }
        }
      }

      auto st = engine.save_state();
      int tc = engine.turn_col;

      engine.make_move_fast(get<0>(move), get<1>(move), tr, tc_sq, promo);
      U64 king_bb = engine.pieces[color][K];
      if (!king_bb ||
          engine.is_attacked(bb_ctzll(king_bb), engine.enemy_col(color))) {
        engine.restore_state(st, tc);
        continue;
      }
      has_legal = true;
      if (is_quiet)
        quiet_count++;

      // LMR
      int reduction = 0;
      if (!in_check && is_quiet && depth >= 3 && move_count >= 3) {
        int d_idx = min(depth, 8);
        int m_idx = min(move_count, 32);
        reduction = max(0, min(LMR_table[d_idx][m_idx], depth - 2));
        if (is_pv && reduction > 0)
          reduction--; // reduce less in PV nodes
      }

      int score;
      if (!pv_search_done) {
        // First legal move: full window
        score = -_negamax(engine, depth - 1 - reduction, -beta, -alpha, ply + 1);
        if (reduction > 0 && score > alpha) {
          score = -_negamax(engine, depth - 1, -beta, -alpha, ply + 1);
        }
        pv_search_done = true;
      } else {
        // PVS: zero-window
        score =
            -_negamax(engine, depth - 1 - reduction, -alpha - 1, -alpha, ply + 1);
        if (score > alpha && score < beta) {
          // Re-search with full window
          score = -_negamax(engine, depth - 1, -beta, -alpha, ply + 1);
        }
      }
      engine.restore_state(st, tc);
      move_count++;

      if (score > best_score)
        best_score = score;
      if (score > alpha) {
        alpha = score;
        best_move = move;
        if (is_quiet) {
          auto &km = killer_moves[max(0, min(ply, (int)killer_moves.size() - 1))];
          if (km.first != move) {
            km.second = km.first;
            km.first = move;
          }
        }
      }

      if (alpha >= beta) {
        if (is_quiet) {
          history[_history_key(move)] += depth * depth;
        }
        break;
      }
    }

    if (!has_legal) {
      return in_check ? -(20000 - ply) : 0;
    }

    int flag = (best_score <= original_alpha)
                   ? TT_ALPHA
                   : ((best_score >= beta) ? TT_BETA : TT_EXACT);
    _tt_store(key, best_score, depth, flag, best_move);

    return best_score;
  }

  // =============================================
  // QUIESCENCE with SEE pruning
  // =============================================
  int _quiescence(ChessEngine &engine, int alpha, int beta) {
    nodes_searched++;

    if ((nodes_searched & 2047) == 0) {
      if (get_time() - start_time > time_limit)
        return 0;
    }

    int stand_pat = _evaluate(engine);
    if (stand_pat >= beta)
      return beta;
    if (alpha < stand_pat)
      alpha = stand_pat;

    int color = engine.turn_col;
    U64 key = _get_hash(engine);
    const TTEntry *tt_ptr = _tt_probe(key);
    auto moves = _gen_ordered_moves(engine, color, 0, true, tt_ptr, nullptr);

    for (auto &move : moves) {
      int tr = get<2>(move);
      int tc = get<3>(move);

      // SEE pruning: skip losing captures
      if (_see(engine, get<0>(move), get<1>(move), tr, tc, color) < 0)
        continue;

      auto st = engine.save_state();
      int tc_save = engine.turn_col;

      engine.make_move_fast(get<0>(move), get<1>(move), tr, tc, get<4>(move));
      U64 king_bb = engine.pieces[color][K];
      if (!king_bb ||
          engine.is_attacked(bb_ctzll(king_bb), engine.enemy_col(color))) {
        engine.restore_state(st, tc_save);
        continue;
      }

      int score = -_quiescence(engine, -beta, -alpha);
      engine.restore_state(st, tc_save);

      if (score >= beta)
        return beta;
      if (score > alpha)
        alpha = score;
    }
    return alpha;
  }

  // =============================================
  // 4. SEE (Static Exchange Evaluation) — full swap-off with x-ray
  // =============================================

  // All pieces (both colors) attacking `sq` given occupancy `occ`.
  static U64 _attackers_to(const ChessEngine &engine, int sq, U64 occ) {
    U64 att = 0;
    att |= pawn_attacks[BLACK][sq] & engine.pieces[WHITE][P];
    att |= pawn_attacks[WHITE][sq] & engine.pieces[BLACK][P];
    att |= knight_attacks[sq] & (engine.pieces[WHITE][N] | engine.pieces[BLACK][N]);
    att |= king_attacks[sq] & (engine.pieces[WHITE][K] | engine.pieces[BLACK][K]);
    U64 bq = engine.pieces[WHITE][B] | engine.pieces[BLACK][B] |
             engine.pieces[WHITE][Q] | engine.pieces[BLACK][Q];
    att |= get_bishop_attacks(sq, occ) & bq;
    U64 rq = engine.pieces[WHITE][R] | engine.pieces[BLACK][R] |
             engine.pieces[WHITE][Q] | engine.pieces[BLACK][Q];
    att |= get_rook_attacks(sq, occ) & rq;
    return att & occ;
  }

  int _see(ChessEngine &engine, int sr, int sc, int tr, int tc, int side) {
    int from_sq = sr * 8 + sc;
    int to_sq = tr * 8 + tc;

    int attacker_piece = -1;
    for (int i = 0; i < 6; i++) {
      if (engine.pieces[side][i] & (1ULL << from_sq)) {
        attacker_piece = i;
        break;
      }
    }
    if (attacker_piece < 0)
      return 0;

    int enemy = engine.enemy_col(side);
    int victim_piece = -1;
    for (int i = 0; i < 6; i++) {
      if (engine.pieces[enemy][i] & (1ULL << to_sq)) {
        victim_piece = i;
        break;
      }
    }
    bool ep = false;
    if (victim_piece < 0 && attacker_piece == P && abs(tc - sc) == 1 &&
        to_sq == engine.ep_square) {
      victim_piece = P;
      ep = true;
    }
    if (victim_piece < 0)
      return 0; // not a capture

    int gain[32];
    int d = 0;
    U64 occ = engine.occupied;
    occ ^= (1ULL << from_sq);
    if (ep) {
      int cap_sq = (side == WHITE) ? to_sq + 8 : to_sq - 8;
      occ ^= (1ULL << cap_sq);
    }

    gain[0] = PIECE_VALUE[victim_piece];
    int on_square_val = PIECE_VALUE[attacker_piece]; // piece now sitting on `to`
    int stm = enemy;

    U64 attackers = _attackers_to(engine, to_sq, occ);

    while (true) {
      // Least valuable attacker of the current side.
      U64 side_att = attackers & engine.colors[stm] & occ;
      if (!side_att)
        break;
      int lva = -1, lva_sq = -1;
      for (int pt = 0; pt < 6; pt++) {
        U64 s = engine.pieces[stm][pt] & side_att;
        if (s) {
          lva = pt;
          lva_sq = bb_ctzll(s);
          break;
        }
      }
      if (lva < 0)
        break;

      d++;
      gain[d] = on_square_val - gain[d - 1];
      if (d >= 31)
        break;

      on_square_val = PIECE_VALUE[lva];
      occ ^= (1ULL << lva_sq);
      // Recompute attackers to pick up x-ray sliders revealed behind lva.
      attackers = _attackers_to(engine, to_sq, occ);
      stm = engine.enemy_col(stm);
    }

    // Minimax the gain array back to the root.
    while (d > 0) {
      gain[d - 1] = -max(-gain[d - 1], gain[d]);
      d--;
    }
    return gain[0];
  }

  int get_piece_value(int c, int sq) { return 0; }

  // =============================================
  // 2+3. EVALUATION: Material + PST + Pawn Structure + King Safety
  // =============================================
  int _evaluate(ChessEngine &engine) {
    int sw = 0, sb = 0;
    int mat_w = 0, mat_b = 0;
    for (int i = 0; i < 5; i++) {
      mat_w += count_bits(engine.pieces[WHITE][i]) * PIECE_VALUE[i];
      mat_b += count_bits(engine.pieces[BLACK][i]) * PIECE_VALUE[i];
    }
    // Game phase (24 = full material, 0 = bare kings) for tapered eval.
    int phase = count_bits(engine.pieces[WHITE][N] | engine.pieces[BLACK][N]) +
                count_bits(engine.pieces[WHITE][B] | engine.pieces[BLACK][B]) +
                2 * count_bits(engine.pieces[WHITE][R] | engine.pieces[BLACK][R]) +
                4 * count_bits(engine.pieces[WHITE][Q] | engine.pieces[BLACK][Q]);
    if (phase > 24)
      phase = 24;
    bool endgame = phase <= 6;

    sw += mat_w;
    sb += mat_b;

    // --- Piece-Square Tables ---
    auto eval_pst = [&](int color, int p_type, const int table[64]) {
      int score = 0;
      U64 bb = engine.pieces[color][p_type];
      while (bb) {
        int sq = bb_ctzll(bb);
        score += table[color == WHITE ? sq : (sq ^ 56)];
        bb &= bb - 1;
      }
      return score;
    };

    sw += eval_pst(WHITE, P, PST_P);
    sw += eval_pst(WHITE, N, PST_N);
    sw += eval_pst(WHITE, B, PST_B);
    sw += eval_pst(WHITE, R, PST_R);
    sw += eval_pst(WHITE, Q, PST_Q);

    sb += eval_pst(BLACK, P, PST_P);
    sb += eval_pst(BLACK, N, PST_N);
    sb += eval_pst(BLACK, B, PST_B);
    sb += eval_pst(BLACK, R, PST_R);
    sb += eval_pst(BLACK, Q, PST_Q);

    // --- Tapered king PST: interpolate midgame/endgame tables by phase ---
    auto king_pst_tapered = [&](int color) {
      U64 kb = engine.pieces[color][K];
      if (!kb)
        return 0;
      int sq = bb_ctzll(kb);
      int idx = (color == WHITE) ? sq : (sq ^ 56);
      return (PST_K_mid[idx] * phase + PST_K_end[idx] * (24 - phase)) / 24;
    };
    sw += king_pst_tapered(WHITE);
    sb += king_pst_tapered(BLACK);

    // --- Bishop pair bonus ---
    if (count_bits(engine.pieces[WHITE][B]) >= 2)
      sw += 30;
    if (count_bits(engine.pieces[BLACK][B]) >= 2)
      sb += 30;

    // --- Mobility + rook file bonuses ---
    auto eval_mobility = [&](int color) {
      int score = 0;
      U64 own = engine.colors[color];
      U64 n = engine.pieces[color][N];
      while (n) {
        int s = bb_ctzll(n);
        score += count_bits(knight_attacks[s] & ~own) * 4;
        n &= n - 1;
      }
      U64 b = engine.pieces[color][B];
      while (b) {
        int s = bb_ctzll(b);
        score += count_bits(get_bishop_attacks(s, engine.occupied) & ~own) * 4;
        b &= b - 1;
      }
      U64 all_pawns = engine.pieces[WHITE][P] | engine.pieces[BLACK][P];
      U64 r = engine.pieces[color][R];
      while (r) {
        int s = bb_ctzll(r);
        score += count_bits(get_rook_attacks(s, engine.occupied) & ~own) * 2;
        int file = s % 8;
        if (!(all_pawns & FILE_MASKS[file]))
          score += 15; // open file
        else if (!(engine.pieces[color][P] & FILE_MASKS[file]))
          score += 8; // semi-open file
        r &= r - 1;
      }
      U64 q = engine.pieces[color][Q];
      while (q) {
        int s = bb_ctzll(q);
        score += count_bits(get_queen_attacks(s, engine.occupied) & ~own) * 1;
        q &= q - 1;
      }
      return score;
    };
    sw += eval_mobility(WHITE);
    sb += eval_mobility(BLACK);

    // =============================================
    // 2. PAWN STRUCTURE EVALUATION
    // =============================================
    auto eval_pawns = [&](int color) {
      int score = 0;
      U64 my_pawns = engine.pieces[color][P];
      U64 opp_pawns = engine.pieces[color == WHITE ? BLACK : WHITE][P];

      for (int file = 0; file < 8; file++) {
        U64 file_pawns = my_pawns & FILE_MASKS[file];
        int pawn_count = count_bits(file_pawns);

        // Doubled pawns penalty
        if (pawn_count > 1) {
          score -= 15 * (pawn_count - 1);
        }

        // Isolated pawns penalty (no friendly pawns on adjacent files)
        if (file_pawns && !(my_pawns & ADJ_FILE_MASKS[file])) {
          score -= 20 * pawn_count;
        }
      }

      // Passed pawns bonus
      U64 pawns_copy = my_pawns;
      while (pawns_copy) {
        int sq = bb_ctzll(pawns_copy);
        int rank = sq / 8;
        int file = sq % 8;

        // Generate forward mask: all squares ahead on same + adjacent files
        U64 forward_mask = 0;
        if (color == WHITE) {
          for (int r = rank - 1; r >= 0; r--) {
            forward_mask |= (1ULL << (r * 8 + file));
            if (file > 0)
              forward_mask |= (1ULL << (r * 8 + file - 1));
            if (file < 7)
              forward_mask |= (1ULL << (r * 8 + file + 1));
          }
          if (!(opp_pawns & forward_mask)) {
            score +=
                PASSED_PAWN_BONUS[7 -
                                  rank]; // closer to promotion = bigger bonus
          }
        } else {
          for (int r = rank + 1; r < 8; r++) {
            forward_mask |= (1ULL << (r * 8 + file));
            if (file > 0)
              forward_mask |= (1ULL << (r * 8 + file - 1));
            if (file < 7)
              forward_mask |= (1ULL << (r * 8 + file + 1));
          }
          if (!(opp_pawns & forward_mask)) {
            score +=
                PASSED_PAWN_BONUS[rank]; // closer to promotion = bigger bonus
          }
        }

        pawns_copy &= pawns_copy - 1;
      }

      return score;
    };

    sw += eval_pawns(WHITE);
    sb += eval_pawns(BLACK);

    // =============================================
    // 3. KING SAFETY EVALUATION (middlegame only)
    // =============================================
    if (!endgame) {
      auto eval_king_safety = [&](int color) {
        int score = 0;
        U64 king_bb = engine.pieces[color][K];
        if (!king_bb)
          return score;
        int king_sq = bb_ctzll(king_bb);
        int king_file = king_sq % 8;

        U64 my_pawns = engine.pieces[color][P];
        int enemy = engine.enemy_col(color);

        // Pawn shield: count friendly pawns in front of king (1-2 ranks ahead)
        U64 shield_mask = 0;
        if (color == WHITE) {
          int shield_rank = king_sq / 8 - 1;
          if (shield_rank >= 0) {
            for (int f = max(0, king_file - 1); f <= min(7, king_file + 1);
                 f++) {
              shield_mask |= (1ULL << (shield_rank * 8 + f));
              if (shield_rank - 1 >= 0)
                shield_mask |= (1ULL << ((shield_rank - 1) * 8 + f));
            }
          }
        } else {
          int shield_rank = king_sq / 8 + 1;
          if (shield_rank < 8) {
            for (int f = max(0, king_file - 1); f <= min(7, king_file + 1);
                 f++) {
              shield_mask |= (1ULL << (shield_rank * 8 + f));
              if (shield_rank + 1 < 8)
                shield_mask |= (1ULL << ((shield_rank + 1) * 8 + f));
            }
          }
        }
        score += count_bits(my_pawns & shield_mask) * 10;

        // Open files near king penalty
        for (int f = max(0, king_file - 1); f <= min(7, king_file + 1); f++) {
          if (!(my_pawns & FILE_MASKS[f])) {
            score -= 25;
          }
        }

        // Enemy attackers in king zone
        U64 king_zone = king_attacks[king_sq] | (1ULL << king_sq);
        int attacker_count = 0;
        // Count enemy knights attacking king zone
        U64 eN = engine.pieces[enemy][N];
        while (eN) {
          int sq = bb_ctzll(eN);
          if (knight_attacks[sq] & king_zone)
            attacker_count++;
          eN &= eN - 1;
        }
        // Count enemy bishops/queens attacking king zone
        U64 eBQ = engine.pieces[enemy][B] | engine.pieces[enemy][Q];
        while (eBQ) {
          int sq = bb_ctzll(eBQ);
          if (get_bishop_attacks(sq, engine.occupied) & king_zone)
            attacker_count++;
          eBQ &= eBQ - 1;
        }
        // Count enemy rooks/queens attacking king zone
        U64 eRQ = engine.pieces[enemy][R] | engine.pieces[enemy][Q];
        while (eRQ) {
          int sq = bb_ctzll(eRQ);
          if (get_rook_attacks(sq, engine.occupied) & king_zone)
            attacker_count++;
          eRQ &= eRQ - 1;
        }

        // Scaling penalty
        if (attacker_count >= 2) {
          score -= 15 * attacker_count * attacker_count / 2;
        }

        return score;
      };

      sw += eval_king_safety(WHITE);
      sb += eval_king_safety(BLACK);
    }

    int raw = sw - sb;
    raw += (engine.turn_col == WHITE) ? 10 : -10; // tempo bonus to side to move
    return engine.turn_col == WHITE ? raw : -raw;
  }

  // =============================================
  // MOVE ORDERING
  // =============================================
  vector<MoveFull> _gen_ordered_moves(ChessEngine &engine, int color, int ply,
                                      bool captures_only = false,
                                      const TTEntry *tt_move_entry = nullptr,
                                      const MoveFull *preferred_move = nullptr) {
    vector<tuple<MoveFull, int>> list_caps, list_kills, list_quiets;
    ply = max(0, min(ply, (int)killer_moves.size() - 1));
    auto &km = killer_moves[ply];

    auto moves = engine.get_pseudo_moves(color);
    int enemy = engine.enemy_col(color);

    for (auto &m : moves) {
      int sr = get<0>(m), sc = get<1>(m), tr = get<2>(m), tc = get<3>(m);
      U64 tsq_bb = 1ULL << (tr * 8 + tc);

      bool is_cap = false;
      int victim_val = 0;
      for (int i = 0; i < 6; i++) {
        if (engine.pieces[enemy][i] & tsq_bb) {
          is_cap = true;
          victim_val = MVV_LVA[i];
          break;
        }
      }

      int moved_kind = P;
      for (int i = 0; i < 6; i++) {
        if (engine.pieces[color][i] & (1ULL << (sr * 8 + sc))) {
          moved_kind = i;
          break;
        }
      }
      bool is_ep = moved_kind == P && abs(tc - sc) == 1 &&
                   !(engine.occupied & tsq_bb) && (tr * 8 + tc) == engine.ep_square;
      if (is_ep) {
        is_cap = true;
        victim_val = MVV_LVA[P];
      }

      if (captures_only && !is_cap) {
        continue;
      }

      if (preferred_move && m == *preferred_move) {
        list_caps.push_back({m, 40000});
        continue;
      }
      if (tt_move_entry && _is_same_move(m, *tt_move_entry)) {
        list_caps.push_back({m, 30000});
        continue;
      }

      if (is_cap) {
        // Use SEE for better capture ordering
        int see_val = _see(engine, sr, sc, tr, tc, color);
        int score = see_val + victim_val * 100 + 10000;
        if (!get<4>(m).empty())
          score += PIECE_VALUE[Q];
        list_caps.push_back({m, score});
      } else {
        if (!get<4>(m).empty()) {
          list_quiets.push_back({m, PIECE_VALUE[Q]});
          continue;
        }
        if (m == km.first || m == km.second) {
          list_kills.push_back({m, 9000});
        } else {
          list_quiets.push_back({m, history[_history_key(m)]});
        }
      }
    }

    auto sf = [](const tuple<MoveFull, int> &a, const tuple<MoveFull, int> &b) {
      return get<1>(a) > get<1>(b);
    };
    sort(list_caps.begin(), list_caps.end(), sf);
    if (captures_only) {
      vector<MoveFull> res;
      for (auto &x : list_caps)
        res.push_back(get<0>(x));
      return res;
    }
    sort(list_kills.begin(), list_kills.end(), sf);
    sort(list_quiets.begin(), list_quiets.end(), sf);

    vector<MoveFull> res;
    for (auto &x : list_caps)
      res.push_back(get<0>(x));
    for (auto &x : list_kills)
      res.push_back(get<0>(x));
    for (auto &x : list_quiets)
      res.push_back(get<0>(x));
    return res;
  }
};

#endif
