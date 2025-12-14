import pygame

class Interactable:
    def __init__(self, rect):
        self.rect = rect

    def interact(self, actor):
        pass


class ArcadeCabinet:
    """Arcade cabinet prop that can be placed in a scene."""
    def __init__(self, x: float, y: float, game=None):
        self.x = x
        self.y = y
        self.game = game
        self.sprite = None
        self.mask = None  # Collision mask for the prop
        
        # Load arcade cabinet image
        if game:
            try:
                self.sprite = game.assets.image("props/arcade_cabinet_spaceship.png")
            except Exception as e:
                print(f"Warning: Could not load arcade cabinet: {e}")
                # Create placeholder
                self.sprite = pygame.Surface((128, 192))
                self.sprite.fill((100, 100, 100))
            
            # Load arcade cabinet mask
            try:
                self.mask = game.assets.image("props/arcade_cabinet_spaceship_mask.png")
            except Exception as e:
                print(f"Warning: Could not load arcade cabinet mask: {e}")
        
        if self.sprite:
            self.rect = self.sprite.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 128, 192)
    
    def update(self, dt: float) -> None:
        """Update arcade cabinet (position, animation, etc)."""
        pass
    
    def draw(self, surface: pygame.Surface, camera=None) -> None:
        """Draw arcade cabinet to surface."""
        if self.sprite:
            if camera:
                screen_x, screen_y = camera.apply(self.x, self.y)
            else:
                screen_x, screen_y = self.x, self.y
            surface.blit(self.sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, (100, 100, 100), self.rect)


class ArcadeCabinetBlocks:
    """Variant arcade cabinet (blocks theme) with its own sprite and mask."""
    def __init__(self, x: float, y: float, game=None):
        self.x = x
        self.y = y
        self.game = game
        self.sprite = None
        self.mask = None

        if game:
            try:
                self.sprite = game.assets.image("props/arcade_cabinet_blocks.png")
            except Exception as e:
                print(f"Warning: Could not load arcade cabinet blocks sprite: {e}")
                self.sprite = pygame.Surface((128, 192))
                self.sprite.fill((120, 120, 120))

            try:
                self.mask = game.assets.image("props/arcade_cabinet_blocks_mask.png")
            except Exception as e:
                print(f"Warning: Could not load arcade cabinet blocks mask: {e}")

        if self.sprite:
            self.rect = self.sprite.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 128, 192)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        if self.sprite:
            if camera:
                screen_x, screen_y = camera.apply(self.x, self.y)
            else:
                screen_x, screen_y = self.x, self.y
            surface.blit(self.sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, (120, 120, 120), self.rect)
