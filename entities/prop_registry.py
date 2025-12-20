"""Central registry for prop presets and helper factory.

Presets are defined in data/props/{prop_id}.json. This module loads those
JSON files on demand to resolve sprite paths, variants, default scale, and
item metadata, then constructs `Prop` instances.
"""
import json
from pathlib import Path
from entities.interactables import Prop
from core.sprite_registry import get_sprite_config

_PROP_CACHE = {}

def _load_prop_preset(name: str) -> dict:
    """Load a prop preset from data/props/{name}.json (with simple caching)."""
    if name in _PROP_CACHE:
        return _PROP_CACHE[name]
    json_path = Path("data/props") / f"{name}.json"
    if not json_path.exists():
        raise ValueError(f"Unknown prop preset: {name} (missing {json_path})")
    try:
        with open(json_path, "r") as f:
            cfg = json.load(f)
            _PROP_CACHE[name] = cfg
            return cfg
    except Exception as e:
        raise ValueError(f"Failed to load prop preset {name}: {e}")

def make_prop(name: str, x: float, y: float, game=None, variant_index: int = None, scale: float = None, item_id: str = None, scene_scale: float = 1.0) -> Prop:
    cfg = _load_prop_preset(name)
    variants = cfg.get("variants", 1)
    default_variant = cfg.get("default_variant", 0)
    sprite_key = cfg.get("sprite_key")

    # Default scale: preset override, otherwise sprite registry, else 1.0
    default_scale = cfg.get("scale")
    if default_scale is None and sprite_key:
        sprite_cfg = get_sprite_config(sprite_key)
        default_scale = sprite_cfg.get("scale", 1.0)
    if default_scale is None:
        default_scale = 1.0

    # Base scale comes from caller override or defaults; scene_scale multiplies on top
    base_scale = scale if scale is not None else default_scale
    is_item = bool(cfg.get("is_item", False))
    item_data = cfg.get("item_data", {}) or {}

    # Resolve sprite paths from registry (preferred) or direct paths (fallback)
    sprite_path = None
    mask_path = None
    if sprite_key:
        sprite_cfg = get_sprite_config(sprite_key)
        sprite_path = sprite_cfg.get("path")
        mask_path = sprite_cfg.get("mask_path")
    else:
        sprite_path = cfg.get("sprite_path")
        mask_path = cfg.get("mask_path")

    if variant_index is None:
        variant_index = default_variant

    # Generate item_id if this is an item and no id provided
    final_item_id = item_id
    if is_item and not final_item_id:
        final_item_id = f"{name}:{int(x)}:{int(y)}"

    return Prop(
        x=x,
        y=y,
        sprite_path=sprite_path,
        mask_path=mask_path,
        game=game,
        name=name,
        variants=variants,
        variant_index=variant_index,
        scale=base_scale,
        scene_scale=scene_scale,
        is_item=is_item,
        item_data=item_data,
        item_id=final_item_id,
    )
