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

- On launch, choose to play as **White** or **Black**, then pick a **difficulty preset** (Beginner → Master) or fine-tune the exact **search depth** (1-20) with estimated response time.
- A live **evaluation bar** on the left shows the engine's assessment of the position (White fills from the bottom; `+1.4` style readout, or `M3` when a forced mate is seen).
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

**Windows (MinGW-w64, e.g. [WinLibs](https://winlibs.com/) UCRT build):**
```powershell
powershell -ExecutionPolicy Bypass -File rebuild.ps1
```
This wraps the g++ command with `-static -static-libgcc -static-libstdc++`, which
is **required** — without static linking the `.pyd` fails to import ("DLL load
failed") because Python 3.8+ won't resolve MinGW runtime DLLs via `PATH`.
(`python build_exe.py` uses the same flags when building the standalone `.exe`.)

### 3. Run

```bash
python3 main.py
```

---

## 📊 Engine Strength Estimate

**~2500–2700 Elo** (estimate, depth 12, hardware-dependent). A self-play match
of the current build vs the previous release scored **+255 Elo (13/16, zero
losses)** at equal fixed depth — and reaches a given depth **~2.3× faster**
thanks to sharper pruning.

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
| Null Move Pruning (adaptive R) | ✅ |
| Late Move Reductions (PV-aware) | ✅ |
| Killer + History Heuristics | ✅ |
| MVV-LVA + SEE Capture Ordering | ✅ |
| Principal Variation Search (PVS) | ✅ |
| **Full Static Exchange Evaluation (swap-off + x-ray)** | ✅ |
| **Check Extensions** | ✅ |
| **Reverse Futility (Static Null Move) Pruning** | ✅ |
| **Futility Pruning** | ✅ |
| **Late Move Pruning** | ✅ |
| Piece-Square Tables (mid+end) | ✅ |
| **Tapered Evaluation (phase-interpolated king PST)** | ✅ |
| **Mobility Eval** | ✅ |
| **Rook Open / Semi-Open File Bonus** | ✅ |
| **Tempo Bonus** | ✅ |
| Pawn Structure Eval | ✅ |
| King Safety Eval | ✅ |
| Bishop Pair Bonus | ✅ |
| Bitboard Move Generation | ✅ |
| Magic Bitboards | ❌ |
| Opening Book | ❌ |

### Depth Timing Snapshot (Current Build)

Move time from a representative middlegame on Windows x86_64 (MinGW GCC 16, `-O3`):

| Depth | Time |
|---|---|
| 9 | ~0.14s |
| 11 | ~0.44s |

The previous build needed ~0.31s just for depth 9 (491k nodes vs 106k now).
UI depth estimates stay conservative to account for slower machines and complex positions.

### Correctness

Move generation is verified by `perft` against known node counts for five
standard positions (start, Kiwipete, and three edge-case positions) through the
depths listed — all exact. Run `python tests/perft_test.py`.

---

## 📜 License

This project is open source. Contributions welcome!
