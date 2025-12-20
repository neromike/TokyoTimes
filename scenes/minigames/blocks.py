import pygame
import random

# Blocks mini-game piece definitions
BLOCKS_PIECES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1], [1, 1]],
    'T': [[1, 1, 1], [0, 1, 0]],
    'L': [[1, 1, 1], [1, 0, 0]],
    'J': [[1, 1, 1], [0, 0, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'Z': [[1, 1, 0], [0, 1, 1]],
}

class BlocksState:
    def __init__(self):
        self.cols = 10
        self.rows = 20
        self.cell = 24
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.colors = {
            0: (20, 20, 20),
            1: (80, 200, 255),
            2: (255, 200, 80),
            3: (200, 120, 255),
            4: (255, 160, 80),
            5: (120, 180, 255),
            6: (120, 220, 120),
            7: (255, 120, 140),
        }
        self.drop_timer = 0.0
        self.drop_interval = 0.7
        self.current = None
        self.pos = [0, 0]
        self.spawn_new()
        self.game_over = False

    def spawn_new(self):
        shape_key = random.choice(list(BLOCKS_PIECES.keys()))
        shape = [row[:] for row in BLOCKS_PIECES[shape_key]]
        self.current = shape
        self.pos = [self.cols // 2 - len(shape[0]) // 2, 0]
        if self.collides(self.pos[0], self.pos[1], self.current):
            self.game_over = True

    def rotate(self, shape):
        return [list(row) for row in zip(*shape[::-1])]

    def collides(self, x, y, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                bx, by = x + c, y + r
                if bx < 0 or bx >= self.cols or by >= self.rows:
                    return True
                if by >= 0 and self.board[by][bx]:
                    return True
        return False

    def lock_piece(self):
        color_id = random.randint(1, 7)
        for r, row in enumerate(self.current):
            for c, cell in enumerate(row):
                if cell:
                    bx, by = self.pos[0] + c, self.pos[1] + r
                    if 0 <= by < self.rows:
                        self.board[by][bx] = color_id
        self.clear_lines()
        self.spawn_new()

    def clear_lines(self):
        new_board = [row for row in self.board if any(v == 0 for v in row)]
        cleared = self.rows - len(new_board)
        if cleared:
            self.board = [[0 for _ in range(self.cols)] for _ in range(cleared)] + new_board

    def hard_drop(self):
        while not self.collides(self.pos[0], self.pos[1] + 1, self.current):
            self.pos[1] += 1
        self.lock_piece()

    def handle_key(self, key):
        if self.game_over:
            return
        if key in (pygame.K_a, pygame.K_LEFT):
            nx = self.pos[0] - 1
            if not self.collides(nx, self.pos[1], self.current):
                self.pos[0] = nx
        elif key in (pygame.K_d, pygame.K_RIGHT):
            nx = self.pos[0] + 1
            if not self.collides(nx, self.pos[1], self.current):
                self.pos[0] = nx
        elif key in (pygame.K_s, pygame.K_DOWN):
            ny = self.pos[1] + 1
            if not self.collides(self.pos[0], ny, self.current):
                self.pos[1] = ny
            else:
                self.lock_piece()
        elif key in (pygame.K_w, pygame.K_UP):
            rotated = self.rotate(self.current)
            if not self.collides(self.pos[0], self.pos[1], rotated):
                self.current = rotated
        elif key == pygame.K_SPACE:
            self.hard_drop()

    def update(self, dt: float):
        if self.game_over:
            return
        self.drop_timer += dt
        if self.drop_timer >= self.drop_interval:
            self.drop_timer = 0.0
            ny = self.pos[1] + 1
            if not self.collides(self.pos[0], ny, self.current):
                self.pos[1] = ny
            else:
                self.lock_piece()

    def draw(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, font: pygame.font.Font):
        board_w = self.cols * self.cell
        board_h = self.rows * self.cell
        bx = x + (w - board_w) // 2
        by = y + (h - board_h) // 2

        pygame.draw.rect(surface, (10, 10, 10), (bx - 4, by - 4, board_w + 8, board_h + 8))

        for r in range(self.rows):
            for c in range(self.cols):
                val = self.board[r][c]
                color = self.colors[val]
                pygame.draw.rect(surface, color, (bx + c * self.cell, by + r * self.cell, self.cell - 1, self.cell - 1))

        if not self.game_over:
            for r, row in enumerate(self.current):
                for c, cell in enumerate(row):
                    if not cell:
                        continue
                    px = self.pos[0] + c
                    py = self.pos[1] + r
                    if py >= 0:
                        pygame.draw.rect(surface, (240, 240, 240), (bx + px * self.cell, by + py * self.cell, self.cell - 1, self.cell - 1))

        for c in range(self.cols + 1):
            pygame.draw.line(surface, (30, 30, 30), (bx + c * self.cell, by), (bx + c * self.cell, by + board_h))
        for r in range(self.rows + 1):
            pygame.draw.line(surface, (30, 30, 30), (bx, by + r * self.cell), (bx + board_w, by + r * self.cell))

        title = font.render("Blocks Arcade (ESC to exit)", True, (255, 255, 255))
        surface.blit(title, (x + 20, y + 20))
        hint = font.render("Arrows/WASD move, UP/W rotate, SPACE drop", True, (200, 200, 200))
        surface.blit(hint, (x + 20, y + 50))
        if self.game_over:
            over = font.render("Game Over (ESC)", True, (255, 120, 120))
            surface.blit(over, (x + 20, y + 80))
