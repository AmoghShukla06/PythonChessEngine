#include "bitboard.h"

U64 pawn_attacks[2][64];
U64 knight_attacks[64];
U64 king_attacks[64];
U64 ray_attacks[64][8];

const U64 FILE_A = 0x0101010101010101ULL;
const U64 FILE_H = 0x8080808080808080ULL;
const U64 FILE_AB = 0x0303030303030303ULL;
const U64 FILE_GH = 0xC0C0C0C0C0C0C0C0ULL;

void init_leapers() {
  for (int sq = 0; sq < 64; sq++) {
    int r = sq / 8;
    int c = sq % 8;
    // U64 sq_bb = 1ULL << sq;

    // Pawns
    pawn_attacks[WHITE][sq] = 0;
    if (r > 0) {
      if (c > 0)
        pawn_attacks[WHITE][sq] |= (1ULL << ((r - 1) * 8 + c - 1));
      if (c < 7)
        pawn_attacks[WHITE][sq] |= (1ULL << ((r - 1) * 8 + c + 1));
    }
    pawn_attacks[BLACK][sq] = 0;
    if (r < 7) {
      if (c > 0)
        pawn_attacks[BLACK][sq] |= (1ULL << ((r + 1) * 8 + c - 1));
      if (c < 7)
        pawn_attacks[BLACK][sq] |= (1ULL << ((r + 1) * 8 + c + 1));
    }

    // Knights
    knight_attacks[sq] = 0;
    int knight_moves[8][2] = {{-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
                              {1, -2},  {1, 2},  {2, -1},  {2, 1}};
    for (int i = 0; i < 8; i++) {
      int nr = r + knight_moves[i][0];
      int nc = c + knight_moves[i][1];
      if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
        knight_attacks[sq] |= (1ULL << (nr * 8 + nc));
      }
    }

    // King
    king_attacks[sq] = 0;
    int king_moves[8][2] = {{-1, -1}, {-1, 0}, {-1, 1}, {0, -1},
                            {0, 1},   {1, -1}, {1, 0},  {1, 1}};
    for (int i = 0; i < 8; i++) {
      int nr = r + king_moves[i][0];
      int nc = c + king_moves[i][1];
      if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
        king_attacks[sq] |= (1ULL << (nr * 8 + nc));
      }
    }
  }
}

void init_sliders() {
  // DIR_N (up, -8), DIR_S (down, +8), DIR_E (right, +1), DIR_W (left, -1)
  // DIR_NE (up-right, -7), DIR_NW (up-left, -9)
  // DIR_SE (down-right, +9), DIR_SW (down-left, +7)
  int dirs[8][2] = {{-1, 0}, {1, 0},   {0, 1}, {0, -1},
                    {-1, 1}, {-1, -1}, {1, 1}, {1, -1}};

  for (int sq = 0; sq < 64; sq++) {
    int r = sq / 8;
    int c = sq % 8;

    for (int d = 0; d < 8; d++) {
      ray_attacks[sq][d] = 0ULL;
      int nr = r + dirs[d][0];
      int nc = c + dirs[d][1];
      while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
        ray_attacks[sq][d] |= (1ULL << (nr * 8 + nc));
        nr += dirs[d][0];
        nc += dirs[d][1];
      }
    }
  }
}

void init_all_bitboards() {
  init_leapers();
  init_sliders();
  init_zobrist();
}

// --- Zobrist Hashing ---
U64 zobrist_pieces[2][6][64];
U64 zobrist_ep[64];
U64 zobrist_castling[16];
U64 zobrist_side;

static U64 xorshift64(U64 &state) {
  state ^= state << 13;
  state ^= state >> 7;
  state ^= state << 17;
  return state;
}

void init_zobrist() {
  U64 seed = 0x12345678ABCDEF01ULL;
  for (int color = 0; color < 2; color++)
    for (int piece = 0; piece < 6; piece++)
      for (int sq = 0; sq < 64; sq++)
        zobrist_pieces[color][piece][sq] = xorshift64(seed);
  for (int sq = 0; sq < 64; sq++)
    zobrist_ep[sq] = xorshift64(seed);
  for (int i = 0; i < 16; i++)
    zobrist_castling[i] = xorshift64(seed);
  zobrist_side = xorshift64(seed);
}

// --- File masks for pawn structure eval ---
const U64 FILE_MASKS[8] = {
    0x0101010101010101ULL, // A
    0x0202020202020202ULL, // B
    0x0404040404040404ULL, // C
    0x0808080808080808ULL, // D
    0x1010101010101010ULL, // E
    0x2020202020202020ULL, // F
    0x4040404040404040ULL, // G
    0x8080808080808080ULL  // H
};

const U64 ADJ_FILE_MASKS[8] = {
    FILE_MASKS[1],                 // A: only B
    FILE_MASKS[0] | FILE_MASKS[2], // B: A+C
    FILE_MASKS[1] | FILE_MASKS[3], // C: B+D
    FILE_MASKS[2] | FILE_MASKS[4], // D: C+E
    FILE_MASKS[3] | FILE_MASKS[5], // E: D+F
    FILE_MASKS[4] | FILE_MASKS[6], // F: E+G
    FILE_MASKS[5] | FILE_MASKS[7], // G: F+H
    FILE_MASKS[6]                  // H: only G
};

U64 get_ray_attacks(int sq, U64 blockers, int dir) {
  U64 attacks = ray_attacks[sq][dir];
  U64 blocker_ray = attacks & blockers;
  if (blocker_ray) {
    int blocker_sq;
    // If direction increases index (South, East, SE, SW), find first LSB
    if (dir == DIR_S || dir == DIR_E || dir == DIR_SE || dir == DIR_SW) {
      blocker_sq = bb_ctzll(blocker_ray);
    } else {
      // Direction decreases index (North, West, NW, NE), find first MSB
      blocker_sq = 63 - bb_clzll(blocker_ray);
    }
    attacks ^= ray_attacks[blocker_sq][dir];
  }
  return attacks;
}

U64 get_bishop_attacks(int sq, U64 blockers) {
  return get_ray_attacks(sq, blockers, DIR_NW) |
         get_ray_attacks(sq, blockers, DIR_NE) |
         get_ray_attacks(sq, blockers, DIR_SW) |
         get_ray_attacks(sq, blockers, DIR_SE);
}

U64 get_rook_attacks(int sq, U64 blockers) {
  return get_ray_attacks(sq, blockers, DIR_N) |
         get_ray_attacks(sq, blockers, DIR_S) |
         get_ray_attacks(sq, blockers, DIR_E) |
         get_ray_attacks(sq, blockers, DIR_W);
}

U64 get_queen_attacks(int sq, U64 blockers) {
  return get_bishop_attacks(sq, blockers) | get_rook_attacks(sq, blockers);
}
