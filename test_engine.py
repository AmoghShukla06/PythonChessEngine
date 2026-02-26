from chess_engine_wrapper import ChessEngine

def print_board(board):
    for r in board:
        print(" ".join(r))
    print()

def main():
    engine = ChessEngine()
    print("Initial Board:")
    print_board(engine.board)
    
    print("Legal Moves for E2 pawn:")
    moves, caps = engine.legal_moves(6, 4)
    print("Moves:", moves)
    print("Captures:", caps)

    print("Making move e2e4...")
    engine.make_move(6, 4, 4, 4)
    print_board(engine.board)
    
    print("Legal Moves for E7 pawn:")
    moves, caps = engine.legal_moves(1, 4)
    print("Moves:", moves)
    
    # testing fast move
    print("Testing make_move D7D5...")
    engine.make_move(1, 3, 3, 3)
    print_board(engine.board)

if __name__ == "__main__":
    main()
