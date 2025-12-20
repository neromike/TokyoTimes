"""Generic scene that loads configuration from JSON files in data/rooms/."""
import pygame
from typing import Any
from scenes.base_scene import MaskedScene


class GenericScene(MaskedScene):
    """A generic scene that loads all configuration from a JSON file.
    
    Usage:
        scene = GenericScene(game, scene_name="cat_cafe", spawn=(100, 200))
    """
    
    def __init__(self, game: Any, scene_name: str = None, spawn: tuple = None):
        # Set SCENE_NAME before calling super().__init__
        # This allows base class to load the JSON config
        if scene_name:
            self.SCENE_NAME = scene_name
        
        super().__init__(game, spawn)
        
        # Update player's prop reference if player exists
        if hasattr(self, 'player') and self.player:
            self.player.props = self.props
    
    def update(self, dt: float) -> None:
        super().update(dt)
        for prop in self.props:
            prop.update(dt)
    
    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        # Optional: Draw scene name for debugging
        if self.scene_name:
            display_name = self.scene_name.replace('_', ' ').title()
            surface.blit(self.font.render(display_name, True, (255, 255, 255)), (8, 8))
