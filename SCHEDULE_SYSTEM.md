# NPC Schedule System

## Overview

NPCs in Tokyo Times now follow a schedule-based behavior system instead of random state changes. Each NPC has a JSON schedule file that defines their actions throughout the game day, similar to a player piano following a roll.

## Schedule File Format

NPC files are located in `data/npcs/` and named `{npc_id}.json`.

### Structure

```json
{
  "npc_id": "henry",
  "speed": 100.0,
  "initial_position": {
    "scene": "cat_cafe",
    "x": 400,
    "y": 720
  },
  "schedule": [
    {
      "time": "08:00",
      "action": "idle",
      "duration": 300
    },
    {
      "time": "09:00",
      "action": "move_to",
      "scene": "cat_cafe",
      "x": 650,
      "y": 850
    }
  ]
}
```

### Fields

- **npc_id**: Unique identifier for the NPC
- **speed**: Movement speed in pixels per second (e.g., 100.0)
- **initial_position**: Where the NPC starts at the beginning of day 1
  - **scene**: Initial scene name
  - **x**, **y**: Initial coordinates (feet position)
- **schedule**: Array of scheduled actions

## Action Types

### 1. idle
Stops the NPC and makes them idle for a specified duration.

```json
{
  "time": "08:00",
  "action": "idle",
  "duration": 300
}
```

**Parameters:**
- `duration` (number): How long to idle in seconds (game time)

---

### 2. move_to
Moves the NPC to specific coordinates, optionally in a different scene.

```json
{
  "time": "09:00",
  "action": "move_to",
  "scene": "cat_cafe",
  "x": 650,
  "y": 850
}
```

**Parameters:**
- `x` (number, required): Target X coordinate
- `y` (number, required): Target Y coordinate
- `scene` (string, optional): Target scene name. If different from current scene, NPC will navigate there first.

---

### 3. navigate_to_scene
Navigates the NPC to a different scene, with optional destination coordinates.

```json
{
  "time": "14:00",
  "action": "navigate_to_scene",
  "target_scene": "outdoor",
  "x": 300,
  "y": 600
}
```

**Parameters:**
- `target_scene` (string, required): Name of the scene to navigate to
- `x` (number, optional): Destination X coordinate in target scene
- `y` (number, optional): Destination Y coordinate in target scene

---

### 4. loop
Marks the end of the schedule and loops back to the beginning.

```json
{
  "time": "22:00",
  "action": "loop"
}
```

**Note:** Loop is optional. If not present, the NPC will stay in their last action.

## Time Format

Times use 24-hour format: `"HH:MM"`
- Examples: `"08:00"`, `"13:30"`, `"21:45"`
- Game runs from 8:00 AM to 10:00 PM (08:00 - 22:00)
- Actions are sorted by time automatically

## How It Works

1. **Schedule Loading**: When an NPC is created, their schedule is loaded from `data/npcs/{npc_id}.json`

2. **Time Tracking**: The ScheduleController checks the current game time every frame

3. **Action Execution**: When game time reaches a scheduled action's time:
   - The action is executed (pathfinding starts, idle begins, etc.)
   - NPC continues executing that action until it's complete

4. **Action Completion**:
   - `idle`: Completes when duration elapses
   - `move_to`/`navigate_to_scene`: Completes when NPC reaches destination
   - After completion, controller checks for next scheduled action

5. **Looping**: If a `loop` action is present, the schedule repeats from the beginning

## Creating a New NPC Schedule

1. Create a new JSON file in `data/npcs/` named after the NPC (e.g., `sarah.json`)

2. Define the NPC properties and initial position:
   ```json
   {
     "npc_id": "sarah",
     "speed": 120.0,
     "initial_position": {
       "scene": "outdoor",
       "x": 500,
       "y": 600
     },
     "schedule": []
   }
   ```

3. Add scheduled actions in chronological order:
   ```json
   "schedule": [
     {
       "time": "08:00",
       "action": "idle",
       "duration": 600
     },
     {
       "time": "08:10",
       "action": "navigate_to_scene",
       "target_scene": "cat_cafe",
       "x": 700,
       "y": 800
     }
   ]
   ```

4. Optionally add a loop at the end:
   ```json
   {
     "time": "22:00",
     "action": "loop"
   }
   ```

5. The schedule will be automatically loaded when the NPC is created

## Tips

- **Timing**: Remember that game time advances in 15-minute increments every ~16 seconds of real time
- **Coordinates**: Use scene editor or debug output to find exact coordinates
- **Cross-Scene Travel**: The system handles portal navigation automatically
- **Testing**: Watch console output to see when actions execute:
  ```
  henry (cat_cafe) at (400, 720): idle @ 08:00
    -> Idling for 300 seconds
  ```

## Example: Full Daily Schedule

See `data/npcs/henry.json` for a complete example of a daily schedule with multiple scene transitions.
