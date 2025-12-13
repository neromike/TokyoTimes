import pygame
from typing import Any
from core.scene import Scene
from world.world import World
from world.camera import Camera

class WorldScene:
    def __init__(self, game: Any):
        self.game = game
        self.world = World()
        self.camera = Camera()
        self.font = pygame.font.Font(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.stack.pop()

    def update(self, dt: float) -> None:
        self.world.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.world.draw(surface, self.camera)
        surface.blit(self.font.render("World", True, (255,255,255)), (8,8))
