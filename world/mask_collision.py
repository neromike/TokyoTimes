"""Mask-based collision system for pixel-perfect collision detection and portal regions."""
import pygame
from typing import Optional


class MaskCollisionSystem:
    """Handles collision detection and portal detection based on a mask image.
    
    Mask color scheme:
    - Black (0, 0, 0) = walkable area
    - Transparent/other colors = collision (walls, obstacles)
    - White (255, 255, 255) = portal regions
    """
    
    def __init__(self, mask_image: pygame.Surface):
        self.mask_image = mask_image
        self.width = mask_image.get_width()
        self.height = mask_image.get_height()
        
        # Detect portal regions
        self.portal_regions = self._detect_portal_regions()
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a pixel coordinate is walkable (black or white in mask)."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        
        color = self.mask_image.get_at((int(x), int(y)))
        # Walkable if black (normal area) or white (portal area)
        if color.a > 0:
            is_black = color.r == 0 and color.g == 0 and color.b == 0
            is_white = color.r == 255 and color.g == 255 and color.b == 255
            return is_black or is_white
        return False
    
    def is_portal(self, x: int, y: int) -> Optional[int]:
        """Check if a pixel is in a portal region. Returns portal ID or None."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return None
        
        color = self.mask_image.get_at((int(x), int(y)))
        # Portal if white
        if color.a > 0 and color.r == 255 and color.g == 255 and color.b == 255:
            # Find which portal region this belongs to
            for portal_id, region in self.portal_regions.items():
                if (int(x), int(y)) in region:
                    return portal_id
        return None
    
    def rect_collides(self, rect: pygame.Rect) -> bool:
        """Check if a rect collides with non-walkable areas (transparent/colored).
        Samples corners and center of the rect.
        """
        # Sample points: corners + center
        test_points = [
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
            (rect.centerx, rect.centery),
        ]
        
        for px, py in test_points:
            if not self.is_walkable(px, py):
                return True
        return False
    
    def rect_in_portal(self, rect: pygame.Rect) -> Optional[int]:
        """Check if rect center is in a portal region. Returns portal ID or None."""
        return self.is_portal(rect.centerx, rect.centery)
    
    def _detect_portal_regions(self) -> dict[int, set[tuple[int, int]]]:
        """Detect white portal regions using flood fill.
        Returns dict mapping portal_id -> set of (x, y) coordinates.
        """
        visited = set()
        regions = {}
        portal_id = 0
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in visited:
                    continue
                
                color = self.mask_image.get_at((x, y))
                # Check if white portal pixel
                if color.a > 0 and color.r == 255 and color.g == 255 and color.b == 255:
                    # Flood fill this region
                    region = self._flood_fill_portal(x, y, visited)
                    if region:
                        regions[portal_id] = region
                        portal_id += 1
        
        return regions
    
    def _flood_fill_portal(self, start_x: int, start_y: int, visited: set) -> set[tuple[int, int]]:
        """Flood fill to find all connected white pixels forming a portal region."""
        region = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
            if x < 0 or y < 0 or x >= self.width or y >= self.height:
                continue
            
            color = self.mask_image.get_at((x, y))
            if not (color.a > 0 and color.r == 255 and color.g == 255 and color.b == 255):
                continue
            
            visited.add((x, y))
            region.add((x, y))
            
            # Add neighbors
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        
        return region
    
    def get_portal_bounds(self, portal_id: int) -> Optional[pygame.Rect]:
        """Get bounding rect for a portal region."""
        if portal_id not in self.portal_regions:
            return None
        
        region = self.portal_regions[portal_id]
        if not region:
            return None
        
        xs = [x for x, y in region]
        ys = [y for x, y in region]
        
        left = min(xs)
        top = min(ys)
        right = max(xs)
        bottom = max(ys)
        
        return pygame.Rect(left, top, right - left + 1, bottom - top + 1)
