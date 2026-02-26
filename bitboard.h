#ifndef BITBOARD_H
#define BITBOARD_H

#include <cstdint>
#include <string>
#include <vector>

typedef uint64_t U64;

// Board representation enum
enum Piece { P, N, B, R, Q, K };
enum Color { WHITE, BLACK };

static inline int square_idx(int r, int c) {
  // Top-left (0,0) is A8 in conventional chess if we consider row 0 as rank 8,
  // col 0 as file A Traditional engine uses Rank 1 as lower bits. Let's map our
  // r, c directly for now: r=0..7, c=0..7 -> r*8 + c (0 is top-left A8, 63 is
  // bottom-right H1) Actually standard bitboard is A1=0, H8=63. Let's stick to
  // A8=0, H1=63 for easier matching with current UI logic where board[r][c] r=0
  // is top.
  return r * 8 + c;
}

static inline U64 set_bit(U64 bb, int sq) { return bb | (1ULL << sq); }
static inline U64 get_bit(U64 bb, int sq) { return bb & (1ULL << sq); }
static inline U64 pop_bit(U64 bb, int sq) { return bb & ~(1ULL << sq); }

static inline int count_bits(U64 bb) { return __builtin_popcountll(bb); }
static inline int get_ls1b(U64 bb) { return __builtin_ctzll(bb); }

// Pre-calculated tables
extern U64 pawn_attacks[2][64];
extern U64 knight_attacks[64];
extern U64 king_attacks[64];

// Masks
extern const U64 FILE_A;
extern const U64 FILE_H;
extern const U64 FILE_AB;
extern const U64 FILE_GH;

// Ray casting for sliding pieces (Classical approach, simple without magics
// initially, or magic if desired) We will use a fast array-based lookup for
// rays to keep it simple but extremely fast.
extern U64 ray_attacks[64][8]; // 8 directions: N, S, W, E, NW, NE, SW, SE

void init_leapers();
void init_sliders();
void init_all_bitboards();

U64 get_bishop_attacks(int sq, U64 blockers);
U64 get_rook_attacks(int sq, U64 blockers);
U64 get_queen_attacks(int sq, U64 blockers);

enum Direction { DIR_N, DIR_S, DIR_E, DIR_W, DIR_NE, DIR_NW, DIR_SE, DIR_SW };

#endif
