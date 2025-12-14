"""Base scene class with automatic mask-based collision support."""
import pygame
from typing import Any, Optional
from entities.player import Player
from world.camera import Camera
from world.mask_collision import MaskCollisionSystem
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
from entities.player_config import (
    PLAYER_HITBOX_OFFSET_CENTERX, 
    PLAYER_HITBOX_OFFSET_BOTTOM,
    PLAYER_HITBOX_WIDTH,
    PLAYER_HITBOX_HEIGHT,
    PLAYER_SPRITE_SCALE,
    PLAYER_SPEED,
)


# Debug flag - set to False to hide collision/portal debug visuals
DEBUG_DRAW = False


class MaskedScene:
    """Base class for scenes that use mask-based collision.
    
    Automatically loads a collision mask by appending '_mask' to the background filename.
    For example: 'backgrounds/scene.jpg' -> 'backgrounds/scene_mask.png'
    
    Customize player size per scene by setting these class variables:
    - PLAYER_HITBOX_WIDTH
    - PLAYER_HITBOX_HEIGHT
    - PLAYER_HITBOX_OFFSET_CENTERX
    - PLAYER_HITBOX_OFFSET_BOTTOM
    - PLAYER_SPRITE_SCALE
    - PLAYER_SPEED
    """
    
    # Subclasses should set these
    BACKGROUND_PATH = None
    PORTAL_MAP = {}
    
    # Player customization (leave None to use defaults from player_config.py)
    PLAYER_HITBOX_WIDTH = None
    PLAYER_HITBOX_HEIGHT = None
    PLAYER_HITBOX_OFFSET_CENTERX = None
    PLAYER_HITBOX_OFFSET_BOTTOM = None
    PLAYER_SPRITE_SCALE = None
    PLAYER_SPEED = None
    
    def __init__(self, game: Any, spawn: tuple = None):
        self.game = game
        
        # Load background
        try:
            self.background = game.assets.image(self.BACKGROUND_PATH)
        except Exception as e:
            print(f"Warning: Could not load background {self.BACKGROUND_PATH}: {e}")
            self.background = None
        
        # Auto-load collision mask
        mask_path = self._get_mask_path(self.BACKGROUND_PATH)
        try:
            mask_img = game.assets.image(mask_path)
            self.mask_system = MaskCollisionSystem(mask_img)
            print(f"Loaded mask for {self.BACKGROUND_PATH}: {len(self.mask_system.portal_regions)} portal regions")
            for pid in self.mask_system.portal_regions:
                bounds = self.mask_system.get_portal_bounds(pid)
                print(f"  Portal {pid}: {bounds}")
        except Exception as e:
            print(f"Warning: Could not load mask {mask_path}: {e}")
            self.mask_system = None
        
        self.font = pygame.font.Font(None, 24)
        
        # World dimensions
        if self.background:
            self.world_width = self.background.get_width()
            self.world_height = self.background.get_height()
        else:
            self.world_width = WINDOW_WIDTH
            self.world_height = WINDOW_HEIGHT
        
        # Camera and player
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Use scene-specific player config if set, otherwise use defaults
        player_sprite_scale = self.PLAYER_SPRITE_SCALE if self.PLAYER_SPRITE_SCALE is not None else PLAYER_SPRITE_SCALE
        
        # Calculate hitbox dimensions - scale them based on sprite scale
        if self.PLAYER_HITBOX_WIDTH is None:
            player_hitbox_width = int(PLAYER_HITBOX_WIDTH * player_sprite_scale / PLAYER_SPRITE_SCALE)
        else:
            player_hitbox_width = self.PLAYER_HITBOX_WIDTH
        
        if self.PLAYER_HITBOX_HEIGHT is None:
            player_hitbox_height = int(PLAYER_HITBOX_HEIGHT * player_sprite_scale / PLAYER_SPRITE_SCALE)
        else:
            player_hitbox_height = self.PLAYER_HITBOX_HEIGHT
        
        if self.PLAYER_HITBOX_OFFSET_CENTERX is None:
            player_hitbox_offset_centerx = int(PLAYER_HITBOX_OFFSET_CENTERX * player_sprite_scale / PLAYER_SPRITE_SCALE)
        else:
            player_hitbox_offset_centerx = self.PLAYER_HITBOX_OFFSET_CENTERX
        
        if self.PLAYER_HITBOX_OFFSET_BOTTOM is None:
            player_hitbox_offset_bottom = int(PLAYER_HITBOX_OFFSET_BOTTOM * player_sprite_scale / PLAYER_SPRITE_SCALE)
        else:
            player_hitbox_offset_bottom = self.PLAYER_HITBOX_OFFSET_BOTTOM
        
        if spawn:
            # Spawn point is the center-bottom of the hitbox (feet position)
            # Convert to sprite top-left coordinates
            sprite_x = spawn[0] - player_hitbox_offset_centerx
            sprite_y = spawn[1] - player_hitbox_offset_bottom
            self.player = Player(
                x=sprite_x, y=sprite_y, game=game,
                hitbox_width=player_hitbox_width,
                hitbox_height=player_hitbox_height,
                hitbox_offset_centerx=player_hitbox_offset_centerx,
                hitbox_offset_bottom=player_hitbox_offset_bottom,
                sprite_scale=player_sprite_scale,
                speed=self.PLAYER_SPEED
            )
        else:
            self.player = Player(
                x=self.world_width // 2, y=self.world_height // 2, game=game,
                hitbox_width=player_hitbox_width,
                hitbox_height=player_hitbox_height,
                hitbox_offset_centerx=player_hitbox_offset_centerx,
                hitbox_offset_bottom=player_hitbox_offset_bottom,
                sprite_scale=player_sprite_scale,
                speed=self.PLAYER_SPEED
            )
        
        # Configure player for mask-based collision
        self.player.mask_system = self.mask_system
        self.player.collision_rects = []
        # Props list will be set by subclasses (e.g., in cat_cafe_scene)
        if not hasattr(self, 'props'):
            self.props = []
        self.player.props = self.props
    
    def _get_mask_path(self, background_path: str) -> str:
        """Convert background path to mask path by inserting '_mask' before extension."""
        if '.' in background_path:
            parts = background_path.rsplit('.', 1)
            return f"{parts[0]}_mask.png"
        return f"{background_path}_mask.png"
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.inventory_scene import InventoryScene
            self.game.stack.push(InventoryScene(self.game))
    
    def update(self, dt: float) -> None:
        self.player.update(dt)
        self.camera.follow(self.player.x, self.player.y, self.world_width, self.world_height)
        
        # Check portals
        if self.mask_system:
            portal_id = self.mask_system.rect_in_portal(self.player.collision_rect)
            if portal_id is not None and portal_id in self.PORTAL_MAP:
                self._enter_portal(portal_id)
    
    def draw(self, surface: pygame.Surface) -> None:
        # Draw background
        if self.background:
            bg_x, bg_y = self.camera.apply(0, 0)
            surface.blit(self.background, (bg_x, bg_y))
        else:
            surface.fill((60, 60, 60))
        
        # Draw portal regions (debug)
        if DEBUG_DRAW and self.mask_system:
            for portal_id in self.mask_system.portal_regions:
                bounds = self.mask_system.get_portal_bounds(portal_id)
                if bounds:
                    px, py = self.camera.apply(bounds.x, bounds.y)
                    pygame.draw.rect(surface, (0, 128, 255), (px, py, bounds.width, bounds.height), 2)
                    label = self.font.render(f"P{portal_id}", True, (0, 128, 255))
                    surface.blit(label, (px + 5, py + 5))
        
        # Draw player
        player_screen_x, player_screen_y = self.camera.apply(self.player.x, self.player.y)
        temp_surface = pygame.Surface((self.player.sprite.get_width(), self.player.sprite.get_height()), pygame.SRCALPHA)
        self.player.sprite and temp_surface.blit(self.player.sprite, (0, 0))
        surface.blit(temp_surface, (player_screen_x, player_screen_y))
        
        # Draw hitbox (debug)
        if DEBUG_DRAW and hasattr(self.player, 'collision_rect'):
            coll_x, coll_y = self.camera.apply(self.player.collision_rect.x, self.player.collision_rect.y)
            hb_surf = pygame.Surface((self.player.collision_rect.width, self.player.collision_rect.height), pygame.SRCALPHA)
            hb_surf.fill((0, 255, 0, 80))
            surface.blit(hb_surf, (coll_x, coll_y))
            pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, self.player.collision_rect.width, self.player.collision_rect.height), 2)
        
        # Draw prop bounding boxes (debug)
        if DEBUG_DRAW and hasattr(self, 'props'):
            for prop in self.props:
                if hasattr(prop, 'mask') and prop.mask:
                    prop_x, prop_y = self.camera.apply(prop.x, prop.y)
                    mask_width = prop.mask.get_width()
                    mask_height = prop.mask.get_height()
                    pygame.draw.rect(surface, (255, 128, 0), (prop_x, prop_y, mask_width, mask_height), 2)
                elif hasattr(prop, 'rect'):
                    prop_x, prop_y = self.camera.apply(prop.rect.x, prop.rect.y)
                    pygame.draw.rect(surface, (255, 128, 0), (prop_x, prop_y, prop.rect.width, prop.rect.height), 2)
    
    def _enter_portal(self, portal_id: int) -> None:
        """Handle portal transition using scene registry."""
        from scenes.scene_registry import get_scene_class
        
        portal_config = self.PORTAL_MAP.get(portal_id)
        if not portal_config:
            return
        
        target_scene_name = portal_config.get("to_scene")
        spawn = portal_config.get("spawn", (self.world_width // 2, self.world_height // 2))
        
        scene_class = get_scene_class(target_scene_name)
        if scene_class:
            self.game.stack.pop()
            self.game.stack.push(scene_class(self.game, spawn=spawn))
        else:
            print(f"Warning: Scene '{target_scene_name}' not found in registry")
