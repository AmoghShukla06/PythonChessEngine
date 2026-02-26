import time
from chess_engine_wrapper import ChessEngine, AlphaBetaEngine

def main():
    engine = ChessEngine()
    ai = AlphaBetaEngine(depth=8, time_limit=15.0)
    
    print("Testing Bitboard AI Init...")
    start_time = time.time()
    
    # Bypass opening book
    best_move = ai._cpp_engine.get_best_move(engine)
    
    end_time = time.time()
    print(f"Time Taken: {end_time - start_time:.4f} seconds")
    print(f"Best Move: {best_move}")

if __name__ == "__main__":
    main()
