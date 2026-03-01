#ifndef BITBOARD_H
#define BITBOARD_H

#include <cstdint>
#include <string>
#include <vector>

#ifdef _MSC_VER
#include <intrin.h>
#endif

typedef uint64_t U64;

// Board representation enum
enum Piece { P, N, B, R, Q, K };
enum Color { WHITE, BLACK };

static inline int square_idx(int r, int c) { return r * 8 + c; }

static inline U64 set_bit(U64 bb, int sq) { return bb | (1ULL << sq); }
static inline U64 get_bit(U64 bb, int sq) { return bb & (1ULL << sq); }
static inline U64 pop_bit(U64 bb, int sq) { return bb & ~(1ULL << sq); }

// --- Cross-platform bit intrinsics ---
#ifdef _MSC_VER
static inline int count_bits(U64 bb) { return (int)__popcnt64(bb); }
static inline int get_ls1b(U64 bb) {
  unsigned long idx;
  _BitScanForward64(&idx, bb);
  return (int)idx;
}
static inline int bb_ctzll(U64 bb) {
  unsigned long idx;
  _BitScanForward64(&idx, bb);
  return (int)idx;
}
static inline int bb_clzll(U64 bb) {
  unsigned long idx;
  _BitScanReverse64(&idx, bb);
  return 63 - (int)idx;
}
#else
static inline int count_bits(U64 bb) { return __builtin_popcountll(bb); }
static inline int get_ls1b(U64 bb) { return __builtin_ctzll(bb); }
static inline int bb_ctzll(U64 bb) { return __builtin_ctzll(bb); }
static inline int bb_clzll(U64 bb) { return __builtin_clzll(bb); }
#endif

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

// --- Zobrist Hashing ---
extern U64 zobrist_pieces[2][6][64];
extern U64 zobrist_ep[64];
extern U64 zobrist_castling[16];
extern U64 zobrist_side;
void init_zobrist();

// --- File masks for pawn evaluation ---
extern const U64 FILE_MASKS[8];
extern const U64 ADJ_FILE_MASKS[8];

#endif
