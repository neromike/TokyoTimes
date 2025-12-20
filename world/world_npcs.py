"""NPC definitions for the world.

Each NPC is defined once with their initial scene and position.
Once the game starts, they become persistent world objects that can move between scenes.

NOTE: Initial position and properties (like speed) are now defined in NPC files in data/npcs/.
The values here serve as fallbacks if file loading fails.
"""

import json
from pathlib import Path


def _load_schedule_data(npc_id: str) -> dict:
    """Load data from NPC schedule file."""
    try:
        schedule_path = Path("data/npcs") / f"{npc_id}.json"
        with open(schedule_path, 'r') as f:
            data = json.load(f)
        init_pos = data.get("initial_position", {})
        return {
            "scene": init_pos.get("scene"),
            "x": init_pos.get("x"),
            "y": init_pos.get("y"),
            "speed": data.get("speed"),
        }
    except Exception:
        return {}


# Map of npc_id -> NPC definition
# Each NPC has a unique ID, type, initial scene, and starting position
# Initial position and speed are loaded from schedule file if available, otherwise uses fallback values
_henry_schedule = _load_schedule_data("henry")

NPCS_DEFINITION = {
    "henry": {
        "type": "henry",
        "initial_scene": _henry_schedule.get("scene", "cat_cafe"),
        "x": _henry_schedule.get("x", 400),
        "y": _henry_schedule.get("y", 720),
        "sprite_scale": 0.5,
    },
    # Add more NPCs here as you create them
    # "sarah": {
    #     "type": "sarah",
    #     "initial_scene": "cat_cafe_kitchen_scene",
    #     "x": 500,
    #     "y": 600,
    #     "sprite_scale": 1.0,
    # },
}


def get_npcs_for_scene(scene_name: str) -> list:
    """Deprecated: Use world_registry.get_npcs_in_scene() instead.
    
    This function is kept for backwards compatibility during migration.
    """
    from world.world_registry import get_npcs_in_scene
    npcs_in_scene = get_npcs_in_scene(scene_name)
    # Convert to the old format for compatibility
    return [
        {
            "type": npc.npc_type,
            "x": npc.x,
            "y": npc.y,
        }
        for npc in npcs_in_scene
    ]

