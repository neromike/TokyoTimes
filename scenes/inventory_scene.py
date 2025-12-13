import pygame
from typing import Any

class InventoryScene:
    def __init__(self, game: Any):
        self.game = game
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.options = ["Resume", "Return to Title"]
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.stack.pop()

    def _activate_option(self) -> None:
        choice = self.options[self.selected].lower()
        if choice == "resume":
            self.game.stack.pop()
        elif choice == "return to title":
            # Pop all scenes to get back to title
            while len(self.game.stack._stack) > 1:
                self.game.stack.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        rect = surface.get_rect()
        title = self.title_font.render("Inventory", True, (200, 255, 200))
        title_pos = (rect.centerx - title.get_width() // 2, rect.top + 80)
        surface.blit(title, title_pos)

        start_y = title_pos[1] + title.get_height() + 40
        for i, opt in enumerate(self.options):
            sel = (i == self.selected)
            color = (255, 255, 0) if sel else (200, 200, 200)
            marker = "> " if sel else "  "
            text = self.menu_font.render(f"{marker}{opt}", True, color)
            x = rect.centerx - text.get_width() // 2
            y = start_y + i * 40
            surface.blit(text, (x, y))
