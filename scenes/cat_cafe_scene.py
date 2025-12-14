import pygame
from typing import Any
from scenes.base_scene import MaskedScene
from scenes.scene_registry import register_scene
from entities.prop_registry import make_prop


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
    SCENE_NAME = "cat_cafe"
    
    # Prop positions - configure here
    ARCADE_CABINET_POS = (600, 350)
    ARCADE_BLOCKS_POS = (740, 350)
    CAT_FOOD_DISH_POS = (850, 650)
    
    def __init__(self, game: Any, spawn: tuple = None):
        # Initialize props list before calling super().__init__ so player can access it
        self.props = []
        
        super().__init__(game, spawn)
        
        # Add props to the scene, but skip items that have been picked up
        self.arcade_cabinet = make_prop("arcade_spaceship", self.ARCADE_CABINET_POS[0], self.ARCADE_CABINET_POS[1], game)
        self.arcade_cabinet_blocks = make_prop("arcade_blocks", self.ARCADE_BLOCKS_POS[0], self.ARCADE_BLOCKS_POS[1], game)
        
        # Create cat_food_dish, but check if it was already picked up globally
        cat_food_dish_id = f"cat_food_dish:{int(self.CAT_FOOD_DISH_POS[0])}:{int(self.CAT_FOOD_DISH_POS[1])}"
        if cat_food_dish_id not in game.picked_up_items:
            self.cat_food_dish = make_prop("cat_food_dish", self.CAT_FOOD_DISH_POS[0], self.CAT_FOOD_DISH_POS[1], game, scale=2.0)
            self.props = [self.arcade_cabinet, self.arcade_cabinet_blocks, self.cat_food_dish]
        else:
            # Item was picked up, don't spawn it
            self.props = [self.arcade_cabinet, self.arcade_cabinet_blocks]
        
        # Spawn any items that were dropped in this scene
        if self.SCENE_NAME in game.dropped_items:
            for dropped_item in game.dropped_items[self.SCENE_NAME]:
                dropped_prop = make_prop(
                    dropped_item['name'],
                    dropped_item['x'],
                    dropped_item['y'],
                    game,
                    variant_index=dropped_item.get('variant_index', 0),
                    scale=dropped_item.get('scale', None)
                )
                self.props.append(dropped_prop)
        
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
