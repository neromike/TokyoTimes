import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene


class ArcadeScene(MaskedScene):
    SCENE_NAME = "arcade"
    # Configuration loaded from data/rooms/arcade.json

    def __init__(self, game: Any, spawn: tuple = None):
        super().__init__(game, spawn)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        surface.blit(self.font.render("Arcade", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("arcade", ArcadeScene)
