"""
Schedule-based NPC behavior system.

NPCs follow a predefined schedule of actions based on in-game time,
similar to a player piano following a roll.
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class ScheduleAction:
    """Represents a single scheduled action for an NPC."""
    
    def __init__(self, time_str: str, action_type: str, params: Dict[str, Any]):
        """
        Args:
            time_str: Time in HH:MM format (24-hour)
            action_type: Type of action (idle, move_to, navigate_to_scene, loop)
            params: Action-specific parameters
        """
        self.time_str = time_str
        self.action_type = action_type
        self.params = params
        
        # Parse time to minutes since midnight
        hours, minutes = map(int, time_str.split(':'))
        self.time_minutes = hours * 60 + minutes
    
    def __repr__(self):
        return f"ScheduleAction({self.time_str}, {self.action_type})"


class ScheduleController:
    """Controls NPC behavior based on a time-scheduled action list."""
    
    def __init__(self, schedule_file: str, npc, game):
        """
        Args:
            schedule_file: Path to the JSON schedule file (relative to data/npcs/)
            npc: The NPC instance this controller manages
            game: Game instance for accessing clock and assets
        """
        self.npc = npc
        self.game = game
        self.schedule_file = schedule_file
        self.actions: List[ScheduleAction] = []
        self.current_action_index = 0
        self.current_action: Optional[ScheduleAction] = None
        self.action_start_time = 0.0  # Game time when current action started
        self.is_executing = False  # Whether we're currently executing an action
        self.loop_enabled = False  # Whether schedule loops
        
        # Initial position
        self.initial_position = None
        
        # NPC properties from schedule
        self.speed = None  # Movement speed from schedule
        
        # Load schedule
        self._load_schedule()
    
    def _load_schedule(self):
        """Load schedule from JSON file."""
        try:
            # Build path relative to game root
            schedule_path = Path("data/npcs") / self.schedule_file
            
            with open(schedule_path, 'r') as f:
                data = json.load(f)
            
            # Parse NPC properties
            self.speed = data.get("speed", 100.0)  # Default speed if not specified
            
            # Parse initial position
            init_pos = data.get("initial_position", {})
            self.initial_position = {
                "scene": init_pos.get("scene", "cat_cafe"),
                "x": init_pos.get("x", 400),
                "y": init_pos.get("y", 720)
            }
            
            # Parse schedule actions
            schedule_data = data.get("schedule", [])
            for action_data in schedule_data:
                time_str = action_data.get("time", "00:00")
                action_type = action_data.get("action", "idle")
                
                # Extract parameters (everything except time and action)
                params = {k: v for k, v in action_data.items() if k not in ["time", "action"]}
                
                # Check for loop action
                if action_type == "loop":
                    self.loop_enabled = True
                else:
                    action = ScheduleAction(time_str, action_type, params)
                    self.actions.append(action)
            
            # Sort actions by time
            self.actions.sort(key=lambda a: a.time_minutes)
            
            print(f"[Schedule] Loaded {len(self.actions)} actions for {self.npc.npc_type}")
            
        except Exception as e:
            print(f"[Schedule] Error loading schedule from {schedule_path}: {e}")
            # Create a minimal default schedule
            self.actions = []
    
    def get_current_game_time_minutes(self) -> int:
        """Get current game time in minutes since midnight."""
        if not self.game:
            return 0
        
        # Use game.hour and game.minute if available
        if hasattr(self.game, 'hour') and hasattr(self.game, 'minute'):
            return self.game.hour * 60 + self.game.minute
        
        # Fallback: try game_time directly
        if hasattr(self.game, 'game_time'):
            return self.game.game_time
        
        return 0
    
    def update(self, dt: float):
        """Update schedule controller - check if it's time for next action."""
        if not self.actions:
            return
        
        current_time = self.get_current_game_time_minutes()
        
        # Always evaluate the most recent action that should be active by now
        next_action = self._find_next_action(current_time)
        
        if next_action and next_action != self.current_action:
            # Warn if we're preempting a movement action that hasn't finished yet
            if self.is_executing and self.current_action and not self._is_action_complete():
                if self.current_action.action_type in ["move_to", "navigate_to_scene"]:
                    npc_name = getattr(self.npc, 'npc_id', self.npc.npc_type)
                    print(f"[Schedule] Warning: {npc_name} still pathfinding during transition from {self.current_action.action_type} to {next_action.action_type} at {next_action.time_str}")
            # Preempt current action at scheduled time
            self._start_action(next_action)
        else:
            # If current action finished early (e.g., reached destination), mark idle
            if self.is_executing and self._is_action_complete():
                self.is_executing = False
            # Occasional wait log when idle before first action of the day
            if not self.is_executing and current_time > 0:
                if not hasattr(self, '_last_wait_log') or current_time - self._last_wait_log >= 10:
                    self._last_wait_log = current_time
                    hours = current_time // 60
                    mins = current_time % 60
                    next_time = next_action.time_str if next_action else "N/A"
                    print(f"[Schedule] {self.npc.npc_type} waiting at {hours:02d}:{mins:02d}, next action at {next_time}")
    
    def _find_next_action(self, current_time: int) -> Optional[ScheduleAction]:
        """Find the next action that should be active at the given time."""
        if not self.actions:
            return None
        
        # Find the most recent action that should have started by now
        active_action = None
        
        for action in self.actions:
            if action.time_minutes <= current_time:
                active_action = action
            else:
                break  # Actions are sorted, so we can stop
        
        # If no action found and loop is enabled, wrap around
        if not active_action and self.loop_enabled:
            # We're past all actions - loop back to first
            active_action = self.actions[0]
        
        return active_action
    
    def _is_action_complete(self) -> bool:
        """Check if current action has completed."""
        if not self.current_action or not self.is_executing:
            return True
        
        action_type = self.current_action.action_type
        
        if action_type == "idle":
            # Idle persists until the next scheduled action.
            return False
        
        elif action_type in ["move_to", "navigate_to_scene"]:
            # Check if NPC has reached destination (no path remaining)
            return not self.npc.path or self.npc.current_waypoint_idx >= len(self.npc.path)
        
        return True
    
    def _start_action(self, action: ScheduleAction):
        """Execute a scheduled action."""
        self.current_action = action
        self.is_executing = True
        self.action_start_time = self.get_current_game_time_minutes() * 60  # Convert to seconds
        
        action_type = action.action_type
        params = action.params
        
        # Get NPC position and scene for logging
        from world.world_registry import get_npc_location
        npc_name = getattr(self.npc, 'npc_id', self.npc.npc_type)
        scene_name = get_npc_location(npc_name) or 'Unknown'
        feet_x, feet_y = self.npc._get_feet_position()
        
        print(f"{npc_name} ({scene_name}) at ({int(feet_x)}, {int(feet_y)}): {action_type} @ {action.time_str}")
        
        if action_type == "idle":
            # Stop moving, clear path
            self.npc.path = []
            self.npc.current_waypoint_idx = 0
            self.npc.velocity_x = 0
            self.npc.velocity_y = 0
            self.npc.destination = None  # Clear destination to prevent re-pathing
            self.npc.scene_path = None  # Clear scene path
            self.npc.target_scene = None
            print(f"  -> Idling until next scheduled action")
        
        elif action_type == "move_to":
            # Move to coordinates in current or specified scene
            target_scene = params.get("scene")
            target_x = params.get("x")
            target_y = params.get("y")
            
            if target_x is None or target_y is None:
                print(f"  -> Warning: move_to missing coordinates")
                return
            
            # Check if we need to change scenes first
            current_scene = getattr(self.npc.scene, 'scene_name', None) if hasattr(self.npc, 'scene') else None
            
            if target_scene and target_scene != current_scene:
                # Need to navigate to different scene first
                print(f"  -> Moving to {target_scene} ({target_x}, {target_y})")
                self.npc.pathfind_to_scene(target_scene, target_x, target_y)
            else:
                # Same scene - just pathfind to coordinates
                print(f"  -> Moving to ({target_x}, {target_y})")
                self.npc.pathfind_to(target_x, target_y)
        
        elif action_type == "navigate_to_scene":
            # Navigate to a different scene
            target_scene = params.get("target_scene")
            target_x = params.get("x")
            target_y = params.get("y")
            
            if not target_scene:
                print(f"  -> Warning: navigate_to_scene missing target_scene")
                return
            
            print(f"  -> Navigating to {target_scene}")
            self.npc.pathfind_to_scene(target_scene, target_x, target_y)
    
    def reset(self):
        """Reset schedule to beginning."""
        self.current_action_index = 0
        self.current_action = None
        self.is_executing = False
