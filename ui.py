# ui.py
import turtle
from resource_path import resource_path

SQUARE = 90

# --- Color Palette ---
LIGHT_SQUARE = "#F5E6D0"   # light warm cream
DARK_SQUARE  = "#7D5A3C"   # dark warm brown
LAST_MOVE_LIGHT     = "#CDD16A"  # soft highlight on light squares
LAST_MOVE_DARK      = "#AAA23A"  # soft highlight on dark squares
COORD_LABEL_LIGHT   = "#7D5A3C"  # label on light square matches dark square
COORD_LABEL_DARK    = "#F5E6D0"  # label on dark square matches light square

# Piece value ordering for display: Q, R, B, N, P
PIECE_ORDER = {'Q': 0, 'R': 1, 'B': 2, 'N': 3, 'P': 4}

FILE_LABELS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANK_LABELS = ['8', '7', '6', '5', '4', '3', '2', '1']


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
        self.coord_turtles = []
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
        self.status_text.goto(0, 375)
        self.status_text.color("white")

    def update_status(self, turn, game_over=False, winner=None):
        self.status_text.clear()
        if game_over:
            # Re-create turtle so it renders on top of everything (fixes Windows visibility)
            self.status_text.hideturtle()
            self.status_text = turtle.Turtle()
            self.status_text.hideturtle()
            self.status_text.penup()
            self.status_text.goto(0, 375)

            if winner == "draw":
                text = "GAME OVER — STALEMATE (DRAW)"
                self.status_text.color("#FFD700")
            elif winner == "w":
                text = "CHECKMATE — WHITE WINS!"
                self.status_text.color("#7CFC00")
            else:
                text = "CHECKMATE — BLACK WINS!"
                self.status_text.color("#7CFC00")
        else:
            if turn == "w":
                text = "● White's Turn"
                self.status_text.color("#F0D9B5")
            else:
                text = "● Black's Turn"
                self.status_text.color("#C0C0C0")

        self.status_text.write(text, align="center", font=("Arial", 22, "bold"))

    # --- Coordinate mapping (flipping-aware) ---

    def board_to_screen(self, r, c):
        """Convert board (row, col) to screen (x, y) for the top-left corner of the square."""
        if self.flipped:
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

    def _square_color(self, r, c):
        """Return light or dark square color based on position."""
        return LIGHT_SQUARE if (r + c) % 2 == 0 else DARK_SQUARE

    # --- Board flip ---

    def flip_board(self, board):
        """Toggle the flipped flag and redraw everything."""
        self.flipped = not self.flipped
        self.draw_board()
        self.init_pieces(board)

    # --- Drawing ---

    def draw_board(self):
        self.drawer.clear()
        for r in range(8):
            for c in range(8):
                self.drawer.penup()
                self.drawer.goto(*self.board_to_screen(r, c))
                self.drawer.fillcolor(self._square_color(r, c))
                self.drawer.pencolor(self._square_color(r, c))
                self.drawer.begin_fill()
                for _ in range(4):
                    self.drawer.forward(SQUARE)
                    self.drawer.right(90)
                self.drawer.end_fill()
        # Draw coordinate labels on the board
        self._draw_coordinates()

    def _draw_coordinates(self):
        """Draw file (a-h) and rank (1-8) labels inside the edge squares."""
        for t in self.coord_turtles:
            t.clear()
            t.hideturtle()
        self.coord_turtles.clear()

        # File labels (a-h) along the bottom row
        for c in range(8):
            disp_c = (7 - c) if self.flipped else c
            r = 7  # bottom row of display
            disp_r = (7 - r) if self.flipped else r
            sx, sy = self.board_to_screen(disp_r, disp_c)
            color = COORD_LABEL_DARK if (disp_r + disp_c) % 2 != 0 else COORD_LABEL_LIGHT

            t = turtle.Turtle()
            t.hideturtle()
            t.penup()
            t.goto(sx + SQUARE - 8, sy - SQUARE + 4)
            t.color(color)
            t.write(FILE_LABELS[c], align="right", font=("Arial", 10, "bold"))
            self.coord_turtles.append(t)

        # Rank labels (1-8) along the left column
        for r in range(8):
            disp_r = (7 - r) if self.flipped else r
            c = 0  # left column of display
            disp_c = (7 - c) if self.flipped else c
            sx, sy = self.board_to_screen(disp_r, disp_c)
            color = COORD_LABEL_DARK if (disp_r + disp_c) % 2 != 0 else COORD_LABEL_LIGHT

            t = turtle.Turtle()
            t.hideturtle()
            t.penup()
            t.goto(sx + 4, sy - 14)
            t.color(color)
            t.write(RANK_LABELS[r], align="left", font=("Arial", 10, "bold"))
            self.coord_turtles.append(t)

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

    def _draw_border(self, r, c, color, width=5):
        """Draw a thick border around a square for highlighting."""
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        sx, sy = self.board_to_screen(r, c)
        inset = width // 2 + 1
        h.goto(sx + inset, sy - inset)
        h.pencolor(color)
        h.pensize(width)
        h.pendown()
        side = SQUARE - 2 * inset
        for _ in range(4):
            h.forward(side)
            h.right(90)
        h.penup()
        self.highlights.append(h)
        return h

    def _draw_dot(self, r, c, color):
        """Draw a small centered dot for available move indication."""
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        sx, sy = self.board_to_screen(r, c)
        h.goto(sx + SQUARE / 2, sy - SQUARE / 2 - 12)
        h.color(color)
        h.begin_fill()
        h.circle(12)
        h.end_fill()
        self.highlights.append(h)
        return h

    def _draw_capture_ring(self, r, c, color):
        """Draw a thick ring around a square for capture indication."""
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        sx, sy = self.board_to_screen(r, c)
        h.goto(sx + 4, sy - 4)
        h.pencolor(color)
        h.pensize(6)
        h.pendown()
        side = SQUARE - 8
        for _ in range(4):
            h.forward(side)
            h.right(90)
        h.penup()
        self.highlights.append(h)
        return h

    def highlight(self, r, c, color):
        """Highlight a square: yellow=selected, green=move, red=capture."""
        if color == "yellow":
            # Selected piece: thick yellow border (doesn't cover the piece)
            self._draw_border(r, c, "#E8D44D", width=5)
        elif color == "green":
            # Available move: subtle dot
            self._draw_dot(r, c, "gray")
        elif color == "red":
            # Capture: thick ring
            self._draw_capture_ring(r, c, "#CC3333")

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
            # Use tinted version of the square color
            color = LAST_MOVE_LIGHT if (r + c) % 2 == 0 else LAST_MOVE_DARK
            h = turtle.Turtle()
            h.penup()
            h.speed(0)
            h.hideturtle()
            sx, sy = self.board_to_screen(r, c)
            h.goto(sx, sy)
            h.fillcolor(color)
            h.pencolor(color)
            h.begin_fill()
            for _ in range(4):
                h.forward(SQUARE)
                h.right(90)
            h.end_fill()
            self.last_move_highlights.append(h)

            # Re-create piece at this square so it's on top of the tint
            if (r, c) in self.piece_map:
                old_t = self.piece_map[(r, c)]
                shape = old_t.shape()
                old_t.hideturtle()
                # Create a fresh turtle on top
                new_t = turtle.Turtle()
                new_t.penup()
                new_t.shape(shape)
                new_t.goto(sx + SQUARE / 2, sy - SQUARE / 2)
                new_t.showturtle()
                self.piece_map[(r, c)] = new_t

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
        Pieces are kept compact so they never overflow beyond the board area.
        """
        self.clear_captured_display()

        def sort_key(piece_code):
            return PIECE_ORDER.get(piece_code[1], 5)

        panel_x = 4 * SQUARE + 15
        board_top = 4 * SQUARE
        board_bottom = -4 * SQUARE

        if self.flipped:
            white_y_start = board_top - 30
            black_y_start = board_bottom + 30
            white_dir = -1
            black_dir = 1
        else:
            white_y_start = board_bottom + 30
            black_y_start = board_top - 30
            white_dir = 1
            black_dir = -1

        # Draw vertical separator line
        sep = turtle.Turtle()
        sep.hideturtle()
        sep.penup()
        sep.goto(panel_x - 8, board_top)
        sep.pencolor("#444466")
        sep.pensize(2)
        sep.pendown()
        sep.goto(panel_x - 8, board_bottom)
        sep.penup()
        self.captured_turtles.append(sep)

        self._draw_capture_group(sorted(white_captured, key=sort_key),
                                 panel_x, white_y_start, white_dir, "White captured:")
        self._draw_capture_group(sorted(black_captured, key=sort_key),
                                 panel_x, black_y_start, black_dir, "Black captured:")

    def _draw_capture_group(self, pieces, x, y_start, y_dir, label):
        """Draw a group of captured pieces as text labels, wrapping compactly."""
        COLS = 4
        SPACING_X = 22
        SPACING_Y = 22
        LABEL_GAP = 22

        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        t.goto(x, y_start)
        t.color("#AAAACC")
        t.write(label, align="left", font=("Arial", 11, "bold"))
        self.captured_turtles.append(t)

        symbols = {
            'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
            'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟',
        }

        col = 0
        row = 0
        for piece in pieces:
            sym = symbols.get(piece, '?')
            pt = turtle.Turtle()
            pt.hideturtle()
            pt.penup()
            px = x + col * SPACING_X
            py = y_start + y_dir * (LABEL_GAP + row * SPACING_Y)
            pt.goto(px, py)
            if piece.startswith('w'):
                pt.color("#E8E8E8")
            else:
                pt.color("#D4A843")
            pt.write(sym, align="left", font=("Arial", 16, "normal"))
            self.captured_turtles.append(pt)
            col += 1
            if col >= COLS:
                col = 0
                row += 1

    # --- Start menu ---

    def show_start_menu(self):
        """Graphical popup with buttons to choose White or Black. Returns 'w' or 'b'."""
        result = {'color': None}

        # Background overlay
        overlay = turtle.Turtle()
        overlay.hideturtle()
        overlay.speed(0)
        overlay.penup()
        overlay.goto(-220, 140)
        overlay.color("#0D0D1A")
        overlay.fillcolor("#0D0D1A")
        overlay.begin_fill()
        for s in [440, 240, 440, 240]:
            overlay.forward(s)
            overlay.right(90)
        overlay.end_fill()

        # Border glow
        overlay.goto(-220, 140)
        overlay.pensize(3)
        overlay.pencolor("#5588DD")
        overlay.pendown()
        for s in [440, 240, 440, 240]:
            overlay.forward(s)
            overlay.right(90)
        overlay.penup()

        # Inner border accent
        overlay.goto(-216, 136)
        overlay.pensize(1)
        overlay.pencolor("#334466")
        overlay.pendown()
        for s in [432, 232, 432, 232]:
            overlay.forward(s)
            overlay.right(90)
        overlay.penup()

        # Title text
        title_t = turtle.Turtle()
        title_t.hideturtle()
        title_t.penup()
        title_t.goto(0, 90)
        title_t.color("#DDDDFF")
        title_t.write("Choose Your Side", align="center", font=("Arial", 22, "bold"))

        # Subtitle
        sub_t = turtle.Turtle()
        sub_t.hideturtle()
        sub_t.penup()
        sub_t.goto(0, 60)
        sub_t.color("#8888AA")
        sub_t.write("Click to select", align="center", font=("Arial", 12, "normal"))

        # --- White button ---
        btn_w = turtle.Turtle()
        btn_w.shape("square")
        btn_w.shapesize(2.8, 6.0)
        btn_w.color("#E8E8E8")
        btn_w.penup()
        btn_w.goto(-85, 10)

        lbl_w = turtle.Turtle()
        lbl_w.hideturtle()
        lbl_w.penup()
        lbl_w.goto(-85, -2)
        lbl_w.color("#1a1a2e")
        lbl_w.write("♔ White", align="center", font=("Arial", 17, "bold"))

        # --- Black button ---
        btn_b = turtle.Turtle()
        btn_b.shape("square")
        btn_b.shapesize(2.8, 6.0)
        btn_b.color("#333333")
        btn_b.penup()
        btn_b.goto(85, 10)

        lbl_b = turtle.Turtle()
        lbl_b.hideturtle()
        lbl_b.penup()
        lbl_b.goto(85, -2)
        lbl_b.color("#E8E8E8")
        lbl_b.write("♚ Black", align="center", font=("Arial", 17, "bold"))

        self.screen.update()

        def pick_white(x, y):
            result['color'] = 'w'
        def pick_black(x, y):
            result['color'] = 'b'

        btn_w.onclick(pick_white)
        btn_b.onclick(pick_black)

        while result['color'] is None:
            self.screen.update()
            import time
            time.sleep(0.05)

        for t in [overlay, title_t, sub_t, btn_w, lbl_w, btn_b, lbl_b]:
            t.clear()
            t.hideturtle()

        self.screen.update()
        return result['color']

    def show_depth_menu(self):
        """Show depth selection popup with estimated response time. Returns chosen depth."""
        import tkinter as tk

        # Estimated response times per depth (rough approximations)
        TIME_ESTIMATES = {
            1: "< 0.01s",  2: "< 0.01s",  3: "< 0.01s",  4: "~ 0.01s",
            5: "~ 0.02s",  6: "~ 0.03s",  7: "~ 0.05s",  8: "~ 0.1s",
            9: "~ 0.3s",  10: "~ 0.8s",  11: "~ 2s",     12: "~ 4s",
            13: "~ 10s",  14: "~ 25s",    15: "~ 1 min",  16: "~ 2 min",
            17: "~ 5 min", 18: "~ 10 min", 19: "~ 20 min", 20: "~ 30+ min",
        }

        result = {'depth': None}

        # Background overlay
        overlay = turtle.Turtle()
        overlay.hideturtle()
        overlay.speed(0)
        overlay.penup()
        overlay.goto(-220, 170)
        overlay.color("#0D0D1A")
        overlay.fillcolor("#0D0D1A")
        overlay.begin_fill()
        for s in [440, 370, 440, 370]:
            overlay.forward(s)
            overlay.right(90)
        overlay.end_fill()

        # Border
        overlay.goto(-220, 170)
        overlay.pensize(3)
        overlay.pencolor("#5588DD")
        overlay.pendown()
        for s in [440, 370, 440, 370]:
            overlay.forward(s)
            overlay.right(90)
        overlay.penup()

        # Title
        title_t = turtle.Turtle()
        title_t.hideturtle()
        title_t.penup()
        title_t.goto(0, 120)
        title_t.color("#DDDDFF")
        title_t.write("Select AI Depth", align="center", font=("Arial", 22, "bold"))

        # Estimated time label (turtle-drawn, updates dynamically)
        time_t = turtle.Turtle()
        time_t.hideturtle()
        time_t.penup()
        time_t.goto(0, -20)
        time_t.color("#AAAACC")

        depth_var = tk.IntVar(value=12)

        def update_time_label(val):
            d = int(val)
            est = TIME_ESTIMATES.get(d, "unknown")
            time_t.clear()
            time_t.goto(0, -20)
            time_t.color("#AAAACC")
            time_t.write(f"Estimated response: {est}", align="center",
                        font=("Arial", 14, "normal"))
            # Also update depth display
            depth_lbl_t.clear()
            depth_lbl_t.goto(0, 55)
            depth_lbl_t.color("#FFFFFF")
            depth_lbl_t.write(f"Depth: {d}", align="center",
                            font=("Arial", 18, "bold"))

        # Depth value display
        depth_lbl_t = turtle.Turtle()
        depth_lbl_t.hideturtle()
        depth_lbl_t.penup()
        depth_lbl_t.goto(0, 55)
        depth_lbl_t.color("#FFFFFF")
        depth_lbl_t.write("Depth: 12", align="center", font=("Arial", 18, "bold"))

        # Create tkinter slider - must use root as parent, not the ScrolledCanvas
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        raw_canvas = canvas._canvas if hasattr(canvas, '_canvas') else canvas
        slider = tk.Scale(root, from_=1, to=20, orient=tk.HORIZONTAL,
                         variable=depth_var, command=update_time_label,
                         bg="#0D0D1A", fg="white", troughcolor="#2a2a4e",
                         highlightthickness=0, length=300, width=20,
                         font=("Arial", 10), showvalue=False)
        slider_window = raw_canvas.create_window(0, 35, window=slider)

        # Show initial time estimate
        update_time_label(12)

        # Start Game button — use tkinter Button (turtle shapes cover text)
        def on_start():
            result['depth'] = depth_var.get()

        btn_start = tk.Button(root, text="SELECT", command=on_start,
                             font=("Arial", 16, "bold"),
                             bg="#3366AA", fg="white", activebackground="#4477BB",
                             activeforeground="white", relief="flat",
                             padx=40, pady=8, cursor="hand2")
        btn_window = raw_canvas.create_window(0, 115, window=btn_start)

        self.screen.update()

        while result['depth'] is None:
            self.screen.update()
            import time
            time.sleep(0.05)

        # Clean up
        raw_canvas.delete(slider_window)
        raw_canvas.delete(btn_window)
        slider.destroy()
        btn_start.destroy()
        for t in [overlay, title_t, time_t, depth_lbl_t]:
            t.clear()
            t.hideturtle()

        self.screen.update()
        return result['depth']