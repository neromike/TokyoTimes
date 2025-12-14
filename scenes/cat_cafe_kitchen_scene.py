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
    SCENE_NAME = "cat_cafe_kitchen"
    
    def __init__(self, game: Any, spawn: tuple = None):
        # Initialize props list before calling super().__init__
        self.props = []
        
        super().__init__(game, spawn)
        
        # Spawn any items that were dropped in this scene
        if self.SCENE_NAME in game.dropped_items:
            for dropped_item in game.dropped_items[self.SCENE_NAME]:
                from entities.prop_registry import make_prop
                dropped_prop = make_prop(
                    dropped_item['name'],
                    dropped_item['x'],
                    dropped_item['y'],
                    game,
                    variant_index=dropped_item.get('variant_index', 0),
                    scale=dropped_item.get('scale', None)
                )
                self.props.append(dropped_prop)
        
        # Update player's prop reference if player exists
        if hasattr(self, 'player'):
            self.player.props = self.props
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        surface.blit(self.font.render("Kitchen (ESC for inventory)", True, (255, 255, 255)), (8, 8))


# Register this scene
register_scene("cat_cafe_kitchen", CatCafeKitchenScene)
