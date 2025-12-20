"""Configuration for NPC properties.

DEPRECATION NOTICE:
As of the schedule system implementation, most behavioral parameters in this file
(idle_min_duration, wander_probability, travel_probability, etc.) are no longer used.
NPCs now follow time-based schedules defined in data/schedules/{npc_id}.json.

The only parameter still actively used is:
- speed: Movement speed in pixels per second

See SCHEDULE_SYSTEM.md for the new NPC behavior system.
"""

class NPCConfig:
    """Configuration for NPC properties.
    
    DEPRECATED: Most parameters are no longer used. NPCs now use schedule files.
    Only 'speed' is still actively used for movement speed.
    """
    def __init__(
        self,
        name: str,
        # Idle state settings
        idle_min_duration: float = 2.0,
        idle_max_duration: float = 5.0,
        # State transition probabilities (from idle state)
        wander_probability: float = 0.65,
        travel_probability: float = 0.10,
        # Idle again probability is calculated as: 1 - wander - travel
        # Wander state settings
        wander_min_distance: float = 50.0,
        wander_radius: float = 200.0,
        wander_portal_min_distance: float = 50.0,
        max_wander_time: float = 10.0,
        # Travel state settings
        max_travel_time: float = 30.0,
        # Movement
        speed: float = 100.0,
    ):
        self.name = name
        # Idle settings
        self.idle_min_duration = idle_min_duration
        self.idle_max_duration = idle_max_duration
        # Probabilities
        self.wander_probability = wander_probability
        self.travel_probability = travel_probability
        self.idle_again_probability = 1.0 - wander_probability - travel_probability
        # Wander settings
        self.wander_min_distance = wander_min_distance
        self.wander_radius = wander_radius
        self.wander_portal_min_distance = wander_portal_min_distance
        self.max_wander_time = max_wander_time
        # Travel settings
        self.max_travel_time = max_travel_time
        # Movement
        self.speed = speed


# Pre-defined NPC configurations
HENRY_CONFIG = NPCConfig(
    name="Henry",
    idle_min_duration=2.0,
    idle_max_duration=5.0,
    wander_probability=0.65,  # 65% chance to wander
    travel_probability=0.10,  # 10% chance to travel to another scene
    # 25% chance to idle again (calculated automatically)
    wander_radius=200.0,
    wander_portal_min_distance=50.0,
    max_wander_time=10.0,
    max_travel_time=30.0,
    speed=100.0,
)

# Example: A more active NPC that wanders more and travels less
ACTIVE_CONFIG = NPCConfig(
    name="Active",
    idle_min_duration=1.0,
    idle_max_duration=3.0,
    wander_probability=0.80,  # 80% chance to wander
    travel_probability=0.05,  # 5% chance to travel
    # 15% chance to idle again
    wander_radius=300.0,
    speed=150.0,
)

# Example: A lazy NPC that mostly idles
LAZY_CONFIG = NPCConfig(
    name="Lazy",
    idle_min_duration=5.0,
    idle_max_duration=10.0,
    wander_probability=0.30,  # 30% chance to wander
    travel_probability=0.05,  # 5% chance to travel
    # 65% chance to idle again
    wander_radius=100.0,
    speed=50.0,
)

# Example: An explorer that loves to travel between scenes
EXPLORER_CONFIG = NPCConfig(
    name="Explorer",
    idle_min_duration=1.0,
    idle_max_duration=2.0,
    wander_probability=0.40,  # 40% chance to wander
    travel_probability=0.50,  # 50% chance to travel!
    # 10% chance to idle again
    wander_radius=250.0,
    speed=120.0,
)
