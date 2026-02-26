# Hybrid Bitboard Chess Engine

A high-performance Chess Engine built with a **Python** frontend and an ultra-fast **C++ Bitboard** backend. This project utilizes `turtle` for the graphical interface while delegating all the heavy lifting (search, move generation, and evaluation) to a highly optimized C++ engine bound to Python via `pybind11`.

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

## 🚀 How to Run the Project

Because the core engine is written in C++, you must compile it into a Python module before running the game.

### Prerequisites

* **Python 3.8+** installed.
* A **C++17 Compiler** (`g++` or `clang++` for Linux/Mac, `MinGW` or `MSVC` for Windows).
* The `pybind11` Python package.

### 1. Setup Your Environment

First, open your terminal/command prompt inside the `chess_engine` directory. We recommend using a virtual environment.

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

### 2. Compile the C++ Engine

You need to compile `bitboard.cpp` and `chess_engine.cpp` into a shared library that Python can load.

**Linux / macOS (using g++ or clang++):**
Compile the code using the following command in your bash terminal:
```bash
g++ -O3 -Wall -shared -std=c++17 -fPIC $(python3 -m pybind11 --includes) bitboard.cpp chess_engine.cpp -o chess_engine_cpp$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
```

**Windows (using MinGW / g++):**
Ensure `g++` is in your PATH, then run:
```cmd
g++ -O3 -Wall -shared -std=c++17 -fPIC -I"%VIRTUAL_ENV%\Include" %VIRTUAL_ENV%\Scripts\python.exe -m pybind11 --includes bitboard.cpp chess_engine.cpp -o chess_engine_cpp.pyd
```
*(Alternatively, you can just run `python -m pybind11 --includes` to grab the include paths and compile manually, ensuring the output file is named `chess_engine_cpp.pyd`)*.

### 3. Play the Game!

Once the C++ compilation is successful, you will see a newly generated `.so` or `.pyd` file in your main directory. Now, simply run the Python game loop:

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
