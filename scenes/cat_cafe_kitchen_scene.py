import pygame
from typing import Any
from entities.player import Player
from world.camera import Camera
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
from scenes.cat_cafe_kitchen_geometry import get_collision_rects, get_portals
from entities.player_config import (
    PLAYER_HITBOX_OFFSET_CENTERX,
    PLAYER_HITBOX_OFFSET_BOTTOM,
)

class CatCafeKitchenScene:
    def __init__(self, game: Any, spawn=(200, 500)):
        self.game = game
        try:
            self.background = game.assets.image("backgrounds/cat_cafe_kitchen.jpg")
        except Exception as e:
            print(f"Warning: Could not load kitchen background: {e}")
            self.background = None
        self.font = pygame.font.Font(None, 24)

        # World dimensions
        if self.background:
            self.world_width = self.background.get_width()
            self.world_height = self.background.get_height()
        else:
            self.world_width = WINDOW_WIDTH
            self.world_height = WINDOW_HEIGHT

        # Camera and player
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.player = Player(x=spawn[0], y=spawn[1], game=game)

        # Geometry lives in scenes/cat_cafe_kitchen_geometry.py
        self.collision_rects = get_collision_rects(self.world_width, self.world_height)
        self.player.collision_rects = self.collision_rects

        # Portal back to cafe (left wall gap)
        self.portals = get_portals(self.world_width, self.world_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.inventory_scene import InventoryScene
            self.game.stack.push(InventoryScene(self.game))

    def update(self, dt: float) -> None:
        self.player.update(dt)
        self.camera.follow(self.player.x, self.player.y, self.world_width, self.world_height)

        for portal in self.portals:
            if portal["rect"].colliderect(self.player.collision_rect):
                self._enter_portal(portal)
                break

    def draw(self, surface: pygame.Surface) -> None:
        if self.background:
            bg_x, bg_y = self.camera.apply(0, 0)
            surface.blit(self.background, (bg_x, bg_y))
        else:
            surface.fill((60, 60, 60))

        # Draw collision shapes (rects + polygons) for debugging
        for shape in self.collision_rects:
            if isinstance(shape, pygame.Rect):
                screen_x, screen_y = self.camera.apply(shape.x, shape.y)
                pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_y, shape.width, shape.height), 2)
            elif isinstance(shape, dict) and 'polygon' in shape:
                pts = shape['polygon']
                screen_pts = [self.camera.apply(px, py) for (px, py) in pts]
                if len(screen_pts) >= 2:
                    pygame.draw.lines(surface, (255, 0, 0), True, screen_pts, 2)

        # Draw portal trigger zone for debugging
        for portal in getattr(self, "portals", []):
            px, py = self.camera.apply(portal["rect"].x, portal["rect"].y)
            pygame.draw.rect(surface, (0, 128, 255), (px, py, portal["rect"].width, portal["rect"].height), 2)

        # Draw player
        player_screen_x, player_screen_y = self.camera.apply(self.player.x, self.player.y)
        temp_surface = pygame.Surface((self.player.sprite.get_width(), self.player.sprite.get_height()), pygame.SRCALPHA)
        self.player.sprite and temp_surface.blit(self.player.sprite, (0, 0))
        surface.blit(temp_surface, (player_screen_x, player_screen_y))

        # Player collision rect (debug)
        coll_x, coll_y = self.camera.apply(
            self.player.collision_rect.x,
            self.player.collision_rect.y,
        )
        hb_surf = pygame.Surface((self.player.collision_rect.width, self.player.collision_rect.height), pygame.SRCALPHA)
        hb_surf.fill((0, 255, 0, 80))
        surface.blit(hb_surf, (coll_x, coll_y))
        pygame.draw.rect(surface, (0, 255, 0), (
            coll_x,
            coll_y,
            self.player.collision_rect.width,
            self.player.collision_rect.height,
        ), 2)

        surface.blit(self.font.render("Kitchen (ESC for inventory)", True, (255, 255, 255)), (8, 8))

    def _enter_portal(self, portal: dict) -> None:
        target = portal.get("to_scene")
        spawn = portal.get("spawn", (self.world_width // 2, self.world_height // 2))
        if target == "cat_cafe":
            from scenes.cat_cafe_scene import CatCafeScene
            self.game.stack.pop()
            self.game.stack.push(CatCafeScene(self.game))
