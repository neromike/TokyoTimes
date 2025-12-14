import pygame

class Collisions:
    @staticmethod
    def _point_in_rect(pt: tuple[int, int], rect: pygame.Rect) -> bool:
        return rect.collidepoint(pt)

    @staticmethod
    def _point_in_polygon(pt: tuple[int, int], poly: list[tuple[int, int]]) -> bool:
        x, y = pt
        inside = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if ((y1 > y) != (y2 > y)):
                xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
                if x < xinters:
                    inside = not inside
        return inside

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4) -> bool:
        def orient(a,b,c):
            return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        o1 = orient(p1,p2,p3)
        o2 = orient(p1,p2,p4)
        o3 = orient(p3,p4,p1)
        o4 = orient(p3,p4,p2)
        return (o1*o2 < 0) and (o3*o4 < 0)

    @staticmethod
    def _rect_edges(rect: pygame.Rect):
        tl = (rect.left, rect.top)
        tr = (rect.right, rect.top)
        bl = (rect.left, rect.bottom)
        br = (rect.right, rect.bottom)
        return [(tl,tr),(tr,br),(br,bl),(bl,tl)]

    @staticmethod
    def rect_vs_polygon(rect: pygame.Rect, poly: list[tuple[int, int]]) -> bool:
        # Any rect corner inside polygon
        corners = [(rect.left, rect.top), (rect.right, rect.top), (rect.right, rect.bottom), (rect.left, rect.bottom)]
        if any(Collisions._point_in_polygon(c, poly) for c in corners):
            return True
        # Any polygon point inside rect
        if any(Collisions._point_in_rect(p, rect) for p in poly):
            return True
        # Any edge intersection
        rect_edges = Collisions._rect_edges(rect)
        for i in range(len(poly)):
            a = poly[i]
            b = poly[(i+1) % len(poly)]
            for e in rect_edges:
                if Collisions._segments_intersect(a, b, e[0], e[1]):
                    return True
        return False
    @staticmethod
    def check_collision(rect: pygame.Rect, collision_shapes: list) -> bool:
        """Check if rect collides with any collision shapes.
        Supports pygame.Rect and dicts with keys: {'polygon': [(x,y), ...]}.
        """
        for shape in collision_shapes:
            if isinstance(shape, pygame.Rect):
                if rect.colliderect(shape):
                    return True
            elif isinstance(shape, dict):
                if 'polygon' in shape:
                    if Collisions.rect_vs_polygon(rect, shape['polygon']):
                        return True
        return False
    
    @staticmethod
    def get_valid_rect_position(old_rect: pygame.Rect, new_rect: pygame.Rect, 
                                collision_rects: list[pygame.Rect]) -> tuple[int, int]:
        """Return valid rect (x, y), sliding along walls if needed.
        Operates directly on the player's collision rect coordinates rather than sprite top-left.
        """
        # If new rect doesn't collide, accept it
        if not Collisions.check_collision(new_rect, collision_rects):
            return new_rect.x, new_rect.y

        # Try X-only movement
        test_rect = new_rect.copy()
        test_rect.x = new_rect.x
        test_rect.y = old_rect.y
        if not Collisions.check_collision(test_rect, collision_rects):
            return test_rect.x, test_rect.y

        # Try Y-only movement
        test_rect.x = old_rect.x
        test_rect.y = new_rect.y
        if not Collisions.check_collision(test_rect, collision_rects):
            return test_rect.x, test_rect.y

        # No valid movement
        return old_rect.x, old_rect.y
