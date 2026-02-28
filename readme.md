
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

- On launch, a **popup** lets you choose to play as **White** or **Black**.
- Click a piece to select it → valid moves highlight in **green**, captures in **red**.
- Click a valid square to make your move.
- The AI's last move is highlighted with a **blue border** on both the source and destination squares.
- **Captured pieces** are displayed on the right panel (white pieces in white, black pieces in gold).
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
│              C++ Engine (pybind11)                  │
│                                                    │
│  bitboard.h / bitboard.cpp                         │
│    └─ U64 bitboard types, bit intrinsics           │
│    └─ Pre-calculated attack tables (leapers,       │
│       sliders, rays)                               │
│                                                    │
│  chess_engine.cpp                                  │
│    └─ ChessEngine class: board state, move gen,    │
│       make/unmake, legality checks, castling,      │
│       en passant, promotion                        │
│                                                    │
│  ai_engine.cpp                                     │
│    └─ AlphaBetaEngine class: search + evaluation   │
│    └─ Iterative deepening with aspiration windows  │
│    └─ Negamax + alpha-beta pruning                 │
│    └─ Quiescence search (captures only)            │
│    └─ Transposition table (hash-based)             │
│    └─ Null move pruning, LMR, killer/history       │
│    └─ Piece-square tables (midgame + endgame)      │
│                                                    │
├────────────────────────────────────────────────────┤
│                  Assets                            │
│  pieces/*.gif ── Piece sprites (wP, bK, etc.)     │
│  background.gif ── Board background               │
└────────────────────────────────────────────────────┘
```

### Data Flow

1. `main.py` creates `ChessEngine` (C++) and `AlphaBetaEngine` (C++)
2. Human clicks → `ui.screen_to_board()` → `engine.legal_moves()` → UI highlights
3. Human move → `engine.make_move()` → triggers `ai.get_best_move(engine)`
4. AI searches iteratively (depth 1→12, 5s time limit) → returns `(sr, sc, tr, tc)`
5. UI updates pieces, highlights, captured panel

---

## 🔧 Build From Source

### Prerequisites

| Requirement | Linux | Windows |
|---|---|---|
| **Python** | 3.8+ | 3.8+ |
| **C++ Compiler** | `g++` or `clang++` (C++17) | MSVC (Visual Studio) or MinGW |
| **pybind11** | `pip install pybind11` | `pip install pybind11` |

### 1. Setup Environment

```bash
# Clone the repo
git clone https://github.com/AmoghShukla06/PythonChessEngine.git
cd PythonChessEngine

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux
# venv\Scripts\activate         # Windows

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

**Windows (MSVC — open Developer Command Prompt):**
```cmd
cl /O2 /std:c++17 /EHsc /MD /LD ^
  /I"%VIRTUAL_ENV%\Include" ^
  bitboard.cpp chess_engine.cpp ^
  /link /OUT:chess_engine_cpp.pyd
```

### 3. Run

```bash
python3 main.py
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started.

### Project Structure Quick Reference

| File | Role | Lines | Language |
|---|---|---|---|
| `main.py` | Game loop, click handler, AI orchestration | ~240 | Python |
| `ui.py` | Turtle-based GUI rendering | ~390 | Python |
| `chess_engine_wrapper.py` | Thin Python wrapper over C++ classes | ~17 | Python |
| `chess_engine.cpp` | Board state, move generation, make/unmake | ~600 | C++17 |
| `ai_engine.cpp` | Search algorithm, evaluation, heuristics | ~510 | C++17 |
| `bitboard.h` / `bitboard.cpp` | Bitboard types, attack tables, intrinsics | ~80 / ~100 | C++17 |
| `build_exe.py` | PyInstaller packaging script | ~90 | Python |

### Areas for Improvement

Here are high-impact features that would strengthen the engine, roughly ordered by Elo gain:

#### 🔴 High Impact (50–100+ Elo each)
- **Proper Zobrist Hashing** — Current hash is ad-hoc XOR; replace with random-number-based Zobrist keys for fewer collisions
- **Pawn structure evaluation** — Doubled, isolated, passed pawns
- **King safety evaluation** — Pawn shield, open files near king, attack count
- **Check extensions** — Extend search depth by 1 when in check

#### 🟡 Medium Impact (30–50 Elo each)
- **Principal Variation Search (PVS)** — Search first move with full window, rest with null window
- **Static Exchange Evaluation (SEE)** — Better capture ordering and pruning
- **Mobility evaluation** — Count legal moves as an evaluation term
- **Futility pruning** — Skip moves that can't possibly raise alpha at low depths

#### 🟢 Lower Impact / Polish (10–30 Elo each)
- **Bishop pair bonus** — Award ~30cp when both bishops are present
- **Opening book** — A compiled `opening_book.py` exists but isn't currently imported
- **Endgame tablebases** — Syzygy or similar for perfect endgame play
- **Pondering** — Think on opponent's time

### Development Workflow

1. **Fork & clone** the repo
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Compile & test** after every C++ change:
   ```bash
   # Recompile
   g++ -O3 -Wall -shared -std=c++17 -fPIC \
     $(python3 -m pybind11 --includes) \
     bitboard.cpp chess_engine.cpp \
     -o chess_engine_cpp$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")

   # Verify module loads
   python3 -c "from chess_engine_cpp import ChessEngine; print('OK')"

   # Play test
   python3 main.py
   ```
4. **Commit** with clear messages: `feat:`, `fix:`, `refactor:`, `docs:`
5. **Open a Pull Request** against `main`

### Key Conventions

- **C++ style**: All engine logic goes in the C++ files. The Python layer only handles UI and orchestration.
- **Piece representation**: `enum Piece { P, N, B, R, Q, K }` and `enum Color { WHITE, BLACK }` in `bitboard.h`.
- **Move format**: Moves are `tuple<int, int, int, int, string>` = `(src_row, src_col, dst_row, dst_col, promo)`.
- **Evaluation is centipawns**: Pawn = 100, Knight = 320, Bishop = 330, Rook = 500, Queen = 900.
- **Search returns negamax scores**: Positive = good for the side to move.
- **Cross-platform intrinsics**: Bit operations (`popcnt`, `ctz`, `clz`) have MSVC and GCC/Clang variants in `bitboard.h`.

### Debugging Tips

- **Watch the terminal** — Every AI move prints depth, score, node count, and time.
- **Score suddenly jumps to ±15000+?** That's a detected checkmate (± 20000 - depth).
- **Engine hangs?** Check if `time_limit` in `main.py` (currently 5.0s) is being respected. The engine checks time every 2048 nodes.
- **Pieces disappear?** Check `ui.piece_map` — pieces are tracked by `(row, col)` key. Castling and en passant need special visual handling.

---

## 🚀 Creating a New Release

To build executables for all platforms and publish a release:

```bash
git tag v0.4
git push origin main --tags
```

This triggers the `build-release.yml` GitHub Actions workflow which automatically:
1. Compiles the C++ engine on Linux and Windows
2. Bundles everything into standalone executables with PyInstaller
3. Creates a GitHub Release with downloadable `.tar.gz` (Linux) and `.zip` (Windows) archives

Users can download from the [Releases page](https://github.com/AmoghShukla06/PythonChessEngine/releases).

---

## 📊 Engine Strength Estimate

**~1800–2000 Elo** (CCRL-like, 5s/move)

| Feature | Status |
|---|---|
| Alpha-Beta + Negamax | ✅ |
| Iterative Deepening (depth 1→12) | ✅ |
| Aspiration Windows | ✅ |
| Transposition Table | ✅ |
| Quiescence Search | ✅ |
| Null Move Pruning (R=2) | ✅ |
| Late Move Reductions | ✅ |
| Killer + History Heuristics | ✅ |
| MVV-LVA Move Ordering | ✅ |
| Piece-Square Tables (mid+end) | ✅ |
| Bitboard Move Generation | ✅ |
| Zobrist Hashing | ❌ (ad-hoc hash) |
| Pawn Structure Eval | ❌ |
| King Safety Eval | ❌ |
| PVS / SEE | ❌ |

With the missing features implemented, the engine could reach **2200+ Elo**.

---

## 📜 License

This project is open source. Contributions welcome!
