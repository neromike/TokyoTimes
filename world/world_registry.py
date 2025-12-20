"""World registry for persistent NPCs and props.

These objects exist independently of scenes and persist throughout gameplay.
Scenes only contain references to which objects are currently present.
"""

from typing import Dict, List, Optional, Tuple
from entities.npc import NPC
from entities.interactables import Prop
from pathlib import Path
import json

# Global world state
_npcs: Dict[str, NPC] = {}  # npc_id -> NPC instance
_props: Dict[str, Prop] = {}  # prop_id -> Prop instance
_npc_locations: Dict[str, str] = {}  # npc_id -> current scene_name
_prop_locations: Dict[str, str] = {}  # prop_id -> current scene_name


def initialize_world(game) -> None:
    """Initialize the world with all NPCs and props.
    
    This is called once at game start, before any scenes load.
    """
    global _npcs, _props, _npc_locations, _prop_locations
    
    _npcs.clear()
    _props.clear()
    _npc_locations.clear()
    _prop_locations.clear()
    
    # Create all NPCs
    from world.world_npcs import NPCS_DEFINITION
    for npc_id, npc_def in NPCS_DEFINITION.items():
        npc = NPC(
            x=npc_def['x'],
            y=npc_def['y'],
            game=game,
            sprite_scale=npc_def.get('sprite_scale', 1.0)
        )
        npc.npc_id = npc_id
        npc.npc_type = npc_def.get('type', 'henry')
        _npcs[npc_id] = npc
        _npc_locations[npc_id] = npc_def['initial_scene']
    
    # Create all props from data/props/*.json
    try:
        from entities.prop_registry import make_prop
        props_path = Path("data/props")
        if props_path.exists():
            for json_file in props_path.glob("*.json"):
                with open(json_file, "r") as f:
                    prop_def = json.load(f)
                prop_id = prop_def.get("prop_id") or json_file.stem
                x = prop_def.get("x", 0)
                y = prop_def.get("y", 0)
                variant_index = prop_def.get("variant_index", prop_def.get("default_variant", 0))
                base_scale = prop_def.get("scale", None)
                prop = make_prop(
                    prop_id,
                    x,
                    y,
                    game,
                    variant_index=variant_index,
                    scale=base_scale,
                    item_id=prop_def.get("item_id", prop_id),
                    scene_scale=1.0,
                )
                prop.prop_id = prop_id
                _props[prop_id] = prop
                init_scene = prop_def.get("initial_scene")
                if init_scene:
                    _prop_locations[prop_id] = init_scene
    except Exception as e:
        print(f"[WorldRegistry] Failed to initialize props from data/props: {e}")


def get_npc(npc_id: str) -> Optional[NPC]:
    """Get an NPC by ID."""
    return _npcs.get(npc_id)


def get_prop(prop_id: str) -> Optional[Prop]:
    """Get a prop by ID."""
    return _props.get(prop_id)


def get_npcs_in_scene(scene_name: str) -> List[NPC]:
    """Get all NPCs currently in a scene."""
    npcs = [_npcs[npc_id] for npc_id in _npc_locations 
            if _npc_locations[npc_id] == scene_name and npc_id in _npcs]
    return npcs


def get_props_in_scene(scene_name: str) -> List[Prop]:
    """Get all props currently in a scene."""
    props = [_props[prop_id] for prop_id in _prop_locations 
            if _prop_locations[prop_id] == scene_name and prop_id in _props]
    return props


def move_npc_to_scene(npc_id: str, scene_name: str) -> None:
    """Move an NPC to a different scene."""
    if npc_id in _npc_locations:
        _npc_locations[npc_id] = scene_name


def move_prop_to_scene(prop_id: str, scene_name: str) -> None:
    """Move a prop to a different scene."""
    if prop_id in _prop_locations:
        _prop_locations[prop_id] = scene_name


def get_npc_location(npc_id: str) -> Optional[str]:
    """Get the current scene of an NPC."""
    return _npc_locations.get(npc_id)


def get_prop_location(prop_id: str) -> Optional[str]:
    """Get the current scene of a prop."""
    return _prop_locations.get(prop_id)


def get_all_npcs() -> List[NPC]:
    """Get all NPCs in the world."""
    return list(_npcs.values())


def get_all_props() -> List[Prop]:
    """Get all props in the world."""
    return list(_props.values())


def snapshot_world_state() -> dict:
    """Serialize NPC and prop state for saving."""
    npcs = []
    for npc_id, npc in _npcs.items():
        npcs.append({
            "id": npc_id,
            "x": getattr(npc, "x", 0),
            "y": getattr(npc, "y", 0),
            "direction": getattr(npc, "direction", None),
            "npc_type": getattr(npc, "npc_type", None),
            "scene": _npc_locations.get(npc_id),
        })

    props = []
    for prop_id, prop in _props.items():
        # Store base scale so we can reapply scene scale later
        base_scale = getattr(prop, "base_scale", getattr(prop, "scale", 1.0))
        props.append({
            "id": prop_id,
            "x": getattr(prop, "x", 0),
            "y": getattr(prop, "y", 0),
            "variant_index": getattr(prop, "variant_index", 0),
            "base_scale": base_scale,
            "is_item": getattr(prop, "is_item", False),
            "item_id": getattr(prop, "item_id", prop_id),
            "picked_up": getattr(prop, "picked_up", False),
            "scene": _prop_locations.get(prop_id),
        })

    return {"npcs": npcs, "props": props}


def apply_world_state(state: dict, game) -> None:
    """Apply serialized world state back into the live registry."""
    if not state:
        return

    # Restore NPC positions and locations
    for npc_state in state.get("npcs", []):
        npc_id = npc_state.get("id")
        if not npc_id or npc_id not in _npcs:
            continue
        npc = _npcs[npc_id]
        npc.x = npc_state.get("x", npc.x)
        npc.y = npc_state.get("y", npc.y)
        npc.direction = npc_state.get("direction", getattr(npc, "direction", "down"))
        if npc_state.get("scene"):
            _npc_locations[npc_id] = npc_state["scene"]

    # Restore props
    for prop_state in state.get("props", []):
        prop_id = prop_state.get("id")
        if not prop_id or prop_id not in _props:
            continue
        prop = _props[prop_id]
        prop.x = prop_state.get("x", prop.x)
        prop.y = prop_state.get("y", prop.y)
        prop.picked_up = prop_state.get("picked_up", getattr(prop, "picked_up", False))
        prop.item_id = prop_state.get("item_id", getattr(prop, "item_id", prop_id))

        # Reapply saved base scale and variant
        saved_base_scale = prop_state.get("base_scale")
        if saved_base_scale is not None:
            prop.base_scale = saved_base_scale
            prop.scale = prop.base_scale * getattr(prop, "scene_scale", 1.0)
        if hasattr(prop, "set_variant"):
            prop.set_variant(prop_state.get("variant_index", getattr(prop, "variant_index", 0)))

        if prop_state.get("scene"):
            _prop_locations[prop_id] = prop_state["scene"]


def update_all_npcs(dt: float, game) -> None:
    """Update all NPCs globally regardless of which scene they're in.
    
    This ensures NPCs continue to advance their state machines (idle/wander/travel)
    even when they're not in the currently-active scene.
    """
    for npc_id, npc in _npcs.items():
        if npc and hasattr(npc, "update"):
            npc.update(dt)


def remove_npc(npc_id: str) -> None:
    """Remove an NPC from the world (e.g., if defeated or removed)."""
    if npc_id in _npcs:
        del _npcs[npc_id]
    if npc_id in _npc_locations:
        del _npc_locations[npc_id]


def remove_prop(prop_id: str) -> None:
    """Remove a prop from the world (e.g., if picked up and discarded)."""
    if prop_id in _props:
        del _props[prop_id]
    if prop_id in _prop_locations:
        del _prop_locations[prop_id]
