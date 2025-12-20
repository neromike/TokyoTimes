"""Generic data-driven scenes loaded from JSON configuration.

This module provides GenericScene - the recommended approach for creating
world scenes without writing Python subclasses.

How GenericScene Works:
========================

1. Create a JSON file: data/rooms/{scene_name}.json
2. Define: background, scale, portals
3. GenericScene automatically loads and uses this configuration
4. scene_registry.py auto-discovers and registers the scene

Example JSON (data/rooms/cat_cafe.json):
    {
      "scene_name": "cat_cafe",
      "background": "backgrounds/cat_cafe.jpg",
      "scale": 1.0,
      "portals": [
        {
          "id": 0,
          "to_scene": "outdoor",
          "spawn": [107, 512]
        },
        {
          "id": 1,
          "to_scene": "cat_cafe_kitchen",
          "spawn": [512, 100]
        }
      ]
    }

Usage:
    scene = GenericScene(game, scene_name="cat_cafe")
    scene = GenericScene(game, scene_name="cat_cafe", spawn=(400, 300))

Auto-Registration:
    Scenes are auto-registered when the app starts:
    - scene_registry.py scans data/rooms/*.json
    - Creates GenericScene factories for each scene
    - Portals use scene_registry.get_scene_class() for transitions
"""
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
