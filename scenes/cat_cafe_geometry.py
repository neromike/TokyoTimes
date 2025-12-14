"""Cat Cafe scene geometry - mask-based collision and portal configuration."""

# Portal mapping: portal_id (from white regions in mask) -> scene configuration
# To find portal IDs, run the game with debug enabled and check console output
PORTAL_MAP = {
    0: {
        "to_scene": "cat_cafe_kitchen",
        "spawn": (200, 500),
    },
    # Add more portals as needed:
    # 1: {
    #     "to_scene": "outdoor_scene",
    #     "spawn": (100, 300),
    # },
}
