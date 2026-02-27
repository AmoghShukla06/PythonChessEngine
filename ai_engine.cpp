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

// PST Tables
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
                       -5, 0, 0, 0, 0, 0, 0, -5, 0,  0,  0,  5,  5,  0,  0,  0};
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

static unordered_map<int, int> PIECE_VALUE = {{P, 100}, {N, 320}, {B, 330},
                                              {R, 500}, {Q, 900}, {K, 20000}};

static unordered_map<int, int> MVV_LVA = {{P, 1}, {N, 2}, {B, 3},
                                          {R, 4}, {Q, 5}, {K, 6}};

static const int TT_EXACT = 0;
static const int TT_ALPHA = 1;
static const int TT_BETA = 2;

struct TTEntry {
  int score;
  int depth;
  int flag;
};

class AlphaBetaEngine {
public:
  int max_depth;
  double time_limit;
  vector<tuple<int, int, int, int>> move_history;

  unordered_map<U64, TTEntry> transposition_table;
  vector<pair<MoveFull, MoveFull>> killer_moves;
  unordered_map<U64, int> history;
  int nodes_searched;
  double start_time;
  vector<vector<int>> LMR_table;

  AlphaBetaEngine(int depth = 5, double time_limit = 5.0) {
    max_depth = depth;
    this->time_limit = time_limit;

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
    transposition_table.clear();
    killer_moves.assign(max_depth + 16, {MoveFull{-1, -1, -1, -1, ""},
                                         MoveFull{-1, -1, -1, -1, ""}});
    history.clear();
    nodes_searched = 0;
    start_time = 0.0;
  }

  double get_time() {
    return chrono::duration_cast<chrono::duration<double>>(
               chrono::steady_clock::now().time_since_epoch())
        .count();
  }

  U64 _get_hash(const ChessEngine &engine) {
    U64 h = 0;
    h ^= engine.colors[WHITE] * 0x9E3779B97F4A7C15ULL;
    h ^= engine.colors[BLACK] * 0xC6A4A7935BD1E995ULL;
    for (int i = 0; i < 6; i++) {
      h ^= engine.pieces[WHITE][i] * (i + 1) * 0x123456789ULL;
      h ^= engine.pieces[BLACK][i] * (i + 7) * 0x987654321ULL;
    }
    h ^= ((U64)engine.turn_col) << 60;
    h ^= ((U64)engine.ep_square & 0x3F) << 50;
    h ^= ((U64)engine.castling & 0xF) << 40;
    return h;
  }

  py::object get_best_move(ChessEngine &engine) {
    _reset_search_state();
    start_time = get_time();

    MoveFull best_move = {-1, -1, -1, -1, ""};
    bool has_best = false;
    int prev_score = 0;
    int asp_window = 50;

    for (int depth = 1; depth <= max_depth; depth++) {
      if (get_time() - start_time > time_limit)
        break;

      int alpha = (depth >= 4) ? prev_score - asp_window : -999999;
      int beta = (depth >= 4) ? prev_score + asp_window : 999999;

      auto res = _root_search(engine, depth, alpha, beta);
      MoveFull move = res.first;
      int score = res.second;

      if (score <= alpha || score >= beta) {
        res = _root_search(engine, depth, -999999, 999999);
        move = res.first;
        score = res.second;
      }

      prev_score = score;
      if (get<0>(move) != -1) {
        best_move = move;
        has_best = true;
      }

      cout << "  [AI-BB] depth=" << depth << "  score=" << score
           << "  nodes=" << nodes_searched
           << "  time=" << (get_time() - start_time) << "s\n";

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
        bool in_chk = engine.is_attacked(bb_ctzll(engine.pieces[tc][K]),
                                         engine.enemy_col(tc));
        engine.restore_state(st, tc);
        if (!in_chk) {
          return py::make_tuple(get<0>(m), get<1>(m), get<2>(m), get<3>(m));
        }
      }
    }
    return py::none();
  }

  pair<MoveFull, int> _root_search(ChessEngine &engine, int depth, int alpha,
                                   int beta) {
    int color = engine.turn_col;
    auto moves = _gen_ordered_moves(engine, color, 0);
    int best_score = -999999;
    MoveFull best_move = {-1, -1, -1, -1, ""};
    int local_alpha = alpha;

    for (auto &move : moves) {
      if (get_time() - start_time > time_limit)
        break;

      auto st = engine.save_state();
      int tc = engine.turn_col;

      engine.make_move_fast(get<0>(move), get<1>(move), get<2>(move),
                            get<3>(move), get<4>(move));

      // Validate move
      if (engine.is_attacked(bb_ctzll(engine.pieces[color][K]),
                             engine.enemy_col(color))) {
        engine.restore_state(st, tc);
        continue;
      }

      int score = -_negamax(engine, depth - 1, -beta, -local_alpha);
      engine.restore_state(st, tc);

      if (score > best_score) {
        best_score = score;
        best_move = move;
      }
      local_alpha = max(local_alpha, score);
      if (local_alpha >= beta)
        break;
    }
    return {best_move, best_score};
  }

  int _negamax(ChessEngine &engine, int depth, int alpha, int beta) {
    nodes_searched++;

    if ((nodes_searched & 2047) == 0) {
      if (get_time() - start_time > time_limit)
        return 0;
    }

    auto key = _get_hash(engine);
    if (transposition_table.find(key) != transposition_table.end()) {
      auto &tt = transposition_table[key];
      if (tt.depth >= depth) {
        if (tt.flag == TT_EXACT)
          return tt.score;
        if (tt.flag == TT_ALPHA && tt.score <= alpha)
          return alpha;
        if (tt.flag == TT_BETA && tt.score >= beta)
          return beta;
      }
    }

    int color = engine.turn_col;
    bool in_check = engine.in_check_col(color);

    if (depth == 0)
      return _quiescence(engine, alpha, beta);

    if (!in_check && depth >= 3) {
      int total_mat = 0;
      for (int i = 0; i < 5; i++) {
        total_mat += count_bits(engine.pieces[WHITE][i]) * PIECE_VALUE[i];
        total_mat += count_bits(engine.pieces[BLACK][i]) * PIECE_VALUE[i];
      }
      if (total_mat > 1500) {
        int R = 2;
        engine.turn_col = engine.enemy_col(color);
        int null_score = -_negamax(engine, depth - 1 - R, -beta, -beta + 1);
        engine.turn_col = color;
        if (null_score >= beta)
          return beta;
      }
    }

    int ply = max(0, max_depth - depth);
    auto moves = _gen_ordered_moves(engine, color, ply);

    int original_alpha = alpha;
    int best_score = -999999;
    int move_count = 0;
    bool has_legal = false;

    for (auto &move : moves) {
      auto st = engine.save_state();
      int tc = engine.turn_col;

      int tr = get<2>(move);
      int tc_sq = get<3>(move);
      string promo = get<4>(move);
      bool is_capture = (engine.occupied & (1ULL << (tr * 8 + tc_sq))) != 0;

      engine.make_move_fast(get<0>(move), get<1>(move), tr, tc_sq, promo);
      if (engine.is_attacked(bb_ctzll(engine.pieces[color][K]),
                             engine.enemy_col(color))) {
        engine.restore_state(st, tc);
        continue;
      }
      has_legal = true;

      int reduction = 0;
      if (!in_check && !is_capture && depth >= 3 && move_count >= 3 &&
          promo.empty()) {
        int d_idx = min(depth, 8);
        int m_idx = min(move_count, 32);
        reduction = max(0, min(LMR_table[d_idx][m_idx], depth - 2));
      }

      int score = -_negamax(engine, depth - 1 - reduction, -beta, -alpha);
      if (reduction > 0 && score > alpha) {
        score = -_negamax(engine, depth - 1, -beta, -alpha);
      }
      engine.restore_state(st, tc);
      move_count++;

      if (score > best_score)
        best_score = score;
      if (score > alpha) {
        alpha = score;
        if (!is_capture && promo.empty()) {
          auto &km = killer_moves[ply];
          if (km.first != move) {
            km.second = km.first;
            km.first = move;
          }
        }
      }

      if (alpha >= beta) {
        if (!is_capture && promo.empty()) {
          history[(U64)get<0>(move) ^ ((U64)get<1>(move) << 8) ^
                  ((U64)tr << 16) ^ ((U64)tc_sq << 24)] += depth * depth;
        }
        break;
      }
    }

    if (!has_legal) {
      return in_check ? -(20000 - depth) : 0;
    }

    if (transposition_table.size() > 500000)
      transposition_table.clear();
    int flag = (best_score <= original_alpha)
                   ? TT_ALPHA
                   : ((best_score >= beta) ? TT_BETA : TT_EXACT);
    transposition_table[key] = {best_score, depth, flag};

    return best_score;
  }

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
    auto moves = _gen_ordered_moves(engine, color, 0);

    for (auto &move : moves) {
      int tr = get<2>(move);
      int tc = get<3>(move);
      if (!(engine.colors[engine.enemy_col(color)] & (1ULL << (tr * 8 + tc))))
        continue; // Only captures

      auto st = engine.save_state();
      int tc_save = engine.turn_col;

      engine.make_move_fast(get<0>(move), get<1>(move), tr, tc, get<4>(move));
      if (engine.is_attacked(bb_ctzll(engine.pieces[color][K]),
                             engine.enemy_col(color))) {
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

  int get_piece_value(int c, int sq) { return 0; }

  int _evaluate(ChessEngine &engine) {
    int sw = 0, sb = 0;
    int mat_w = 0, mat_b = 0;
    for (int i = 0; i < 5; i++) {
      mat_w += count_bits(engine.pieces[WHITE][i]) * PIECE_VALUE[i];
      mat_b += count_bits(engine.pieces[BLACK][i]) * PIECE_VALUE[i];
    }
    bool endgame = (mat_w + mat_b) < 1500;

    sw += mat_w;
    sb += mat_b;

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
    sw += eval_pst(WHITE, K, endgame ? PST_K_end : PST_K_mid);

    sb += eval_pst(BLACK, P, PST_P);
    sb += eval_pst(BLACK, N, PST_N);
    sb += eval_pst(BLACK, B, PST_B);
    sb += eval_pst(BLACK, R, PST_R);
    sb += eval_pst(BLACK, Q, PST_Q);
    sb += eval_pst(BLACK, K, endgame ? PST_K_end : PST_K_mid);

    int raw = sw - sb;
    return engine.turn_col == WHITE ? raw : -raw;
  }

  vector<MoveFull> _gen_ordered_moves(ChessEngine &engine, int color, int ply) {
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

      if (is_cap) {
        int score = victim_val * 10 - MVV_LVA[moved_kind];
        if (!get<4>(m).empty())
          score += PIECE_VALUE[Q]; // proxy for promo
        list_caps.push_back({m, score});
      } else {
        if (!get<4>(m).empty()) {
          list_quiets.push_back({m, PIECE_VALUE[Q]});
          continue;
        }
        if (m == km.first || m == km.second) {
          list_kills.push_back({m, 9000});
        } else {
          U64 hist_key =
              (U64)sr ^ ((U64)sc << 8) ^ ((U64)tr << 16) ^ ((U64)tc << 24);
          list_quiets.push_back({m, history[hist_key]});
        }
      }
    }

    auto sf = [](const tuple<MoveFull, int> &a, const tuple<MoveFull, int> &b) {
      return get<1>(a) > get<1>(b);
    };
    sort(list_caps.begin(), list_caps.end(), sf);
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
