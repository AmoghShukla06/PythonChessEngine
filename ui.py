# ui.py
import turtle
from resource_path import resource_path

SQUARE = 90

# Piece value ordering for display: Q, R, B, N, P
PIECE_ORDER = {'Q': 0, 'R': 1, 'B': 2, 'N': 3, 'P': 4}

class ChessUI:
    def __init__(self, screen):
        self.screen = screen
        self.drawer = turtle.Turtle()
        self.drawer.hideturtle()
        self.drawer.speed(0)
        self.piece_map = {}
        self.highlights = []
        self.last_move_highlights = []
        self.captured_turtles = []
        self.status_text = None
        self.flipped = False
        self.load_shapes()
        self.setup_status_display()

    def load_shapes(self):
        for p in ["wP","wR","wN","wB","wQ","wK","bP","bR","bN","bB","bQ","bK"]:
            try:
                self.screen.addshape(resource_path(f"pieces/{p}.gif"))
            except:
                print(f"Warning: Could not load pieces/{p}.gif")

    def setup_status_display(self):
        self.status_text = turtle.Turtle()
        self.status_text.hideturtle()
        self.status_text.penup()
        self.status_text.goto(0, 400)
        self.status_text.color("white")

    def update_status(self, turn, game_over=False, winner=None):
        self.status_text.clear()
        if game_over:
            if winner == "draw":
                text = "GAME OVER - STALEMATE (DRAW)"
                self.status_text.color("yellow")
            elif winner == "w":
                text = "CHECKMATE - WHITE WINS!"
                self.status_text.color("lightgreen")
            else:
                text = "CHECKMATE - BLACK WINS!"
                self.status_text.color("lightgreen")
        else:
            if turn == "w":
                text = "White's Turn"
                self.status_text.color("white")
            else:
                text = "Black's Turn"
                self.status_text.color("lightgray")

        self.status_text.write(text, align="center", font=("Arial", 24, "bold"))

    # --- Coordinate mapping (flipping-aware) ---

    def board_to_screen(self, r, c):
        """Convert board (row, col) to screen (x, y) for the top-left corner of the square."""
        if self.flipped:
            # row 7 at top, col 7 at left
            return -4 * SQUARE + (7 - c) * SQUARE, 4 * SQUARE - (7 - r) * SQUARE
        else:
            return -4 * SQUARE + c * SQUARE, 4 * SQUARE - r * SQUARE

    def screen_to_board(self, x, y):
        """Convert screen (x, y) to board (row, col), respecting flip."""
        if self.flipped:
            c = 7 - int((x + 4 * SQUARE) // SQUARE)
            r = 7 - int((4 * SQUARE - y) // SQUARE)
        else:
            c = int((x + 4 * SQUARE) // SQUARE)
            r = int((4 * SQUARE - y) // SQUARE)
        return (r, c) if 0 <= r < 8 and 0 <= c < 8 else (None, None)

    # --- Board flip ---

    def flip_board(self, board):
        """Toggle the flipped flag and redraw everything."""
        self.flipped = not self.flipped
        self.draw_board()
        self._redraw_pieces(board)

    def _redraw_pieces(self, board):
        """Reposition all existing piece turtles to match current flip state."""
        for (r, c), t in self.piece_map.items():
            x, y = self.board_to_screen(r, c)
            t.goto(x + SQUARE / 2, y - SQUARE / 2)

    # --- Drawing ---

    def draw_board(self):
        colors = ["white", "gray"]
        self.drawer.clear()
        for r in range(8):
            for c in range(8):
                self.drawer.penup()
                self.drawer.goto(*self.board_to_screen(r, c))
                self.drawer.fillcolor(colors[(r + c) % 2])
                self.drawer.begin_fill()
                for _ in range(4):
                    self.drawer.forward(SQUARE)
                    self.drawer.right(90)
                self.drawer.end_fill()

    def init_pieces(self, board):
        for (r, c), t in self.piece_map.items():
            t.hideturtle()
        self.piece_map.clear()
        for r in range(8):
            for c in range(8):
                if board[r][c] != "--":
                    t = turtle.Turtle()
                    t.penup()
                    t.shape(resource_path(f"pieces/{board[r][c]}.gif"))
                    x, y = self.board_to_screen(r, c)
                    t.goto(x + SQUARE / 2, y - SQUARE / 2)
                    t.showturtle()
                    self.piece_map[(r, c)] = t

    def move_piece(self, sr, sc, tr, tc):
        if (sr, sc) in self.piece_map:
            t = self.piece_map[(sr, sc)]
            x, y = self.board_to_screen(tr, tc)
            t.goto(x + SQUARE / 2, y - SQUARE / 2)
            t.showturtle()
            self.piece_map[(tr, tc)] = t
            del self.piece_map[(sr, sc)]

    def remove_piece(self, r, c):
        if (r, c) in self.piece_map:
            self.piece_map[(r, c)].hideturtle()
            del self.piece_map[(r, c)]

    def promote_piece_visual(self, r, c, new_piece_code):
        """Removes the pawn and places the new promoted piece sprite."""
        self.remove_piece(r, c)
        t = turtle.Turtle()
        t.penup()
        t.shape(resource_path(f"pieces/{new_piece_code}.gif"))
        x, y = self.board_to_screen(r, c)
        t.goto(x + SQUARE / 2, y - SQUARE / 2)
        t.showturtle()
        self.piece_map[(r, c)] = t

    def get_promotion_choice(self, turn_color):
        """Pop-up dialog to ask user for promotion choice."""
        prompt = f"{'White' if turn_color == 'w' else 'Black'} Promotion"
        choice = self.screen.textinput(prompt, "Promote to (Q, R, B, N):")
        if choice:
            choice = choice.upper()
            if choice in ['Q', 'R', 'B', 'N']:
                return choice
        return 'Q'

    # --- Selection highlights ---

    def clear_highlights(self):
        for h in self.highlights:
            h.clear()
            h.hideturtle()
        self.highlights.clear()

    def highlight(self, r, c, color):
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        h.goto(*self.board_to_screen(r, c))
        h.pensize(4)
        h.pencolor(color)
        h.pendown()
        for _ in range(4):
            h.forward(SQUARE)
            h.right(90)
        h.penup()
        self.highlights.append(h)

    # --- Last-move highlighting ---

    def clear_last_move_highlights(self):
        for h in self.last_move_highlights:
            h.clear()
            h.hideturtle()
        self.last_move_highlights.clear()

    def highlight_last_move(self, sr, sc, tr, tc):
        """Highlight both the source and destination squares of the last move."""
        self.clear_last_move_highlights()
        for (r, c) in [(sr, sc), (tr, tc)]:
            h = turtle.Turtle()
            h.penup()
            h.speed(0)
            h.hideturtle()
            sx, sy = self.board_to_screen(r, c)
            # Draw a thick border outline (not filled, so pieces stay visible)
            h.goto(sx + 3, sy - 3)  # inset slightly so border is inside the square
            h.pencolor("#4488ff")
            h.pensize(5)
            h.pendown()
            side = SQUARE - 6
            for _ in range(4):
                h.forward(side)
                h.right(90)
            h.penup()
            self.last_move_highlights.append(h)

    def redraw_last_move(self, sr, sc, tr, tc):
        """Re-highlight last move squares (e.g. after a board flip)."""
        if sr is not None:
            self.highlight_last_move(sr, sc, tr, tc)

    # --- Captured pieces display ---

    def clear_captured_display(self):
        for t in self.captured_turtles:
            t.clear()
            t.hideturtle()
        self.captured_turtles.clear()

    def draw_captured_pieces(self, white_captured, black_captured):
        """
        Draw captured pieces along the side of the board.
        white_captured = pieces that WHITE has captured (black pieces).
        black_captured = pieces that BLACK has captured (white pieces).

        Displayed on the right side of the board, grouped by capturer.
        """
        self.clear_captured_display()

        # Sort by piece value (Q first, P last)
        def sort_key(piece_code):
            return PIECE_ORDER.get(piece_code[1], 5)

        # Right edge of the board
        panel_x = 4 * SQUARE + 15

        # White's captures (black pieces taken by white) — shown at bottom-right
        # Black's captures (white pieces taken by black) — shown at top-right
        if self.flipped:
            white_y_start = 4 * SQUARE - 30
            black_y_start = -4 * SQUARE + 30
            white_dir = -1
            black_dir = 1
        else:
            white_y_start = -4 * SQUARE + 30
            black_y_start = 4 * SQUARE - 30
            white_dir = 1
            black_dir = -1

        # Draw label + pieces for white's captures
        self._draw_capture_group(sorted(white_captured, key=sort_key),
                                 panel_x, white_y_start, white_dir, "White captured:")

        # Draw label + pieces for black's captures
        self._draw_capture_group(sorted(black_captured, key=sort_key),
                                 panel_x, black_y_start, black_dir, "Black captured:")

    def _draw_capture_group(self, pieces, x, y_start, y_dir, label):
        """Draw a group of captured pieces as text labels."""
        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        t.goto(x, y_start)
        t.color("white")
        t.write(label, align="left", font=("Arial", 11, "bold"))
        self.captured_turtles.append(t)

        # Map piece codes to nice unicode symbols
        symbols = {
            'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
            'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟',
        }

        # Render pieces in a compact row, wrapping after 8
        col = 0
        row = 0
        for piece in pieces:
            sym = symbols.get(piece, '?')
            pt = turtle.Turtle()
            pt.hideturtle()
            pt.penup()
            px = x + col * 22
            py = y_start + y_dir * (25 + row * 25)
            pt.goto(px, py)
            # Color-code: white pieces in white, black pieces in gold
            if piece.startswith('w'):
                pt.color("white")
            else:
                pt.color("#D4A843")
            pt.write(sym, align="left", font=("Arial", 18, "normal"))
            self.captured_turtles.append(pt)
            col += 1
            if col >= 8:
                col = 0
                row += 1

    # --- Start menu ---

    def show_start_menu(self):
        """Graphical popup with buttons to choose White or Black. Returns 'w' or 'b'."""
        result = {'color': None}

        # Semi-transparent overlay
        overlay = turtle.Turtle()
        overlay.hideturtle()
        overlay.speed(0)
        overlay.penup()
        overlay.goto(-200, 120)
        overlay.color("#1a1a2e")
        overlay.fillcolor("#1a1a2e")
        overlay.begin_fill()
        for s in [400, 200, 400, 200]:
            overlay.forward(s)
            overlay.right(90)
        overlay.end_fill()

        # Border
        overlay.goto(-200, 120)
        overlay.pensize(3)
        overlay.pencolor("#4488ff")
        overlay.pendown()
        for s in [400, 200, 400, 200]:
            overlay.forward(s)
            overlay.right(90)
        overlay.penup()

        # Title text
        title_t = turtle.Turtle()
        title_t.hideturtle()
        title_t.penup()
        title_t.goto(0, 75)
        title_t.color("white")
        title_t.write("Choose Your Side", align="center", font=("Arial", 22, "bold"))

        # --- White button ---
        btn_w = turtle.Turtle()
        btn_w.shape("square")
        btn_w.shapesize(2.2, 5.5)
        btn_w.color("#e8e8e8")
        btn_w.penup()
        btn_w.goto(-80, 10)

        lbl_w = turtle.Turtle()
        lbl_w.hideturtle()
        lbl_w.penup()
        lbl_w.goto(-80, 0)
        lbl_w.color("#1a1a2e")
        lbl_w.write("♔ White", align="center", font=("Arial", 16, "bold"))

        # --- Black button ---
        btn_b = turtle.Turtle()
        btn_b.shape("square")
        btn_b.shapesize(2.2, 5.5)
        btn_b.color("#333333")
        btn_b.penup()
        btn_b.goto(80, 10)

        lbl_b = turtle.Turtle()
        lbl_b.hideturtle()
        lbl_b.penup()
        lbl_b.goto(80, 0)
        lbl_b.color("white")
        lbl_b.write("♚ Black", align="center", font=("Arial", 16, "bold"))

        self.screen.update()

        def pick_white(x, y):
            result['color'] = 'w'
        def pick_black(x, y):
            result['color'] = 'b'

        btn_w.onclick(pick_white)
        btn_b.onclick(pick_black)

        # Wait for a click
        while result['color'] is None:
            self.screen.update()
            import time
            time.sleep(0.05)

        # Clean up popup
        for t in [overlay, title_t, btn_w, lbl_w, btn_b, lbl_b]:
            t.clear()
            t.hideturtle()

        self.screen.update()
        return result['color']