"""Cat Cafe Kitchen scene geometry - collision rects, portals, and spawn points."""
import pygame

# Wall dimensions
WALL_THICKNESS = 80
DOORWAY_TOP = 420
DOORWAY_HEIGHT = 140

# Spawn point in cafe when returning from kitchen
PORTAL_TO_CAFE_SPAWN_OFFSET_FROM_RIGHT = 200  # Distance from right edge
PORTAL_TO_CAFE_SPAWN_Y = 500


def get_collision_rects(world_width: int, world_height: int):
    """Build collision rectangles for the kitchen scene."""
    return [
        pygame.Rect(0, 0, world_width, WALL_THICKNESS),  # Top
        pygame.Rect(0, world_height - WALL_THICKNESS, world_width, WALL_THICKNESS),  # Bottom
        pygame.Rect(0, 0, WALL_THICKNESS, world_height),  # Left
        pygame.Rect(world_width - WALL_THICKNESS, 0, WALL_THICKNESS, world_height),  # Right
    ]


def get_portals(world_width: int, world_height: int):
    """Build portal definitions for the kitchen scene using coordinates."""
    spawn_x = world_width - PORTAL_TO_CAFE_SPAWN_OFFSET_FROM_RIGHT
    # Define by coordinates: top-left and bottom-right
    top_left = (0, DOORWAY_TOP)
    bottom_right = (WALL_THICKNESS, DOORWAY_TOP + DOORWAY_HEIGHT)
    rect = pygame.Rect(
        top_left[0],
        top_left[1],
        bottom_right[0] - top_left[0],
        bottom_right[1] - top_left[1],
    )
    return [
        {
            "rect": rect,
            "to_scene": "cat_cafe",
            "spawn": (spawn_x, PORTAL_TO_CAFE_SPAWN_Y),
        }
    ]
