# main.py
import sys
import turtle
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
raw_canvas = canvas._canvas if hasattr(canvas, "_canvas") else canvas
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
ui.draw_game_buttons()  # Add buttons
ui.draw_captured_pieces([], [])
ui.draw_game_buttons()
ui.update_status(engine.turn)
screen.update()

selected = None
valid_moves = []
capture_moves = []

# Track captured pieces and last move
white_captured = []  # pieces white has captured (black piece codes like "bP")
black_captured = []  # pieces black has captured (white piece codes like "wP")
last_move = None     # (sr, sc, tr, tc) of the most recent move, for highlighting
piece_drag = {"candidate": None, "start_xy": None, "active": False}
suppress_next_left_click = False


def refresh_captured():
    ui.draw_captured_pieces(white_captured, black_captured)
    # Keep action buttons above the captured panel redraw.
    ui.draw_game_buttons()


def canvas_event_to_screen(event):
    """Convert tkinter canvas event coordinates to turtle coordinates."""
    canvas_w = raw_canvas.winfo_width()
    canvas_h = raw_canvas.winfo_height()
    x = raw_canvas.canvasx(event.x) - canvas_w / 2
    y = canvas_h / 2 - raw_canvas.canvasy(event.y)
    return x, y


def reset_piece_drag():
    piece_drag["candidate"] = None
    piece_drag["start_xy"] = None
    piece_drag["active"] = False


def select_piece(r, c):
    """Select a human piece and show legal targets."""
    global selected, valid_moves, capture_moves
    selected = (r, c)
    valid_moves, capture_moves = engine.legal_moves(r, c)

    ui.clear_highlights()
    ui.highlight(r, c, "yellow")
    for (mr, mc) in valid_moves:
        ui.highlight(mr, mc, "green")
    for (cr, cc) in capture_moves:
        ui.highlight(cr, cc, "red")


def on_left_press(event):
    if engine.game_over or engine.turn != human_color:
        return

    x, y = canvas_event_to_screen(event)
    r, c = ui.screen_to_board(x, y)
    if r is None or c is None:
        return

    # Start drag from currently selected piece or select a new human piece.
    if selected == (r, c):
        piece_drag["candidate"] = (r, c)
        piece_drag["start_xy"] = (x, y)
        piece_drag["active"] = False
        return

    if engine.board[r][c].startswith(human_color):
        piece_drag["candidate"] = (r, c)
        piece_drag["start_xy"] = (x, y)
        piece_drag["active"] = False


def on_left_motion(event):
    candidate = piece_drag["candidate"]
    if candidate is None:
        return

    x, y = canvas_event_to_screen(event)
    sx, sy = piece_drag["start_xy"] if piece_drag["start_xy"] else (x, y)

    if not piece_drag["active"]:
        if abs(x - sx) + abs(y - sy) < 6:
            return
        cr, cc = candidate
        if selected != (cr, cc):
            select_piece(cr, cc)
        if not ui.begin_piece_drag(cr, cc):
            reset_piece_drag()
            return
        piece_drag["active"] = True

    ui.drag_piece_to(x, y)
    screen.update()
    return "break"


def perform_human_move(sr, sc, r, c):
    """Execute a validated human move and run shared post-move UI updates."""
    global selected, valid_moves, capture_moves, last_move

    # Track captures
    target_piece = engine.board[r][c]
    is_en_passant = (engine.board[sr][sc][1] == "P" and
                     (r, c) == engine.en_passant and
                     target_piece == "--")

    capture_made = False
    if target_piece != "--":
        if human_color == "w":
            white_captured.append(target_piece)
        else:
            black_captured.append(target_piece)
        ui.remove_piece(r, c)
        capture_made = True
    elif is_en_passant:
        ep_piece = engine.board[sr][c]
        if human_color == "w":
            white_captured.append(ep_piece)
        else:
            black_captured.append(ep_piece)
        ui.remove_piece(sr, c)
        capture_made = True

    ui.end_piece_drag()
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

    if capture_made:
        refresh_captured()
    ui.update_status(engine.turn, engine.game_over, engine.winner)
    screen.update()

    # If game is over after human's move, show end-game menu
    if engine.game_over:
        screen.ontimer(show_end_game_menu, 500)
    # Trigger AI
    elif engine.turn == ai_color:
        screen.ontimer(play_ai_turn, 500)


def on_left_release(event):
    global suppress_next_left_click
    if not piece_drag["active"]:
        reset_piece_drag()
        return

    suppress_next_left_click = True

    x, y = canvas_event_to_screen(event)
    r, c = ui.screen_to_board(x, y)
    sr, sc = piece_drag["candidate"]

    if (r is None or c is None or
            (r, c) == (sr, sc) or
            ((r, c) not in valid_moves and (r, c) not in capture_moves)):
        ui.cancel_piece_drag()
        screen.update()
        reset_piece_drag()
        return "break"

    ui.end_piece_drag()
    perform_human_move(sr, sc, r, c)
    reset_piece_drag()
    return "break"


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
        capture_made = False
        is_en_passant = (engine.board[sr][sc][1] == "P" and
                         engine.en_passant == (tr, tc) and
                         target_piece == "--")

        if target_piece != "--":
            if ai_color == "w":
                white_captured.append(target_piece)
            else:
                black_captured.append(target_piece)
            ui.remove_piece(tr, tc)
            capture_made = True
        elif is_en_passant:
            ep_piece = engine.board[sr][tc]
            if ai_color == "w":
                white_captured.append(ep_piece)
            else:
                black_captured.append(ep_piece)
            ui.remove_piece(sr, tc)
            capture_made = True

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

        if capture_made:
            refresh_captured()
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.title("Chess: Human vs AI")
        screen.update()
        
        # If game is over after AI's move, show end-game menu
        if engine.game_over:
            screen.ontimer(show_end_game_menu, 500)
    else:
        print("AI has no legal moves (Stalemate/Checkmate)")



# --- HUMAN CLICK HANDLER ---
def on_click(x, y):
    global selected, valid_moves, capture_moves, suppress_next_left_click

    if suppress_next_left_click:
        suppress_next_left_click = False
        return

    # Check for button clicks first
    button_clicked = ui.check_button_click(x, y)
    if button_clicked == "resign":
        on_resign()
        return
    elif button_clicked == "quit":
        on_quit()
        return

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
            select_piece(r, c)
        return

    # 2. MOVE THE PIECE
    else:
        sr, sc = selected

        if (r, c) == (sr, sc):
            selected = None
            valid_moves = []
            capture_moves = []
            ui.clear_highlights()
            return

        if (r, c) not in valid_moves and (r, c) not in capture_moves:
            if engine.board[r][c].startswith(human_prefix):
                select_piece(r, c)
            else:
                selected = None
                valid_moves = []
                capture_moves = []
                ui.clear_highlights()
            return

        perform_human_move(sr, sc, r, c)


# --- KEYBOARD BINDINGS ---
def on_flip():
    """Toggle board flip and redraw."""
    ui.flip_board(engine.board)
    if last_move:
        ui.redraw_last_move(*last_move)
    refresh_captured()
    ui.update_status(engine.turn, engine.game_over, engine.winner)
    screen.update()


def on_clear_annotations():
    ui.clear_highlights()
    screen.update()


def on_resign():
    """Handle resign request."""
    if engine.game_over or engine.turn != human_color:
        return
    
    if ui.show_resign_menu():
        # Player resigned - mark as game over
        engine.game_over = True
        engine.winner = ai_color  # AI wins by resignation
        ui.update_status(engine.turn, engine.game_over, engine.winner)
        screen.update()
        show_end_game_menu()


def on_quit():
    """Quit the game immediately."""
    # Exit the game
    import sys
    sys.exit(0)


def show_end_game_menu():
    """Show end-game menu and handle play again or exit."""
    action = ui.show_end_menu(engine.game_over, engine.winner)
    
    if action == "play_again":
        restart_game()
    else:
        import sys
        sys.exit(0)


def restart_game():
    """Restart the game with new parameters."""
    global selected, valid_moves, capture_moves, last_move, human_color, ai_color, engine, ai
    global white_captured, black_captured, piece_drag, suppress_next_left_click
    
    # Reset variables
    selected = None
    valid_moves = []
    capture_moves = []
    last_move = None
    white_captured = []
    black_captured = []
    piece_drag = {"candidate": None, "start_xy": None, "active": False}
    suppress_next_left_click = False

    # Clear visual artifacts from the previous game without resetting bindings.
    ui.end_piece_drag()
    ui.clear_highlights()
    ui.clear_last_move_highlights()
    ui.clear_captured_display()
    ui.clear_game_buttons()
    ui.init_pieces([["--"] * 8 for _ in range(8)])
    
    # Show menus again
    human_color = ui.show_start_menu()
    ai_color = "b" if human_color == "w" else "w"
    chosen_depth = ui.show_depth_menu()
    
    # Reinitialize engine and AI
    engine = ChessEngine()
    ai = AlphaBetaEngine(depth=chosen_depth, time_limit=99999.0)
    
    # Flip board if needed
    ui.flipped = human_color == "b"
    
    # Draw new game
    ui.draw_board()
    ui.init_pieces(engine.board)
    ui.draw_game_buttons()  # Add buttons
    refresh_captured()
    ui.update_status(engine.turn)
    screen.update()
    
    # If human is black, AI plays first
    if human_color == "b":
        screen.ontimer(play_ai_turn, 1000)


screen.listen()
screen.onkey(on_flip, "f")
screen.onkey(on_clear_annotations, "c")
screen.onkey(on_clear_annotations, "C")
screen.onkey(on_resign, "r")
screen.onclick(on_click)
raw_canvas.bind("<ButtonPress-1>", on_left_press, add="+")
raw_canvas.bind("<B1-Motion>", on_left_motion, add="+")
raw_canvas.bind("<ButtonRelease-1>", on_left_release, add="+")

# If human chose black, AI plays first as white
if human_color == "b":
    screen.ontimer(play_ai_turn, 1000)

turtle.done()
