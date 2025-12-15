import pygame
from typing import Any
from core.scene import Scene

# Import scenes to register them
from scenes.cat_cafe_scene import CatCafeScene
from scenes.cat_cafe_kitchen_scene import CatCafeKitchenScene
from scenes.load_game_scene import LoadGameScene

class TitleScene:
    def __init__(self, game: Any):
        self.game = game
        self.title_font = pygame.font.Font(None, 64)
        self.menu_font = pygame.font.Font(None, 36)
        self.options = ["Start", "Load", "Exit"]
        self.selected = 0
        self.option_rects = []  # Store menu option rects for click detection

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.quit()
        elif event.type == pygame.MOUSEMOTION:
            # Check if mouse is over any menu option
            mouse_pos = event.pos
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected = i
                        self._activate_option()
                        break

    def _activate_option(self) -> None:
        choice = self.options[self.selected].lower()
        if choice == "start":
            # Start a brand-new run: reset global state and clear any previous scenes
            if hasattr(self.game, "reset_run_state"):
                self.game.reset_run_state()
            self.game.stack._stack = [self]
            self.game.stack.push(CatCafeScene(self.game))
        elif choice == "load":
            self.game.stack.push(LoadGameScene(self.game))
        elif choice == "exit":
            self.game.quit()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        rect = surface.get_rect()
        title = self.title_font.render("Tokyo Times", True, (255,255,255))
        title_pos = (rect.centerx - title.get_width() // 2, rect.top + 120)
        surface.blit(title, title_pos)

        start_y = title_pos[1] + title.get_height() + 40
        self.option_rects = []  # Clear and rebuild each frame
        for i, opt in enumerate(self.options):
            sel = (i == self.selected)
            color = (255,255,0) if sel else (200,200,200)
            marker = "> " if sel else "  "
            text = self.menu_font.render(f"{marker}{opt}", True, color)
            x = rect.centerx - text.get_width() // 2
            y = start_y + i * 40
            surface.blit(text, (x, y))
            
            # Store clickable rect for this option
            self.option_rects.append(pygame.Rect(x, y, text.get_width(), text.get_height()))
            marker = "> " if sel else "  "
            text = self.menu_font.render(f"{marker}{opt}", True, color)
            x = rect.centerx - text.get_width() // 2
            y = start_y + i * 40
            surface.blit(text, (x, y))
