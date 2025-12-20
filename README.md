# Tokyo Times

A pygame-based adventure game featuring room traversal, NPCs, inventory management, and mini-games. Built with a scene stack architecture for clean modal and screen management.

## Getting Started

### Prerequisites
- Python 3.8+
- pygame

### Installation

1. Clone or download the project.
2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - **Windows:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   - **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies:
```bash
pip install pygame
```

### Running the Game

From the project root:
```bash
python main.py
```

## Game Features

### Title Screen
- **Start**: Begin a new game in the Cat Cafe
- **Save**: Save your progress to slot 1
- **Load**: Load the most recent save
- **Exit**: Quit the game

Navigation: Use **Up/Down** or **W/S**, confirm with **Enter/Space**

### Gameplay
- **ESC**: Open inventory/pause menu
- **Inventory Menu**: Resume or Return to Title

### Locations
- **Cat Cafe**: The starting location with a background image

## Project Structure

```
TokyoTimes/
├── main.py                 # Entry point
├── settings.py             # Game configuration (FPS, window size, etc.)
├── README.md              # This file
├── .gitignore             # Git ignore rules
│
├── core/                  # Engine core (scene stack, assets, input, saves)
│   ├── game.py            # Main Game class with loop
│   ├── scene_stack.py     # Scene stack management
│   ├── scene.py           # Base Scene protocol
│   ├── constants.py       # Game constants
│   ├── input.py           # Input mapping and keybinds
│   ├── assets.py          # Asset loading (images, sounds)
│   ├── events.py          # Event bus for inter-scene communication
│   └── save_system.py     # Save/load functionality
│
├── scenes/                # Game screens/modes
│   ├── base_scene.py      # Base scene with mask-based collision
│   ├── generic_scene.py   # Generic scene that loads from JSON
│   ├── scene_registry.py  # Auto-registers scenes from data/rooms/
│   ├── title_scene.py     # Title screen with main menu
│   ├── world_scene.py     # Legacy world scene
│   ├── inventory_scene.py # Inventory/pause menu
│   ├── pause_scene.py     # Pause screen
│   ├── dialog_scene.py    # Dialogue display
│   ├── load_game_scene.py # Load game menu
│   └── minigames/         # Mini-game scenes
│       ├── arcade_base.py # Base class for arcade games
│       ├── asteroids.py   # Asteroids mini-game
│       └── blocks.py      # Block-breaking mini-game
│
├── world/                 # World and room management
│   ├── world.py           # Global world model
│   ├── room.py            # Individual room class
│   ├── room_loader.py     # Load room data from JSON
│   ├── camera.py          # Camera/viewport (stub)
│   └── collisions.py      # Collision detection (stub)
│
├── entities/              # Game objects
│   ├── entity.py          # Base entity class
│   ├── character.py       # Base character (movement, animation)
│   ├── player.py          # Player character
│   ├── npc.py             # Non-player characters
│   ├── interactables.py   # Interactive objects
│   └── components/        # Modular entity features
│       ├── animation.py   # Animation component (stub)
│       ├── inventory.py   # Inventory component
│       └── dialogue.py    # Dialogue component (stub)
│
├── ai/                    # NPC AI and pathfinding
│   ├── schedule.py        # Schedule-based NPC behavior system
│   ├── behavior.py        # NPC behaviors (follow, wander)
│   ├── pathfinding.py     # A* pathfinding (stub)
│   └── navigation.py      # Cross-room navigation (stub)
│
├── ui/                    # User interface
│   ├── widgets.py         # UI elements (buttons, lists)
│   ├── hud.py             # Heads-up display
│   ├── menus.py           # Menu layouts
│   └── modal.py           # Modal dialogs
│
├── data/                  # Game content (JSON data files)
│   ├── rooms/             # Room definitions
│   │   ├── room_001.json
│   │   └── room_002.json
│   ├── npcs/              # NPC definitions
│   │   └── bob.json
│   ├── items.json         # Item definitions
│   └── dialogue/          # Dialogue scripts
│       └── intro.json
│
├── assets/                # Game media
│   ├── backgrounds/       # Background images (cat_cafe.jpg, etc.)
│   ├── sprites/           # Character and object sprites
│   ├── tilesets/          # Tile map graphics
│   ├── ui/                # UI graphics
│   └── audio/             # Sound effects and music
│
└── saves/                 # Save game files
    ├── slot1.sav
    └── slot2.sav
```

## Architecture Overview

### Scene Stack System
The game uses a **scene stack** for clean screen and modal management:
- Push scenes on top for modals, menus, and mini-games.
- Pop scenes to return to the previous context.
- Only the top scene receives input; lower scenes can be updated optionally.

Example: `Start Game` → TitleScene pops and CatCafeScene is pushed on stack.

### Save System
Saves are split into two buckets:
- **Run State**: Current room, player position, inventory, NPC positions.
- **Knowledge State**: Discovered facts, unlocked shortcuts, seen cutscenes.

Reset on loop keeps run state fresh while preserving knowledge.

### Absolute Imports
All imports use absolute paths from the project root:
```python
from core.game import Game
from scenes.generic_scene import GenericScene
from entities.player import Player

# Load a scene from JSON
scene = GenericScene(game, scene_name="cat_cafe")
```

No relative imports (`.` or `..`) needed.

## Controls

| Key | Action |
|-----|--------|
| **Up/W** | Navigate menu up |
| **Down/S** | Navigate menu down |
| **Enter/Space** | Confirm selection |
| **ESC** | Open inventory / Pause |

## Next Steps

- [ ] Add player sprite and movement
- [ ] Create additional rooms with transitions
- [ ] Implement NPC schedules and dialogue
- [ ] Add collision detection
- [ ] Implement pathfinding for NPCs
- [ ] Create mini-game implementations
- [ ] Add visual effects and animations
- [ ] Implement audio (background music, SFX)

## License

This project is created for learning and development purposes.
