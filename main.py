# main.py
import turtle
import time
from chess_engine_wrapper import ChessEngine, AlphaBetaEngine
from ui import ChessUI
from resource_path import resource_path

# --- SETUP ---
screen = turtle.Screen()
screen.setup(900,900)
screen.title("Chess: Human (White) vs AI [Alpha-Beta | depth=5 | multi-core]")
#screen.bgcolor("#2C3E50") # Darker, more modern background
screen.bgpic(resource_path("background.gif"))
screen.tracer(0)

engine = ChessEngine()
ui = ChessUI(screen)
ai = AlphaBetaEngine(depth=12, time_limit=5.0)

ui.draw_board()
ui.init_pieces(engine.board)
ui.update_status(engine.turn)
screen.update()

selected = None
valid_moves = []
capture_moves = []

# --- AI TURN HANDLER ---
def play_ai_turn():
    if engine.game_over: return

    screen.title("Chess - AI is thinking [Alpha-Beta]...")
    screen.update()
    
    # 1. AI decides
    move = ai.get_best_move(engine)
    
    if move:
        sr, sc, tr, tc = move
        
        # 2. Visual Update
        target_piece = engine.board[tr][tc]
        if target_piece != "--":
            ui.remove_piece(tr, tc)
        elif engine.board[sr][sc][1] == "P" and engine.en_passant == (tr, tc):
            ui.remove_piece(sr, tc) # En Passant visual fix

        ui.move_piece(sr, sc, tr, tc)
        
        # Handling Castling Visuals for AI
        if engine.board[sr][sc][1] == "K" and abs(tc - sc) == 2:
            if tc > sc: ui.move_piece(sr, 7, sr, 5) # Kingside
            else: ui.move_piece(sr, 0, sr, 3) # Queenside

        # Handling Promotion for AI (Always Queen for now)
        if engine.board[sr][sc][1] == "P" and (tr == 0 or tr == 7):
             ui.promote_piece_visual(tr, tc, "bQ")
             engine.make_move(sr, sc, tr, tc, promoted_piece="Q")
        else:
             engine.make_move(sr, sc, tr, tc)

        ai.record_move((sr, sc, tr, tc))   # keep opening book in sync

        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.title("Chess: Human (White) vs AI [Alpha-Beta | depth=5 | multi-core]")
        screen.update()
    else:
        print("AI has no legal moves (Stalemate/Checkmate)")

# --- HUMAN CLICK HANDLER ---
def on_click(x, y):
    global selected, valid_moves, capture_moves
    
    # Disable clicks if it's AI's turn or game over
    if engine.game_over or engine.turn == "b":
        return
    
    r, c = screen_to_board(x, y)
    
    # Click outside board
    if r is None or c is None:
        selected = None
        ui.clear_highlights()
        return

    # 1. SELECT A PIECE
    if selected is None:
        if engine.board[r][c].startswith("w"):
            selected = (r, c)
            # Get legal moves for this piece
            valid_moves, capture_moves = engine.legal_moves(r, c)
            
            # Highlight Selected Square + Moves
            ui.highlight(r, c, "yellow")
            for (mr, mc) in valid_moves:
                ui.highlight(mr, mc, "green")
            for (cr, cc) in capture_moves:
                ui.highlight(cr, cc, "red")
        return

    # 2. MOVE THE PIECE
    else:
        sr, sc = selected
        
        # If clicked same square or invalid move, deselect
        if (r, c) == (sr, sc) or ((r, c) not in valid_moves and (r, c) not in capture_moves):
            selected = None
            valid_moves = []
            capture_moves = []
            ui.clear_highlights()
            # Allow re-selecting immediately if clicked another white piece
            if engine.board[r][c].startswith("w"):
                on_click(x, y) 
            return
        
        # Valid Move Detected
        # 2a. Visual Update
        target_piece = engine.board[r][c]
        if target_piece != "--":
            ui.remove_piece(r, c)
        # En Passant Visual
        elif engine.board[sr][sc][1] == "P" and (r, c) == engine.en_passant:
            ui.remove_piece(sr, c) # Remove pawn behind

        ui.move_piece(sr, sc, r, c)
        
        # Castling Visuals (Human)
        if engine.board[sr][sc][1] == "K" and abs(c - sc) == 2:
            if c > sc: ui.move_piece(sr, 7, sr, 5) # Kingside
            else: ui.move_piece(sr, 0, sr, 3) # Queenside

        ui.clear_highlights()

        # 2b. Engine Update
        # Promotion Check
        if engine.board[sr][sc][1] == "P" and (r == 0 or r == 7):
            promo_char = ui.get_promotion_choice(engine.turn)
            # Visual promote
            ui.promote_piece_visual(r, c, engine.turn + promo_char)
            engine.make_move(sr, sc, r, c, promoted_piece=promo_char)
        else:
            engine.make_move(sr, sc, r, c)

        ai.record_move((sr, sc, r, c))   # keep opening book in sync

        # 2c. Reset State
        selected = None
        valid_moves = []
        capture_moves = []
        
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.update()

        # 3. Trigger AI
        if not engine.game_over and engine.turn == "b":
            screen.ontimer(play_ai_turn, 500)

# --- HELPER (Copy from your main.py) ---
def screen_to_board(x, y):
    c = int((x + 4*90) // 90)
    r = int((4*90 - y) // 90)
    return (r, c) if 0 <= r < 8 and 0 <= c < 8 else (None, None)

screen.onclick(on_click)
turtle.done()