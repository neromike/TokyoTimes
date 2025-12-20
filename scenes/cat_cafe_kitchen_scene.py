import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene


class CatCafeKitchenScene(MaskedScene):
    SCENE_NAME = "cat_cafe_kitchen"
    # Configuration loaded from data/rooms/cat_cafe_kitchen.json
    
    def __init__(self, game: Any, spawn: tuple = None):
        super().__init__(game, spawn)
        
        # Update player's prop reference if player exists
        if hasattr(self, 'player'):
            self.player.props = self.props
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        surface.blit(self.font.render("Kitchen", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("cat_cafe_kitchen", CatCafeKitchenScene)
