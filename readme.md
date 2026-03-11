# ♟ Hybrid Bitboard Chess Engine

A high-performance Chess Engine built with a **Python** frontend and an ultra-fast **C++ Bitboard** backend. This project utilizes `turtle` for the graphical interface while delegating all the heavy lifting (search, move generation, and evaluation) to a highly optimized C++ engine bound to Python via `pybind11`.

---

## ⬇️ Download & Run (No Setup Required!)

**No Python, no compiler, no dependencies needed.** Just download and play!

### 🪟 Windows
1. Go to the [**Releases page**](https://github.com/AmoghShukla06/PythonChessEngine/releases/latest)
2. Download **`ChessEngine-windows-x64.zip`**
3. Extract the ZIP file
4. Double-click **`ChessEngine.exe`** inside the `ChessEngine` folder
5. Play! 🎉

### 🐧 Linux
1. Go to the [**Releases page**](https://github.com/AmoghShukla06/PythonChessEngine/releases/latest)
2. Download **`ChessEngine-linux-x86_64.tar.gz`**
3. Extract and run:
```bash
tar xzf ChessEngine-linux-x86_64.tar.gz
cd ChessEngine
./ChessEngine
```

---

## 🎮 Playing Instructions

- On launch, choose to play as **White** or **Black**, then **select AI depth** (1-20) with estimated response time.
- Click a piece to select it → valid moves highlight in **green**, captures in **red**.
- Move with either **click-to-move** or **left-drag and drop** (piece hovers with the cursor while dragging).
- Press **`C`** to clear selection highlights.
- The AI's last move is highlighted with a **tinted overlay** on both the source and destination squares.
- **Captured pieces** are displayed on the right panel.
- Use the right-side **Resign** and **Quit** buttons at any time on your turn.
- Press **`F`** at any time to **flip the board**.
- The AI search progress (depth, score, nodes, time) is printed to the terminal in real-time.

---

## 🧠 Architecture Overview

```
┌────────────────────────────────────────────────────┐
│                  Python Layer                      │
│                                                    │
│  main.py ─── Game loop, click handler, AI trigger  │
│  ui.py ───── Turtle-based GUI, board rendering     │
│  chess_engine_wrapper.py ── Thin wrapper over C++  │
│  resource_path.py ── Asset path resolution         │
│                                                    │
├────────────────────────────────────────────────────┤
│              C++ Engine (pybind11)                 │
│                                                    │
│  bitboard.h / bitboard.cpp                         │
│    └─ U64 bitboard types, bit intrinsics           │
│    └─ Pre-calculated attack tables                 │
│    └─ Zobrist hashing tables                       │
│    └─ File masks for pawn evaluation               │
│                                                    │
│  chess_engine.cpp                                  │
│    └─ ChessEngine class: board state, move gen,    │
│       make/unmake, legality, castling, en passant  │
│                                                    │
│  ai_engine.cpp                                     │
│    └─ PVS (Principal Variation Search)             │
│    └─ Quiescence search with SEE pruning           │
│    └─ Zobrist hashing + persistent TT              │
│    └─ Null move pruning, LMR, killer/history       │
│    └─ Hash/PV move ordering + capture-only qsearch │
│    └─ Pawn structure eval (doubled/isolated/passed)│
│    └─ King safety eval (shield, open files, zone)  │
│    └─ Piece-square tables (midgame + endgame)      │
│                                                    │
├────────────────────────────────────────────────────┤
│                  Assets                            │
│  pieces/*.gif ── Piece sprites (wP, bK, etc.)      │
│  background.gif ── Board background                │
└────────────────────────────────────────────────────┘
```

---

## 🔧 Build From Source

### Prerequisites

| Requirement | Linux | Windows |
|---|---|---|
| **Python** | 3.8+ | 3.8+ |
| **C++ Compiler** | `g++` or `clang++` (C++17) | MSVC or MinGW |
| **pybind11** | `pip install pybind11` | `pip install pybind11` |

### 1. Setup Environment

```bash
git clone https://github.com/AmoghShukla06/PythonChessEngine.git
cd PythonChessEngine
python3 -m venv venv
source venv/bin/activate
pip install pybind11
```

### 2. Compile the C++ Engine

**Linux / macOS:**
```bash
g++ -O3 -Wall -shared -std=c++17 -fPIC \
  $(python3 -m pybind11 --includes) \
  bitboard.cpp chess_engine.cpp \
  -o chess_engine_cpp$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
```

### 3. Run

```bash
python3 main.py
```

---

## 📊 Engine Strength Estimate

**~2200–2400 Elo** (CCRL-like estimate, depth 12, hardware-dependent)

| Feature | Status |
|---|---|
| Alpha-Beta + Negamax | ✅ |
| Iterative Deepening (depth 1→20) | ✅ |
| Aspiration Windows | ✅ |
| Zobrist Hashing | ✅ |
| Persistent Transposition Table | ✅ |
| Hash Move Ordering | ✅ |
| Quiescence Search | ✅ |
| Capture-Only Quiescence Move Gen | ✅ |
| Null Move Pruning (R=2) | ✅ |
| Late Move Reductions | ✅ |
| Killer + History Heuristics | ✅ |
| MVV-LVA + SEE-Style Capture Ordering | ✅ |
| Principal Variation Search (PVS) | ✅ |
| Static Exchange Evaluation (SEE-lite) | ✅ |
| Piece-Square Tables (mid+end) | ✅ |
| Pawn Structure Eval | ✅ |
| King Safety Eval | ✅ |
| Bishop Pair Bonus | ✅ |
| Bitboard Move Generation | ✅ |
| Check Extensions | ❌ |
| Mobility Eval | ❌ |
| Futility Pruning | ❌ |
| Magic Bitboards | ❌ |

### Depth Timing Snapshot (Current Build)

Average move time from three representative positions (start/opening/middlegame) on Linux x86_64:

| Depth | Avg Time |
|---|---|
| 6 | ~0.02s |
| 7 | ~0.05s |
| 8 | ~0.11s |
| 9 | ~0.19s |
| 10 | ~0.35s |
| 11 | ~0.69s |
| 12 | ~1.35s |
| 13 | ~2.90s |
| 14 | ~5.17s |

UI depth estimates are intentionally more conservative than this benchmark to account for slower machines and complex positions.

---

## 📜 License

This project is open source. Contributions welcome!
