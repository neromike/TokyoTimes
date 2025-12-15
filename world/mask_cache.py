"""Cache of collision masks for all scenes, loaded at startup.

This allows off-screen NPCs to validate wander positions without loading masks on-demand.
"""

# Global mask cache: scene_name -> MaskCollisionSystem
_mask_cache = {}


def get_mask_for_scene(scene_name: str):
    """Get the cached mask for a scene, or None if not cached."""
    return _mask_cache.get(scene_name)


def precache_all_masks(game):
    """Load and cache collision masks for all registered scenes at startup.
    
    This should be called once during game initialization after scene registration.
    
    Args:
        game: The Game instance (for access to assets)
    """
    from scenes.scene_registry import SCENE_REGISTRY
    from world.mask_collision import MaskCollisionSystem
    
    count = 0
    for scene_name, scene_class in SCENE_REGISTRY.items():
        # Get background path from scene class
        background_path = getattr(scene_class, 'BACKGROUND_PATH', None)
        if not background_path:
            continue
        
        # Convert to mask path
        if '.' in background_path:
            parts = background_path.rsplit('.', 1)
            mask_path = f"{parts[0]}_mask.png"
        else:
            mask_path = f"{background_path}_mask.png"
        
        # Load mask image
        mask_img = game.assets.image(mask_path)
        if mask_img:
            _mask_cache[scene_name] = MaskCollisionSystem(mask_img)
            count += 1
    
    if count > 0:
        print(f"[MaskCache] Precached masks for {count} scenes")
