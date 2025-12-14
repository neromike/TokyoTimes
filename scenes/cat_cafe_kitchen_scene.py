import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene


# Portal mapping: portal_id (from white regions in mask) -> scene configuration
PORTAL_MAP = {
    0: {
        "to_scene": "cat_cafe",
        "spawn": (650, 920),
    },
}


class CatCafeKitchenScene(MaskedScene):
    BACKGROUND_PATH = "backgrounds/cat_cafe_kitchen.jpg"
    PORTAL_MAP = PORTAL_MAP
    PLAYER_SPRITE_SCALE = 0.6
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        surface.blit(self.font.render("Kitchen (ESC for inventory)", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("cat_cafe_kitchen", CatCafeKitchenScene)
