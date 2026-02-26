#ifndef AI_ENGINE_H
#define AI_ENGINE_H

#include "pst.h"
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

extern std::unordered_map<std::string, std::vector<std::vector<int>>> PST;

namespace py = pybind11;
using namespace std;

// We need ChessEngine defined before this
// Assume included from chess_engine.cpp

static unordered_map<char, int> PIECE_VALUE = {
    {'P', 100}, {'N', 320}, {'B', 330}, {'R', 500}, {'Q', 900}, {'K', 20000}};

static unordered_map<char, int> MVV_LVA = {{'P', 1}, {'N', 2}, {'B', 3},
                                           {'R', 4}, {'Q', 5}, {'K', 6}};

static const int TT_EXACT = 0;
static const int TT_ALPHA = 1;
static const int TT_BETA = 2;

struct TTEntry {
  int score;
  int depth;
  int flag;
};

// Custom hash for unordered_map
struct BoardHash {
  size_t
  operator()(const tuple<vector<vector<string>>, string, Square> &key) const {
    size_t res = 17;
    const auto &b = get<0>(key);
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        res = res * 31 + hash<string>()(b[r][c]);
      }
    }
    res = res * 31 + hash<string>()(get<1>(key));
    res = res * 31 + get<2>(key).first * 8 + get<2>(key).second;
    return res;
  }
};

struct HistoryHash {
  size_t operator()(const tuple<string, int, int> &key) const {
    return hash<string>()(get<0>(key)) ^ (get<1>(key) << 8) ^ get<2>(key);
  }
};

class AlphaBetaEngine {
public:
  int max_depth;
  double time_limit;
  vector<tuple<int, int, int, int>> move_history;

  // search state
  unordered_map<tuple<vector<vector<string>>, string, Square>, TTEntry,
                BoardHash>
      transposition_table;
  vector<pair<MoveFull, MoveFull>> killer_moves;
  unordered_map<tuple<string, int, int>, int, HistoryHash> history;
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

  py::object get_best_move(ChessEngine &engine) {
    // Python wrapper will handle opening book, so here we ONLY do the search
    _reset_search_state();
    start_time = get_time();

    MoveFull best_move = {-1, -1, -1, -1, ""};
    bool has_best = false;
    int prev_score = 0;
    int asp_window = 50;

    for (int depth = 1; depth <= max_depth; depth++) {
      if (get_time() - start_time > time_limit)
        break;

      int alpha, beta;
      if (depth >= 4) {
        alpha = prev_score - asp_window;
        beta = prev_score + asp_window;
      } else {
        alpha = -999999;
        beta = 999999;
      }

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

      cout << "  [AI-C++] depth=" << depth << "  score=" << score
           << "  nodes=" << nodes_searched
           << "  time=" << (get_time() - start_time) << "s\n";

      if (abs(score) >= 15000)
        break;
    }

    if (has_best) {
      return py::make_tuple(get<0>(best_move), get<1>(best_move),
                            get<2>(best_move), get<3>(best_move));
    } else {
      // fallback
      for (int r = 0; r < 8; r++) {
        for (int c = 0; c < 8; c++) {
          if (engine.board[r][c].substr(0, 1) == engine.turn) {
            auto lm = engine.legal_moves(r, c);
            if (!lm.first.empty())
              return py::make_tuple(r, c, lm.first[0].first,
                                    lm.first[0].second);
            if (!lm.second.empty())
              return py::make_tuple(r, c, lm.second[0].first,
                                    lm.second[0].second);
          }
        }
      }
    }
    return py::none();
  }

  pair<MoveFull, int> _root_search(ChessEngine &engine, int depth, int alpha,
                                   int beta) {
    string color = engine.turn;
    auto moves = _gen_ordered_moves(engine, color, 0);
    int best_score = -999999;
    MoveFull best_move = {-1, -1, -1, -1, ""};
    int local_alpha = alpha;

    for (auto &move : moves) {
      if (get_time() - start_time > time_limit)
        break;

      int sr = get<0>(move), sc = get<1>(move), tr = get<2>(move),
          tc = get<3>(move);
      string promo = get<4>(move);

      UndoInfo undo = _make_move(engine, sr, sc, tr, tc, promo);
      int score = -_negamax(engine, depth - 1, -beta, -local_alpha);
      _undo_move(engine, undo);

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

    auto key = _board_hash(engine);
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

    if (engine.game_over) {
      return engine.winner == "draw" ? 0 : -(20000 - depth);
    }

    if (depth == 0)
      return _quiescence(engine, alpha, beta);

    string color = engine.turn;
    bool in_check = engine.in_check(color);

    if (!in_check && depth >= 3 && _material_count(engine) > 1500) {
      int R = 2;
      engine.turn = engine.enemy(color);
      int null_score = -_negamax(engine, depth - 1 - R, -beta, -beta + 1);
      engine.turn = color;
      if (null_score >= beta)
        return beta;
    }

    int ply = max(0, max_depth - depth);
    auto moves = _gen_ordered_moves(engine, color, ply);

    if (moves.empty()) {
      return in_check ? -(20000 - depth) : 0;
    }

    int original_alpha = alpha;
    int best_score = -999999;
    int move_count = 0;

    for (auto &move : moves) {
      int sr = get<0>(move), sc = get<1>(move), tr = get<2>(move),
          tc = get<3>(move);
      string promo = get<4>(move);

      bool is_capture =
          engine.board[tr][tc] != "--" ||
          (engine.board[sr][sc][1] == 'P' && engine.en_passant.first == tr &&
           engine.en_passant.second == tc);

      int reduction = 0;
      if (!in_check && !is_capture && depth >= 3 && move_count >= 3 &&
          promo.empty()) {
        int d_idx = min(depth, 8);
        int m_idx = min(move_count, 32);
        reduction = max(0, min(LMR_table[d_idx][m_idx], depth - 2));
      }

      UndoInfo undo = _make_move(engine, sr, sc, tr, tc, promo);
      int score = -_negamax(engine, depth - 1 - reduction, -beta, -alpha);
      if (reduction > 0 && score > alpha) {
        score = -_negamax(engine, depth - 1, -beta, -alpha);
      }
      _undo_move(engine, undo);
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
          history[{color, tr, tc}] += depth * depth;
        }
        break;
      }
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

    for (auto &move : _gen_capture_moves(engine, engine.turn)) {
      UndoInfo undo = _make_move(engine, get<0>(move), get<1>(move),
                                 get<2>(move), get<3>(move), get<4>(move));
      int score = -_quiescence(engine, -beta, -alpha);
      _undo_move(engine, undo);
      if (score >= beta)
        return beta;
      if (score > alpha)
        alpha = score;
    }
    return alpha;
  }

  int _evaluate(ChessEngine &engine) {
    int total_mat = _material_count(engine);
    bool endgame = total_mat < 1500;
    int sw = 0, sb = 0;

    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        string p = engine.board[r][c];
        if (p == "--")
          continue;
        string color = p.substr(0, 1);
        char kind = p[1];
        int val = PIECE_VALUE[kind];

        string pst_key = string(1, kind);
        if (kind == 'K')
          pst_key = endgame ? "K_end" : "K_mid";

        if (color == "w") {
          sw += val + PST[pst_key][r][c];
        } else {
          sb += val + PST[pst_key][7 - r][c];
        }
      }
    }

    sw += _mobility(engine, "w") * 5;
    sb += _mobility(engine, "b") * 5;

    sw += _pawn_structure(engine, "w");
    sb += _pawn_structure(engine, "b");

    int raw = sw - sb;
    return engine.turn == "w" ? raw : -raw;
  }

  int _mobility(ChessEngine &engine, const string &color) {
    int count = 0;
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        if (engine.board[r][c].substr(0, 1) == color) {
          auto m = engine.pseudo_moves(r, c);
          count += m.first.size() + m.second.size();
        }
      }
    }
    return count;
  }

  int _pawn_structure(ChessEngine &engine, const string &color) {
    string enemy = engine.enemy(color);
    int PASSED_BONUS[] = {0, 80, 60, 40, 30, 20, 10, 0};
    int DOUBLED_PENALTY = -20;
    int ISOLATED_PENALTY = -15;

    vector<vector<int>> own_files(8), enemy_files(8);
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        string p = engine.board[r][c];
        if (p == "--" || p[1] != 'P')
          continue;
        if (p.substr(0, 1) == color)
          own_files[c].push_back(r);
        else
          enemy_files[c].push_back(r);
      }
    }

    int score = 0;
    for (int c = 0; c < 8; c++) {
      if (own_files[c].empty())
        continue;

      if (own_files[c].size() > 1) {
        score += DOUBLED_PENALTY * (own_files[c].size() - 1);
      }

      bool has_neighbor = (c > 0 && !own_files[c - 1].empty()) ||
                          (c < 7 && !own_files[c + 1].empty());
      if (!has_neighbor) {
        score += ISOLATED_PENALTY * own_files[c].size();
      }

      for (int r : own_files[c]) {
        bool is_passed = true;
        int ranks_from_start;
        if (color == "w") {
          for (int f = max(0, c - 1); f <= min(7, c + 1); f++) {
            for (int er : enemy_files[f]) {
              if (er < r) {
                is_passed = false;
                break;
              }
            }
          }
          ranks_from_start = r;
        } else {
          for (int f = max(0, c - 1); f <= min(7, c + 1); f++) {
            for (int er : enemy_files[f]) {
              if (er > r) {
                is_passed = false;
                break;
              }
            }
          }
          ranks_from_start = 7 - r;
        }
        if (is_passed) {
          score += PASSED_BONUS[min(ranks_from_start, 7)];
        }
      }
    }
    return score;
  }

  int _material_count(ChessEngine &engine) {
    int count = 0;
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        string p = engine.board[r][c];
        if (p != "--" && p[1] != 'K')
          count += PIECE_VALUE[p[1]];
      }
    }
    return count;
  }

  vector<MoveFull> _gen_ordered_moves(ChessEngine &engine, const string &color,
                                      int ply) {
    vector<tuple<MoveFull, int>> captures, killers, quiets;
    ply = max(0, min(ply, (int)killer_moves.size() - 1));
    auto &km = killer_moves[ply];

    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        if (engine.board[r][c].substr(0, 1) != color)
          continue;
        char kind = engine.board[r][c][1];
        auto lm = engine.legal_moves(r, c);

        for (auto &mc : lm.second) {
          int tr = mc.first, tc = mc.second;
          string victim = engine.board[tr][tc];
          int vval = (victim != "--") ? MVV_LVA[victim[1]] : MVV_LVA['P'];
          int score = vval * 10 - MVV_LVA[kind];
          if (kind == 'P' && (tr == 0 || tr == 7)) {
            for (string promo : {"Q", "R", "B", "N"}) {
              captures.push_back(
                  {{r, c, tr, tc, promo}, score + PIECE_VALUE[promo[0]]});
            }
          } else {
            captures.push_back({{r, c, tr, tc, ""}, score});
          }
        }

        for (auto &mv : lm.first) {
          int tr = mv.first, tc = mv.second;
          if (kind == 'P' && (tr == 0 || tr == 7)) {
            for (string promo : {"Q", "R", "B", "N"}) {
              quiets.push_back({{r, c, tr, tc, promo}, PIECE_VALUE[promo[0]]});
            }
            continue;
          }
          MoveFull move = {r, c, tr, tc, ""};
          bool is_killer = (move == km.first || move == km.second);
          int hist_val = history[{color, tr, tc}];

          string pst_key = string(1, kind);
          if (kind == 'K')
            pst_key = "K_mid";
          int pst_d = 0;
          if (color == "w") {
            pst_d = PST[pst_key][tr][tc] - PST[pst_key][r][c];
          } else {
            pst_d = PST[pst_key][7 - tr][tc] - PST[pst_key][7 - r][c];
          }

          if (is_killer) {
            killers.push_back({move, 9000 + pst_d});
          } else {
            quiets.push_back({move, hist_val + pst_d});
          }
        }
      }
    }

    auto sort_func = [](const tuple<MoveFull, int> &a,
                        const tuple<MoveFull, int> &b) {
      return get<1>(a) > get<1>(b);
    };
    sort(captures.begin(), captures.end(), sort_func);
    sort(killers.begin(), killers.end(), sort_func);
    sort(quiets.begin(), quiets.end(), sort_func);

    vector<MoveFull> res;
    for (auto &x : captures)
      res.push_back(get<0>(x));
    for (auto &x : killers)
      res.push_back(get<0>(x));
    for (auto &x : quiets)
      res.push_back(get<0>(x));
    return res;
  }

  vector<MoveFull> _gen_capture_moves(ChessEngine &engine,
                                      const string &color) {
    vector<MoveFull> out;
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        if (engine.board[r][c].substr(0, 1) != color)
          continue;
        char kind = engine.board[r][c][1];
        auto lm = engine.legal_moves(r, c);
        for (auto &mc : lm.second) {
          int tr = mc.first, tc = mc.second;
          string promo = (kind == 'P' && (tr == 0 || tr == 7)) ? "Q" : "";
          out.push_back({r, c, tr, tc, promo});
        }
      }
    }
    return out;
  }

  UndoInfo _make_move(ChessEngine &engine, int sr, int sc, int tr, int tc,
                      const string &promo) {
    UndoInfo undo = {engine.board,         engine.turn,       engine.en_passant,
                     engine.castle_rights, engine.king_moved, engine.game_over,
                     engine.winner};
    engine.make_move_fast(sr, sc, tr, tc, promo);
    return undo;
  }

  void _undo_move(ChessEngine &engine, const UndoInfo &undo) {
    engine.board = undo.board;
    engine.turn = undo.turn;
    engine.en_passant = undo.en_passant;
    engine.castle_rights = undo.castle_rights;
    engine.king_moved = undo.king_moved;
    engine.game_over = undo.game_over;
    engine.winner = undo.winner;
  }

  tuple<vector<vector<string>>, string, Square>
  _board_hash(ChessEngine &engine) {
    return {engine.board, engine.turn, engine.en_passant};
  }
};

#endif
