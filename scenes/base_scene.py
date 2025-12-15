"""Base scene class with automatic mask-based collision support."""
import pygame
import random
from typing import Any, Optional
from entities.player import Player
from entities.npc import NPC
from world.camera import Camera
from world.mask_collision import MaskCollisionSystem
from world.world_props import get_props_for_scene
from world.world_npcs import get_npcs_for_scene
from entities.prop_registry import make_prop
from world.scene_graph import register_scene_portals
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
from entities.player_config import (
    PLAYER_HITBOX_OFFSET_CENTERX, 
    PLAYER_HITBOX_OFFSET_BOTTOM,
    PLAYER_HITBOX_WIDTH,
    PLAYER_HITBOX_HEIGHT,
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
    - PLAYER_SPEED
    - SCENE_SCALE (multiplier for all objects, default 1.0)
    """
    
    # Subclasses should set these
    BACKGROUND_PATH = None
    PORTAL_MAP = {}
    
    # Player customization (leave None to use defaults from player_config.py)
    PLAYER_HITBOX_WIDTH = None
    PLAYER_HITBOX_HEIGHT = None
    PLAYER_HITBOX_OFFSET_CENTERX = None
    PLAYER_HITBOX_OFFSET_BOTTOM = None
    PLAYER_SPEED = None
    SCENE_NAME = None  # Subclasses should set this to match registry name
    SCENE_SCALE = 1.0  # Optional per-scene multiplier for props/items
    
    def __init__(self, game: Any, spawn: tuple = None):
        self.game = game
        self.scene_name = self.SCENE_NAME  # Store scene name for item tracking
        self.scene_scale = self.SCENE_SCALE if self.SCENE_SCALE is not None else 1.0
        self.active_modal = None  # Holds modal state when an arcade is open
        self.current_interact_prop = None  # Cached interactable prop for this frame
        
        # Register this scene's portals with the scene graph
        if self.SCENE_NAME and self.PORTAL_MAP:
            register_scene_portals(self.SCENE_NAME, self.PORTAL_MAP)
        
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
        # NPC container
        if not hasattr(self, 'npcs'):
            self.npcs = []
        
        # Use default hitbox dimensions/offsets (player gets scale from sprite registry)
        player_hitbox_width = self.PLAYER_HITBOX_WIDTH if self.PLAYER_HITBOX_WIDTH is not None else PLAYER_HITBOX_WIDTH
        player_hitbox_height = self.PLAYER_HITBOX_HEIGHT if self.PLAYER_HITBOX_HEIGHT is not None else PLAYER_HITBOX_HEIGHT
        player_hitbox_offset_centerx = self.PLAYER_HITBOX_OFFSET_CENTERX if self.PLAYER_HITBOX_OFFSET_CENTERX is not None else PLAYER_HITBOX_OFFSET_CENTERX
        player_hitbox_offset_bottom = self.PLAYER_HITBOX_OFFSET_BOTTOM if self.PLAYER_HITBOX_OFFSET_BOTTOM is not None else PLAYER_HITBOX_OFFSET_BOTTOM
        
        # Reuse existing player if available (preserves inventory across scenes)
        if hasattr(game, 'player') and game.player:
            self.player = game.player
            # Update player's scene-level scaling if it changed
            old_combined_scale = self.player.sprite_scale
            self.player.scene_scale = self.scene_scale
            self.player.sprite_scale = self.player.base_scale * self.scene_scale
            # Recreate animations with new scale if combined scale changed
            if self.player.sprite_scale != old_combined_scale:
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
                    speed=self.PLAYER_SPEED,
                    scene_scale=self.scene_scale
                )
            else:
                self.player = Player(
                    x=self.world_width // 2, y=self.world_height // 2, game=game,
                    hitbox_width=player_hitbox_width,
                    hitbox_height=player_hitbox_height,
                    hitbox_offset_centerx=player_hitbox_offset_centerx,
                    hitbox_offset_bottom=player_hitbox_offset_bottom,
                    speed=self.PLAYER_SPEED,
                    scene_scale=self.scene_scale
                )
            # Store player on game object
            game.player = self.player
        
        # Configure player for mask-based collision (update every scene)
        self.player.mask_system = self.mask_system
        self.player.collision_rects = []
        # Update collision rect after configuring everything
        self.player.collision_rect.centerx = int(self.player.x) + player_hitbox_offset_centerx
        self.player.collision_rect.bottom = int(self.player.y) + player_hitbox_offset_bottom

        # If a pending player state exists (from loading), apply it now
        pending_state = getattr(self.game, "pending_player_state", None)
        if pending_state:
            if hasattr(self.game, "saves"):
                self.game.saves.apply_player_state(self.player, pending_state)
            self.game.pending_player_state = None
        
        # Load props from world registry
        self._load_scene_props()
        self.player.props = self.props
        
        # Load NPCs from world registry
        self._load_scene_npcs()
    
    def _load_scene_props(self) -> None:
        """Load props currently in this scene from the world registry."""
        from world.world_registry import get_props_in_scene
        
        if not hasattr(self, 'props'):
            self.props = []
        
        # Get props that are currently in this scene from the world registry
        props_in_scene = get_props_in_scene(self.scene_name)
        
        for prop in props_in_scene:
            # Skip if already picked up
            if getattr(prop, 'picked_up', False):
                continue
            
            # Update prop's scene-level scaling if it changed
            old_combined_scale = prop.scale
            prop.scene_scale = self.scene_scale
            prop.scale = prop.base_scale * prop.scene_scale
            
            # Rebuild variant surface if scale changed (will update sprite and collision boxes)
            if prop.scale != old_combined_scale and hasattr(prop, '_rebuild_variant_surface'):
                prop._rebuild_variant_surface()
            
            # Don't re-add if already in the list
            if prop not in self.props:
                self.props.append(prop)
        
        # Spawn any dropped items for this scene
        if self.scene_name in self.game.dropped_items:
            for dropped_item in self.game.dropped_items[self.scene_name]:
                try:
                    dropped_prop = make_prop(
                        dropped_item['name'],
                        dropped_item['x'],
                        dropped_item['y'],
                        self.game,
                        variant_index=dropped_item.get('variant_index', 0),
                        scale=dropped_item.get('scale', None),
                        scene_scale=self.scene_scale,
                    )
                    dropped_prop.is_dropped = True
                    self.props.append(dropped_prop)
                except Exception as e:
                    print(f"Warning: Could not respawn dropped item {dropped_item.get('name')}: {e}")
    
    def _load_scene_npcs(self) -> None:
        """Load NPCs currently in this scene from the world registry."""
        from world.world_registry import get_npcs_in_scene
        
        if not hasattr(self, 'npcs'):
            self.npcs = []
        
        # Get NPCs that are currently in this scene from the world registry
        npcs_in_scene = get_npcs_in_scene(self.scene_name)
        
        for npc in npcs_in_scene:
            # Update NPC's scene reference and systems (always, even if already in list)
            npc.scene = self
            npc.mask_system = self.mask_system
            npc.props = self.props

            # If position is not walkable (e.g., off-screen warp), snap to nearest walkable spot
            if npc.mask_system:
                feet_x, feet_y = npc._get_feet_position()
                if not npc.mask_system.is_walkable(int(feet_x), int(feet_y)):
                    found = False
                    for radius in range(20, 141, 20):  # search up to ~140px
                        for dx in range(-radius, radius + 1, 20):
                            for dy in range(-radius, radius + 1, 20):
                                test_x = feet_x + dx
                                test_y = feet_y + dy
                                if npc.mask_system.is_walkable(int(test_x), int(test_y)):
                                    npc._set_position_from_feet(test_x, test_y)
                                    if hasattr(npc, 'rect'):
                                        npc.rect.topleft = (npc.x, npc.y)
                                    print(f"NPC {getattr(npc, 'npc_id', 'unknown')} snapped to walkable ({int(test_x)}, {int(test_y)}) in {self.scene_name}")
                                    found = True
                                    break
                            if found:
                                break
                        if found:
                            break
            
            # Update NPC's scene-level scaling if it changed
            old_combined_scale = npc.sprite_scale
            npc.scene_scale = self.scene_scale
            npc.sprite_scale = npc.base_scale * npc.scene_scale
            
            # Recreate animations with new scale if combined scale changed
            if npc.sprite_scale != old_combined_scale and hasattr(npc, 'spritesheet') and npc.spritesheet:
                npc.idle_animations["down"] = npc._create_animation([0])
                npc.idle_animations["up"] = npc._create_animation([3])
                npc.idle_animations["right"] = npc._create_animation([6])
                npc.idle_animations["left"] = npc._create_animation_mirrored([6])
                npc.moving_animations["down"] = npc._create_animation([0, 1, 0, 2])
                npc.moving_animations["up"] = npc._create_animation([3, 4, 3, 5])
                npc.moving_animations["right"] = npc._create_animation([6, 7, 6, 8])
                npc.moving_animations["left"] = npc._create_animation_mirrored([6, 7, 6, 8])
            
            # Add to scene if not already present
            is_new_to_scene = npc not in self.npcs
            if is_new_to_scene:
                self.npcs.append(npc)
                print(f"Added {getattr(npc, 'npc_id', 'unknown')} to scene {self.scene_name}")
            
            # Continue cross-scene pathfinding if applicable (regardless of whether newly added)
            if npc.scene_path and npc.current_scene_step < len(npc.scene_path):
                npc_name = getattr(npc, 'npc_id', 'unknown')
                next_step = npc.scene_path[npc.current_scene_step]
                print(f"NPC {npc_name} has scene_path, checking if {next_step[0]} == {self.scene_name}")
                if next_step[0] == self.scene_name:
                    # We're in the right scene, continue to next portal or destination
                    if npc.current_scene_step + 1 < len(npc.scene_path):
                        # Path to next portal
                        next_portal_step = npc.scene_path[npc.current_scene_step]
                        next_portal_id = next_portal_step[1]
                        print(f"  Resuming travel in {self.scene_name}, pathfinding to portal {next_portal_id}")
                        if next_portal_id is not None:
                            portal_bounds = self.mask_system.get_portal_bounds(next_portal_id)
                            if portal_bounds:
                                portal_center_x = portal_bounds.centerx
                                portal_center_y = portal_bounds.centery
                                # Don't avoid portals when intentionally trying to reach one
                                npc.pathfind_to(portal_center_x, portal_center_y, avoid_portals=False)
                    else:
                        # Reached final scene
                        npc.scene_path = None
    
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
            # Store sprite path for inventory display
            if hasattr(prop, 'sprite_path') and prop.sprite_path:
                item_to_add['sprite'] = prop.sprite_path
            # Store variant and scale info for when we drop it again
            if hasattr(prop, 'variant_index'):
                item_to_add['variant_index'] = prop.variant_index
            if hasattr(prop, 'variants'):
                item_to_add['variants'] = prop.variants
            if hasattr(prop, 'scale'):
                # Store item-level scale only; scene scale is applied on spawn
                base_scale = getattr(prop, 'base_scale', None)
                if base_scale is not None:
                    item_to_add['scale'] = base_scale
                else:
                    item_to_add['scale'] = prop.scale / (self.scene_scale or 1.0)
            self.player.inventory.add_item(item_to_add)
            # Mark the prop as picked up so it doesn't show in the scene
            prop.picked_up = True
            
            # Handle tracking differently for original vs dropped items
            if getattr(prop, 'is_dropped', False):
                # This is a dropped item - remove it from dropped_items for this scene
                if self.scene_name and self.scene_name in self.game.dropped_items:
                    # Find and remove this item from the dropped_items list
                    self.game.dropped_items[self.scene_name] = [
                        d for d in self.game.dropped_items[self.scene_name]
                        if not (d['x'] == prop.x and d['y'] == prop.y and d['name'] == prop.name)
                    ]
            else:
                # This is an original scene item - track so it doesn't respawn
                if hasattr(prop, 'item_id') and prop.item_id:
                    self.game.picked_up_items.add(prop.item_id)
            
        else:
            print("Warning: Player has no inventory to pick up item into")

    def _spawn_dropped_item(self, item: dict, player: Any) -> None:
        """Spawn an item prop at the player's feet position, finding a valid location if needed."""
        from entities.prop_registry import make_prop
        import random
        
        item_name = item.get('name', 'unknown')
        variant_index = item.get('variant_index', 0)
        base_scale = item.get('scale', None)
        
        # Calculate initial drop position at player's feet with slight random offset
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-10, 10)
        
        # Use frame-based collision box if available
        if hasattr(player, '_get_frame_collision_box'):
            try:
                frame_box = player._get_frame_collision_box()
                if frame_box:
                    drop_rect = frame_box.copy()
                    drop_rect.x += int(player.x)
                    drop_rect.y += int(player.y)
                    initial_x = drop_rect.centerx + offset_x
                    initial_y = drop_rect.bottom + offset_y
                else:
                    initial_x = player.collision_rect.centerx + offset_x
                    initial_y = player.collision_rect.bottom + offset_y
            except:
                initial_x = player.collision_rect.centerx + offset_x
                initial_y = player.collision_rect.bottom + offset_y
        else:
            initial_x = player.collision_rect.centerx + offset_x
            initial_y = player.collision_rect.bottom + offset_y
        
        # Find a valid drop location (no collision with walls or props)
        drop_x, drop_y = self._find_valid_drop_location(initial_x, initial_y, item_name)
        
        try:
            # Create the prop at drop position (with unique ID for this dropped instance)
            dropped_prop = make_prop(
                item_name,
                drop_x,
                drop_y,
                self.game,
                variant_index=variant_index,
                scale=base_scale,
                scene_scale=self.scene_scale,
            )
            dropped_prop.picked_up = False
            dropped_prop.is_dropped = True  # Mark as dropped so we handle it differently when picked up
            
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
                    'scale': base_scale,
                })
            
            print(f"Dropped {item_name} at ({drop_x}, {drop_y})")
        except Exception as e:
            print(f"Failed to drop item {item_name}: {e}")
    
    def _find_valid_drop_location(self, initial_x: float, initial_y: float, item_name: str, max_attempts: int = 20) -> tuple:
        """Find a valid location to drop an item by searching in a spiral pattern around the initial position.
        
        Returns: (x, y) tuple of a valid drop location
        """
        import math
        
        # Check if a location is valid (not blocked by mask and not overlapping props)
        def is_valid_drop_location(x, y):
            # Check collision mask
            if self.mask_system and not self.mask_system.is_walkable(int(x), int(y)):
                return False
            
            # Check collision with other props
            if hasattr(self, 'props'):
                for prop in self.props:
                    if prop.name == item_name and prop.x == initial_x and prop.y == initial_y:
                        # Skip the prop we're currently dropping
                        continue
                    
                    # Get prop collision rects
                    if hasattr(prop, 'collision_rects') and prop.collision_rects:
                        for collision_rect in prop.collision_rects:
                            # Scale the rect according to prop scale
                            prop_scale = getattr(prop, 'scale', 1.0)
                            scaled_rect = collision_rect.copy()
                            scaled_rect.x = int(prop.x + collision_rect.x * prop_scale)
                            scaled_rect.y = int(prop.y + collision_rect.y * prop_scale)
                            scaled_rect.width = int(collision_rect.width * prop_scale)
                            scaled_rect.height = int(collision_rect.height * prop_scale)
                            
                            # Check if drop point is too close (within 15 pixels of collision box)
                            if (abs(x - scaled_rect.centerx) < 15 and 
                                abs(y - scaled_rect.centery) < 15):
                                return False
            
            return True
        
        # Try initial position first
        if is_valid_drop_location(initial_x, initial_y):
            return (initial_x, initial_y)
        
        # Spiral search around initial position
        for attempt in range(1, max_attempts):
            # Create a spiral pattern: 4 points per "ring"
            ring = (attempt - 1) // 4 + 1
            step = 30 * ring  # Increase distance each ring
            
            # Try 8 directions in expanding rings
            angles = [0, 45, 90, 135, 180, 225, 270, 315]
            for angle_deg in angles:
                angle_rad = math.radians(angle_deg)
                test_x = initial_x + step * math.cos(angle_rad)
                test_y = initial_y + step * math.sin(angle_rad)
                
                if is_valid_drop_location(test_x, test_y):
                    return (test_x, test_y)
        
        # Fallback: return initial position even if invalid (shouldn't happen in normal play)
        print(f"Warning: Could not find valid drop location for {item_name}, using initial position")
        return (initial_x, initial_y)
    
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
        
        # Update NPCs
        if hasattr(self, 'npcs'):
            for npc in self.npcs:
                npc.update(dt)

        self.camera.follow(self.player.x, self.player.y, self.world_width, self.world_height)
        
        # Check portals
        if self.mask_system:
            # Use frame-based collision box if available, otherwise use static rect
            if hasattr(self.player, '_get_frame_collision_box'):
                try:
                    frame_box = self.player._get_frame_collision_box()
                    if frame_box:
                        # Position frame box at player's current position
                        portal_rect = frame_box.copy()
                        portal_rect.x += int(self.player.x)
                        portal_rect.y += int(self.player.y)
                    else:
                        portal_rect = self.player.collision_rect
                except:
                    portal_rect = self.player.collision_rect
            else:
                portal_rect = self.player.collision_rect
            
            portal_id = self.mask_system.rect_in_portal(portal_rect)
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
        # Use frame-based collision box if available for accurate depth
        if hasattr(self.player, '_get_frame_collision_box'):
            try:
                frame_box = self.player._get_frame_collision_box()
                if frame_box:
                    player_depth = int(self.player.y) + frame_box.bottom
                else:
                    player_depth = self.player.collision_rect.bottom if hasattr(self.player, 'collision_rect') else (self.player.y + (self.player.sprite.get_height() if self.player.sprite else 0))
            except:
                player_depth = self.player.collision_rect.bottom if hasattr(self.player, 'collision_rect') else (self.player.y + (self.player.sprite.get_height() if self.player.sprite else 0))
        else:
            player_depth = self.player.collision_rect.bottom if hasattr(self.player, 'collision_rect') else (self.player.y + (self.player.sprite.get_height() if self.player.sprite else 0))
        drawables.append(('player', self.player, player_depth))
        
        # Add NPCs
        if hasattr(self, 'npcs') and self.npcs:
            for npc in self.npcs:
                npc_bottom = npc.y + (npc.sprite.get_height() if npc.sprite else 0)
                drawables.append(('npc', npc, npc_bottom))

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
                    # Use frame-based collision box if available, otherwise use static rect
                    if hasattr(obj, '_get_frame_collision_box'):
                        try:
                            frame_box = obj._get_frame_collision_box()
                            if frame_box:
                                # Position frame box at player's current position
                                hitbox_x = frame_box.x + int(obj.x)
                                hitbox_y = frame_box.y + int(obj.y)
                                coll_x, coll_y = self.camera.apply(hitbox_x, hitbox_y)
                                hb_surf = pygame.Surface((frame_box.width, frame_box.height), pygame.SRCALPHA)
                                hb_surf.fill((0, 255, 0, 80))
                                surface.blit(hb_surf, (coll_x, coll_y))
                                pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, frame_box.width, frame_box.height), 2)
                            else:
                                # Fallback to static rect
                                coll_x, coll_y = self.camera.apply(obj.collision_rect.x, obj.collision_rect.y)
                                hb_surf = pygame.Surface((obj.collision_rect.width, obj.collision_rect.height), pygame.SRCALPHA)
                                hb_surf.fill((0, 255, 0, 80))
                                surface.blit(hb_surf, (coll_x, coll_y))
                                pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, obj.collision_rect.width, obj.collision_rect.height), 2)
                        except:
                            coll_x, coll_y = self.camera.apply(obj.collision_rect.x, obj.collision_rect.y)
                            hb_surf = pygame.Surface((obj.collision_rect.width, obj.collision_rect.height), pygame.SRCALPHA)
                            hb_surf.fill((0, 255, 0, 80))
                            surface.blit(hb_surf, (coll_x, coll_y))
                            pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, obj.collision_rect.width, obj.collision_rect.height), 2)
                    else:
                        coll_x, coll_y = self.camera.apply(obj.collision_rect.x, obj.collision_rect.y)
                        hb_surf = pygame.Surface((obj.collision_rect.width, obj.collision_rect.height), pygame.SRCALPHA)
                        hb_surf.fill((0, 255, 0, 80))
                        surface.blit(hb_surf, (coll_x, coll_y))
                        pygame.draw.rect(surface, (0, 255, 0), (coll_x, coll_y, obj.collision_rect.width, obj.collision_rect.height), 2)
            
            elif obj_type == 'npc':
                npc_x, npc_y = self.camera.apply(obj.x, obj.y)
                if obj.sprite:
                    surface.blit(obj.sprite, (npc_x, npc_y))
                else:
                    pygame.draw.rect(surface, (180, 180, 220), (npc_x, npc_y, 40, 60))
                
                # Draw NPC position marker (feet/coordinate)
                if DEBUG_DRAW:
                    # Get actual feet position and draw circle there
                    if hasattr(obj, '_get_feet_position'):
                        feet_x, feet_y = obj._get_feet_position()
                        screen_feet_x, screen_feet_y = self.camera.apply(feet_x, feet_y)
                        pygame.draw.circle(surface, (0, 255, 0), (int(screen_feet_x), int(screen_feet_y)), 5)
                        pygame.draw.circle(surface, (0, 100, 0), (int(screen_feet_x), int(screen_feet_y)), 5, 1)
                    else:
                        # Fallback: draw at sprite position
                        pygame.draw.circle(surface, (0, 255, 0), (int(npc_x), int(npc_y)), 5)
                        pygame.draw.circle(surface, (0, 100, 0), (int(npc_x), int(npc_y)), 5, 1)
                
                # Draw NPC state above character
                if DEBUG_DRAW and hasattr(obj, 'state_machine'):
                    state_name = obj.state_machine.get_current_state_name()
                    if state_name:
                        state_text = self.font.render(state_name, True, (255, 255, 0))
                        text_x = npc_x + (obj.sprite.get_width() // 2 if obj.sprite else 20) - (state_text.get_width() // 2)
                        text_y = npc_y
                        surface.blit(state_text, (text_x, text_y))

            elif obj_type == 'prop':
                obj.draw(surface, camera=self.camera)
                
                # Draw prop debug boxes
                if DEBUG_DRAW:
                    prop_scale = getattr(obj, 'scale', 1.0)
                    
                    # Draw collision areas (blocking) in green
                    if hasattr(obj, 'collision_rects'):
                        for collision_rect in obj.collision_rects:
                            screen_rect = pygame.Rect(
                                int(obj.x + collision_rect.x * prop_scale),
                                int(obj.y + collision_rect.y * prop_scale),
                                int(collision_rect.width * prop_scale),
                                int(collision_rect.height * prop_scale)
                            )
                            screen_x, screen_y = self.camera.apply(screen_rect.x, screen_rect.y)
                            pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_y, screen_rect.width, screen_rect.height), 2)
                    
                    # Draw interaction areas in orange
                    if hasattr(obj, 'interaction_rects'):
                        for interaction_rect in obj.interaction_rects:
                            screen_rect = pygame.Rect(
                                int(obj.x + interaction_rect.x * prop_scale),
                                int(obj.y + interaction_rect.y * prop_scale),
                                int(interaction_rect.width * prop_scale),
                                int(interaction_rect.height * prop_scale)
                            )
                            screen_x, screen_y = self.camera.apply(screen_rect.x, screen_rect.y)
                            pygame.draw.rect(surface, (255, 128, 0), (screen_x, screen_y, screen_rect.width, screen_rect.height), 2)

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
    
    def trigger_npc_portal_transition(self, npc: NPC, portal_id: int) -> None:
        """Handle NPC transition through a portal to another scene.
        
        This moves the NPC to the next scene in their cross-scene path.
        """
        from scenes.scene_registry import get_scene_class
        
        portal_config = self.PORTAL_MAP.get(portal_id)
        if not portal_config:
            return
        
        target_scene_name = portal_config.get("to_scene")
        spawn = portal_config.get("spawn", (self.world_width // 2, self.world_height // 2))
        
        # Remove NPC from current scene
        if npc in self.npcs:
            self.npcs.remove(npc)
        
        # Update world registry to track NPC's new location AND position
        from world.world_registry import move_npc_to_scene
        move_npc_to_scene(getattr(npc, 'npc_id', 'unknown'), target_scene_name)
        
        # Update NPC's actual position to the spawn point in the new scene
        # Spawn coordinates are in feet coordinates, convert to sprite coordinates
        # using the NPC's collision mask offset (same as in NPC.__init__)
        if hasattr(npc, 'mask_offset_x') and hasattr(npc, 'mask_offset_y'):
            scaled_offset_x = int(npc.mask_offset_x * npc.sprite_scale)
            scaled_offset_y = int(npc.mask_offset_y * npc.sprite_scale)
            npc.x = spawn[0] - scaled_offset_x
            npc.y = spawn[1] - scaled_offset_y
        else:
            npc.x = spawn[0]
            npc.y = spawn[1]
        
        # Update rect if it exists
        if hasattr(npc, 'rect'):
            npc.rect.topleft = (npc.x, npc.y)
        
        # If the target scene is currently active, add the NPC to it immediately
        if hasattr(self.game, 'stack') and self.game.stack.top():
            active_scene = self.game.stack.top()
            if (hasattr(active_scene, 'scene_name') and 
                active_scene.scene_name == target_scene_name and
                hasattr(active_scene, 'npcs')):
                # Add NPC to the active scene
                if npc not in active_scene.npcs:
                    active_scene.npcs.append(npc)
                    # Update NPC's scene reference and systems
                    npc.scene = active_scene
                    npc.mask_system = active_scene.mask_system
                    npc.props = active_scene.props
                else:
                    # Ensure references are up to date even if already present
                    npc.scene = active_scene
                    npc.mask_system = active_scene.mask_system
                    npc.props = active_scene.props
                    
                    # Verify spawn point is walkable; if not, find nearby walkable spot
                    if npc.mask_system:
                        feet_x, feet_y = npc._get_feet_position()
                        if not npc.mask_system.is_walkable(int(feet_x), int(feet_y)):
                            print(f"NPC spawn at ({int(feet_x)}, {int(feet_y)}) not walkable, searching nearby...")
                            found = False
                            for offset_x in range(-100, 101, 20):
                                for offset_y in range(-100, 101, 20):
                                    test_x = feet_x + offset_x
                                    test_y = feet_y + offset_y
                                    if npc.mask_system.is_walkable(int(test_x), int(test_y)):
                                        # Move NPC to this walkable position
                                        if hasattr(npc, 'mask_offset_x') and hasattr(npc, 'mask_offset_y'):
                                            scaled_offset_x = int(npc.mask_offset_x * npc.sprite_scale)
                                            scaled_offset_y = int(npc.mask_offset_y * npc.sprite_scale)
                                            npc.x = test_x - scaled_offset_x
                                            npc.y = test_y - scaled_offset_y
                                        else:
                                            npc.x = test_x
                                            npc.y = test_y
                                        if hasattr(npc, 'rect'):
                                            npc.rect.topleft = (npc.x, npc.y)
                                            print(f"Moved NPC to walkable position ({int(test_x)}, {int(test_y)})")
                                        found = True
                                        break
                                if found:
                                    break
                    
                        feet_x, feet_y = npc._get_feet_position()
                        print(f"Added NPC to active scene {target_scene_name} at ({int(feet_x)}, {int(feet_y)})")

                        # If this was the final step of a scene_path, clear it
                        if getattr(npc, 'scene_path', None) and getattr(npc, 'current_scene_step', 0) >= len(npc.scene_path) - 1:
                            npc.scene_path = None
                            npc.target_scene = None
            else:
                # Scene not active: clear immediate pathfinding but preserve scene_path for cross-scene travel
                print(f"Target scene {target_scene_name} not yet active, deferring NPC setup to scene load")
                npc.path = []
                npc.destination = None
                # Keep scene/mask_system/props cleared so state machine knows NPC is off-screen
                # but DON'T clear scene_path - the NPC will resume travel when this scene loads
                npc.scene = None
                npc.mask_system = None
                npc.props = []
                # scene_path remains set, so when _load_scene_npcs() restores mask_system,
                # the NPC can continue its cross-scene journey
        
        # Clear transitioning flag so NPC can be loaded normally in the new scene
        npc.transitioning = False

