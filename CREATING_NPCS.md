# Creating NPCs with Scheduled Behaviors

## Overview
NPCs in Tokyo Times use a schedule-based system where their behavior is defined by a timeline of actions, similar to a player piano. Each NPC follows a JSON schedule file that defines what they do at specific times throughout the game day.

## Quick Start

### 1. Create an NPC File

Create a JSON file in `data/npcs/` named after your NPC (e.g., `sarah.json`):

```json
{
  "npc_id": "sarah",
  "initial_position": {
    "scene": "outdoor",
    "x": 500,
    "y": 600
  },
  "schedule": [
    {
      "time": "08:00",
      "action": "idle",
      "duration": 600
    },
    {
      "time": "09:00",
      "action": "navigate_to_scene",
      "target_scene": "cat_cafe",
      "x": 700,
      "y": 800
    },
    {
      "time": "12:00",
      "action": "idle",
      "duration": 1800
    },
    {
      "time": "22:00",
      "action": "loop"
    }
  ]
}
```

### 2. Register the NPC

Add the NPC to `world/world_npcs.py`:

```python
NPCS_DEFINITION = {
    "sarah": {
        "type": "sarah",
        "initial_scene": "outdoor",  # Will be overridden by schedule
        "x": 500,
        "y": 600,
        "sprite_scale": 0.5,
    },
}
```

The NPC will automatically load its schedule and follow it!

## Schedule System

For complete documentation on the schedule system, see [SCHEDULE_SYSTEM.md](SCHEDULE_SYSTEM.md).

## NPC Properties

NPC properties are now defined in the schedule file:
- `speed`: Movement speed in pixels per second (defined in schedule JSON)
