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

#include "bitboard.h"

namespace py = pybind11;
using namespace std;

typedef pair<int, int> Square;
typedef tuple<int, int, int, int, string> MoveFull;

struct UndoInfo {
  U64 pieces[2][6];
  U64 colors[2];
  U64 occupied;
  int turn_col;
  int ep_square;
  int castling;
  bool game_over;
  string winner;
};

class ChessEngine {
public:
  U64 pieces[2][6];
  U64 colors[2];
  U64 occupied;

  int turn_col; // WHITE(0), BLACK(1)
  int ep_square;
  int castling; // bit 0=WK, 1=WQ, 2=BK, 3=BQ

  bool game_over = false;
  string winner = "";

  ChessEngine() {
    init_all_bitboards();
    reset_board();
  }

  void reset_board() {
    for (int i = 0; i < 2; i++) {
      colors[i] = 0;
      for (int j = 0; j < 6; j++)
        pieces[i][j] = 0;
    }

    // Pawns
    pieces[WHITE][P] = 0x00FF000000000000ULL;
    pieces[BLACK][P] = 0x000000000000FF00ULL;
    // Knights
    pieces[WHITE][N] = 0x4200000000000000ULL;
    pieces[BLACK][N] = 0x0000000000000042ULL;
    // Bishops
    pieces[WHITE][B] = 0x2400000000000000ULL;
    pieces[BLACK][B] = 0x0000000000000024ULL;
    // Rooks
    pieces[WHITE][R] = 0x8100000000000000ULL;
    pieces[BLACK][R] = 0x0000000000000081ULL;
    // Queens
    pieces[WHITE][Q] = 0x0800000000000000ULL;
    pieces[BLACK][Q] = 0x0000000000000008ULL;
    // Kings
    pieces[WHITE][K] = 0x1000000000000000ULL;
    pieces[BLACK][K] = 0x0000000000000010ULL;

    colors[WHITE] = pieces[WHITE][P] | pieces[WHITE][N] | pieces[WHITE][B] |
                    pieces[WHITE][R] | pieces[WHITE][Q] | pieces[WHITE][K];
    colors[BLACK] = pieces[BLACK][P] | pieces[BLACK][N] | pieces[BLACK][B] |
                    pieces[BLACK][R] | pieces[BLACK][Q] | pieces[BLACK][K];
    occupied = colors[WHITE] | colors[BLACK];

    turn_col = WHITE;
    ep_square = -1;
    castling = 15; // all rights 1111 (binary 15)
    game_over = false;
    winner = "";
  }

  // --- PYTHON / LEGACY COMPATIBILITY METHODS ---

  vector<vector<string>> get_board() const {
    vector<vector<string>> b(8, vector<string>(8, "--"));
    for (int sq = 0; sq < 64; sq++) {
      U64 bit = 1ULL << sq;
      if (bit & occupied) {
        int r = sq / 8;
        int c = sq % 8;
        int col = (bit & colors[WHITE]) ? WHITE : BLACK;
        string cStr = (col == WHITE) ? "w" : "b";
        if (bit & pieces[col][P])
          b[r][c] = cStr + "P";
        else if (bit & pieces[col][N])
          b[r][c] = cStr + "N";
        else if (bit & pieces[col][B])
          b[r][c] = cStr + "B";
        else if (bit & pieces[col][R])
          b[r][c] = cStr + "R";
        else if (bit & pieces[col][Q])
          b[r][c] = cStr + "Q";
        else if (bit & pieces[col][K])
          b[r][c] = cStr + "K";
      }
    }
    return b;
  }

  string get_turn() const { return turn_col == WHITE ? "w" : "b"; }
  Square get_ep() const {
    return ep_square == -1 ? Square(-1, -1)
                           : Square(ep_square / 8, ep_square % 8);
  }

  unordered_map<string, unordered_map<string, bool>> get_castle_rights() const {
    unordered_map<string, unordered_map<string, bool>> res;
    res["w"]["kingside"] = (castling & 1) != 0;
    res["w"]["queenside"] = (castling & 2) != 0;
    res["b"]["kingside"] = (castling & 4) != 0;
    res["b"]["queenside"] = (castling & 8) != 0;
    return res;
  }

  // Legacy stubs just returning dummy or basic data to fulfill older interface
  // requirements
  bool in_bounds(int r, int c) const {
    return 0 <= r && r < 8 && 0 <= c && c < 8;
  }
  string enemy(const string &color) const { return color == "w" ? "b" : "w"; }
  int enemy_col(int color) const { return color ^ 1; }

  vector<MoveFull> get_pseudo_moves(int color) const {
    vector<MoveFull> moves;
    int enemy = enemy_col(color);

    U64 p = pieces[color][P];
    while (p) {
      int sq = get_ls1b(p);
      U64 sq_bb = 1ULL << sq;
      int push_dir = (color == WHITE) ? -8 : 8;
      int push_sq = sq + push_dir;
      if (!(occupied & (1ULL << push_sq))) {
        int r = sq / 8, c = sq % 8;
        int tr = push_sq / 8, tc = push_sq % 8;
        if (tr == 0 || tr == 7) {
          moves.push_back({r, c, tr, tc, "Q"});
          moves.push_back({r, c, tr, tc, "R"});
          moves.push_back({r, c, tr, tc, "B"});
          moves.push_back({r, c, tr, tc, "N"});
        } else {
          moves.push_back({r, c, tr, tc, ""});
          if ((color == WHITE && r == 6) || (color == BLACK && r == 1)) {
            int dp_sq = push_sq + push_dir;
            if (!(occupied & (1ULL << dp_sq))) {
              moves.push_back({r, c, dp_sq / 8, dp_sq % 8, ""});
            }
          }
        }
      }
      U64 caps = 0;
      if (color == WHITE) {
        caps |= (sq_bb >> 7) & ~FILE_A &
                (colors[BLACK] | (ep_square != -1 ? (1ULL << ep_square) : 0));
        caps |= (sq_bb >> 9) & ~FILE_H &
                (colors[BLACK] | (ep_square != -1 ? (1ULL << ep_square) : 0));
      } else {
        caps |= (sq_bb << 9) & ~FILE_A &
                (colors[WHITE] | (ep_square != -1 ? (1ULL << ep_square) : 0));
        caps |= (sq_bb << 7) & ~FILE_H &
                (colors[WHITE] | (ep_square != -1 ? (1ULL << ep_square) : 0));
      }
      while (caps) {
        int tsq = get_ls1b(caps);
        int r = sq / 8, c = sq % 8, tr = tsq / 8, tc = tsq % 8;
        if (tr == 0 || tr == 7) {
          moves.push_back({r, c, tr, tc, "Q"});
          moves.push_back({r, c, tr, tc, "R"});
          moves.push_back({r, c, tr, tc, "B"});
          moves.push_back({r, c, tr, tc, "N"});
        } else {
          moves.push_back({r, c, tr, tc, ""});
        }
        caps &= caps - 1;
      }
      p &= p - 1;
    }

    U64 n = pieces[color][N];
    while (n) {
      int sq = get_ls1b(n);
      U64 att = knight_attacks[sq] & ~colors[color];
      while (att) {
        int tsq = get_ls1b(att);
        moves.push_back({sq / 8, sq % 8, tsq / 8, tsq % 8, ""});
        att &= att - 1;
      }
      n &= n - 1;
    }

    U64 b = pieces[color][B];
    while (b) {
      int sq = get_ls1b(b);
      U64 att = get_bishop_attacks(sq, occupied) & ~colors[color];
      while (att) {
        int tsq = get_ls1b(att);
        moves.push_back({sq / 8, sq % 8, tsq / 8, tsq % 8, ""});
        att &= att - 1;
      }
      b &= b - 1;
    }

    U64 rk = pieces[color][R];
    while (rk) {
      int sq = get_ls1b(rk);
      U64 att = get_rook_attacks(sq, occupied) & ~colors[color];
      while (att) {
        int tsq = get_ls1b(att);
        moves.push_back({sq / 8, sq % 8, tsq / 8, tsq % 8, ""});
        att &= att - 1;
      }
      rk &= rk - 1;
    }

    U64 q = pieces[color][Q];
    while (q) {
      int sq = get_ls1b(q);
      U64 att = get_queen_attacks(sq, occupied) & ~colors[color];
      while (att) {
        int tsq = get_ls1b(att);
        moves.push_back({sq / 8, sq % 8, tsq / 8, tsq % 8, ""});
        att &= att - 1;
      }
      q &= q - 1;
    }

    U64 k = pieces[color][K];
    if (k) {
      int sq = get_ls1b(k);
      U64 att = king_attacks[sq] & ~colors[color];
      while (att) {
        int tsq = get_ls1b(att);
        moves.push_back({sq / 8, sq % 8, tsq / 8, tsq % 8, ""});
        att &= att - 1;
      }

      if (!is_attacked(sq, enemy)) {
        if (color == WHITE) {
          if ((castling & 1) && !(occupied & ((1ULL << 61) | (1ULL << 62))) &&
              !is_attacked(61, BLACK) && !is_attacked(62, BLACK)) {
            moves.push_back({7, 4, 7, 6, ""});
          }
          if ((castling & 2) &&
              !(occupied & ((1ULL << 57) | (1ULL << 58) | (1ULL << 59))) &&
              !is_attacked(59, BLACK) && !is_attacked(58, BLACK)) {
            moves.push_back({7, 4, 7, 2, ""});
          }
        } else {
          if ((castling & 4) && !(occupied & ((1ULL << 5) | (1ULL << 6))) &&
              !is_attacked(5, WHITE) && !is_attacked(6, WHITE)) {
            moves.push_back({0, 4, 0, 6, ""});
          }
          if ((castling & 8) &&
              !(occupied & ((1ULL << 1) | (1ULL << 2) | (1ULL << 3))) &&
              !is_attacked(3, WHITE) && !is_attacked(2, WHITE)) {
            moves.push_back({0, 4, 0, 2, ""});
          }
        }
      }
    }
    return moves;
  }

  U64 get_attacks(int color) const {
    U64 attacks = 0;
    U64 p = pieces[color][P];
    if (color == WHITE) {
      attacks |= (p >> 9) & ~FILE_H;
      attacks |= (p >> 7) & ~FILE_A;
    } else {
      attacks |= (p << 7) & ~FILE_H;
      attacks |= (p << 9) & ~FILE_A;
    }

    U64 n = pieces[color][N];
    while (n) {
      int sq = bb_ctzll(n);
      attacks |= knight_attacks[sq];
      n &= n - 1;
    }

    U64 k = pieces[color][K];
    if (k)
      attacks |= king_attacks[bb_ctzll(k)];

    U64 b = pieces[color][B] | pieces[color][Q];
    while (b) {
      int sq = bb_ctzll(b);
      attacks |= get_bishop_attacks(sq, occupied);
      b &= b - 1;
    }

    U64 r = pieces[color][R] | pieces[color][Q];
    while (r) {
      int sq = bb_ctzll(r);
      attacks |= get_rook_attacks(sq, occupied);
      r &= r - 1;
    }
    return attacks;
  }

  bool is_attacked(int sq, int by_color) const {
    U64 sq_bb = 1ULL << sq;
    if (by_color == WHITE) {
      if ((sq_bb << 9) & ~FILE_A & pieces[WHITE][P])
        return true;
      if ((sq_bb << 7) & ~FILE_H & pieces[WHITE][P])
        return true;
    } else {
      if ((sq_bb >> 7) & ~FILE_A & pieces[BLACK][P])
        return true;
      if ((sq_bb >> 9) & ~FILE_H & pieces[BLACK][P])
        return true;
    }
    if (knight_attacks[sq] & pieces[by_color][N])
      return true;
    if (king_attacks[sq] & pieces[by_color][K])
      return true;
    if (get_bishop_attacks(sq, occupied) &
        (pieces[by_color][B] | pieces[by_color][Q]))
      return true;
    if (get_rook_attacks(sq, occupied) &
        (pieces[by_color][R] | pieces[by_color][Q]))
      return true;
    return false;
  }

  bool in_check_col(int color) const {
    U64 k = pieces[color][K];
    if (!k)
      return false;
    return is_attacked(bb_ctzll(k), enemy_col(color));
  }

  // Engine State Backup for Search
  struct EngineState {
    U64 pieces[2][6];
    U64 colors[2];
    U64 occupied;
    int ep_square;
    int castling;
  };
  EngineState save_state() const {
    EngineState st;
    for (int i = 0; i < 2; i++) {
      st.colors[i] = colors[i];
      for (int j = 0; j < 6; j++)
        st.pieces[i][j] = pieces[i][j];
    }
    st.occupied = occupied;
    st.ep_square = ep_square;
    st.castling = castling;
    return st;
  }
  void restore_state(const EngineState &st, int turn_col_saved) {
    for (int i = 0; i < 2; i++) {
      colors[i] = st.colors[i];
      for (int j = 0; j < 6; j++)
        pieces[i][j] = st.pieces[i][j];
    }
    occupied = st.occupied;
    ep_square = st.ep_square;
    castling = st.castling;
    turn_col = turn_col_saved;
  }

  bool in_check(const string &color) {
    return in_check_col(color == "w" ? WHITE : BLACK);
  }

  py::tuple legal_moves_py(int r, int c) {
    if (r < 0 || r > 7 || c < 0 || c > 7)
      return py::make_tuple(py::list(), py::list());
    vector<Square> lm, lc;
    int sq = r * 8 + c;
    U64 sq_bb = 1ULL << sq;
    int p_color = -1;
    if (colors[WHITE] & sq_bb)
      p_color = WHITE;
    else if (colors[BLACK] & sq_bb)
      p_color = BLACK;
    if (p_color == -1)
      return py::make_tuple(lm, lc);

    auto pms = get_pseudo_moves(p_color);
    for (auto &m : pms) {
      if (get<0>(m) == r && get<1>(m) == c) {
        int tr = get<2>(m);
        int tc = get<3>(m);
        auto st = save_state();
        int tc_save = turn_col;

        make_move_fast(r, c, tr, tc, get<4>(m));
        bool in_check_after =
            is_attacked(bb_ctzll(pieces[p_color][K]), enemy_col(p_color));
        restore_state(st, tc_save);

        if (!in_check_after) {
          int tsq = tr * 8 + tc;
          bool cap = false;
          if (colors[enemy_col(p_color)] & (1ULL << tsq))
            cap = true;
          else if ((pieces[p_color][P] & sq_bb) && abs(tc - c) == 1)
            cap = true;

          if (cap)
            lc.push_back({tr, tc});
          else
            lm.push_back({tr, tc});
        }
      }
    }
    return py::make_tuple(lm, lc);
  }

  bool has_legal_moves(const string &color_str) {
    int color = (color_str == "w") ? WHITE : BLACK;
    auto pms = get_pseudo_moves(color);
    for (auto &m : pms) {
      auto st = save_state();
      int tc_save = turn_col;
      make_move_fast(get<0>(m), get<1>(m), get<2>(m), get<3>(m), get<4>(m));
      bool in_check_after =
          is_attacked(bb_ctzll(pieces[color][K]), enemy_col(color));
      restore_state(st, tc_save);
      if (!in_check_after)
        return true;
    }
    return false;
  }

  bool check_game_over() {
    if (!has_legal_moves(turn_col == WHITE ? "w" : "b")) {
      game_over = true;
      if (in_check_col(turn_col))
        winner = enemy(turn_col == WHITE ? "w" : "b");
      else
        winner = "draw";
      return true;
    }
    return false;
  }

  void make_move(int sr, int sc, int tr, int tc,
                 py::object promoted_piece_obj = py::none()) {
    string promo = "";
    if (!promoted_piece_obj.is_none())
      promo = promoted_piece_obj.cast<string>();
    make_move_fast(sr, sc, tr, tc, promo);
    check_game_over();
  }

  void make_move_fast(int sr, int sc, int tr, int tc,
                      const string &promo = "") {
    int sq = sr * 8 + sc;
    int tsq = tr * 8 + tc;
    int color = turn_col;
    int enemy = enemy_col(color);
    U64 sq_bb = 1ULL << sq;
    U64 tsq_bb = 1ULL << tsq;

    int moved_piece = -1;
    for (int i = 0; i < 6; i++) {
      if (pieces[color][i] & sq_bb) {
        moved_piece = i;
        break;
      }
    }
    if (moved_piece == -1)
      return;

    int captured_piece = -1;
    for (int i = 0; i < 6; i++) {
      if (pieces[enemy][i] & tsq_bb) {
        captured_piece = i;
        break;
      }
    }

    pieces[color][moved_piece] ^= (sq_bb | tsq_bb);
    if (captured_piece != -1) {
      pieces[enemy][captured_piece] ^= tsq_bb;
    }

    if (!promo.empty() && promo != "None") {
      pieces[color][P] ^= tsq_bb;
      if (promo[0] == 'Q')
        pieces[color][Q] |= tsq_bb;
      else if (promo[0] == 'R')
        pieces[color][R] |= tsq_bb;
      else if (promo[0] == 'B')
        pieces[color][B] |= tsq_bb;
      else if (promo[0] == 'N')
        pieces[color][N] |= tsq_bb;
    }

    if (moved_piece == K && abs(tc - sc) == 2) {
      if (tc > sc) {
        pieces[color][R] ^= (1ULL << (sr * 8 + 7)) | (1ULL << (sr * 8 + 5));
      } else {
        pieces[color][R] ^= (1ULL << (sr * 8 + 0)) | (1ULL << (sr * 8 + 3));
      }
    }

    if (moved_piece == P && tsq == ep_square) {
      int cap_sq = (color == WHITE) ? tsq + 8 : tsq - 8;
      pieces[enemy][P] ^= (1ULL << cap_sq);
    }

    ep_square = -1;
    if (moved_piece == P && abs(tr - sr) == 2) {
      ep_square = (tr + sr) / 2 * 8 + sc;
    }

    if (moved_piece == K) {
      castling &= (color == WHITE) ? ~3 : ~12;
    }
    if (moved_piece == R) {
      if (color == WHITE) {
        if (sc == 7)
          castling &= ~1;
        if (sc == 0)
          castling &= ~2;
      } else {
        if (sc == 7)
          castling &= ~4;
        if (sc == 0)
          castling &= ~8;
      }
    }
    if (captured_piece == R) {
      if (enemy == WHITE) {
        if (tc == 7 && tr == 7)
          castling &= ~1;
        if (tc == 0 && tr == 7)
          castling &= ~2;
      } else {
        if (tc == 7 && tr == 0)
          castling &= ~4;
        if (tc == 0 && tr == 0)
          castling &= ~8;
      }
    }

    colors[WHITE] = pieces[WHITE][P] | pieces[WHITE][N] | pieces[WHITE][B] |
                    pieces[WHITE][R] | pieces[WHITE][Q] | pieces[WHITE][K];
    colors[BLACK] = pieces[BLACK][P] | pieces[BLACK][N] | pieces[BLACK][B] |
                    pieces[BLACK][R] | pieces[BLACK][Q] | pieces[BLACK][K];
    occupied = colors[WHITE] | colors[BLACK];

    turn_col = enemy;
  }
};

#include "ai_engine.cpp"

PYBIND11_MODULE(chess_engine_cpp, m) {
  py::class_<ChessEngine>(m, "ChessEngine")
      .def(py::init<>())
      .def_property_readonly("board", &ChessEngine::get_board)
      .def_property_readonly("turn", &ChessEngine::get_turn)
      .def_property_readonly("en_passant", &ChessEngine::get_ep)
      .def_property_readonly("castle_rights", &ChessEngine::get_castle_rights)
      .def_readwrite("game_over", &ChessEngine::game_over)
      .def_readwrite("winner", &ChessEngine::winner)
      .def("in_bounds", &ChessEngine::in_bounds)
      .def("enemy", &ChessEngine::enemy)
      .def("in_check", &ChessEngine::in_check)
      .def("legal_moves", &ChessEngine::legal_moves_py)
      .def("has_legal_moves", &ChessEngine::has_legal_moves)
      .def("check_game_over", &ChessEngine::check_game_over)
      .def("make_move", &ChessEngine::make_move, py::arg("sr"), py::arg("sc"),
           py::arg("tr"), py::arg("tc"),
           py::arg("promoted_piece") = py::none());

  py::class_<AlphaBetaEngine>(m, "AlphaBetaEngine")
      .def(py::init<int, double>(), py::arg("depth") = 5,
           py::arg("time_limit") = 5.0)
      .def("record_move", &AlphaBetaEngine::record_move)
      .def("get_best_move", &AlphaBetaEngine::get_best_move);
}
