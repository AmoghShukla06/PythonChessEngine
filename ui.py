# ui.py
import turtle
from resource_path import resource_path

SQUARE = 90

class ChessUI:
    def __init__(self, screen):
        self.screen = screen
        self.drawer = turtle.Turtle()
        self.drawer.hideturtle()
        self.drawer.speed(0)
        self.piece_map = {}
        self.highlights = []
        self.status_text = None
        self.load_shapes()
        self.setup_status_display()
    
    def load_shapes(self):
        # ensure you have a folder named 'pieces' with gifs: wP.gif, bQ.gif, etc.
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
    
    def board_to_screen(self, r, c):
        return -4*SQUARE + c*SQUARE, 4*SQUARE - r*SQUARE
    
    def draw_board(self):
        colors = ["white","gray"]
        for r in range(8):
            for c in range(8):
                self.drawer.penup()
                self.drawer.goto(*self.board_to_screen(r,c))
                self.drawer.fillcolor(colors[(r+c)%2])
                self.drawer.begin_fill()
                for _ in range(4):
                    self.drawer.forward(SQUARE)
                    self.drawer.right(90)
                self.drawer.end_fill()
    
    def init_pieces(self, board):
        for (r,c), t in self.piece_map.items():
            t.hideturtle()
        self.piece_map.clear()
        for r in range(8):
            for c in range(8):
                if board[r][c] != "--":
                    t = turtle.Turtle()
                    t.penup()
                    t.shape(resource_path(f"pieces/{board[r][c]}.gif"))
                    x,y = self.board_to_screen(r,c)
                    t.goto(x+SQUARE/2, y-SQUARE/2)
                    t.showturtle()
                    self.piece_map[(r,c)] = t
    
    def move_piece(self, sr, sc, tr, tc):
        if (sr, sc) in self.piece_map:
            t = self.piece_map[(sr,sc)]
            x,y = self.board_to_screen(tr,tc)
            t.goto(x+SQUARE/2, y-SQUARE/2)
            t.showturtle()
            self.piece_map[(tr,tc)] = t
            del self.piece_map[(sr,sc)]

    def remove_piece(self, r, c):
        if (r,c) in self.piece_map:
            self.piece_map[(r,c)].hideturtle()
            del self.piece_map[(r,c)]

    def promote_piece_visual(self, r, c, new_piece_code):
        """Removes the pawn and places the new promoted piece sprite."""
        self.remove_piece(r, c)
        t = turtle.Turtle()
        t.penup()
        t.shape(resource_path(f"pieces/{new_piece_code}.gif"))
        x,y = self.board_to_screen(r,c)
        t.goto(x+SQUARE/2, y-SQUARE/2)
        t.showturtle()
        self.piece_map[(r,c)] = t

    def get_promotion_choice(self, turn_color):
        """Pop-up dialog to ask user for promotion choice."""
        prompt = f"{'White' if turn_color == 'w' else 'Black'} Promotion"
        choice = self.screen.textinput(prompt, "Promote to (Q, R, B, N):")
        if choice:
            choice = choice.upper()
            if choice in ['Q', 'R', 'B', 'N']:
                return choice
        return 'Q' # Default to Queen if invalid or cancelled
    
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
        h.goto(*self.board_to_screen(r,c))
        h.pensize(4)
        h.pencolor(color)
        h.pendown()
        for _ in range(4):
            h.forward(SQUARE)
            h.right(90)
        h.penup()
        self.highlights.append(h)