# Currently unused

import pygame

class Room:
    def __init__(self, data: dict):
        self.data = data
        self.id = data.get("id", "room")
        self.spawn_points = data.get("spawn_points", {})
        self.portals = data.get("portals", [])
        self.interactables = data.get("interactables", [])

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera) -> None:
        surface.fill((30, 30, 40))
