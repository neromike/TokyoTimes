import pygame
from entities.character import Character
from entities.components.animation import Spritesheet, Animation
from entities.player_config import (
    PLAYER_HITBOX_WIDTH,
    PLAYER_HITBOX_HEIGHT,
    PLAYER_HITBOX_OFFSET_CENTERX,
    PLAYER_HITBOX_OFFSET_BOTTOM,
    PLAYER_SPEED,
    PLAYER_SPRITE_SCALE,
)

class Player(Character):
    def __init__(self, x: float = 0, y: float = 0, game=None):
        self.game = game
        self.animation = None
        self.spritesheet = None
        sprite = None
        self.direction = "down"
        self.animations = {}
        self.collision_rects = []  # Will be set by scene
        self.collision_rect = pygame.Rect(0, 0, PLAYER_HITBOX_WIDTH, PLAYER_HITBOX_HEIGHT)  # Small hitbox for feet area
        
        if game:
            try:
                sheet_img = game.assets.image("sprites/girl.png")
                # 870x1320 image, 3x3 grid with each frame being 290x440
                self.spritesheet = Spritesheet(sheet_img, frame_width=290, frame_height=440)
                
                # Animation order: 1-2-1-3 for a nicer ping-pong loop
                self.animations["down"] = self._create_animation([0, 1, 0, 2])
                self.animations["up"] = self._create_animation([3, 4, 3, 5])
                self.animations["left"] = self._create_animation([6, 7, 6, 8])
                self.animations["right"] = self._create_animation_mirrored([6, 7, 6, 8])
                
                self.animation = self.animations["down"]
                sprite = self.spritesheet.get_frame(0)
            except Exception as e:
                print(f"Warning: Could not load girl spritesheet: {e}")
                sprite = pygame.Surface((290, 440))
                sprite.fill((100, 200, 250))
        
        super().__init__(x, y, sprite)
        self.speed = PLAYER_SPEED
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
        
        # Calculate new position
        old_x, old_y = self.x, self.y
        new_x = self.x + self.velocity_x * dt
        new_y = self.y + self.velocity_y * dt
        
        # Check collision - mask-based or rect-based
        if hasattr(self, 'mask_system') and self.mask_system:
            # Mask-based collision with proper diagonal sliding
            old_rect = self.collision_rect.copy()
            old_rect.centerx = int(old_x) + PLAYER_HITBOX_OFFSET_CENTERX
            old_rect.bottom = int(old_y) + PLAYER_HITBOX_OFFSET_BOTTOM

            new_rect = self.collision_rect.copy()
            new_rect.centerx = int(new_x) + PLAYER_HITBOX_OFFSET_CENTERX
            new_rect.bottom = int(new_y) + PLAYER_HITBOX_OFFSET_BOTTOM
            
            # Check if new position collides
            if not self.mask_system.rect_collides(new_rect):
                # No collision - allow full movement
                pass
            else:
                # Collision detected - try sliding along the wall
                slide_distance = 10  # pixels to search for valid slide
                found_slide = False
                
                # Determine primary movement direction
                dx = abs(new_x - old_x)
                dy = abs(new_y - old_y)
                
                if dx > dy:
                    # Primarily horizontal movement - try sliding vertically
                    for y_offset in range(-slide_distance, slide_distance + 1):
                        test_y = new_y + y_offset
                        test_rect = self.collision_rect.copy()
                        test_rect.centerx = int(new_x) + PLAYER_HITBOX_OFFSET_CENTERX
                        test_rect.bottom = int(test_y) + PLAYER_HITBOX_OFFSET_BOTTOM
                        
                        if not self.mask_system.rect_collides(test_rect):
                            new_y = test_y
                            found_slide = True
                            break
                else:
                    # Primarily vertical movement - try sliding horizontally
                    for x_offset in range(-slide_distance, slide_distance + 1):
                        test_x = new_x + x_offset
                        test_rect = self.collision_rect.copy()
                        test_rect.centerx = int(test_x) + PLAYER_HITBOX_OFFSET_CENTERX
                        test_rect.bottom = int(new_y) + PLAYER_HITBOX_OFFSET_BOTTOM
                        
                        if not self.mask_system.rect_collides(test_rect):
                            new_x = test_x
                            found_slide = True
                            break
                
                if not found_slide:
                    # Can't slide - try simple axis-aligned movement
                    test_rect_x = self.collision_rect.copy()
                    test_rect_x.centerx = int(new_x) + PLAYER_HITBOX_OFFSET_CENTERX
                    test_rect_x.bottom = int(old_y) + PLAYER_HITBOX_OFFSET_BOTTOM
                    
                    test_rect_y = self.collision_rect.copy()
                    test_rect_y.centerx = int(old_x) + PLAYER_HITBOX_OFFSET_CENTERX
                    test_rect_y.bottom = int(new_y) + PLAYER_HITBOX_OFFSET_BOTTOM
                    
                    if not self.mask_system.rect_collides(test_rect_x):
                        new_y = old_y
                    elif not self.mask_system.rect_collides(test_rect_y):
                        new_x = old_x
                    else:
                        new_x, new_y = old_x, old_y
            
            # Update collision rect to resolved position
            self.collision_rect.centerx = int(new_x) + PLAYER_HITBOX_OFFSET_CENTERX
            self.collision_rect.bottom = int(new_y) + PLAYER_HITBOX_OFFSET_BOTTOM
            
            self.velocity_x = (new_x - old_x) / dt if dt > 0 else 0
            self.velocity_y = (new_y - old_y) / dt if dt > 0 else 0
            
        elif self.collision_rects:
            # Rect-based collision
            from world.collisions import Collisions
            # Build old and new collision rects based on sprite movement
            old_rect = self.collision_rect.copy()
            old_rect.centerx = int(old_x) + PLAYER_HITBOX_OFFSET_CENTERX
            old_rect.bottom = int(old_y) + PLAYER_HITBOX_OFFSET_BOTTOM

            new_rect = self.collision_rect.copy()
            new_rect.centerx = int(new_x) + PLAYER_HITBOX_OFFSET_CENTERX
            new_rect.bottom = int(new_y) + PLAYER_HITBOX_OFFSET_BOTTOM

            valid_rx, valid_ry = Collisions.get_valid_rect_position(
                old_rect, new_rect, self.collision_rects
            )

            # Derive valid sprite top-left from rect using offsets
            # Convert rect top-left back to sprite top-left
            # sprite_x = rect_x - offset_centerx + rect_width/2
            valid_x = valid_rx - PLAYER_HITBOX_OFFSET_CENTERX + (self.collision_rect.width // 2)
            # sprite_y = rect_y + rect_height - offset_bottom
            valid_y = valid_ry + self.collision_rect.height - PLAYER_HITBOX_OFFSET_BOTTOM

            self.velocity_x = (valid_x - old_x) / dt if dt > 0 else 0
            self.velocity_y = (valid_y - old_y) / dt if dt > 0 else 0
            
            # Update the live collision rect to the resolved coordinates for debug drawing
            self.collision_rect.x = valid_rx
            self.collision_rect.y = valid_ry
        
        super().update(dt)
        if self.animation and self.spritesheet:
            # Only animate when moving
            if moving:
                self.animation.update(dt)
            frame_idx = getattr(self.animation, 'frame_indices', [0])[self.animation.current_frame % len(getattr(self.animation, 'frame_indices', [0]))]
            self.sprite = self.spritesheet.get_frame(frame_idx)
            
            if hasattr(self.animation, 'mirrored') and self.animation.mirrored:
                self.sprite = pygame.transform.flip(self.sprite, True, False)
            
            # Scale sprite
            if self.sprite:
                new_width = int(self.sprite.get_width() * PLAYER_SPRITE_SCALE)
                new_height = int(self.sprite.get_height() * PLAYER_SPRITE_SCALE)
                self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))

    def draw(self, surface: pygame.Surface) -> None:
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
