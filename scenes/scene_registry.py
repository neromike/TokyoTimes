"""Central scene registry for portal transitions."""
import json
from pathlib import Path

# Scene registry maps scene names to their classes
# Populated by scenes as they're imported
SCENE_REGISTRY = {}


def register_scene(name: str, scene_class):
    """Register a scene class with a name for portal transitions."""
    SCENE_REGISTRY[name] = scene_class


def get_scene_class(name: str):
    """Get a scene class by name."""
    return SCENE_REGISTRY.get(name)


def auto_register_json_scenes():
    """Automatically register all scenes from data/rooms/ JSON files."""
    from scenes.generic_scene import GenericScene
    from functools import partial
    
    rooms_path = Path("data/rooms")
    if not rooms_path.exists():
        return
    
    for json_file in rooms_path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                config = json.load(f)
            
            scene_name = config.get("scene_name")
            if scene_name and scene_name not in SCENE_REGISTRY:
                # Create a factory function that returns GenericScene with the scene_name preset
                def make_scene(name, game, spawn=None):
                    return GenericScene(game, scene_name=name, spawn=spawn)
                
                # Register using partial to bind the scene_name
                SCENE_REGISTRY[scene_name] = partial(make_scene, scene_name)
                print(f"[SceneRegistry] Auto-registered '{scene_name}' from {json_file.name}")
        except Exception as e:
            print(f"[SceneRegistry] Failed to load {json_file.name}: {e}")


# Auto-register all JSON scenes on import
auto_register_json_scenes()
