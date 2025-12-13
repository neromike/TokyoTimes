import pygame
from entities.entity import Entity

class Character(Entity):
    def __init__(self, x: float = 0, y: float = 0, sprite: pygame.Surface = None):
        super().__init__(x, y)
        self.speed = 120
        self.sprite = sprite
        self.velocity_x = 0
        self.velocity_y = 0
        if sprite:
            self.rect = sprite.get_rect(topleft=(x, y))

    def update(self, dt: float) -> None:
        # Apply velocity
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Update rect position
        if self.sprite:
            self.rect.topleft = (self.x, self.y)

    def draw(self, surface: pygame.Surface) -> None:
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
        else:
            pygame.draw.rect(surface, (100,200,250), self.rect)
