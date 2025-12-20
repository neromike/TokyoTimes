"""Prop data moved to data/props/*.json.

This module now provides only a compatibility helper for legacy code paths
that expect `get_props_for_scene()`. Use world_registry.get_props_in_scene()
for the live Prop instances.
"""

def get_props_for_scene(scene_name: str) -> list:
    """Deprecated: Use world_registry.get_props_in_scene() instead.
    
    This function is kept for backwards compatibility during migration.
    """
    from world.world_registry import get_props_in_scene
    props_in_scene = get_props_in_scene(scene_name)
    # Convert to the old format for compatibility
    return [
        {
            "name": prop.prop_id,
            "x": prop.x,
            "y": prop.y,
            "scale": getattr(prop, 'scale', 1.0),
        }
        for prop in props_in_scene
    ]

