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
    def __init__(self, x: float = 0, y: float = 0, game=None, 
                 hitbox_width: int = None, hitbox_height: int = None,
                 hitbox_offset_centerx: int = None, hitbox_offset_bottom: int = None,
                 sprite_scale: float = None, speed: int = None):
        self.game = game
        self.animation = None
        self.spritesheet = None
        sprite = None
        self.direction = "down"
        self.animations = {}
        self.collision_rects = []  # Will be set by scene
        self.props = []  # List of props in the scene (set by scene)
        
        # Use custom values or defaults
        hitbox_width = hitbox_width if hitbox_width is not None else PLAYER_HITBOX_WIDTH
        hitbox_height = hitbox_height if hitbox_height is not None else PLAYER_HITBOX_HEIGHT
        hitbox_offset_centerx = hitbox_offset_centerx if hitbox_offset_centerx is not None else PLAYER_HITBOX_OFFSET_CENTERX
        hitbox_offset_bottom = hitbox_offset_bottom if hitbox_offset_bottom is not None else PLAYER_HITBOX_OFFSET_BOTTOM
        sprite_scale = sprite_scale if sprite_scale is not None else PLAYER_SPRITE_SCALE
        speed = speed if speed is not None else PLAYER_SPEED
        
        self.collision_rect = pygame.Rect(0, 0, hitbox_width, hitbox_height)  # Small hitbox for feet area
        self.hitbox_offset_centerx = hitbox_offset_centerx
        self.hitbox_offset_bottom = hitbox_offset_bottom
        self.sprite_scale = sprite_scale
        
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
                
                # Scale sprite if needed
                if sprite_scale and sprite_scale != 1.0:
                    new_width = int(sprite.get_width() * sprite_scale)
                    new_height = int(sprite.get_height() * sprite_scale)
                    sprite = pygame.transform.scale(sprite, (new_width, new_height))
            except Exception as e:
                print(f"Warning: Could not load girl spritesheet: {e}")
                sprite = pygame.Surface((290, 440))
                sprite.fill((100, 200, 250))
        
        super().__init__(x, y, sprite)
        self.speed = speed
        self.last_direction = "down"

    def _create_animation(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=10, scale=self.sprite_scale)
        anim.frame_indices = frame_indices
        return anim

    def _create_animation_mirrored(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=10, scale=self.sprite_scale)
        anim.frame_indices = frame_indices
        anim.mirrored = True
        return anim
    
    def _rect_collides_with_props(self, rect: pygame.Rect) -> bool:
        """Check if rect collides with any prop mask.
        Black pixels = walkable, transparent = blocked, other colors = blocked.
        """
        for prop in self.props:
            if not hasattr(prop, 'mask') or not prop.mask or not hasattr(prop, 'x') or not hasattr(prop, 'y'):
                continue
            
            # Check if rect overlaps with prop's bounding box
            prop_rect = pygame.Rect(prop.x, prop.y, prop.mask.get_width(), prop.mask.get_height())
            if not rect.colliderect(prop_rect):
                continue
            
            # Sample collision points within the mask
            # Check corners and center of the rect
            sample_points = [
                (rect.left, rect.top),
                (rect.right - 1, rect.top),
                (rect.left, rect.bottom - 1),
                (rect.right - 1, rect.bottom - 1),
                (rect.centerx, rect.centery),
            ]
            
            for px, py in sample_points:
                # Convert world coordinates to prop mask coordinates
                local_x = int(px - prop.x)
                local_y = int(py - prop.y)
                
                # Check if point is within mask bounds
                if 0 <= local_x < prop.mask.get_width() and 0 <= local_y < prop.mask.get_height():
                    try:
                        # Get pixel color at this position
                        color = prop.mask.get_at((local_x, local_y))
                        
                        # Check if transparent (alpha = 0)
                        if len(color) >= 4 and color[3] == 0:
                            # Transparent - collision!
                            return True
                        elif len(color) >= 3:
                            # Check if it's black (walkable): (0, 0, 0) or close to it
                            r, g, b = color[0], color[1], color[2]
                            is_black = r < 50 and g < 50 and b < 50  # Allow slight variance
                            
                            if not is_black and color[3] > 0 if len(color) >= 4 else True:
                                # Not black and not transparent - collision!
                                return True
                    except Exception as e:
                        print(f"Error checking prop collision: {e}")
                        continue
        
        return False

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
        
        # Normalize diagonal movement to maintain consistent speed
        if self.velocity_x != 0 and self.velocity_y != 0:
            # Moving diagonally - normalize to maintain speed
            import math
            magnitude = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
            self.velocity_x = (self.velocity_x / magnitude) * self.speed
            self.velocity_y = (self.velocity_y / magnitude) * self.speed
        
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
            old_rect.centerx = int(old_x) + self.hitbox_offset_centerx
            old_rect.bottom = int(old_y) + self.hitbox_offset_bottom

            new_rect = self.collision_rect.copy()
            new_rect.centerx = int(new_x) + self.hitbox_offset_centerx
            new_rect.bottom = int(new_y) + self.hitbox_offset_bottom
            
            # Check if new position collides with room or props
            room_collides = self.mask_system.rect_collides(new_rect)
            prop_collides = self._rect_collides_with_props(new_rect)
            
            if not room_collides and not prop_collides:
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
                        test_rect.centerx = int(new_x) + self.hitbox_offset_centerx
                        test_rect.bottom = int(test_y) + self.hitbox_offset_bottom
                        
                        if not self.mask_system.rect_collides(test_rect) and not self._rect_collides_with_props(test_rect):
                            new_y = test_y
                            found_slide = True
                            break
                else:
                    # Primarily vertical movement - try sliding horizontally
                    for x_offset in range(-slide_distance, slide_distance + 1):
                        test_x = new_x + x_offset
                        test_rect = self.collision_rect.copy()
                        test_rect.centerx = int(test_x) + self.hitbox_offset_centerx
                        test_rect.bottom = int(new_y) + self.hitbox_offset_bottom
                        
                        if not self.mask_system.rect_collides(test_rect) and not self._rect_collides_with_props(test_rect):
                            new_x = test_x
                            found_slide = True
                            break
                
                if not found_slide:
                    # Can't slide - try simple axis-aligned movement
                    test_rect_x = self.collision_rect.copy()
                    test_rect_x.centerx = int(new_x) + self.hitbox_offset_centerx
                    test_rect_x.bottom = int(old_y) + self.hitbox_offset_bottom
                    
                    test_rect_y = self.collision_rect.copy()
                    test_rect_y.centerx = int(old_x) + self.hitbox_offset_centerx
                    test_rect_y.bottom = int(new_y) + self.hitbox_offset_bottom
                    
                    if not self.mask_system.rect_collides(test_rect_x) and not self._rect_collides_with_props(test_rect_x):
                        new_y = old_y
                    elif not self.mask_system.rect_collides(test_rect_y) and not self._rect_collides_with_props(test_rect_y):
                        new_x = old_x
                    else:
                        new_x, new_y = old_x, old_y
            
            # Update collision rect to resolved position
            self.collision_rect.centerx = int(new_x) + self.hitbox_offset_centerx
            self.collision_rect.bottom = int(new_y) + self.hitbox_offset_bottom
            
            self.velocity_x = (new_x - old_x) / dt if dt > 0 else 0
            self.velocity_y = (new_y - old_y) / dt if dt > 0 else 0
            
        elif self.collision_rects:
            # Rect-based collision
            from world.collisions import Collisions
            # Build old and new collision rects based on sprite movement
            old_rect = self.collision_rect.copy()
            old_rect.centerx = int(old_x) + self.hitbox_offset_centerx
            old_rect.bottom = int(old_y) + self.hitbox_offset_bottom

            new_rect = self.collision_rect.copy()
            new_rect.centerx = int(new_x) + self.hitbox_offset_centerx
            new_rect.bottom = int(new_y) + self.hitbox_offset_bottom

            valid_rx, valid_ry = Collisions.get_valid_rect_position(
                old_rect, new_rect, self.collision_rects
            )

            # Derive valid sprite top-left from rect using offsets
            # Convert rect top-left back to sprite top-left
            # sprite_x = rect_x - offset_centerx + rect_width/2
            valid_x = valid_rx - self.hitbox_offset_centerx + (self.collision_rect.width // 2)
            # sprite_y = rect_y + rect_height - offset_bottom
            valid_y = valid_ry + self.collision_rect.height - self.hitbox_offset_bottom

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
            # Get current frame (with scaling applied)
            self.sprite = self.animation.get_current_frame()

    def draw(self, surface: pygame.Surface) -> None:
        if self.sprite:
            surface.blit(self.sprite, (self.x, self.y))
