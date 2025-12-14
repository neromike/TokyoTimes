import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene
from entities.interactables import ArcadeCabinet, ArcadeCabinetBlocks


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
    ARCADE_BLOCKS_POS = (740, 350)
    
    def __init__(self, game: Any, spawn: tuple = None):
        # Initialize props list before calling super().__init__ so player can access it
        self.props = []
        
        super().__init__(game, spawn)
        
        # Add props to the scene
        self.arcade_cabinet = ArcadeCabinet(x=self.ARCADE_CABINET_POS[0], y=self.ARCADE_CABINET_POS[1], game=game)
        self.arcade_cabinet_blocks = ArcadeCabinetBlocks(x=self.ARCADE_BLOCKS_POS[0], y=self.ARCADE_BLOCKS_POS[1], game=game)
        self.props = [self.arcade_cabinet, self.arcade_cabinet_blocks]
        # Update player's prop reference
        self.player.props = self.props
    
    def update(self, dt: float) -> None:
        super().update(dt)
        for prop in self.props:
            prop.update(dt)
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        # Base scene now handles depth-sorted drawing of player and props
        surface.blit(self.font.render("Cat Cafe (ESC for inventory)", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("cat_cafe", CatCafeScene)
