
# Hybrid Bitboard Chess Engine

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

### 🍎 macOS
1. Go to the [**Releases page**](https://github.com/AmoghShukla06/PythonChessEngine/releases/latest)
2. Download **`ChessEngine-macos-x86_64.zip`**
3. Extract and open the **`ChessEngine`** app
4. If macOS blocks it: right-click → Open → confirm

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

## 🧠 How it Works

The architecture is split into two primary components to maximize both usability and performance:

1. **Python UI & Orchestrator:**
   * Uses the Python `turtle` module to draw the board, pieces, and handle user clicks.
   * `main.py` handles the game loop, checking for game over conditions, and interfacing between the human player and the AI.

2. **C++ Bitboard Engine (`chess_engine.cpp` & `ai_engine.cpp`):**
   * **Bitboards:** The board state is represented using sets of 64-bit integers (`U64`), allowing for hyper-efficient $O(1)$ piece lookups and move validations using bitwise operators (`&`, `|`, `^`, `~`).
   * **Move Generation:** Utilizes pre-calculated attack masks instead of slow array manipulation.
   * **AI Search Algorithm:** Uses **Alpha-Beta Pruning** overlaid with **Quiescence Search** (to stabilize tactical skirmishes). 
   * **Advanced Heuristics:** Includes **Transposition Tables (Zobrist Hashing)**, **Killer Move heuristic**, **History heuristic**, **Null Move Pruning (NMP)**, and **Late Move Reductions (LMR)**.
   * Compiles into a dynamic library (`.so` on Unix, `.pyd` on Windows) that Python imports natively as `chess_engine_cpp`.

Currently, this engine evaluates positions at a theoretical **1.5+ Million Nodes Per Second (NPS)** on a single thread and easily reaches Depth 10+ in complex middlegames.

---

## 🔧 Build From Source (For Developers)

If you want to modify the engine or build the executable yourself:

### Prerequisites

* **Python 3.8+** installed
* A **C++17 Compiler** (`g++` or `clang++` for Linux/Mac, `MinGW` or `MSVC` for Windows)
* The `pybind11` Python package

### Quick Build (Automatic)

The build script handles compilation + packaging into a standalone executable:

```bash
pip install pybind11 pyinstaller
python build_exe.py
```

The executable will be created in `dist/ChessEngine/`.

### Manual Build

#### 1. Setup Your Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install pybind11
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install pybind11
```

#### 2. Compile the C++ Engine

**Linux / macOS (using g++ or clang++):**
```bash
g++ -O3 -Wall -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) bitboard.cpp chess_engine.cpp -o chess_engine_cpp$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
```

**Windows (using MinGW / g++):**
```cmd
g++ -O3 -Wall -shared -std=c++17 -fPIC -I"%VIRTUAL_ENV%\Include" %VIRTUAL_ENV%\Scripts\python.exe -m pybind11 --includes bitboard.cpp chess_engine.cpp -o chess_engine_cpp.pyd
```

#### 3. Play the Game!

**Windows:**
```cmd
python main.py
```

**Linux / macOS:**
```bash
python3 main.py
```

### 🎮 Playing Instructions
- The game will launch a window treating you as White. 
- Click on a piece to select it (it will become highlighted).
- Click on a valid square to move it.
- As soon as your move executes, the C++ AI will start calculating. You can check your terminal to see real-time updates of the AI's search depth, evaluation score, nodes searched, and search time!

---

## 🚀 Creating a New Release (For Maintainers)

To build executables for all platforms and publish a release:

```bash
git tag v1.0
git push origin v1.0
```

This triggers GitHub Actions to automatically build Windows/macOS/Linux executables and attach them to a GitHub Release. Users can then download from the [Releases page](https://github.com/AmoghShukla06/PythonChessEngine/releases).

