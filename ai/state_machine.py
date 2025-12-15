import random
import math

# State name constants
STATE_IDLE = "IdleState"
STATE_WANDER = "WanderState"
STATE_TRAVEL = "TravelToSceneState"

# Config defaults
DEFAULT_IDLE_MIN = 2.0
DEFAULT_IDLE_MAX = 5.0
DEFAULT_WANDER_PROB = 0.65
DEFAULT_TRAVEL_PROB = 0.10
DEFAULT_WANDER_MIN_DIST = 50.0
DEFAULT_WANDER_RADIUS = 200.0
DEFAULT_PORTAL_MIN_DIST = 50.0
DEFAULT_MAX_TRAVEL_TIME = 30.0
DEFAULT_NPC_SPEED = 100.0

# Wander constants
WANDER_MAX_ATTEMPTS = 20
TWO_PI = 2 * math.pi
TRAVEL_PROBABILITY_MULT = 0.2  # Boost for mid-travel idle

class State:
    """Base class for NPC states."""
    def __init__(self, npc):
        self.npc = npc
        self.time_in_state = 0.0
    
    def enter(self):
        """Called when entering this state."""
        self.time_in_state = 0.0
    
    def exit(self):
        """Called when exiting this state."""
        pass
    
    def update(self, dt: float) -> str:
        """Update state logic. Returns name of next state or None to stay in current state."""
        self.time_in_state += dt
        return None
    
    def is_complete(self) -> bool:
        """Check if this state has finished its task. Subclasses should override."""
        return False
    
    def get_name(self) -> str:
        """Get the name of this state."""
        return self.__class__.__name__


class IdleState(State):
    """NPC stands still for a duration."""
    def __init__(self, npc):
        super().__init__(npc)
        # Get config from NPC, fallback to constants
        config = getattr(npc, 'config', None)
        self.min_duration = config.idle_min_duration if config else DEFAULT_IDLE_MIN
        self.max_duration = config.idle_max_duration if config else DEFAULT_IDLE_MAX
        self.wander_probability = config.wander_probability if config else DEFAULT_WANDER_PROB
        self.travel_probability = config.travel_probability if config else DEFAULT_TRAVEL_PROB
        self.duration = random.uniform(self.min_duration, self.max_duration)
    
    def enter(self):
        super().enter()
        # Pick a random idle duration
        self.duration = random.uniform(self.min_duration, self.max_duration)
        # Stop any current movement
        self.npc.path = []
        self.npc.current_waypoint_idx = 0
        self.npc.destination = None
    
    def is_complete(self) -> bool:
        """Idle is complete when the idle duration has elapsed."""
        return self.time_in_state >= self.duration
    
    def update(self, dt: float) -> None:
        super().update(dt)


class WanderState(State):
    """NPC walks to a random nearby location within the current scene."""
    def __init__(self, npc):
        super().__init__(npc)
        # Get config from NPC, fallback to constants
        config = getattr(npc, 'config', None)
        self.wander_min_distance = config.wander_min_distance if config else DEFAULT_WANDER_MIN_DIST
        self.wander_radius = config.wander_radius if config else DEFAULT_WANDER_RADIUS
        self.portal_min_distance = config.wander_portal_min_distance if config else DEFAULT_PORTAL_MIN_DIST
        
        # For off-screen warping
        self.target_x = None
        self.target_y = None
        self.warp_time = 0.0
    
    def enter(self):
        super().enter()
        
        mask_system = self.npc.mask_system
        is_offscreen = not mask_system
        
        # Get feet position as reference point for wander calculations
        feet_x, feet_y = self.npc._get_feet_position()
        
        # If off-screen, use precached mask for destination validation
        if not mask_system:
            from world.mask_cache import get_mask_for_scene
            from world.world_registry import get_npc_location
            
            npc_name = getattr(self.npc, 'npc_id', '?')
            scene_name = get_npc_location(npc_name)
            
            mask_system = get_mask_for_scene(scene_name)
            if not mask_system:
                print(f"    [WanderState] {npc_name}: No precached mask for {scene_name}, skipping wander")
                self.npc.path = []
                return
        
        npc_name = getattr(self.npc, 'npc_id', '?')
        
        target_x = None
        target_y = None
        
        for attempt in range(WANDER_MAX_ATTEMPTS):
            # Pick a random point near current position
            angle = random.uniform(0, TWO_PI)
            distance = random.uniform(self.wander_min_distance, self.wander_radius)
            test_x = feet_x + distance * math.cos(angle)
            test_y = feet_y + distance * math.sin(angle)
            
            # Check if this point is walkable
            is_walkable = mask_system.is_walkable(int(test_x), int(test_y))
            if not is_walkable:
                continue
            
            # Check if point is in or too close to a portal
            is_too_close_to_portal = False
            
            # Check if directly in a portal
            if mask_system.is_portal(int(test_x), int(test_y)) is not None:
                continue
            
            # Check distance to all portal regions
            for portal_id in mask_system.portal_regions:
                portal_bounds = mask_system.get_portal_bounds(portal_id)
                if portal_bounds:
                    # Calculate distance to closest point in portal bounds
                    portal_center_x = (portal_bounds.left + portal_bounds.right) / 2
                    portal_center_y = (portal_bounds.top + portal_bounds.bottom) / 2
                    dist_to_portal = math.sqrt((test_x - portal_center_x)**2 + (test_y - portal_center_y)**2)
                    
                    if dist_to_portal < self.portal_min_distance:
                        is_too_close_to_portal = True
                        break
            
            if is_too_close_to_portal:
                continue
            
            # This point is valid - not in portal and not too close
            target_x, target_y = test_x, test_y
            break
        
        # Store target and set up movement
        self.target_x = target_x
        self.target_y = target_y
        
        if target_x is not None:
            if is_offscreen:
                # Off-screen: calculate warp time based on distance and NPC speed
                dist = math.sqrt((target_x - feet_x)**2 + (target_y - feet_y)**2)
                npc_speed = getattr(self.npc, 'speed', DEFAULT_NPC_SPEED)
                self.warp_time = dist / npc_speed if npc_speed > 0 else 0.0
            else:
                # On-screen: pathfind to the destination
                self.npc.pathfind_to(target_x, target_y, avoid_portals=True)
                self.warp_time = 0.0
        else:
            # No valid point found
            npc_name = getattr(self.npc, 'npc_id', '?')
            print(f"    [WanderState] {npc_name}: No valid wander target found after {WANDER_MAX_ATTEMPTS} attempts")
            self.npc.path = []
            self.warp_time = 0.0
    
    def update(self, dt: float) -> None:
        super().update(dt)
    
    def is_complete(self) -> bool:
        """Wander is complete when path is finished (on-screen) or warp timer expires (off-screen)."""
        if self.warp_time > 0:
            # Off-screen warp: check if timer has elapsed
            if self.time_in_state >= self.warp_time:
                # Warp NPC to target position
                if self.target_x is not None and self.target_y is not None:
                    # Apply mask offset when warping (target is feet position, not sprite position)
                    if hasattr(self.npc, 'mask_offset_x') and hasattr(self.npc, 'mask_offset_y'):
                        scaled_offset_x = self.npc.mask_offset_x * self.npc.sprite_scale
                        scaled_offset_y = self.npc.mask_offset_y * self.npc.sprite_scale
                        self.npc.x = self.target_x - scaled_offset_x
                        self.npc.y = self.target_y - scaled_offset_y
                    else:
                        self.npc.x = self.target_x
                        self.npc.y = self.target_y
                return True
            return False
        else:
            # On-screen pathfinding: check if path is finished
            has_path = self.npc.path and self.npc.current_waypoint_idx < len(self.npc.path)
            return not has_path


class TravelToSceneState(State):
    """NPC decides to travel to a different scene."""
    def __init__(self, npc):
        super().__init__(npc)
        # Get config from NPC, fallback to constant
        config = getattr(npc, 'config', None)
        self.max_travel_time = config.max_travel_time if config else DEFAULT_MAX_TRAVEL_TIME
    
    def enter(self):
        super().enter()
        npc_name = getattr(self.npc, 'npc_id', '?')
        
        # Determine current scene using registry
        from world.world_registry import get_npc_location
        current_scene = get_npc_location(npc_name)
        
        if not current_scene:
            self.npc.path = []
            print(f"    No current scene found, aborting travel")
            return

        # Gather portal connections for the current scene from the scene graph
        from world.scene_graph import get_scene_graph
        graph = get_scene_graph()
        connections = graph.connections.get(current_scene, [])

        portals = [{"to_scene": conn[1], "spawn": conn[2]} for conn in connections]

        if not portals:
            self.npc.path = []
            print(f"    No portals found in scene graph or PORTAL_MAP, aborting travel")
            return

        # Filter out portals that lead to the same scene we're already in
        valid_portals = [p for p in portals if p.get('to_scene') and p.get('to_scene') != current_scene]
        

        if not valid_portals:
            self.npc.path = []
            print(f"    No valid portals (all lead to same scene or missing to_scene), aborting travel")
            return

        target_portal = random.choice(valid_portals)
        target_scene = target_portal.get('to_scene')
        if target_scene:
            self.npc.pathfind_to_scene(target_scene)
            return

        # No valid scene found - path will be empty
        self.npc.path = []
        print(f"    No target scene selected, aborting travel")
    
    def is_complete(self) -> bool:
        """Travel is complete when local path and scene path are finished, or timeout reached."""
        has_path = self.npc.path and self.npc.current_waypoint_idx < len(self.npc.path)
        has_scene_path = self.npc.scene_path and self.npc.current_scene_step < len(self.npc.scene_path)
        return (not has_path and not has_scene_path) or self.time_in_state >= self.max_travel_time
    
    def exit(self):
        """When travel is complete, ensure NPC is added to the destination scene if it's active."""
        super().exit()
        
        # Get the NPC's current scene from world registry
        from world.world_registry import get_npc_location
        npc_name = getattr(self.npc, 'npc_id', None)
        current_scene_name = get_npc_location(npc_name)
        
        if not current_scene_name or not self.npc.game:
            return
        
        # Check if this scene is currently active
        active_scene = self.npc.game.stack.top()
        if not active_scene or getattr(active_scene, 'scene_name', None) != current_scene_name:
            return
        
        # Add NPC to scene if not already present
        if self.npc not in active_scene.npcs:
            active_scene.npcs.append(self.npc)
            self.npc.scene = active_scene
            self.npc.mask_system = active_scene.mask_system
            self.npc.props = active_scene.props
    
    def update(self, dt: float) -> None:
        super().update(dt)


class StateMachine:
    """Manages NPC state transitions."""
    def __init__(self, npc, initial_state_name=STATE_IDLE):
        self.npc = npc
        self.states = {}
        self.current_state = None
        self.current_state_name = None
        
        # Register default states
        self.register_state(STATE_IDLE, IdleState(npc))
        self.register_state(STATE_WANDER, WanderState(npc))
        self.register_state(STATE_TRAVEL, TravelToSceneState(npc))
        
        # Set initial state
        self.set_state(initial_state_name)
    
    # ========== Helper predicates ==========
    
    def _get_npc_attr(self, attr_name, default=None):
        """Safely get NPC attribute with default fallback."""
        return getattr(self.npc, attr_name, default)
    
    def _is_mid_travel(self):
        """Check if NPC is in the middle of a scene-to-scene path."""
        scene_path = self._get_npc_attr('scene_path', None)
        current_step = self._get_npc_attr('current_scene_step', 0)
        return bool(scene_path and current_step < len(scene_path))
    
    def register_state(self, name: str, state: State):
        """Register a new state by name."""
        self.states[name] = state
    
    def set_state(self, state_name: str):
        """Transition to a new state."""
        if state_name not in self.states:
            print(f"Warning: State '{state_name}' not registered")
            return
        
        # Exit current state
        if self.current_state:
            self.current_state.exit()
        
        # Enter new state
        self.current_state = self.states[state_name]
        self.current_state_name = state_name
        self.current_state.enter()
    
    def update(self, dt: float):
        """Update the current state. When state is complete, decide the next state."""
        if not self.current_state:
            return
        
        # Tick the current state (accumulates timer, performs actions)
        self.current_state.update(dt)
        
        # Only transition when current state reports completion
        if self.current_state.is_complete():
            next_state = self._decide_next_state()
            if next_state:
                self.set_state(next_state)
    
    def _decide_next_state(self) -> str:
        """Decide the next state when current state is complete.
        
        Called only when current_state.is_complete() is True.
        Chooses between Wander, Travel, or re-enter current state based on probabilities.
        """
        # Get probabilities from idle state config (used for all transitions)
        idle_state = self.states[STATE_IDLE]
        rand = random.random()
        
        # If mid-travel, prefer Travel heavily over Wander
        if self._is_mid_travel():
            wander_p = max(idle_state.wander_probability * TRAVEL_PROBABILITY_MULT, 0.0)
            travel_p = 1.0 - wander_p
        else:
            wander_p = idle_state.wander_probability
            travel_p = idle_state.travel_probability
        
        # Force travel flag override (takes priority)
        if self._get_npc_attr('force_travel_next', False):
            self.npc.force_travel_next = False
            next_state = STATE_TRAVEL
        # Determine next state based on probabilities
        elif rand < wander_p:
            next_state = STATE_WANDER
        elif rand < wander_p + travel_p:
            next_state = STATE_TRAVEL
        else:
            # Idle state (remaining probability)
            next_state = STATE_IDLE
        
        # Log transition decision
        npc_name = getattr(self.npc, 'npc_id', 'Unknown')
        if npc_name and npc_name != 'Unknown':
            from world.world_registry import get_npc_location
            scene_name = get_npc_location(npc_name) or 'Unknown'
            feet_x, feet_y = self.npc._get_feet_position()
            current_state_name = self.current_state_name
            next_state_display = next_state if next_state else current_state_name
            print(f"{npc_name} ({scene_name}) at ({int(feet_x)}, {int(feet_y)}): {next_state_display}")
        
        return next_state


    
    def get_current_state_name(self) -> str:
        """Get the name of the current state."""
        return self.current_state_name
