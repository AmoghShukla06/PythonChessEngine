# ui.py
import time
import math
import platform
import turtle
from resource_path import resource_path

SQUARE = 90
BOARD_HALF = 4 * SQUARE

# --- Color palette ---
LIGHT_SQUARE = "#ECDCC7"
DARK_SQUARE = "#7E6147"
FRAME_BG = "#141A26"
FRAME_SHADOW = "#0A0E17"
FRAME_OUTLINE = "#364052"
COORD_LABEL_LIGHT = "#6D513B"
COORD_LABEL_DARK = "#F1E4D2"
LAST_MOVE_LIGHT = "#C5D06D"
LAST_MOVE_DARK = "#A6AE57"
STATUS_BG = "#0F1522"
STATUS_TURN_WHITE = "#F5D7AF"
STATUS_TURN_BLACK = "#CFD8EA"
STATUS_WIN = "#93D360"
STATUS_DRAW = "#E9C45D"
PANEL_BG = "#111828"
PANEL_OUTLINE = "#38445C"
PANEL_TEXT = "#C9D3EB"
HINT_TEXT = "#8D9AB7"
SELECT_BORDER = "#F0CF66"
MOVE_DOT = "#65748F"
CAPTURE_RING = "#C65255"
ANNOTATION_COLORS = {
    "green": "#63C36B",
    "red": "#D96060",
    "blue": "#5F8EE8",
    "yellow": "#E2C85E",
}

# Piece display ordering and value
PIECE_ORDER = {"Q": 0, "R": 1, "B": 2, "N": 3, "P": 4}
PIECE_VALUES = {"Q": 9, "R": 5, "B": 3, "N": 3, "P": 1}

FILE_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]
RANK_LABELS = ["8", "7", "6", "5", "4", "3", "2", "1"]


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
        self.status_panel = None
        self.status_hint = None
        self.flipped = False
        self.move_animation_steps = 5
        self.move_animation_delay = 0.006
        if platform.system() == "Windows":
            self.move_animation_steps = 3
            self.move_animation_delay = 0.003
        self.annotations = {}
        self.annotation_order = []
        self.annotation_preview = None
        self.dragging_piece_key = None
        self.dragging_piece_origin = None
        self.button_turtles = {}
        self.button_bounds = {}  # Store button clickable areas
        self.eval_bar = None
        self.eval_label = None
        self.eval_white_frac = 0.5
        self.move_list_turtles = []
        self.load_shapes()
        self.setup_status_display()
        self.setup_hints()
        self.setup_eval_bar()
        self.setup_move_list()

    def load_shapes(self):
        for p in ["wP", "wR", "wN", "wB", "wQ", "wK", "bP", "bR", "bN", "bB", "bQ", "bK"]:
            try:
                self.screen.addshape(resource_path(f"pieces/{p}.gif"))
            except Exception:
                print(f"Warning: Could not load pieces/{p}.gif")

    def _draw_rect(self, artist, x, y, width, height, fill, outline=None, pen_size=1):
        """Draw a filled rectangle from top-left (x, y)."""
        artist.penup()
        artist.setheading(0)
        artist.goto(x, y)
        artist.fillcolor(fill)
        artist.pencolor(outline if outline else fill)
        artist.pensize(pen_size)
        artist.begin_fill()
        artist.pendown()
        artist.forward(width)
        artist.right(90)
        artist.forward(height)
        artist.right(90)
        artist.forward(width)
        artist.right(90)
        artist.forward(height)
        artist.right(90)
        artist.end_fill()
        artist.penup()

    def setup_status_display(self):
        self.status_panel = turtle.Turtle()
        self.status_panel.hideturtle()
        self.status_panel.penup()
        self.status_panel.speed(0)

        self.status_text = turtle.Turtle()
        self.status_text.hideturtle()
        self.status_text.penup()
        self.status_text.speed(0)

    def setup_hints(self):
        self.status_hint = turtle.Turtle()
        self.status_hint.hideturtle()
        self.status_hint.penup()
        self.status_hint.goto(0, -395)
        self.status_hint.color(HINT_TEXT)
        self.status_hint.write(
            "Left drag: move | C: clear | F: flip | R: resign | P: save PGN",
            align="center", font=("Trebuchet MS", 11, "normal"))

    # --- Evaluation bar (engine score, White at the bottom) ---
    EVAL_BAR_X = -448
    EVAL_BAR_W = 30
    EVAL_BAR_BOTTOM = -BOARD_HALF
    EVAL_BAR_H = 2 * BOARD_HALF

    def setup_eval_bar(self):
        self.eval_bar = turtle.Turtle()
        self.eval_bar.hideturtle()
        self.eval_bar.penup()
        self.eval_bar.speed(0)
        self.eval_label = turtle.Turtle()
        self.eval_label.hideturtle()
        self.eval_label.penup()
        self.eval_label.speed(0)
        self.draw_eval_bar(0.0)

    def draw_eval_bar(self, white_cp, mate_in=None):
        """Render the eval bar. white_cp is centipawns from White's POV;
        mate_in is signed plies-to-mate (+ = White mating) if a mate is seen."""
        if self.eval_bar is None:
            return

        if mate_in is not None and mate_in != 0:
            frac = 1.0 if mate_in > 0 else 0.0
            label = f"M{abs((mate_in + 1) // 2)}"
        else:
            p = white_cp / 100.0  # pawns
            frac = 1.0 / (1.0 + 10 ** (-p / 4.0))  # logistic squash
            frac = max(0.03, min(0.97, frac))
            label = f"{p:+.1f}" if abs(p) < 100 else f"{p:+.0f}"
        self.eval_white_frac = frac

        x = self.EVAL_BAR_X
        w = self.EVAL_BAR_W
        bottom = self.EVAL_BAR_BOTTOM
        h = self.EVAL_BAR_H
        white_h = h * frac

        self.eval_bar.clear()
        # Black (top) background for the whole bar.
        self._draw_rect(self.eval_bar, x, bottom + h, w, h, "#26272B",
                        "#0A0E17", pen_size=2)
        # White fill from the bottom.
        if white_h > 1:
            self._draw_rect(self.eval_bar, x, bottom + white_h, w, white_h,
                            "#E9EDF2")
        # Midline marker at 0.0.
        self.eval_bar.penup()
        self.eval_bar.pensize(1)
        self.eval_bar.pencolor("#6B7280")
        self.eval_bar.goto(x, bottom + h / 2)
        self.eval_bar.pendown()
        self.eval_bar.setheading(0)
        self.eval_bar.forward(w)
        self.eval_bar.penup()

        # Numeric label above the bar, colored by who is favored.
        self.eval_label.clear()
        self.eval_label.goto(x + w / 2, bottom + h + 12)
        self.eval_label.color("#E9EDF2" if frac >= 0.5 else "#9AA6BF")
        self.eval_label.write(label, align="center",
                              font=("Consolas", 13, "bold"))

    def draw_game_buttons(self):
        """Draw Resign and Quit buttons on the right side of the board."""
        # Clear previous buttons if they exist
        for btn_turtle in self.button_turtles.values():
            btn_turtle.clear()
        self.button_turtles = {}
        self.button_bounds = {}
        
        button_width = 90
        button_height = 40
        button_x = 410  # Right side of board
        button_y_resign = 150
        button_y_quit = 80
        
        # Resign button
        resign_btn = turtle.Turtle()
        resign_btn.hideturtle()
        resign_btn.penup()
        resign_btn.speed(0)
        
        self._draw_button(resign_btn, button_x, button_y_resign, button_width, button_height,
                         "#8B3A3A", "#F0F0F0", "Resign")
        self.button_turtles["resign"] = resign_btn
        self.button_bounds["resign"] = {
            "x1": button_x, "x2": button_x + button_width,
            "y1": button_y_resign - button_height, "y2": button_y_resign
        }
        
        # Quit button
        quit_btn = turtle.Turtle()
        quit_btn.hideturtle()
        quit_btn.penup()
        quit_btn.speed(0)
        
        self._draw_button(quit_btn, button_x, button_y_quit, button_width, button_height,
                         "#364052", "#C9D3EB", "Quit")
        self.button_turtles["quit"] = quit_btn
        self.button_bounds["quit"] = {
            "x1": button_x, "x2": button_x + button_width,
            "y1": button_y_quit - button_height, "y2": button_y_quit
        }

    def _draw_button(self, turtle_obj, x, y, width, height, bg_color, text_color, text):
        """Draw a button with text."""
        # Draw button background
        self._draw_rect(turtle_obj, x, y, width, height, bg_color, "#555555", pen_size=2)
        
        # Draw button text
        text_turtle = turtle.Turtle()
        text_turtle.hideturtle()
        text_turtle.penup()
        text_turtle.speed(0)
        text_turtle.goto(x + width / 2, y - height / 2 - 6)
        text_turtle.color(text_color)
        text_turtle.write(text, align="center", font=("Trebuchet MS", 11, "bold"))
        self.button_turtles[f"{text}_text"] = text_turtle

    def clear_game_buttons(self):
        """Clear all game buttons."""
        for btn_turtle in self.button_turtles.values():
            btn_turtle.clear()
        self.button_turtles = {}
        self.button_bounds = {}

    def check_button_click(self, x, y):
        """Check if a click is on a button. Returns button name or None."""
        for btn_name, bounds in self.button_bounds.items():
            if bounds["x1"] <= x <= bounds["x2"] and bounds["y1"] <= y <= bounds["y2"]:
                return btn_name
        return None

    def update_status(self, turn, game_over=False, winner=None):
        self.status_panel.clear()
        self.status_text.clear()

        banner_width = 430
        banner_height = 54
        banner_x = -banner_width / 2
        banner_y = 445

        if game_over:
            if winner == "draw":
                text = "GAME OVER - STALEMATE"
                text_color = STATUS_DRAW
            elif winner == "w":
                text = "CHECKMATE - WHITE WINS"
                text_color = STATUS_WIN
            else:
                text = "CHECKMATE - BLACK WINS"
                text_color = STATUS_WIN
        else:
            if turn == "w":
                text = "White to move"
                text_color = STATUS_TURN_WHITE
            else:
                text = "Black to move"
                text_color = STATUS_TURN_BLACK

        self._draw_rect(self.status_panel, banner_x, banner_y, banner_width, banner_height,
                        STATUS_BG, FRAME_OUTLINE, pen_size=2)
        self.status_text.goto(0, 410)
        self.status_text.color(text_color)
        self.status_text.write(text, align="center", font=("Georgia", 20, "bold"))

    # --- Coordinate mapping ---

    def board_to_screen(self, r, c):
        """Convert board (row, col) to screen (x, y) for top-left square corner."""
        if self.flipped:
            return -BOARD_HALF + (7 - c) * SQUARE, BOARD_HALF - (7 - r) * SQUARE
        return -BOARD_HALF + c * SQUARE, BOARD_HALF - r * SQUARE

    def screen_to_board(self, x, y):
        """Convert screen (x, y) to board (row, col), respecting flip."""
        if self.flipped:
            c = 7 - int((x + BOARD_HALF) // SQUARE)
            r = 7 - int((BOARD_HALF - y) // SQUARE)
        else:
            c = int((x + BOARD_HALF) // SQUARE)
            r = int((BOARD_HALF - y) // SQUARE)
        return (r, c) if 0 <= r < 8 and 0 <= c < 8 else (None, None)

    def _square_color(self, r, c):
        return LIGHT_SQUARE if (r + c) % 2 == 0 else DARK_SQUARE

    def flip_board(self, board):
        self.flipped = not self.flipped
        self.clear_annotation_preview()
        self.end_piece_drag()
        self.draw_board()
        self.init_pieces(board)

    def draw_board(self):
        self.drawer.clear()

        board_left = -BOARD_HALF
        board_top = BOARD_HALF
        board_size = 8 * SQUARE

        # Board shell and shadow
        self._draw_rect(self.drawer, board_left - 18, board_top + 18,
                        board_size + 36, board_size + 36, FRAME_SHADOW)
        self._draw_rect(self.drawer, board_left - 10, board_top + 10,
                        board_size + 20, board_size + 20, FRAME_BG, FRAME_OUTLINE, pen_size=3)

        # Squares
        for r in range(8):
            for c in range(8):
                sx, sy = self.board_to_screen(r, c)
                color = self._square_color(r, c)
                self._draw_rect(self.drawer, sx, sy, SQUARE, SQUARE, color)

        self._draw_coordinates()

    def _draw_coordinates(self):
        for t in self.coord_turtles:
            t.clear()
            t.hideturtle()
        self.coord_turtles.clear()

        # File labels on displayed bottom row
        for c in range(8):
            disp_c = (7 - c) if self.flipped else c
            r = 7
            disp_r = (7 - r) if self.flipped else r
            sx, sy = self.board_to_screen(disp_r, disp_c)
            color = COORD_LABEL_DARK if (disp_r + disp_c) % 2 != 0 else COORD_LABEL_LIGHT

            t = turtle.Turtle()
            t.hideturtle()
            t.penup()
            t.goto(sx + SQUARE - 8, sy - SQUARE + 6)
            t.color(color)
            t.write(FILE_LABELS[c], align="right", font=("Trebuchet MS", 10, "bold"))
            self.coord_turtles.append(t)

        # Rank labels on displayed left column
        for r in range(8):
            disp_r = (7 - r) if self.flipped else r
            c = 0
            disp_c = (7 - c) if self.flipped else c
            sx, sy = self.board_to_screen(disp_r, disp_c)
            color = COORD_LABEL_DARK if (disp_r + disp_c) % 2 != 0 else COORD_LABEL_LIGHT

            t = turtle.Turtle()
            t.hideturtle()
            t.penup()
            t.goto(sx + 5, sy - 16)
            t.color(color)
            t.write(RANK_LABELS[r], align="left", font=("Trebuchet MS", 10, "bold"))
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
                    t.speed(0)
                    t.shape(resource_path(f"pieces/{board[r][c]}.gif"))
                    x, y = self.board_to_screen(r, c)
                    t.goto(x + SQUARE / 2, y - SQUARE / 2)
                    t.showturtle()
                    self.piece_map[(r, c)] = t

    def move_piece(self, sr, sc, tr, tc):
        if (sr, sc) in self.piece_map:
            t = self.piece_map[(sr, sc)]
            x, y = self.board_to_screen(tr, tc)
            target_x = x + SQUARE / 2
            target_y = y - SQUARE / 2
            start_x, start_y = t.pos()

            if self.move_animation_steps <= 1:
                t.goto(target_x, target_y)
            else:
                for step in range(1, self.move_animation_steps + 1):
                    ratio = step / self.move_animation_steps
                    next_x = start_x + (target_x - start_x) * ratio
                    next_y = start_y + (target_y - start_y) * ratio
                    t.goto(next_x, next_y)
                    self.screen.update()
                    if step != self.move_animation_steps:
                        time.sleep(self.move_animation_delay)

            t.showturtle()
            self.piece_map[(tr, tc)] = t
            del self.piece_map[(sr, sc)]

    def begin_piece_drag(self, r, c):
        """Lift a piece so it can follow the mouse while dragging."""
        key = (r, c)
        if key not in self.piece_map:
            return False

        self.end_piece_drag()
        old_t = self.piece_map[key]
        origin = old_t.pos()
        shape = old_t.shape()
        old_t.hideturtle()

        # Recreate piece turtle to ensure it's drawn above other board elements.
        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        t.speed(0)
        t.shape(shape)
        t.goto(origin[0], origin[1])
        t.showturtle()
        self.piece_map[key] = t

        self.dragging_piece_key = key
        self.dragging_piece_origin = origin
        return True

    def drag_piece_to(self, x, y):
        if self.dragging_piece_key is None:
            return
        key = self.dragging_piece_key
        if key not in self.piece_map:
            return
        # Slight vertical lift gives a "picked up" feel.
        self.piece_map[key].goto(x, y + 10)

    def cancel_piece_drag(self):
        if self.dragging_piece_key is None:
            return
        key = self.dragging_piece_key
        if key in self.piece_map and self.dragging_piece_origin is not None:
            ox, oy = self.dragging_piece_origin
            self.piece_map[key].goto(ox, oy)
        self.end_piece_drag()

    def end_piece_drag(self):
        self.dragging_piece_key = None
        self.dragging_piece_origin = None

    def remove_piece(self, r, c):
        if (r, c) in self.piece_map:
            self.piece_map[(r, c)].hideturtle()
            del self.piece_map[(r, c)]

    def promote_piece_visual(self, r, c, new_piece_code):
        self.remove_piece(r, c)
        t = turtle.Turtle()
        t.penup()
        t.speed(0)
        t.shape(resource_path(f"pieces/{new_piece_code}.gif"))
        x, y = self.board_to_screen(r, c)
        t.goto(x + SQUARE / 2, y - SQUARE / 2)
        t.showturtle()
        self.piece_map[(r, c)] = t

    def get_promotion_choice(self, turn_color):
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
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        sx, sy = self.board_to_screen(r, c)
        h.goto(sx + SQUARE / 2, sy - SQUARE / 2 - 10)
        h.color(color)
        h.begin_fill()
        h.circle(10)
        h.end_fill()
        self.highlights.append(h)
        return h

    def _draw_capture_ring(self, r, c, color):
        h = turtle.Turtle()
        h.penup()
        h.speed(0)
        h.hideturtle()
        sx, sy = self.board_to_screen(r, c)
        h.goto(sx + 5, sy - 5)
        h.pencolor(color)
        h.pensize(5)
        h.pendown()
        side = SQUARE - 10
        for _ in range(4):
            h.forward(side)
            h.right(90)
        h.penup()
        self.highlights.append(h)
        return h

    def highlight(self, r, c, color):
        if color == "yellow":
            self._draw_border(r, c, SELECT_BORDER, width=5)
        elif color == "green":
            self._draw_dot(r, c, MOVE_DOT)
        elif color == "red":
            self._draw_capture_ring(r, c, CAPTURE_RING)

    def clear_last_move_highlights(self):
        for h in self.last_move_highlights:
            h.clear()
            h.hideturtle()
        self.last_move_highlights.clear()

    def highlight_last_move(self, sr, sc, tr, tc):
        self.clear_last_move_highlights()
        for (r, c) in [(sr, sc), (tr, tc)]:
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

            if (r, c) in self.piece_map:
                old_t = self.piece_map[(r, c)]
                shape = old_t.shape()
                old_t.hideturtle()
                new_t = turtle.Turtle()
                new_t.penup()
                new_t.speed(0)
                new_t.shape(shape)
                new_t.goto(sx + SQUARE / 2, sy - SQUARE / 2)
                new_t.showturtle()
                self.piece_map[(r, c)] = new_t

    def redraw_last_move(self, sr, sc, tr, tc):
        if sr is not None:
            self.highlight_last_move(sr, sc, tr, tc)

    # --- Arrow and square annotations ---

    def annotation_color_from_state(self, state):
        """Pick annotation color based on keyboard modifiers."""
        # Default to yellow (chess.com style). Only switch when modifiers are explicit.
        if state & 0x0004:  # Control
            return "blue"
        if state & 0x0001:  # Shift
            return "red"
        if state & (0x0008 | 0x20000):  # Alt (platform-dependent masks)
            return "green"
        return "yellow"

    def clear_annotations(self):
        self.clear_annotation_preview()
        for entry in self.annotations.values():
            artist = entry.get("artist")
            if artist:
                artist.clear()
                artist.hideturtle()
        self.annotations.clear()
        self.annotation_order.clear()

    def redraw_annotations(self):
        """Re-render annotations after board redraws/flips/layer changes."""
        self.clear_annotation_preview()
        for entry in self.annotations.values():
            artist = entry.get("artist")
            if artist:
                artist.clear()
                artist.hideturtle()
            entry["artist"] = None

        for key in self.annotation_order:
            self.annotations[key]["artist"] = self._draw_annotation(self.annotations[key])

    def toggle_arrow(self, sr, sc, tr, tc, color_name):
        key = ("arrow", sr, sc, tr, tc, color_name)
        self._toggle_annotation(key, {
            "kind": "arrow",
            "sr": sr,
            "sc": sc,
            "tr": tr,
            "tc": tc,
            "color_name": color_name,
            "artist": None,
        })

    def toggle_marker(self, r, c, color_name):
        key = ("marker", r, c, color_name)
        self._toggle_annotation(key, {
            "kind": "marker",
            "r": r,
            "c": c,
            "color_name": color_name,
            "artist": None,
        })

    def _toggle_annotation(self, key, entry):
        if key in self.annotations:
            old = self.annotations.pop(key)
            artist = old.get("artist")
            if artist:
                artist.clear()
                artist.hideturtle()
            self.annotation_order = [k for k in self.annotation_order if k != key]
            return

        entry["artist"] = self._draw_annotation(entry)
        self.annotations[key] = entry
        self.annotation_order.append(key)

    def _draw_annotation(self, entry):
        color = ANNOTATION_COLORS.get(entry["color_name"], ANNOTATION_COLORS["green"])
        if entry["kind"] == "arrow":
            return self._draw_arrow(entry["sr"], entry["sc"], entry["tr"], entry["tc"], color)
        return self._draw_marker(entry["r"], entry["c"], color)

    def clear_annotation_preview(self):
        if self.annotation_preview:
            self.annotation_preview.clear()
            self.annotation_preview.hideturtle()
            self.annotation_preview = None

    def preview_annotation(self, sr, sc, tr, tc, color_name):
        """Show temporary arrow/marker while right-dragging."""
        self.clear_annotation_preview()
        color = ANNOTATION_COLORS.get(color_name, ANNOTATION_COLORS["green"])
        if (sr, sc) == (tr, tc):
            self.annotation_preview = self._draw_marker(sr, sc, color, pen_size=3)
        else:
            self.annotation_preview = self._draw_arrow(sr, sc, tr, tc, color,
                                                       line_width=6, head_half=9)

    def _square_center(self, r, c):
        sx, sy = self.board_to_screen(r, c)
        return sx + SQUARE / 2, sy - SQUARE / 2

    def _draw_arrow(self, sr, sc, tr, tc, color, line_width=9, head_half=11):
        start_x, start_y = self._square_center(sr, sc)
        end_x, end_y = self._square_center(tr, tc)
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.hypot(dx, dy)
        if length < 1:
            return self._draw_marker(sr, sc, color)

        ux = dx / length
        uy = dy / length
        head_len = min(28, max(18, length * 0.28))
        shaft_end_x = end_x - ux * head_len
        shaft_end_y = end_y - uy * head_len
        perp_x = -uy
        perp_y = ux
        half_head = head_half

        t = turtle.Turtle()
        t.hideturtle()
        t.speed(0)
        t.penup()
        t.pencolor(color)
        t.fillcolor(color)
        t.pensize(line_width)
        t.goto(start_x, start_y)
        t.pendown()
        t.goto(shaft_end_x, shaft_end_y)
        t.penup()

        left_x = shaft_end_x + perp_x * half_head
        left_y = shaft_end_y + perp_y * half_head
        right_x = shaft_end_x - perp_x * half_head
        right_y = shaft_end_y - perp_y * half_head
        t.goto(left_x, left_y)
        t.begin_fill()
        t.goto(end_x, end_y)
        t.goto(right_x, right_y)
        t.goto(left_x, left_y)
        t.end_fill()
        return t

    def _draw_marker(self, r, c, color, pen_size=5):
        center_x, center_y = self._square_center(r, c)
        radius = SQUARE * 0.36
        t = turtle.Turtle()
        t.hideturtle()
        t.speed(0)
        t.penup()
        t.pencolor(color)
        t.pensize(pen_size)
        t.goto(center_x, center_y - radius)
        t.pendown()
        t.circle(radius)
        t.penup()
        return t

    # --- Move list panel (SAN scoresheet) ---
    MOVE_PANEL_LEFT = 556
    MOVE_PANEL_WIDTH = 178

    def setup_move_list(self):
        self.move_list_turtles = []

    def clear_move_list(self):
        for t in getattr(self, "move_list_turtles", []):
            t.clear()
            t.hideturtle()
        self.move_list_turtles = []

    def draw_move_list(self, san_moves):
        """Render a two-column SAN scoresheet, auto-scrolled to the latest moves."""
        self.clear_move_list()

        left = self.MOVE_PANEL_LEFT
        width = self.MOVE_PANEL_WIDTH
        top = BOARD_HALF + 10
        height = 2 * BOARD_HALF + 20

        panel = turtle.Turtle()
        panel.hideturtle(); panel.penup(); panel.speed(0)
        self._draw_rect(panel, left + 6, top - 6, width, height, "#080C14")
        self._draw_rect(panel, left, top, width, height, PANEL_BG,
                        PANEL_OUTLINE, pen_size=2)
        self.move_list_turtles.append(panel)

        title = turtle.Turtle()
        title.hideturtle(); title.penup(); title.speed(0)
        title.goto(left + width / 2, top - 34)
        title.color(PANEL_TEXT)
        title.write("Moves", align="center", font=("Georgia", 15, "bold"))
        self.move_list_turtles.append(title)

        # Group plies into (number, white, black) rows.
        rows = []
        for i in range(0, len(san_moves), 2):
            num = i // 2 + 1
            w = san_moves[i]
            b = san_moves[i + 1] if i + 1 < len(san_moves) else ""
            rows.append((num, w, b))

        row_h = 22
        start_y = top - 62
        max_rows = int((height - 80) // row_h)
        visible = rows[-max_rows:] if len(rows) > max_rows else rows

        num_x = left + 14
        white_x = left + 52
        black_x = left + 120
        for i, (num, w, b) in enumerate(visible):
            y = start_y - i * row_h
            t = turtle.Turtle()
            t.hideturtle(); t.penup(); t.speed(0)
            t.goto(num_x, y)
            t.color(HINT_TEXT)
            t.write(f"{num}.", align="left", font=("Consolas", 11, "normal"))
            self.move_list_turtles.append(t)

            tw = turtle.Turtle()
            tw.hideturtle(); tw.penup(); tw.speed(0)
            tw.goto(white_x, y)
            tw.color("#EAEEF6")
            tw.write(w, align="left", font=("Consolas", 11, "bold"))
            self.move_list_turtles.append(tw)

            if b:
                tb = turtle.Turtle()
                tb.hideturtle(); tb.penup(); tb.speed(0)
                tb.goto(black_x, y)
                tb.color("#C7D0E4")
                tb.write(b, align="left", font=("Consolas", 11, "bold"))
                self.move_list_turtles.append(tb)

    def clear_captured_display(self):
        for t in self.captured_turtles:
            t.clear()
            t.hideturtle()
        self.captured_turtles.clear()

    def draw_captured_pieces(self, white_captured, black_captured):
        self.clear_captured_display()

        def sort_key(piece_code):
            return PIECE_ORDER.get(piece_code[1], 5)

        panel_left = BOARD_HALF + 8
        panel_top = BOARD_HALF + 10
        panel_width = 176
        panel_height = 740
        board_top = BOARD_HALF
        board_bottom = -BOARD_HALF

        panel = turtle.Turtle()
        panel.hideturtle()
        panel.penup()
        panel.speed(0)

        self._draw_rect(panel, panel_left + 6, panel_top + 6, panel_width, panel_height, "#080C14")
        self._draw_rect(panel, panel_left, panel_top, panel_width, panel_height,
                        PANEL_BG, PANEL_OUTLINE, pen_size=2)
        self.captured_turtles.append(panel)

        title_t = turtle.Turtle()
        title_t.hideturtle()
        title_t.penup()
        title_t.goto(panel_left + panel_width / 2, panel_top - 34)
        title_t.color(PANEL_TEXT)
        title_t.write("Captured", align="center", font=("Georgia", 15, "bold"))
        self.captured_turtles.append(title_t)

        white_gain = sum(PIECE_VALUES.get(p[1], 0) for p in white_captured)
        black_gain = sum(PIECE_VALUES.get(p[1], 0) for p in black_captured)
        material_delta = white_gain - black_gain
        if material_delta > 0:
            material_text = f"Material: White +{material_delta}"
            material_color = STATUS_TURN_WHITE
        elif material_delta < 0:
            material_text = f"Material: Black +{abs(material_delta)}"
            material_color = STATUS_TURN_BLACK
        else:
            material_text = "Material: Equal"
            material_color = PANEL_TEXT

        material_t = turtle.Turtle()
        material_t.hideturtle()
        material_t.penup()
        material_t.goto(panel_left + panel_width / 2, panel_top - 64)
        material_t.color(material_color)
        material_t.write(material_text, align="center", font=("Trebuchet MS", 10, "bold"))
        self.captured_turtles.append(material_t)

        if self.flipped:
            white_y_start = board_top - 108
            black_y_start = board_bottom + 108
            white_dir = -1
            black_dir = 1
        else:
            white_y_start = board_bottom + 108
            black_y_start = board_top - 108
            white_dir = 1
            black_dir = -1

        self._draw_capture_group(sorted(white_captured, key=sort_key),
                                 panel_left + 14, white_y_start, white_dir, "White captured")
        self._draw_capture_group(sorted(black_captured, key=sort_key),
                                 panel_left + 14, black_y_start, black_dir, "Black captured")

    def _draw_capture_group(self, pieces, x, y_start, y_dir, label):
        cols = 5
        spacing_x = 28
        spacing_y = 28
        label_gap = 26

        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        t.goto(x, y_start)
        t.color(PANEL_TEXT)
        t.write(label, align="left", font=("Trebuchet MS", 11, "bold"))
        self.captured_turtles.append(t)

        symbols = {
            "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
            "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
        }

        col = 0
        row = 0
        for piece in pieces:
            sym = symbols.get(piece, "?")
            pt = turtle.Turtle()
            pt.hideturtle()
            pt.penup()
            px = x + col * spacing_x
            py = y_start + y_dir * (label_gap + row * spacing_y)
            pt.goto(px, py)
            if piece.startswith("w"):
                pt.color("#E6EAF3")
            else:
                pt.color("#D8B05A")
            pt.write(sym, align="left", font=("Georgia", 16, "normal"))
            self.captured_turtles.append(pt)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        if not pieces:
            empty_t = turtle.Turtle()
            empty_t.hideturtle()
            empty_t.penup()
            empty_t.goto(x, y_start + y_dir * label_gap)
            empty_t.color(HINT_TEXT)
            empty_t.write("-", align="left", font=("Trebuchet MS", 12, "normal"))
            self.captured_turtles.append(empty_t)

    def show_start_menu(self):
        import tkinter as tk

        result = {"color": "w"}
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        root.update_idletasks()
        try:
            root.update()
        except Exception:
            pass

        dialog = tk.Toplevel(root)
        dialog.title("Choose Side")
        dialog.configure(bg="#0F1522")
        bind_id = self._attach_modal_dialog(root, dialog, 410, 280)

        frame = tk.Frame(dialog, bg="#0F1522", padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Choose Your Side", bg="#0F1522", fg="#E5ECFF",
                 font=("Georgia", 22, "bold")).pack(pady=(0, 8))
        tk.Label(frame, text="White moves first", bg="#0F1522", fg="#8EA0C4",
                 font=("Trebuchet MS", 11)).pack(pady=(0, 18))

        btn_row = tk.Frame(frame, bg="#0F1522")
        btn_row.pack()

        def pick_white():
            result["color"] = "w"
            self._close_modal_dialog(root, dialog, bind_id)

        def pick_black():
            result["color"] = "b"
            self._close_modal_dialog(root, dialog, bind_id)

        tk.Button(btn_row, text="♔ White", command=pick_white, cursor="hand2",
                  bg="#F2E7D8", fg="#1B2436", activebackground="#E5D6C2", activeforeground="#1B2436",
                  relief="flat", padx=24, pady=12, font=("Trebuchet MS", 14, "bold")).grid(row=0, column=0, padx=8)
        tk.Button(btn_row, text="♚ Black", command=pick_black, cursor="hand2",
                  bg="#1E2639", fg="#ECF1FF", activebackground="#2A3550", activeforeground="#ECF1FF",
                  relief="flat", padx=24, pady=12, font=("Trebuchet MS", 14, "bold")).grid(row=0, column=1, padx=8)

        tk.Label(frame, text="Shortcut: press W or B", bg="#0F1522", fg="#7487AA",
                 font=("Trebuchet MS", 10)).pack(pady=(16, 0))

        dialog.bind("<w>", lambda _event: pick_white())
        dialog.bind("<W>", lambda _event: pick_white())
        dialog.bind("<b>", lambda _event: pick_black())
        dialog.bind("<B>", lambda _event: pick_black())
        dialog.protocol("WM_DELETE_WINDOW", pick_white)
        dialog.wait_window()
        return result["color"]

    def show_depth_menu(self):
        import tkinter as tk

        # Response-time estimates for the improved engine (much faster than the
        # old build thanks to sharper pruning); conservative for slow machines.
        TIME_ESTIMATES = {
            1: "instant",  2: "instant",  3: "instant",  4: "instant",
            5: "< 0.05s",  6: "~ 0.05s",  7: "~ 0.1s",   8: "~ 0.2s",
            9: "~ 0.3s",  10: "~ 0.6s",  11: "~ 1s",    12: "~ 2s",
            13: "~ 4s",   14: "~ 7s",    15: "~ 13s",   16: "~ 25s",
            17: "~ 45s",  18: "~ 1.5 min", 19: "~ 3 min", 20: "~ 6 min",
        }
        # Named difficulty presets -> search depth.
        PRESETS = [
            ("Beginner", 2), ("Easy", 4), ("Intermediate", 7),
            ("Advanced", 10), ("Expert", 13), ("Master", 16),
        ]

        result = {"depth": 10}
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        root.update_idletasks()
        try:
            root.update()
        except Exception:
            pass

        dialog = tk.Toplevel(root)
        dialog.title("Difficulty")
        dialog.configure(bg="#0F1522")
        bind_id = self._attach_modal_dialog(root, dialog, 500, 400)

        frame = tk.Frame(dialog, bg="#0F1522", padx=30, pady=22)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Select Difficulty", bg="#0F1522", fg="#E5ECFF",
                 font=("Georgia", 22, "bold")).pack(pady=(0, 4))
        tk.Label(frame, text="Pick a preset or fine-tune the search depth",
                 bg="#0F1522", fg="#8EA0C4",
                 font=("Trebuchet MS", 10)).pack(pady=(0, 12))

        depth_var = tk.IntVar(value=10)
        depth_text = tk.StringVar()
        eta_text = tk.StringVar()

        def label_for(d):
            best = PRESETS[0][0]
            for name, pd in PRESETS:
                if d >= pd:
                    best = name
            return best

        def on_depth_change(value):
            d = int(float(value))
            depth_text.set(f"{label_for(d)}  ·  depth {d}")
            eta_text.set(f"Estimated response: {TIME_ESTIMATES.get(d, 'unknown')}")

        # Preset buttons (two rows of three).
        preset_wrap = tk.Frame(frame, bg="#0F1522")
        preset_wrap.pack(pady=(0, 14))
        for i, (name, pd) in enumerate(PRESETS):
            def make_cmd(val):
                return lambda: (depth_var.set(val), on_depth_change(val))
            tk.Button(preset_wrap, text=f"{name}\n(d{pd})", command=make_cmd(pd),
                      cursor="hand2", width=10, bg="#1E2639", fg="#ECF1FF",
                      activebackground="#2A3550", activeforeground="#ECF1FF",
                      relief="flat", padx=4, pady=6,
                      font=("Trebuchet MS", 10, "bold")).grid(
                          row=i // 3, column=i % 3, padx=6, pady=5)

        tk.Label(frame, textvariable=depth_text, bg="#0F1522", fg="#FFFFFF",
                 font=("Trebuchet MS", 15, "bold")).pack(pady=(4, 6))

        slider = tk.Scale(frame, from_=1, to=20, orient=tk.HORIZONTAL, variable=depth_var,
                          command=on_depth_change, bg="#0F1522", fg="#DEE6FA",
                          troughcolor="#2A3550", highlightthickness=0, length=360,
                          showvalue=False, font=("Trebuchet MS", 10), width=16)
        slider.pack(pady=(0, 8))

        tk.Label(frame, textvariable=eta_text, bg="#0F1522", fg="#8EA0C4",
                 font=("Trebuchet MS", 11)).pack(pady=(0, 14))

        def submit():
            result["depth"] = depth_var.get()
            self._close_modal_dialog(root, dialog, bind_id)

        tk.Button(frame, text="Start Game", command=submit, cursor="hand2",
                  bg="#2A7E54", fg="#F0F7F2", activebackground="#359965", activeforeground="#F0F7F2",
                  relief="flat", padx=30, pady=8, font=("Trebuchet MS", 14, "bold")).pack()

        on_depth_change(10)
        dialog.bind("<Return>", lambda _event: submit())
        dialog.protocol("WM_DELETE_WINDOW", submit)
        dialog.wait_window()
        return result["depth"]

    def show_end_menu(self, game_over, winner=None):
        """Show end-game menu with options to play again or exit."""
        import tkinter as tk

        result = {"action": "exit"}
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        root.update_idletasks()
        try:
            root.update()
        except Exception:
            pass

        dialog = tk.Toplevel(root)
        dialog.title("Game Over")
        dialog.configure(bg="#0F1522")
        bind_id = self._attach_modal_dialog(root, dialog, 380, 240)

        frame = tk.Frame(dialog, bg="#0F1522", padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        # Determine game status message
        if winner:
            if winner == "draw":
                status_text = "DRAW"
                winner_text = "Draw!"
            else:
                status_text = "GAME OVER"
                winner_text = "White Wins!" if winner == "w" else "Black Wins!"
        else:
            status_text = "GAME OVER"
            winner_text = "Game Ended"

        tk.Label(frame, text=status_text, bg="#0F1522", fg="#E9C45D",
                 font=("Georgia", 18, "bold")).pack(pady=(0, 8))
        tk.Label(frame, text=winner_text, bg="#0F1522", fg="#93D360",
                 font=("Trebuchet MS", 14)).pack(pady=(0, 20))

        btn_row = tk.Frame(frame, bg="#0F1522")
        btn_row.pack()

        def play_again():
            result["action"] = "play_again"
            self._close_modal_dialog(root, dialog, bind_id)

        def exit_game():
            result["action"] = "exit"
            self._close_modal_dialog(root, dialog, bind_id)

        tk.Button(btn_row, text="Play Again", command=play_again, cursor="hand2",
                  bg="#2A7E54", fg="#F0F7F2", activebackground="#359965", activeforeground="#F0F7F2",
                  relief="flat", padx=20, pady=10, font=("Trebuchet MS", 12, "bold")).grid(row=0, column=0, padx=8)
        tk.Button(btn_row, text="Exit", command=exit_game, cursor="hand2",
                  bg="#8B3A3A", fg="#F0F0F0", activebackground="#A84C4C", activeforeground="#F0F0F0",
                  relief="flat", padx=20, pady=10, font=("Trebuchet MS", 12, "bold")).grid(row=0, column=1, padx=8)

        dialog.wait_window()
        return result["action"]

    def show_resign_menu(self):
        """Show confirmation dialog for resigning."""
        import tkinter as tk

        result = {"confirm": False}
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        root.update_idletasks()
        try:
            root.update()
        except Exception:
            pass
        dialog = tk.Toplevel(root)
        dialog.title("Resign")
        dialog.configure(bg="#0F1522")
        bind_id = self._attach_modal_dialog(root, dialog, 340, 200)

        frame = tk.Frame(dialog, bg="#0F1522", padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Resign Game?", bg="#0F1522", fg="#E5ECFF",
                 font=("Georgia", 18, "bold")).pack(pady=(0, 8))
        tk.Label(frame, text="Are you sure you want to resign?", bg="#0F1522", fg="#8EA0C4",
                 font=("Trebuchet MS", 11)).pack(pady=(0, 20))

        btn_row = tk.Frame(frame, bg="#0F1522")
        btn_row.pack()

        def confirm_resign():
            result["confirm"] = True
            self._close_modal_dialog(root, dialog, bind_id)

        def cancel_resign():
            result["confirm"] = False
            self._close_modal_dialog(root, dialog, bind_id)

        tk.Button(btn_row, text="Yes, Resign", command=confirm_resign, cursor="hand2",
                  bg="#8B3A3A", fg="#F0F0F0", activebackground="#A84C4C", activeforeground="#F0F0F0",
                  relief="flat", padx=20, pady=10, font=("Trebuchet MS", 12, "bold")).grid(row=0, column=0, padx=8)
        tk.Button(btn_row, text="Cancel", command=cancel_resign, cursor="hand2",
                  bg="#364052", fg="#C9D3EB", activebackground="#4A5A7A", activeforeground="#C9D3EB",
                  relief="flat", padx=20, pady=10, font=("Trebuchet MS", 12, "bold")).grid(row=0, column=1, padx=8)

        dialog.protocol("WM_DELETE_WINDOW", cancel_resign)
        dialog.wait_window()
        return result["confirm"]

    def _attach_modal_dialog(self, root, dialog, base_width, base_height):
        """Make a modal dialog that stays centered and scales with root."""
        is_windows = platform.system() == "Windows"
        borderless = not is_windows
        if borderless:
            dialog.overrideredirect(True)
        else:
            dialog.resizable(False, False)
        try:
            dialog.transient(root)
        except Exception:
            pass
        if borderless:
            dialog.withdraw()

        state = {"updating": False, "x": 0, "y": 0, "w": base_width, "h": base_height}

        def recenter(_event=None):
            if state["updating"]:
                return
            root.update_idletasks()
            rw = max(root.winfo_width(), 640)
            rh = max(root.winfo_height(), 480)
            avail_w = max(rw - 120, 320)
            avail_h = max(rh - 120, 220)
            scale = min(avail_w / base_width, avail_h / base_height)
            scale = max(0.85, min(scale, 1.35))
            width = int(base_width * scale)
            height = int(base_height * scale)
            root_x = root.winfo_rootx()
            root_y = root.winfo_rooty()

            # Tk can report very negative roots before mapping on Windows.
            if root_x < -10000 or root_y < -10000:
                root_x = max((root.winfo_screenwidth() - rw) // 2, 0)
                root_y = max((root.winfo_screenheight() - rh) // 2, 0)

            x = root_x + max((rw - width) // 2, 0)
            y = root_y + max((rh - height) // 2, 0)

            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            x = max(0, min(x, max(screen_w - width, 0)))
            y = max(0, min(y, max(screen_h - height, 0)))
            state["x"], state["y"], state["w"], state["h"] = x, y, width, height
            state["updating"] = True
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            state["updating"] = False

        def keep_attached(_event=None):
            if state["updating"]:
                return
            # Snap back if user tries moving dialog independently.
            if (dialog.winfo_x() != state["x"] or dialog.winfo_y() != state["y"]):
                recenter()

        root_bind_id = root.bind("<Configure>", recenter, add="+")
        dialog_bind_id = None
        if borderless:
            dialog_bind_id = dialog.bind("<Configure>", keep_attached, add="+")
        recenter()
        if borderless:
            dialog.deiconify()
        else:
            dialog.update_idletasks()
        try:
            dialog.lift(root)
        except Exception:
            dialog.lift()
        try:
            dialog.focus_force()
        except Exception:
            pass
        if is_windows:
            try:
                dialog.attributes("-topmost", True)
                dialog.after(80, lambda: dialog.attributes("-topmost", False))
            except Exception:
                pass
        try:
            dialog.grab_set()
        except Exception:
            pass
        return (root_bind_id, dialog_bind_id)

    def _close_modal_dialog(self, root, dialog, bind_id):
        if bind_id:
            root_bind_id, dialog_bind_id = bind_id
            try:
                if root_bind_id:
                    root.unbind("<Configure>", root_bind_id)
            except Exception:
                pass
            try:
                if dialog_bind_id:
                    dialog.unbind("<Configure>", dialog_bind_id)
            except Exception:
                pass
        try:
            dialog.grab_release()
        except Exception:
            pass
        dialog.destroy()
