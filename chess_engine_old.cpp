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

// Types
typedef pair<int, int> Square;
typedef tuple<int, int, int, int, string> MoveFull; // sr, sc, tr, tc, promo

// Structs
struct UndoInfo {
  vector<vector<string>> board;
  string turn;
  Square en_passant;
  unordered_map<string, unordered_map<string, bool>> castle_rights;
  unordered_map<string, bool> king_moved;
  bool game_over;
  string winner;
};

class ChessEngine {
public:
  vector<vector<string>> board;
  string turn = "w";
  Square en_passant = {-1, -1};
  unordered_map<string, unordered_map<string, bool>> castle_rights;
  unordered_map<string, bool> king_moved;
  bool game_over = false;
  string winner;

  ChessEngine() {
    board = {{"bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"},
             {"bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"},
             {"--", "--", "--", "--", "--", "--", "--", "--"},
             {"--", "--", "--", "--", "--", "--", "--", "--"},
             {"--", "--", "--", "--", "--", "--", "--", "--"},
             {"--", "--", "--", "--", "--", "--", "--", "--"},
             {"wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"},
             {"wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"}};
    castle_rights["w"]["kingside"] = true;
    castle_rights["w"]["queenside"] = true;
    castle_rights["b"]["kingside"] = true;
    castle_rights["b"]["queenside"] = true;
    king_moved["w"] = false;
    king_moved["b"] = false;
  }

  bool in_bounds(int r, int c) const {
    return 0 <= r && r < 8 && 0 <= c && c < 8;
  }

  string enemy(const string &color) const { return color == "w" ? "b" : "w"; }

  pair<vector<Square>, vector<Square>> pawn_moves(int r, int c) const {
    vector<Square> moves, caps;
    string color = board[r][c].substr(0, 1);
    int d = (color == "w") ? -1 : 1;
    int start = (color == "w") ? 6 : 1;

    if (in_bounds(r + d, c) && board[r + d][c] == "--") {
      moves.push_back({r + d, c});
      if (r == start && board[r + 2 * d][c] == "--") {
        moves.push_back({r + 2 * d, c});
      }
    }

    for (int dc : {-1, 1}) {
      int nr = r + d, nc = c + dc;
      if (in_bounds(nr, nc)) {
        if (board[nr][nc] != "--" && board[nr][nc].substr(0, 1) != color) {
          caps.push_back({nr, nc});
        }
      }
    }

    if (en_passant.first != -1) {
      int er = en_passant.first, ec = en_passant.second;
      if (er == r + d && abs(ec - c) == 1) {
        caps.push_back({er, ec});
      }
    }
    return {moves, caps};
  }

  pair<vector<Square>, vector<Square>> knight_moves(int r, int c) const {
    vector<Square> moves, caps;
    string color = board[r][c].substr(0, 1);
    int drs[] = {2, 1, -1, -2, -2, -1, 1, 2};
    int dcs[] = {1, 2, 2, 1, -1, -2, -2, -1};
    for (int i = 0; i < 8; i++) {
      int nr = r + drs[i], nc = c + dcs[i];
      if (in_bounds(nr, nc)) {
        if (board[nr][nc] == "--")
          moves.push_back({nr, nc});
        else if (board[nr][nc].substr(0, 1) != color)
          caps.push_back({nr, nc});
      }
    }
    return {moves, caps};
  }

  pair<vector<Square>, vector<Square>>
  slide_moves(int r, int c, const vector<pair<int, int>> &dirs) const {
    vector<Square> moves, caps;
    string color = board[r][c].substr(0, 1);
    for (auto &dir : dirs) {
      int dr = dir.first, dc = dir.second;
      int nr = r + dr, nc = c + dc;
      while (in_bounds(nr, nc)) {
        if (board[nr][nc] == "--") {
          moves.push_back({nr, nc});
        } else {
          if (board[nr][nc].substr(0, 1) != color) {
            caps.push_back({nr, nc});
          }
          break;
        }
        nr += dr;
        nc += dc;
      }
    }
    return {moves, caps};
  }

  pair<vector<Square>, vector<Square>> king_moves(int r, int c) const {
    vector<Square> moves, caps;
    string color = board[r][c].substr(0, 1);
    for (int dr : {-1, 0, 1}) {
      for (int dc : {-1, 0, 1}) {
        if (dr == 0 && dc == 0)
          continue;
        int nr = r + dr, nc = c + dc;
        if (in_bounds(nr, nc)) {
          if (board[nr][nc] == "--")
            moves.push_back({nr, nc});
          else if (board[nr][nc].substr(0, 1) != color)
            caps.push_back({nr, nc});
        }
      }
    }
    return {moves, caps};
  }

  pair<vector<Square>, vector<Square>> pseudo_moves(int r, int c) const {
    string piece = board[r][c];
    if (piece == "--")
      return {{}, {}};
    char kind = piece[1];
    if (kind == 'P')
      return pawn_moves(r, c);
    if (kind == 'N')
      return knight_moves(r, c);
    if (kind == 'B')
      return slide_moves(r, c, {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}});
    if (kind == 'R')
      return slide_moves(r, c, {{1, 0}, {-1, 0}, {0, 1}, {0, -1}});
    if (kind == 'Q')
      return slide_moves(r, c,
                         {{1, 0},
                          {-1, 0},
                          {0, 1},
                          {0, -1},
                          {1, 1},
                          {1, -1},
                          {-1, 1},
                          {-1, -1}});
    if (kind == 'K')
      return king_moves(r, c);
    return {{}, {}};
  }

  Square find_king(const string &color) const {
    string target = color + "K";
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        if (board[r][c] == target)
          return {r, c};
      }
    }
    return {-1, -1};
  }

  bool square_attacked(int r, int c, const string &by_color) const {
    for (int i = 0; i < 8; i++) {
      for (int j = 0; j < 8; j++) {
        if (board[i][j].substr(0, 1) == by_color) {
          auto pm = pseudo_moves(i, j);
          for (auto &m : pm.first)
            if (m.first == r && m.second == c)
              return true;
          for (auto &caps : pm.second)
            if (caps.first == r && caps.second == c)
              return true;
        }
      }
    }
    return false;
  }

  bool in_check(const string &color) const {
    Square k = find_king(color);
    if (k.first == -1)
      return false;
    return square_attacked(k.first, k.second, enemy(color));
  }

  pair<vector<Square>, vector<Square>> legal_moves(int r, int c) {
    string color = board[r][c].substr(0, 1);
    string piece = board[r][c];
    auto pm = pseudo_moves(r, c);
    vector<Square> lm, lc;

    if (piece[1] == 'K' && !king_moved[color] && !in_check(color)) {
      if (castle_rights[color]["kingside"]) {
        if (board[r][c + 1] == "--" && board[r][c + 2] == "--" &&
            !square_attacked(r, c + 1, enemy(color)) &&
            !square_attacked(r, c + 2, enemy(color))) {
          pm.first.push_back({r, c + 2});
        }
      }
      if (castle_rights[color]["queenside"]) {
        if (board[r][c - 1] == "--" && board[r][c - 2] == "--" &&
            board[r][c - 3] == "--" &&
            !square_attacked(r, c - 1, enemy(color)) &&
            !square_attacked(r, c - 2, enemy(color))) {
          pm.first.push_back({r, c - 2});
        }
      }
    }

    vector<Square> all_moves = pm.first;
    all_moves.insert(all_moves.end(), pm.second.begin(), pm.second.end());

    for (auto &trc : all_moves) {
      int tr = trc.first, tc = trc.second;
      string captured = board[tr][tc];
      board[tr][tc] = board[r][c];
      board[r][c] = "--";

      if (!in_check(color)) {
        bool is_move = false;
        for (auto &m : pm.first)
          if (m == trc)
            is_move = true;
        if (is_move)
          lm.push_back(trc);
        else
          lc.push_back(trc);
      }
      board[r][c] = board[tr][tc];
      board[tr][tc] = captured;
    }
    return std::make_pair(lm, lc);
  }

  // Exported helper wrapper for Python
  py::tuple legal_moves_py(int r, int c) {
    auto res = legal_moves(r, c);
    return py::make_tuple(res.first, res.second);
  }

  bool has_legal_moves(const string &color) {
    for (int r = 0; r < 8; r++) {
      for (int c = 0; c < 8; c++) {
        if (board[r][c].substr(0, 1) == color) {
          auto lm = legal_moves(r, c);
          if (!lm.first.empty() || !lm.second.empty())
            return true;
        }
      }
    }
    return false;
  }

  bool check_game_over() {
    if (!has_legal_moves(turn)) {
      game_over = true;
      if (in_check(turn))
        winner = enemy(turn);
      else
        winner = "draw";
      return true;
    }
    return false;
  }

  void make_move(int sr, int sc, int tr, int tc,
                 py::object promoted_piece_obj = py::none()) {
    string promoted_piece = "";
    if (!promoted_piece_obj.is_none()) {
      promoted_piece = promoted_piece_obj.cast<string>();
    }

    string piece = board[sr][sc];
    if (piece == "--")
      return; // Safety
    string color = piece.substr(0, 1);
    string target = board[tr][tc];

    if (target != "--" && target[1] == 'R') {
      if (tr == 0 && tc == 0)
        castle_rights["b"]["queenside"] = false;
      if (tr == 0 && tc == 7)
        castle_rights["b"]["kingside"] = false;
      if (tr == 7 && tc == 0)
        castle_rights["w"]["queenside"] = false;
      if (tr == 7 && tc == 7)
        castle_rights["w"]["kingside"] = false;
    }

    if (piece[1] == 'K' && abs(tc - sc) == 2) {
      board[tr][tc] = piece;
      board[sr][sc] = "--";
      if (tc > sc) { // kingside
        board[tr][5] = board[tr][7];
        board[tr][7] = "--";
      } else { // queenside
        board[tr][3] = board[tr][0];
        board[tr][0] = "--";
      }
      king_moved[color] = true;
      castle_rights[color]["kingside"] = false;
      castle_rights[color]["queenside"] = false;
    } else {
      if (piece[1] == 'P' && en_passant.first == tr &&
          en_passant.second == tc) {
        board[sr][tc] = "--";
      }

      if (!promoted_piece.empty() && promoted_piece != "None") {
        board[tr][tc] = color + promoted_piece;
      } else {
        board[tr][tc] = piece;
      }
      board[sr][sc] = "--";

      if (piece[1] == 'K') {
        king_moved[color] = true;
        castle_rights[color]["kingside"] = false;
        castle_rights[color]["queenside"] = false;
      } else if (piece[1] == 'R') {
        if (sr == 7 && sc == 7)
          castle_rights["w"]["kingside"] = false;
        else if (sr == 7 && sc == 0)
          castle_rights["w"]["queenside"] = false;
        else if (sr == 0 && sc == 7)
          castle_rights["b"]["kingside"] = false;
        else if (sr == 0 && sc == 0)
          castle_rights["b"]["queenside"] = false;
      }
    }

    en_passant = {-1, -1};
    if (piece[1] == 'P' && abs(tr - sr) == 2) {
      en_passant = {(tr + sr) / 2, sc};
    }

    turn = enemy(turn);
    check_game_over();
  }
  void make_move_fast(int sr, int sc, int tr, int tc,
                      const string &promoted_piece = "") {
    string piece = board[sr][sc];
    if (piece == "--")
      return; // Safety
    string color = piece.substr(0, 1);
    string target = board[tr][tc];

    if (target != "--" && target[1] == 'R') {
      if (tr == 0 && tc == 0)
        castle_rights["b"]["queenside"] = false;
      if (tr == 0 && tc == 7)
        castle_rights["b"]["kingside"] = false;
      if (tr == 7 && tc == 0)
        castle_rights["w"]["queenside"] = false;
      if (tr == 7 && tc == 7)
        castle_rights["w"]["kingside"] = false;
    }

    if (piece[1] == 'K' && abs(tc - sc) == 2) {
      board[tr][tc] = piece;
      board[sr][sc] = "--";
      if (tc > sc) { // kingside
        board[tr][5] = board[tr][7];
        board[tr][7] = "--";
      } else { // queenside
        board[tr][3] = board[tr][0];
        board[tr][0] = "--";
      }
      king_moved[color] = true;
      castle_rights[color]["kingside"] = false;
      castle_rights[color]["queenside"] = false;
    } else {
      if (piece[1] == 'P' && en_passant.first == tr &&
          en_passant.second == tc) {
        board[sr][tc] = "--";
      }

      if (!promoted_piece.empty() && promoted_piece != "None") {
        board[tr][tc] = color + promoted_piece;
      } else {
        board[tr][tc] = piece;
      }
      board[sr][sc] = "--";

      if (piece[1] == 'K') {
        king_moved[color] = true;
        castle_rights[color]["kingside"] = false;
        castle_rights[color]["queenside"] = false;
      } else if (piece[1] == 'R') {
        if (sr == 7 && sc == 7)
          castle_rights["w"]["kingside"] = false;
        else if (sr == 7 && sc == 0)
          castle_rights["w"]["queenside"] = false;
        else if (sr == 0 && sc == 7)
          castle_rights["b"]["kingside"] = false;
        else if (sr == 0 && sc == 0)
          castle_rights["b"]["queenside"] = false;
      }
    }

    en_passant = {-1, -1};
    if (piece[1] == 'P' && abs(tr - sr) == 2) {
      en_passant = {(tr + sr) / 2, sc};
    }

    turn = enemy(turn);
  }
};

#include "ai_engine.cpp"

PYBIND11_MODULE(chess_engine_cpp, m) {
  py::class_<ChessEngine>(m, "ChessEngine")
      .def(py::init<>())
      .def_readwrite("board", &ChessEngine::board)
      .def_readwrite("turn", &ChessEngine::turn)
      .def_readwrite("en_passant", &ChessEngine::en_passant)
      .def_readwrite("castle_rights", &ChessEngine::castle_rights)
      .def_readwrite("king_moved", &ChessEngine::king_moved)
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
