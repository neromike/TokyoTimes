import pygame
from entities.character import Character
from entities.components.animation import Spritesheet, Animation

class Player(Character):
    def __init__(self, x: float = 0, y: float = 0, game=None):
        self.game = game
        self.animation = None
        self.spritesheet = None
        sprite = None
        self.direction = "down"
        self.animations = {}
        
        if game:
            try:
                sheet_img = game.assets.image("sprites/girl.png")
                # 870x1320 image, 3x3 grid with each frame being 290x440
                self.spritesheet = Spritesheet(sheet_img, frame_width=290, frame_height=440)
                
                self.animations["down"] = self._create_animation([0, 1, 2])
                self.animations["up"] = self._create_animation([3, 4, 5])
                self.animations["left"] = self._create_animation([6, 7, 8])
                self.animations["right"] = self._create_animation_mirrored([6, 7, 8])
                
                self.animation = self.animations["down"]
                sprite = self.spritesheet.get_frame(0)
            except Exception as e:
                print(f"Warning: Could not load girl spritesheet: {e}")
                sprite = pygame.Surface((290, 440))
                sprite.fill((100, 200, 250))
        
        super().__init__(x, y, sprite)
        self.speed = 300
        self.last_direction = "down"

    def _create_animation(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=10)
        anim.frame_indices = frame_indices
        return anim

    def _create_animation_mirrored(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=10)
        anim.frame_indices = frame_indices
        anim.mirrored = True
        return anim

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self.velocity_x = 0
        self.velocity_y = 0
        moving = False
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.velocity_y = -self.speed
            self.direction = "up"
            moving = True
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.velocity_y = self.speed
            self.direction = "down"
            moving = True
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity_x = -self.speed
            self.direction = "left"
            moving = True
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity_x = self.speed
            self.direction = "right"
            moving = True
        
        if moving:
            self.last_direction = self.direction
            if self.direction in self.animations:
                self.animation = self.animations[self.direction]
        
        super().update(dt)
        if self.animation and self.spritesheet:
            # Only animate when moving
            if moving:
                self.animation.update(dt)
            frame_idx = getattr(self.animation, 'frame_indices', [0])[self.animation.current_frame % len(getattr(self.animation, 'frame_indices', [0]))]
            self.sprite = self.spritesheet.get_frame(frame_idx)
            
            if hasattr(self.animation, 'mirrored') and self.animation.mirrored:
                self.sprite = pygame.transform.flip(self.sprite, True, False)
            
            # Scale to 50%
            if self.sprite:
                new_width = int(self.sprite.get_width() * 0.5)
                new_height = int(self.sprite.get_height() * 0.5)
                self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))

    def draw(self, surface: pygame.Surface) -> None:
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
