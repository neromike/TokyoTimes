import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene
from entities.interactables import ArcadeCabinet


# Portal mapping: portal_id (from white regions in mask) -> scene configuration
# To find portal IDs, run the game with debug enabled and check console output
PORTAL_MAP = {
    0: {
        "to_scene": "cat_cafe_kitchen",
        "spawn": (1085, 460),
    },
    1: {
        "to_scene": "cat_cafe_kitchen",
        "spawn": (1085, 460),
    },
}


class CatCafeScene(MaskedScene):
    BACKGROUND_PATH = "backgrounds/cat_cafe.jpg"
    PORTAL_MAP = PORTAL_MAP
    PLAYER_SPRITE_SCALE = 0.5
    
    # Prop positions - configure here
    ARCADE_CABINET_POS = (600, 350)
    
    def __init__(self, game: Any, spawn: tuple = None):
        super().__init__(game, spawn)
        
        # Add props
        self.arcade_cabinet = ArcadeCabinet(x=self.ARCADE_CABINET_POS[0], y=self.ARCADE_CABINET_POS[1], game=game)
        self.props = [self.arcade_cabinet]
    
    def update(self, dt: float) -> None:
        super().update(dt)
        for prop in self.props:
            prop.update(dt)
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        # Draw props after base scene with camera transformation
        for prop in self.props:
            prop.draw(surface, camera=self.camera)
        surface.blit(self.font.render("Cat Cafe (ESC for inventory)", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("cat_cafe", CatCafeScene)
