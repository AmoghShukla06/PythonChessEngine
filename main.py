# main.py
import sys
import platform

# --- Windows High-DPI fix (must be called BEFORE any tkinter/turtle imports) ---
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import turtle
import time
from chess_engine_wrapper import ChessEngine, AlphaBetaEngine
from ui import ChessUI
from resource_path import resource_path

# --- SETUP ---
screen = turtle.Screen()
screen.setup(1100, 900)  # Wider to accommodate captured pieces panel
screen.title("Chess: Human vs AI [Alpha-Beta]")
screen.bgcolor("#1a1a2e")  # Dark background fills entire window
screen.bgpic(resource_path("background.gif"))
screen.tracer(0)

# Make window smoothly resizable (cross-platform: Linux + Windows)
canvas = screen.getcanvas()
root = canvas.winfo_toplevel()
root.resizable(True, True)
root.minsize(800, 700)

# Make canvas expand to fill the window when resized
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
canvas.grid(sticky="nsew")

engine = ChessEngine()
ui = ChessUI(screen)

# --- PRE-GAME MENUS ---
human_color = ui.show_start_menu()  # 'w' or 'b'
ai_color = "b" if human_color == "w" else "w"

chosen_depth = ui.show_depth_menu()  # 1-20
ai = AlphaBetaEngine(depth=chosen_depth, time_limit=99999.0)  # No time limit
screen.title("Chess: Human vs AI")

# If human is black, flip the board so black is at bottom
if human_color == "b":
    ui.flipped = True

ui.draw_board()
ui.init_pieces(engine.board)
ui.update_status(engine.turn)
screen.update()

selected = None
valid_moves = []
capture_moves = []

# Track captured pieces and last move
white_captured = []  # pieces white has captured (black piece codes like "bP")
black_captured = []  # pieces black has captured (white piece codes like "wP")
last_move = None     # (sr, sc, tr, tc) of the most recent move, for highlighting


def refresh_captured():
    ui.draw_captured_pieces(white_captured, black_captured)


# --- AI TURN HANDLER ---
def play_ai_turn():
    global last_move
    if engine.game_over:
        return

    screen.title("Chess - AI is thinking...")
    screen.update()

    # AI decides
    move = ai.get_best_move(engine)

    if move:
        sr, sc, tr, tc = move

        # Track captures
        target_piece = engine.board[tr][tc]
        is_en_passant = (engine.board[sr][sc][1] == "P" and
                         engine.en_passant == (tr, tc) and
                         target_piece == "--")

        if target_piece != "--":
            if ai_color == "w":
                white_captured.append(target_piece)
            else:
                black_captured.append(target_piece)
            ui.remove_piece(tr, tc)
        elif is_en_passant:
            ep_piece = engine.board[sr][tc]
            if ai_color == "w":
                white_captured.append(ep_piece)
            else:
                black_captured.append(ep_piece)
            ui.remove_piece(sr, tc)

        ui.move_piece(sr, sc, tr, tc)

        # Castling visuals
        if engine.board[sr][sc][1] == "K" and abs(tc - sc) == 2:
            if tc > sc:
                ui.move_piece(sr, 7, sr, 5)
            else:
                ui.move_piece(sr, 0, sr, 3)

        # Promotion (AI always queens)
        if engine.board[sr][sc][1] == "P" and (tr == 0 or tr == 7):
            promo_color = "b" if ai_color == "b" else "w"
            ui.promote_piece_visual(tr, tc, f"{promo_color}Q")
            engine.make_move(sr, sc, tr, tc, promoted_piece="Q")
        else:
            engine.make_move(sr, sc, tr, tc)

        ai.record_move((sr, sc, tr, tc))

        # Highlight the AI's last move
        last_move = (sr, sc, tr, tc)
        ui.highlight_last_move(sr, sc, tr, tc)

        refresh_captured()
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.title("Chess: Human vs AI")
        screen.update()
    else:
        print("AI has no legal moves (Stalemate/Checkmate)")


# --- HUMAN CLICK HANDLER ---
def on_click(x, y):
    global selected, valid_moves, capture_moves, last_move

    # Disable clicks if it's AI's turn or game over
    if engine.game_over or engine.turn != human_color:
        return

    r, c = ui.screen_to_board(x, y)

    # Click outside board
    if r is None or c is None:
        selected = None
        ui.clear_highlights()
        return

    human_prefix = human_color

    # 1. SELECT A PIECE
    if selected is None:
        if engine.board[r][c].startswith(human_prefix):
            selected = (r, c)
            valid_moves, capture_moves = engine.legal_moves(r, c)

            ui.highlight(r, c, "yellow")
            for (mr, mc) in valid_moves:
                ui.highlight(mr, mc, "green")
            for (cr, cc) in capture_moves:
                ui.highlight(cr, cc, "red")
        return

    # 2. MOVE THE PIECE
    else:
        sr, sc = selected

        # Deselect if same square or invalid
        if (r, c) == (sr, sc) or ((r, c) not in valid_moves and (r, c) not in capture_moves):
            selected = None
            valid_moves = []
            capture_moves = []
            ui.clear_highlights()
            if engine.board[r][c].startswith(human_prefix):
                on_click(x, y)
            return

        # Track captures
        target_piece = engine.board[r][c]
        is_en_passant = (engine.board[sr][sc][1] == "P" and
                         (r, c) == engine.en_passant and
                         target_piece == "--")

        if target_piece != "--":
            if human_color == "w":
                white_captured.append(target_piece)
            else:
                black_captured.append(target_piece)
            ui.remove_piece(r, c)
        elif is_en_passant:
            ep_piece = engine.board[sr][c]
            if human_color == "w":
                white_captured.append(ep_piece)
            else:
                black_captured.append(ep_piece)
            ui.remove_piece(sr, c)

        ui.move_piece(sr, sc, r, c)

        # Castling visuals
        if engine.board[sr][sc][1] == "K" and abs(c - sc) == 2:
            if c > sc:
                ui.move_piece(sr, 7, sr, 5)
            else:
                ui.move_piece(sr, 0, sr, 3)

        ui.clear_highlights()

        # Promotion check
        if engine.board[sr][sc][1] == "P" and (r == 0 or r == 7):
            promo_char = ui.get_promotion_choice(engine.turn)
            ui.promote_piece_visual(r, c, engine.turn + promo_char)
            engine.make_move(sr, sc, r, c, promoted_piece=promo_char)
        else:
            engine.make_move(sr, sc, r, c)

        ai.record_move((sr, sc, r, c))

        # Highlight human's last move
        last_move = (sr, sc, r, c)
        ui.highlight_last_move(sr, sc, r, c)

        # Reset selection state
        selected = None
        valid_moves = []
        capture_moves = []

        refresh_captured()
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.update()

        # Trigger AI
        if not engine.game_over and engine.turn == ai_color:
            screen.ontimer(play_ai_turn, 500)


# --- KEYBOARD BINDINGS ---
def on_flip():
    """Toggle board flip and redraw."""
    ui.flip_board(engine.board)
    if last_move:
        ui.redraw_last_move(*last_move)
    refresh_captured()
    ui.update_status(engine.turn, engine.game_over, engine.winner)
    screen.update()


screen.listen()
screen.onkey(on_flip, "f")
screen.onclick(on_click)

# If human chose black, AI plays first as white
if human_color == "b":
    screen.ontimer(play_ai_turn, 1000)

turtle.done()