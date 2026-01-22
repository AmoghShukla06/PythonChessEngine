# main.py
import turtle
from engine import ChessEngine
from ui import ChessUI

# ---------------- SCREEN ----------------
screen = turtle.Screen()
screen.setup(900, 900)
screen.title("Chess")
screen.bgcolor("#8B4513")
screen.tracer(0)

# ---------------- ENGINE / UI ----------------
engine = ChessEngine()
ui = ChessUI(screen)
ui.draw_board()
ui.init_pieces(engine.board)
ui.update_status(engine.turn)
screen.update()

# ---------------- STATE ----------------
selected = None
valid_moves = []
capture_moves = []

# ---------------- HELPERS ----------------
def screen_to_board(x, y):
    c = int((x + 4*90) // 90)
    r = int((4*90 - y) // 90)
    return (r, c) if 0 <= r < 8 and 0 <= c < 8 else (None, None)

# ---------------- CLICK HANDLER ----------------
def on_click(x, y):
    global selected, valid_moves, capture_moves
    
    if engine.game_over:
        return
    
    r, c = screen_to_board(x, y)
    if r is None:
        return
    
    # ---------------- EXECUTE MOVE ----------------
    if selected and (r, c) in valid_moves + capture_moves:
        sr, sc = selected
        moving_piece = engine.board[sr][sc]
        is_castling = moving_piece[1] == "K" and abs(c - sc) == 2
        
        # Check for Promotion (Pawn reaches end of board)
        promotion_choice = None
        if moving_piece[1] == "P" and (r == 0 or r == 7):
            # Ask User for Choice via UI Pop-up
            promotion_choice = ui.get_promotion_choice(engine.turn)

        # --- 1. VISUAL UPDATE ---
        if is_castling:
            ui.move_piece(sr, sc, r, c)
            if c > sc: # Kingside
                ui.move_piece(r, 7, r, 5)
            else: # Queenside
                ui.move_piece(r, 0, r, 3)
        else:
            target_piece = engine.board[r][c]
            
            # Standard Capture Visuals
            if target_piece != "--":
                ui.remove_piece(r, c)
            # En Passant Capture Visuals
            elif moving_piece[1] == "P" and engine.en_passant == (r, c):
                ui.remove_piece(sr, c) # Remove the pawn "behind" the move
            
            ui.move_piece(sr, sc, r, c)
            
            # Promotion Visual Update (Swap Pawn for new piece)
            if promotion_choice:
                ui.promote_piece_visual(r, c, engine.turn + promotion_choice)

        # --- 2. ENGINE UPDATE ---
        engine.make_move(sr, sc, r, c, promoted_piece=promotion_choice)

        ui.clear_highlights()
        selected = None
        valid_moves = []
        capture_moves = []
        
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.update()
        return
    
    # ---------------- SELECT PIECE ----------------
    if engine.board[r][c] != "--" and engine.board[r][c][0] == engine.turn:
        ui.clear_highlights()
        selected = (r, c)
        valid_moves, capture_moves = engine.legal_moves(r, c)
        for m in valid_moves:
            ui.highlight(*m, "green")
        for m in capture_moves:
            ui.highlight(*m, "yellow")
        screen.update()

# ---------------- RUN ----------------
print("Chess game started.")
screen.onclick(on_click)
turtle.done()