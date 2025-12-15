import pygame
import math
from entities.character import Character
from entities.components.animation import Spritesheet, Animation
from core.sprites import SpriteLoader
from core.sprite_registry import get_sprite_config
from core.collision_masks import CollisionMaskExtractor
from ai.pathfinding import Pathfinding
from ai.state_machine import StateMachine
from world.scene_graph import get_scene_graph
from entities.npc_configs import NPCConfig, HENRY_CONFIG

class NPC(Character):
    def __init__(self, x: float, y: float, game=None, sprite_scale: float = 1.0, config: NPCConfig = None, scene_scale: float = 1.0):
        self.game = game
        self.animation = None
        self.spritesheet = None
        sprite = None
        self.direction = "down"
        self.animations = {}
        # Default scale: provided or registry default
        if sprite_scale is None and game:
            try:
                sprite_scale = get_sprite_config("npc_henry").get("scale", 1.0)
            except Exception:
                sprite_scale = 1.0
        self.base_scale = sprite_scale if sprite_scale is not None else 1.0
        self.scene_scale = max(0.1, float(scene_scale)) if scene_scale is not None else 1.0
        # Combined scale applies base scale and scene-level multiplier together
        self.sprite_scale = self.base_scale * self.scene_scale
        self.collision_mask_extractor = None  # Will be loaded if mask exists
        self.mask_offset_x = 0  # Offset from sprite top-left to mask center
        self.mask_offset_y = 0

        # Load Henry spritesheet (same layout as player: 3x3 frames of 290x440)
        if game:
            try:
                loader = SpriteLoader(game.assets)
                henry_cfg = get_sprite_config("npc_henry")
                sheet_img = game.assets.image(henry_cfg["path"]) 
                self.spritesheet = Spritesheet(sheet_img, frame_width=henry_cfg["frame_width"], frame_height=henry_cfg["frame_height"]) 
                # Idle animations (single frame - first pose of each direction)
                self.idle_animations = {}
                self.idle_animations["down"] = self._create_animation([0])
                self.idle_animations["up"] = self._create_animation([3])
                self.idle_animations["right"] = self._create_animation([6])
                self.idle_animations["left"] = self._create_animation_mirrored([6])
                # Moving animations (cycling frames)
                self.moving_animations = {}
                self.moving_animations["down"] = self._create_animation([0, 1, 0, 2])
                self.moving_animations["up"] = self._create_animation([3, 4, 3, 5])
                self.moving_animations["right"] = self._create_animation([6, 7, 6, 8])
                self.moving_animations["left"] = self._create_animation_mirrored([6, 7, 6, 8])
                # Start with idle down
                self.animation = self.idle_animations["down"]
                sprite = self.animation.get_current_frame()
                
                # Try to load collision mask
                try:
                    mask_img = game.assets.image("sprites/henry_mask.png")
                    self.collision_mask_extractor = CollisionMaskExtractor(
                        mask_img,
                        variants=3,  # 3x3 grid (3 columns)
                        frame_width=henry_cfg["frame_width"],
                        frame_height=henry_cfg["frame_height"]
                    )
                    
                    # Get the collision box from first frame to calculate offset
                    if self.collision_mask_extractor:
                        collision_box = self.collision_mask_extractor.get_frame_collision_box(0)
                        if collision_box:
                            # Calculate offset to bottom-center of collision box
                            # This will be our reference point (feet position)
                            self.mask_offset_x = collision_box.x + (collision_box.width // 2)
                            self.mask_offset_y = collision_box.y + collision_box.height
                except Exception as e:
                    print(f"Warning: Could not load NPC collision mask: {e}")
            except Exception as e:
                print(f"Warning: Could not load henry spritesheet: {e}")
                sprite = pygame.Surface((290, 440))
                sprite.fill((200, 170, 120))

        # Convert initial position from feet coordinates to sprite top-left
        # The x, y parameters represent where the NPC's feet should be
        initial_sprite_x = x
        initial_sprite_y = y
        if self.collision_mask_extractor and hasattr(self, 'mask_offset_x'):
            # Adjust for mask offset (scale it)
            scaled_offset_x = int(self.mask_offset_x * self.sprite_scale)
            scaled_offset_y = int(self.mask_offset_y * self.sprite_scale)
            initial_sprite_x = x - scaled_offset_x
            initial_sprite_y = y - scaled_offset_y
        elif sprite:
            # Fallback: assume feet are at bottom-center of sprite
            initial_sprite_x = x - (sprite.get_width() // 2)
            initial_sprite_y = y - sprite.get_height()
        
        super().__init__(initial_sprite_x, initial_sprite_y, sprite)
        # NPCs don't move by default
        self.velocity_x = 0
        self.velocity_y = 0
        
        # NPC Configuration (use provided or default to Henry's config)
        self.config = config if config is not None else HENRY_CONFIG
        self.npc_type = "henry"  # Type identifier for scene tracking
        
        # Pathfinding
        self.pathfinder = Pathfinding(cell_size=20)
        self.path = []  # Current path waypoints (list of (x, y) tuples)
        self.current_waypoint_idx = 0
        self.speed = self.config.speed  # Get speed from config
        self.mask_system = None  # Will be set by scene
        self.destination = None  # Target destination (x, y) for re-pathfinding
        self.stuck_timer = 0.0  # Time spent not making progress
        self.last_position = self._get_feet_position()  # Track position for stuck detection
        self.repath_interval = 2.0  # Re-pathfind every N seconds if moving
        self.repath_timer = 0.0
        
        # AI State Machine
        self.state_machine = StateMachine(self, initial_state_name="IdleState")
        
        # Cross-scene pathfinding
        self.target_scene = None  # Target scene name for cross-scene movement
        self.scene_path = None  # List of (scene_name, portal_id, spawn_point) for cross-scene path
        self.current_scene_step = 0  # Which step in the scene path we're on
        # Cache for off-screen mask sampling per scene
        self.offscreen_mask_cache = {}

    def _create_animation(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=6, scale=self.sprite_scale)
        anim.frame_indices = frame_indices
        return anim

    def _create_animation_mirrored(self, frame_indices: list) -> Animation:
        anim = Animation(self.spritesheet, fps=6, scale=self.sprite_scale)
        anim.frame_indices = frame_indices
        anim.mirrored = True
        return anim
    
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
    
    def _get_feet_position(self) -> tuple:
        """Get the feet position (bottom-center of collision box) in world coordinates.
        
        The NPC's x, y is stored as sprite top-left, but we want to use feet as reference.
        """
        if self.collision_mask_extractor:
            # Use mask offset (scaled)
            scaled_offset_x = int(self.mask_offset_x * self.sprite_scale)
            scaled_offset_y = int(self.mask_offset_y * self.sprite_scale)
            return (self.x + scaled_offset_x, self.y + scaled_offset_y)
        else:
            # Fallback: bottom-center of sprite
            return (self.x + self.sprite.get_width() // 2, self.y + self.sprite.get_height())
    
    def _set_position_from_feet(self, feet_x: float, feet_y: float):
        """Set NPC position based on feet coordinates.
        
        Converts feet position back to sprite top-left coordinates.
        """
        if self.collision_mask_extractor:
            # Use mask offset (scaled)
            scaled_offset_x = int(self.mask_offset_x * self.sprite_scale)
            scaled_offset_y = int(self.mask_offset_y * self.sprite_scale)
            self.x = feet_x - scaled_offset_x
            self.y = feet_y - scaled_offset_y
        else:
            # Fallback: bottom-center of sprite
            self.x = feet_x - (self.sprite.get_width() // 2)
            self.y = feet_y - self.sprite.get_height()

    def update(self, dt: float) -> None:
        # Skip update if transitioning between scenes
        if getattr(self, 'transitioning', False):
            return
        
        # Update AI state machine
        self.state_machine.update(dt)
        
        # Check for portal collision (using center of mass / feet position)
        if self.mask_system and hasattr(self, 'scene'):
            feet_x, feet_y = self._get_feet_position()
            portal_id = self.mask_system.is_portal(int(feet_x), int(feet_y))
            
            if portal_id is not None:
                # NPC has entered a portal
                # Check if this is intentional (part of cross-scene pathfinding)
                if self.scene_path and self.current_scene_step < len(self.scene_path):
                    current_step = self.scene_path[self.current_scene_step]
                    expected_portal_id = current_step[1]
                    
                    # Only transition if we're at the expected portal or path is complete
                    if expected_portal_id == portal_id or (not self.path or self.current_waypoint_idx >= len(self.path)):
                        if hasattr(self.scene, 'trigger_npc_portal_transition'):
                            self.scene.trigger_npc_portal_transition(self, portal_id)
                        self.current_scene_step += 1
                else:
                    # Unintentional portal entry (e.g., wandering too close)
                    if hasattr(self.scene, 'trigger_npc_portal_transition'):
                        self.scene.trigger_npc_portal_transition(self, portal_id)
                    # Clear current path since we're leaving the scene
                    self.path = []
                    self.destination = None
        
        # Determine if moving
        is_moving = self.path and self.current_waypoint_idx < len(self.path)
        
        # Check if stuck or need to re-path
        if is_moving and self.destination:
            # Check if stuck (not making progress) - use feet position
            current_pos = self._get_feet_position()
            distance_moved = math.sqrt((current_pos[0] - self.last_position[0])**2 + 
                                     (current_pos[1] - self.last_position[1])**2)
            
            if distance_moved < 1.0:  # Less than 1 pixel moved
                self.stuck_timer += dt
                if self.stuck_timer > 0.5:  # Stuck for more than 0.5 seconds
                    print(f"  NPC stuck, re-pathfinding to {self.destination}")
                    self.pathfind_to(self.destination[0], self.destination[1])
                    self.stuck_timer = 0.0
            else:
                self.stuck_timer = 0.0
            
            self.last_position = current_pos
            
            # Periodic re-pathfinding to handle dynamic obstacles
            self.repath_timer += dt
            if self.repath_timer >= self.repath_interval:
                self.repath_timer = 0.0
                # Re-pathfind to destination
                if self.destination:
                    self.pathfind_to(self.destination[0], self.destination[1])
        
        # Choose animation based on movement state
        if is_moving:
            # Use moving animation for current direction
            self.animation = self.moving_animations.get(self.direction, self.idle_animations.get(self.direction))
        else:
            # Use idle animation (single frame)
            self.animation = self.idle_animations.get(self.direction, self.idle_animations.get("down"))
        
        # Update animation frame
        if self.animation:
            self.animation.update(dt)
            self.sprite = self.animation.get_current_frame()
        
        # Update rect position
        if self.sprite:
            if not hasattr(self, 'rect') or self.rect is None:
                self.rect = self.sprite.get_rect(topleft=(self.x, self.y))
            else:
                self.rect.topleft = (self.x, self.y)
        
        # Follow path if one exists, OR if we're in cross-scene travel trying to reach a portal
        if self.path or (self.scene_path and self.current_scene_step < len(self.scene_path)):
            self._follow_path(dt)
    
    def pathfind_to(self, target_x: float, target_y: float, avoid_portals: bool = False) -> None:
        """Pathfind from current position to target using A* algorithm.
        
        Uses feet position for pathfinding calculations.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            avoid_portals: If True, portals are treated as unwalkable (for same-scene wandering)
        """
        npc_name = getattr(self, 'npc_id', '?')
        if not self.mask_system:
            print(f"    [pathfind_to] {npc_name}: No mask_system, cannot pathfind")
            return
        
        # Get current feet position for pathfinding
        start_x, start_y = self._get_feet_position()
        
        # Store destination for re-pathfinding
        self.destination = (target_x, target_y)
        self.stuck_timer = 0.0
        self.repath_timer = 0.0
        
        # Define walkable function: a position is walkable if it's not colliding
        def is_walkable(x, y):
            # Check if position is blocked by collision mask
            walkable = self.mask_system.is_walkable(int(x), int(y))
            if not walkable:
                return False
            
            # If avoiding portals, reject portal areas
            if avoid_portals:
                if self.mask_system.is_portal(int(x), int(y)) is not None:
                    return False
            
            # Check props (if they have collision)
            if hasattr(self, 'props') and self.props:
                for prop in self.props:
                    if not getattr(prop, 'picked_up', False):
                        prop_scale = getattr(prop, 'scale', 1.0)
                        if hasattr(prop, 'sprite') and prop.sprite:
                            bbox = prop.sprite.get_bounding_rect(min_alpha=1)
                            scaled_width = int(bbox.width * prop_scale)
                            scaled_height = int(bbox.height * prop_scale)
                            prop_rect = pygame.Rect(
                                int(prop.x + bbox.x * prop_scale),
                                int(prop.y + bbox.y * prop_scale),
                                scaled_width,
                                scaled_height
                            )
                            check_rect = pygame.Rect(int(x) - 5, int(y) - 5, 10, 10)
                            if check_rect.colliderect(prop_rect):
                                return False
            
            return True
        
        # If start is not walkable, try to find a nearby walkable position
        if not is_walkable(start_x, start_y):
            print(f"Start position ({start_x}, {start_y}) not walkable, searching nearby...")
            found_start = False
            for offset_x in range(-50, 51, 10):
                for offset_y in range(-50, 51, 10):
                    test_x = start_x + offset_x
                    test_y = start_y + offset_y
                    if is_walkable(test_x, test_y):
                        print(f"Found walkable position at ({test_x}, {test_y})")
                        self._set_position_from_feet(test_x, test_y)
                        start_x, start_y = test_x, test_y
                        found_start = True
                        break
                if found_start:
                    break
            if not found_start:
                print(f"Could not find walkable start position!")
                return
        
        # Calculate path using A*
        world_width = 1920  # Default; can be made dynamic
        world_height = 1080
        if hasattr(self, 'scene') and hasattr(self.scene, 'world_width'):
            world_width = self.scene.world_width
            world_height = self.scene.world_height
        
        self.path = self.pathfinder.astar(
            is_walkable,
            (start_x, start_y),
            (target_x, target_y),
            (world_width, world_height)
        )
        self.current_waypoint_idx = 0

    def pathfind_to_scene(self, target_scene: str, target_x: float = None, target_y: float = None):
        """Pathfind to a location in a different scene (or current scene).
        
        Args:
            target_scene: Name of the target scene
            target_x: X coordinate in target scene (optional, uses scene center if not provided)
            target_y: Y coordinate in target scene (optional, uses scene center if not provided)
        """
        npc_name = getattr(self, 'npc_id', '?')
        # Get current scene from world registry (more reliable than self.scene)
        from world.world_registry import get_npc_location
        current_scene = get_npc_location(npc_name)
        
        if not current_scene:
            # Fallback to self.scene if registry lookup fails
            if hasattr(self, 'scene') and self.scene:
                current_scene = self.scene.scene_name
                print(f"      Fell back to self.scene: {current_scene}")
            else:
                print(f"      No scene reference, aborting cross-scene pathfinding")
                return
        
        # If target is current scene, just pathfind normally
        if target_scene == current_scene:
            print(f"      Target is same scene, doing local pathfind")
            if target_x is not None and target_y is not None:
                self.pathfind_to(target_x, target_y)
            return
        
        # Find path through scene graph
        scene_graph = get_scene_graph()
        scene_path = scene_graph.find_scene_path(current_scene, target_scene)
        
        if not scene_path:
            print(f"      No path found from scene '{current_scene}' to '{target_scene}'")
            return
        
        
        # Store the scene path and final destination
        self.target_scene = target_scene
        self.scene_path = scene_path
        self.current_scene_step = 0
        
        # If we lack a mask/system (off-screen), fast-forward one scene hop using graph spawn
        if (not self.mask_system or not getattr(self, 'scene', None)) and len(scene_path) > 1:
            first_step = scene_path[0]
            next_step = scene_path[1]
            portal_spawn = first_step[2]
            next_scene = next_step[0]
            try:
                from world.world_registry import move_npc_to_scene
                move_npc_to_scene(npc_name, next_scene)
                if hasattr(self, 'mask_offset_x') and hasattr(self, 'mask_offset_y') and portal_spawn:
                    scaled_offset_x = int(self.mask_offset_x * self.sprite_scale)
                    scaled_offset_y = int(self.mask_offset_y * self.sprite_scale)
                    self.x = portal_spawn[0] - scaled_offset_x
                    self.y = portal_spawn[1] - scaled_offset_y
                elif portal_spawn:
                    self.x, self.y = portal_spawn
                # Trim the scene_path to continue from the new scene
                self.scene_path = scene_path[1:]
                self.current_scene_step = 0
            except Exception as e:
                print(f"      Fast-forward failed: {e}")
            return
        
        # Start by pathfinding to the first portal in current scene (when mask is available)
        if len(scene_path) > 1:
            first_step = scene_path[0]
            portal_id = first_step[1]
            
            # Get portal location in current scene
            if self.mask_system and portal_id is not None:
                portal_bounds = self.mask_system.get_portal_bounds(portal_id)
                if portal_bounds:
                    # Pathfind to center of portal
                    portal_center_x = portal_bounds.centerx
                    portal_center_y = portal_bounds.centery
                    # Don't avoid portals when intentionally trying to reach one
                    self.pathfind_to(portal_center_x, portal_center_y, avoid_portals=False)
    
    def _follow_path(self, dt: float) -> None:
        """Move along the current path using feet position."""
        if self.current_waypoint_idx >= len(self.path):
            # Path complete - but if we're doing cross-scene travel, keep moving toward portal
            if self.scene_path and self.current_scene_step < len(self.scene_path):
                # Continue moving toward portal center even if path is complete
                current_step = self.scene_path[self.current_scene_step]
                portal_id = current_step[1]
                
                # If portal_id is None, we've reached the final destination scene
                if portal_id is None:
                    self.scene_path = None
                    self.target_scene = None
                    self.path = []
                    self.current_waypoint_idx = 0
                    return
                
                if self.mask_system:
                    feet_x, feet_y = self._get_feet_position()
                    
                    # Check if we're in the portal yet
                    if self.mask_system.point_in_portal(int(feet_x), int(feet_y), portal_id):
                        # We're in the portal, stop moving
                        self.path = []
                        self.current_waypoint_idx = 0
                        return
                    
                    # Not in portal yet - continue moving toward portal center
                    portal_bounds = self.mask_system.get_portal_bounds(portal_id)
                    if portal_bounds:
                        portal_center_x = portal_bounds.centerx
                        portal_center_y = portal_bounds.centery
                        
                        dx = portal_center_x - feet_x
                        dy = portal_center_y - feet_y
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance > 1:
                            # Keep moving toward portal (update direction for animation)
                            if abs(dx) > abs(dy):
                                self.direction = "right" if dx > 0 else "left"
                            else:
                                self.direction = "down" if dy > 0 else "up"
                            
                            move_distance = self.speed * dt
                            if move_distance >= distance:
                                self._set_position_from_feet(portal_center_x, portal_center_y)
                            else:
                                new_feet_x = feet_x + (dx / distance) * move_distance
                                new_feet_y = feet_y + (dy / distance) * move_distance
                                self._set_position_from_feet(new_feet_x, new_feet_y)
                            return
            
            self.path = []
            self.current_waypoint_idx = 0
            return
        
        # Get current feet position
        feet_x, feet_y = self._get_feet_position()
        
        target = self.path[self.current_waypoint_idx]
        dx = target[0] - feet_x
        dy = target[1] - feet_y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Update direction based on movement
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        else:
            self.direction = "down" if dy > 0 else "up"
        
        # Use smaller threshold for intermediate waypoints, but never mark the path as
        # complete if we're doing cross-scene travel - let the portal check handle that
        waypoint_threshold = 5
        is_final_waypoint = (self.current_waypoint_idx == len(self.path) - 1)
        
        if is_final_waypoint and self.scene_path and self.current_scene_step < len(self.scene_path):
            # For cross-scene travel, don't advance past the final waypoint
            # Instead, let the path-complete logic above handle portal entry
            waypoint_threshold = 2  # Very small threshold - we want to get close then let portal logic take over
        
        # If close enough to waypoint, move to next
        if distance < waypoint_threshold:
            self.current_waypoint_idx += 1
            return
        
        # Move towards waypoint
        if distance > 0:
            move_distance = self.speed * dt
            if move_distance >= distance:
                # Reached waypoint - set position using feet coordinates
                self._set_position_from_feet(target[0], target[1])
                self.current_waypoint_idx += 1
            else:
                # Move incrementally using feet coordinates
                new_feet_x = feet_x + (dx / distance) * move_distance
                new_feet_y = feet_y + (dy / distance) * move_distance
                self._set_position_from_feet(new_feet_x, new_feet_y)
