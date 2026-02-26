#include "bitboard.h"
#include <iostream>

void print_bb(U64 bb) {
  for (int r = 0; r < 8; r++) {
    for (int c = 0; c < 8; c++) {
      std::cout << ((bb & (1ULL << (r * 8 + c))) ? "1 " : ". ");
    }
    std::cout << std::endl;
  }
  std::cout << "---" << std::endl;
}

int main() {
  init_all_bitboards();
  int sq = 35; // D4

  std::cout << "Knight on D4 (sq=35):\n";
  print_bb(knight_attacks[sq]);

  std::cout << "Rook on D4 (sq=35) empty board:\n";
  print_bb(get_rook_attacks(sq, 0));

  std::cout
      << "Rook on D4 (sq=35) with blockers on D2 (sq=51) and E4 (sq=36):\n";
  U64 blockers = (1ULL << 51) | (1ULL << 36);
  print_bb(get_rook_attacks(sq, blockers));

  std::cout
      << "Bishop on D4 (sq=35) with blockers on F2 (sq=53) and B6 (sq=17):\n";
  blockers = (1ULL << 53) | (1ULL << 17);
  print_bb(get_bishop_attacks(sq, blockers));

  return 0;
}
