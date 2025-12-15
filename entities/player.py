import pygame
from entities.character import Character
from entities.components.animation import Spritesheet, Animation
from core.sprites import SpriteLoader
from core.sprite_registry import get_sprite_config
from core.collision_masks import CollisionMaskExtractor
from entities.components.inventory import Inventory
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
        self.props = []  # Scene props for collision/interact
        self.interact_prop = None  # Prop currently interactable under hitbox
        self.inventory = Inventory()  # Player inventory for items
        self.props = []  # List of props in the scene (set by scene)
        
        # Use custom values or defaults
        hitbox_width = hitbox_width if hitbox_width is not None else PLAYER_HITBOX_WIDTH
        hitbox_height = hitbox_height if hitbox_height is not None else PLAYER_HITBOX_HEIGHT
        hitbox_offset_centerx = hitbox_offset_centerx if hitbox_offset_centerx is not None else PLAYER_HITBOX_OFFSET_CENTERX
        hitbox_offset_bottom = hitbox_offset_bottom if hitbox_offset_bottom is not None else PLAYER_HITBOX_OFFSET_BOTTOM
        # Default scale: provided -> scene/player_config -> sprite registry
        registry_scale = 1.0
        if game:
            try:
                registry_scale = get_sprite_config("player_girl").get("scale", 1.0)
            except Exception:
                registry_scale = 1.0
        sprite_scale = sprite_scale if sprite_scale is not None else (PLAYER_SPRITE_SCALE if PLAYER_SPRITE_SCALE is not None else registry_scale)
        speed = speed if speed is not None else PLAYER_SPEED
        
        self.collision_rect = pygame.Rect(0, 0, hitbox_width, hitbox_height)  # Kept for compatibility
        self.sprite_scale = sprite_scale
        self.collision_mask_extractor = None  # Will be loaded if mask exists
        
        if game:
            try:
                loader = SpriteLoader(game.assets)
                girl_cfg = get_sprite_config("player_girl")
                sheet_img = game.assets.image(girl_cfg["path"]) 
                self.spritesheet = Spritesheet(sheet_img, frame_width=girl_cfg["frame_width"], frame_height=girl_cfg["frame_height"]) 
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
                
                # Try to load collision mask
                try:
                    mask_img = game.assets.image("sprites/girl_mask.png")
                    self.collision_mask_extractor = CollisionMaskExtractor(
                        mask_img,
                        variants=3,  # 3x3 grid (3 columns)
                        frame_width=girl_cfg["frame_width"],
                        frame_height=girl_cfg["frame_height"]
                    )
                    print("Loaded collision mask for player")
                except Exception as e:
                    print(f"Warning: Could not load player collision mask: {e}")
            except Exception as e:
                print(f"Warning: Could not load girl spritesheet: {e}")
                sprite = pygame.Surface((290, 440))
                sprite.fill((100, 200, 250))
        
        super().__init__(x, y, sprite)
        self.speed = speed
        self.last_direction = "down"
    
    def _get_frame_collision_box(self) -> pygame.Rect:
        """Get the collision box for the current animation frame, scaled and positioned."""
        if not self.collision_mask_extractor or not self.animation:
            return None
        
        # Get the current frame index from animation
        frame_idx = self.animation.current_frame if hasattr(self.animation, 'current_frame') else 0
        
        # Get collision box from mask (relative to frame origin in unscaled coords)
        collision_box = self.collision_mask_extractor.get_frame_collision_box(frame_idx)
        
        # Scale the collision box
        scaled_box = pygame.Rect(
            int(collision_box.x * self.sprite_scale),
            int(collision_box.y * self.sprite_scale),
            int(collision_box.width * self.sprite_scale),
            int(collision_box.height * self.sprite_scale)
        )
        
        return scaled_box

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
        """Check if rect collides with any prop using pre-computed collision boxes."""
        for prop in self.props:
            # Skip picked-up items
            if getattr(prop, 'picked_up', False):
                continue
            
            # Get prop scale
            prop_scale = getattr(prop, 'scale', 1.0)
            
            # Check collision rects (blocking areas)
            if hasattr(prop, 'collision_rects'):
                for collision_rect in prop.collision_rects:
                    # Scale and position the rect
                    scaled_rect = pygame.Rect(
                        int(prop.x + collision_rect.x * prop_scale),
                        int(prop.y + collision_rect.y * prop_scale),
                        int(collision_rect.width * prop_scale),
                        int(collision_rect.height * prop_scale)
                    )
                    if rect.colliderect(scaled_rect):
                        return True
            
            # Check interaction rects (mark as interactable but don't block)
            if hasattr(prop, 'interaction_rects'):
                for interaction_rect in prop.interaction_rects:
                    # Scale and position the rect
                    scaled_rect = pygame.Rect(
                        int(prop.x + interaction_rect.x * prop_scale),
                        int(prop.y + interaction_rect.y * prop_scale),
                        int(interaction_rect.width * prop_scale),
                        int(interaction_rect.height * prop_scale)
                    )
                    if rect.colliderect(scaled_rect):
                        self.interact_prop = prop
        
        return False

    def update(self, dt: float) -> None:
        # Reset interactable each frame
        self.interact_prop = None
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
        
        # Check collision - mask-based only
        if hasattr(self, 'mask_system') and self.mask_system:
            # Get collision rect for current frame from mask
            if not self.collision_mask_extractor or not self.animation:
                # No mask available - skip collision
                self.x = new_x
                self.y = new_y
                return
            
            collision_box = self._get_frame_collision_box()
            if not collision_box:
                # Failed to get collision box - skip collision
                self.x = new_x
                self.y = new_y
                return
            
            # Use frame-based collision mask
            old_rect = collision_box.copy()
            old_rect.x += int(old_x)
            old_rect.y += int(old_y)
            
            new_rect = collision_box.copy()
            new_rect.x += int(new_x)
            new_rect.y += int(new_y)
            
            # Check if new position collides with room or props
            room_collides = self.mask_system.rect_collides(new_rect)
            prop_collides = self._rect_collides_with_props(new_rect)
            
            if room_collides or prop_collides:
                # Collision detected - try sliding along walls
                # Calculate movement deltas
                dx = new_x - old_x
                dy = new_y - old_y
                
                import math
                movement_magnitude = math.sqrt(dx*dx + dy*dy)
                
                # Generate slide attempts
                slide_attempts = []
                
                # Try axis-aligned slides first (for diagonal movement into straight walls)
                if dx != 0:
                    slide_attempts.append((dx, 0))  # X-only
                if dy != 0:
                    slide_attempts.append((0, dy))  # Y-only
                
                # Try diagonal slides (for cardinal movement into diagonal walls)
                # Only try slides that maintain some original direction
                if movement_magnitude > 0:
                    if abs(dx) >= abs(dy):
                        # Moving horizontally - try diagonal slides with perpendicular component
                        slide_attempts.extend([
                            (dx * 0.7, movement_magnitude * 0.7),   # Diagonal up
                            (dx * 0.7, -movement_magnitude * 0.7),  # Diagonal down
                            (dx * 0.5, movement_magnitude * 0.5),
                            (dx * 0.5, -movement_magnitude * 0.5),
                        ])
                    else:
                        # Moving vertically - try diagonal slides with perpendicular component
                        slide_attempts.extend([
                            (movement_magnitude * 0.7, dy * 0.7),   # Diagonal right
                            (-movement_magnitude * 0.7, dy * 0.7),  # Diagonal left
                            (movement_magnitude * 0.5, dy * 0.5),
                            (-movement_magnitude * 0.5, dy * 0.5),
                        ])
                    
                    # Also try reduced movement
                    slide_attempts.extend([
                        (dx * 0.7, dy * 0.7),
                        (dx * 0.5, dy * 0.5),
                    ])
                
                # Test each slide attempt
                slid = False
                for slide_dx, slide_dy in slide_attempts:
                    test_slide_rect = collision_box.copy()
                    test_slide_rect.x += int(old_x + slide_dx)
                    test_slide_rect.y += int(old_y + slide_dy)
                    
                    if not (self.mask_system.rect_collides(test_slide_rect) or self._rect_collides_with_props(test_slide_rect)):
                        new_x = old_x + slide_dx
                        new_y = old_y + slide_dy
                        slid = True
                        break
                
                # If nothing worked, stop
                if not slid:
                    new_x, new_y = old_x, old_y
            
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
