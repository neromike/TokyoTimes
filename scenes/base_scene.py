"""Base scene class with automatic mask-based collision support."""
import pygame
import random
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
from scenes.minigames.blocks import BlocksState
from scenes.minigames.asteroids import AsteroidsState




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
    SCENE_NAME = None  # Subclasses should set this to match registry name
    
    def __init__(self, game: Any, spawn: tuple = None):
        self.game = game
        self.scene_name = self.SCENE_NAME  # Store scene name for item tracking
        self.active_modal = None  # Holds modal state when an arcade is open
        self.current_interact_prop = None  # Cached interactable prop for this frame
        
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
        
        # Reuse existing player if available (preserves inventory across scenes)
        if hasattr(game, 'player') and game.player:
            self.player = game.player
            # Update player's scale and regenerate animations if scale changed
            if self.player.sprite_scale != player_sprite_scale:
                self.player.sprite_scale = player_sprite_scale
                # Recreate animations with new scale
                if hasattr(self.player, 'spritesheet') and self.player.spritesheet:
                    self.player.animations["down"] = self.player._create_animation([0, 1, 0, 2])
                    self.player.animations["up"] = self.player._create_animation([3, 4, 3, 5])
                    self.player.animations["left"] = self.player._create_animation([6, 7, 6, 8])
                    self.player.animations["right"] = self.player._create_animation_mirrored([6, 7, 6, 8])
                    # Update current animation
                    if self.player.direction in self.player.animations:
                        self.player.animation = self.player.animations[self.player.direction]
                    # Update sprite
                    if self.player.animation:
                        self.player.sprite = self.player.animation.get_current_frame()
            # Update player's hitbox dimensions and offsets to match the new scene's scale
            self.player.collision_rect.width = player_hitbox_width
            self.player.collision_rect.height = player_hitbox_height
            self.player.hitbox_offset_centerx = player_hitbox_offset_centerx
            self.player.hitbox_offset_bottom = player_hitbox_offset_bottom
            # Update player position for spawn point
            if spawn:
                sprite_x = spawn[0] - player_hitbox_offset_centerx
                sprite_y = spawn[1] - player_hitbox_offset_bottom
                self.player.x = sprite_x
                self.player.y = sprite_y
        else:
            # Create new player
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
            # Store player on game object
            game.player = self.player
        
        # Configure player for mask-based collision (update every scene)
        self.player.mask_system = self.mask_system
        self.player.collision_rects = []
        # Update collision rect after configuring everything
        self.player.collision_rect.centerx = int(self.player.x) + player_hitbox_offset_centerx
        self.player.collision_rect.bottom = int(self.player.y) + player_hitbox_offset_bottom
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

    def _interact_with_prop(self, prop: Any) -> None:
        """Handle prop interaction - pick up items or open modals for arcades."""
        # Handle item pickup
        if getattr(prop, 'is_item', False) and not getattr(prop, 'picked_up', False):
            self._pickup_item(prop)
            return
        
        # If this is the blocks arcade, start blocks
        if getattr(prop, 'name', None) == 'arcade_blocks':
            self.active_modal = {
                "type": "blocks",
                "prop": prop,
                "state": BlocksState(),
            }
        elif getattr(prop, 'name', None) == 'arcade_spaceship':
            self.active_modal = {
                "type": "asteroids",
                "prop": prop,
                "state": AsteroidsState(),
            }
        else:
            self.active_modal = {"type": "generic", "prop": prop}

    def _pickup_item(self, prop: Any) -> None:
        """Add an item prop to player inventory and mark it as picked up."""
        if self.player and hasattr(self.player, 'inventory'):
            # Add item data to inventory
            item_to_add = getattr(prop, 'item_data', {}).copy()
            if not item_to_add.get('name'):
                item_to_add['name'] = getattr(prop, 'name', 'unknown_item')
            # Store variant info and scale for when we drop it again
            if hasattr(prop, 'variant_index'):
                item_to_add['variant_index'] = prop.variant_index
            if hasattr(prop, 'scale'):
                item_to_add['scale'] = prop.scale
            self.player.inventory.add_item(item_to_add)
            # Mark the prop as picked up so it doesn't show in the scene
            prop.picked_up = True
            
            # Track item pickup globally so it doesn't respawn in original scene
            if hasattr(prop, 'item_id') and prop.item_id:
                self.game.picked_up_items.add(prop.item_id)
            
            print(f"Picked up: {item_to_add.get('name')}")
        else:
            print("Warning: Player has no inventory to pick up item into")

    def _spawn_dropped_item(self, item: dict, player: Any) -> None:
        """Spawn an item prop at the player's feet position."""
        from entities.prop_registry import make_prop
        
        item_name = item.get('name', 'unknown')
        variant_index = item.get('variant_index', 0)
        scale = item.get('scale', None)
        
        # Calculate drop position at player's feet with slight random offset
        import random
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-10, 10)
        drop_x = player.collision_rect.centerx + offset_x
        drop_y = player.collision_rect.bottom + offset_y
        
        try:
            # Create the prop at drop position (with unique ID for this dropped instance)
            dropped_prop = make_prop(item_name, drop_x, drop_y, self.game, variant_index=variant_index, scale=scale)
            dropped_prop.picked_up = False
            
            # Add to scene props
            if hasattr(self, 'props'):
                self.props.append(dropped_prop)
                # Update player's prop reference
                if hasattr(self.player, 'props'):
                    self.player.props = self.props
            
            # Track this dropped item globally
            if self.scene_name:
                if self.scene_name not in self.game.dropped_items:
                    self.game.dropped_items[self.scene_name] = []
                
                # Store dropped item data for scene respawn
                self.game.dropped_items[self.scene_name].append({
                    'name': item_name,
                    'x': drop_x,
                    'y': drop_y,
                    'variant_index': variant_index,
                    'scale': scale,
                })
            
            print(f"Dropped {item_name} at ({drop_x}, {drop_y})")
        except Exception as e:
            print(f"Failed to drop item {item_name}: {e}")
    
    def handle_event(self, event: pygame.event.Event) -> None:
        # If a modal is open, route inputs or close
        if self.active_modal:
            if isinstance(self.active_modal, dict):
                mtype = self.active_modal.get("type")
                state = self.active_modal.get("state")
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.active_modal = None
                    return
                if mtype == "blocks" and state:
                    if event.type == pygame.KEYDOWN:
                        state.handle_key(event.key)
                        return
                elif mtype == "asteroids" and state:
                    if event.type == pygame.KEYDOWN:
                        state.handle_key(event.key)
                        return
                # Close generic modal on click
                if mtype == "generic" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.active_modal = None
                    return
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.inventory_scene import InventoryScene
            self.game.stack.push(InventoryScene(self.game))

        # Interact with prop via Enter
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.current_interact_prop:
                self._interact_with_prop(self.current_interact_prop)
                return

        # Interact with prop via mouse click (left)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.current_interact_prop:
            mx, my = event.pos
            world_x, world_y = mx + self.camera.x, my + self.camera.y

            prop = self.current_interact_prop
            prop_scale = getattr(prop, 'scale', 1.0)
            
            if hasattr(prop, 'sprite') and prop.sprite:
                bbox = prop.sprite.get_bounding_rect(min_alpha=1)
                # Account for scale when determining clickable area
                scaled_width = int(bbox.width * prop_scale)
                scaled_height = int(bbox.height * prop_scale)
                scaled_x = int(bbox.x * prop_scale)
                scaled_y = int(bbox.y * prop_scale)
                prop_rect = pygame.Rect(prop.x + scaled_x, prop.y + scaled_y, scaled_width, scaled_height)
            elif hasattr(prop, 'rect'):
                prop_rect = prop.rect
            else:
                prop_rect = pygame.Rect(prop.x, prop.y, 1, 1)

            if prop_rect.collidepoint(world_x, world_y):
                self._interact_with_prop(prop)
                return
    
    def update(self, dt: float) -> None:
        # Freeze game world updates while modal is open; update modal if needed
        if self.active_modal:
            if isinstance(self.active_modal, dict):
                mtype = self.active_modal.get("type")
                state = self.active_modal.get("state")
                if mtype in ("blocks", "asteroids") and state:
                    state.update(dt)
            return

        self.player.update(dt)
        # Cache interactable prop for this frame
        self.current_interact_prop = getattr(self.player, 'interact_prop', None)

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
        
        # Collect and sort drawable objects by Y position (depth sorting)
        # Objects further down (higher Y) should be drawn last so they appear on top
        drawables = []
        
        # Add player, depth based on feet (collision rect bottom)
        player_depth = self.player.collision_rect.bottom if hasattr(self.player, 'collision_rect') else (self.player.y + (self.player.sprite.get_height() if self.player.sprite else 0))
        drawables.append(('player', self.player, player_depth))
        
        # Add props
        if hasattr(self, 'props'):
            for prop in self.props:
                # Skip picked-up items
                if getattr(prop, 'picked_up', False):
                    continue
                # Prefer prop.depth() if available to ignore transparent interaction extensions
                if hasattr(prop, 'depth') and callable(prop.depth):
                    prop_bottom = prop.depth()
                elif hasattr(prop, 'sprite') and prop.sprite:
                    prop_bottom = prop.y + prop.sprite.get_height()
                elif hasattr(prop, 'rect'):
                    prop_bottom = prop.rect.bottom
                elif hasattr(prop, 'mask') and prop.mask:
                    prop_bottom = prop.y + prop.mask.get_height()
                else:
                    prop_bottom = prop.y
                drawables.append(('prop', prop, prop_bottom))
        
        # Sort by Y position (bottom of sprite)
        drawables.sort(key=lambda x: x[2])
        
        # Draw in sorted order
        for obj_type, obj, _ in drawables:
            if obj_type == 'player':
                player_screen_x, player_screen_y = self.camera.apply(obj.x, obj.y)
                temp_surface = pygame.Surface((obj.sprite.get_width(), obj.sprite.get_height()), pygame.SRCALPHA)
                obj.sprite and temp_surface.blit(obj.sprite, (0, 0))
                surface.blit(temp_surface, (player_screen_x, player_screen_y))
                
                # Draw hitbox (debug)
                if DEBUG_DRAW and hasattr(obj, 'collision_rect'):
                    coll_x, coll_y = self.camera.apply(obj.collision_rect.x, obj.collision_rect.y)
                    hb_surf = pygame.Surface((obj.collision_rect.width, obj.collision_rect.height), pygame.SRCALPHA)
                    hb_surf.fill((0, 255, 0, 80))
                    surface.blit(hb_surf, (coll_x, coll_y))
                    pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, obj.collision_rect.width, obj.collision_rect.height), 2)
            
            elif obj_type == 'prop':
                obj.draw(surface, camera=self.camera)
                
                # Draw prop bounding box (debug)
                if DEBUG_DRAW:
                    if hasattr(obj, 'mask') and obj.mask:
                        prop_x, prop_y = self.camera.apply(obj.x, obj.y)
                        prop_scale = getattr(obj, 'scale', 1.0)
                        mask_width = int(obj.mask.get_width() * prop_scale)
                        mask_height = int(obj.mask.get_height() * prop_scale)
                        pygame.draw.rect(surface, (255, 128, 0), (prop_x, prop_y, mask_width, mask_height), 2)
                    elif hasattr(obj, 'rect'):
                        prop_x, prop_y = self.camera.apply(obj.rect.x, obj.rect.y)
                        pygame.draw.rect(surface, (255, 128, 0), (prop_x, prop_y, obj.rect.width, obj.rect.height), 2)

        # Modal overlay
        if self.active_modal:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            modal_w, modal_h = int(WINDOW_WIDTH * 0.8), int(WINDOW_HEIGHT * 0.7)
            modal_x = (WINDOW_WIDTH - modal_w) // 2
            modal_y = (WINDOW_HEIGHT - modal_h) // 2
            pygame.draw.rect(surface, (30, 30, 30), (modal_x, modal_y, modal_w, modal_h))
            pygame.draw.rect(surface, (200, 200, 200), (modal_x, modal_y, modal_w, modal_h), 3)

            if isinstance(self.active_modal, dict):
                mtype = self.active_modal.get("type")
                state = self.active_modal.get("state")
                if mtype == "blocks" and state:
                    state.draw(surface, modal_x, modal_y, modal_w, modal_h, self.font)
                elif mtype == "asteroids" and state:
                    state.draw(surface, modal_x, modal_y, modal_w, modal_h, self.font)
                else:
                    title = self.font.render("Arcade", True, (255, 255, 255))
                    surface.blit(title, (modal_x + 20, modal_y + 20))
                    hint = self.font.render("(ESC to close)", True, (180, 180, 180))
                    surface.blit(hint, (modal_x + 20, modal_y + 60))
    
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
