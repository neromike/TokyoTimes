"""Central registry for prop presets and helper factory."""
from entities.interactables import Prop

# Add new props here; keep sprite/mask paths in one place
PROP_PRESETS = {
    "arcade_spaceship": {
        "sprite": "props/arcade_cabinet_spaceship.png",
        "mask": "props/arcade_cabinet_spaceship_mask.png",
        "variants": 1,
        "default_variant": 0,
    },
    "arcade_blocks": {
        "sprite": "props/arcade_cabinet_blocks.png",
        "mask": "props/arcade_cabinet_blocks_mask.png",
        "variants": 1,
        "default_variant": 0,
    },
    "cat_food_dish": {
        "sprite": "props/cat_food_dish.png",
        "mask": "props/cat_food_dish_mask.png",
        "variants": 3,
        "default_variant": 0,
        "scale": 2.0,
        "is_item": True,
        "item_data": {"name": "cat_food_dish", "description": "A tasty cat food dish", "sprite": "props/cat_food_dish.png"},
    },
}

def make_prop(name: str, x: float, y: float, game=None, variant_index: int = None, scale: float = None, item_id: str = None) -> Prop:
    cfg = PROP_PRESETS.get(name)
    if not cfg:
        raise ValueError(f"Unknown prop preset: {name}")
    variants = cfg.get("variants", 1)
    default_variant = cfg.get("default_variant", 0)
    default_scale = cfg.get("scale", 1.0)
    is_item = cfg.get("is_item", False)
    item_data = cfg.get("item_data", {})
    if variant_index is None:
        variant_index = default_variant
    if scale is None:
        scale = default_scale
    
    # Generate item_id if this is an item and no id provided
    final_item_id = item_id
    if is_item and not final_item_id:
        # Default ID format: name:x:y
        final_item_id = f"{name}:{int(x)}:{int(y)}"
    
    return Prop(
        x=x,
        y=y,
        sprite_path=cfg.get("sprite"),
        mask_path=cfg.get("mask"),
        game=game,
        name=name,
        variants=variants,
        variant_index=variant_index,
        scale=scale,
        is_item=is_item,
        item_data=item_data,
        item_id=final_item_id
    )
