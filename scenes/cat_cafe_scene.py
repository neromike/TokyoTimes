import pygame
from typing import Any
from entities.player import Player
from world.camera import Camera
from world.mask_collision import MaskCollisionSystem
from settings import WINDOW_WIDTH, WINDOW_HEIGHT
from scenes.cat_cafe_geometry import PORTAL_MAP
from entities.player_config import (
    PLAYER_HITBOX_OFFSET_CENTERX,
    PLAYER_HITBOX_OFFSET_BOTTOM,
)

class CatCafeScene:
    def __init__(self, game: Any):
        self.game = game
        try:
            self.background = game.assets.image("backgrounds/cat_cafe.jpg")
        except Exception as e:
            print(f"Warning: Could not load cat cafe background: {e}")
            self.background = None
        
        # Load collision mask
        try:
            mask_img = game.assets.image("backgrounds/cat_cafe_mask.png")
            self.mask_system = MaskCollisionSystem(mask_img)
            print(f"Loaded mask: {len(self.mask_system.portal_regions)} portal regions detected")
            for pid in self.mask_system.portal_regions:
                bounds = self.mask_system.get_portal_bounds(pid)
                print(f"  Portal {pid}: {bounds}")
        except Exception as e:
            print(f"Warning: Could not load cat cafe mask: {e}")
            self.mask_system = None
        
        self.font = pygame.font.Font(None, 24)
        
        # Get world dimensions from background or use defaults
        if self.background:
            self.world_width = self.background.get_width()
            self.world_height = self.background.get_height()
        else:
            self.world_width = WINDOW_WIDTH
            self.world_height = WINDOW_HEIGHT
        
        # Create camera and player
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.player = Player(x=self.world_width // 2, y=self.world_height // 2, game=game)
        
        # Use mask-based collision if available
        self.player.mask_system = self.mask_system
        self.player.collision_rects = []  # Clear rect-based collisions

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.inventory_scene import InventoryScene
                self.game.stack.push(InventoryScene(self.game))

    def update(self, dt: float) -> None:
        self.player.update(dt)
        # Camera follows player but respects world bounds
        self.camera.follow(self.player.x, self.player.y, self.world_width, self.world_height)

        # Check portals using mask system
        if self.mask_system:
            portal_id = self.mask_system.rect_in_portal(self.player.collision_rect)
            if portal_id is not None and portal_id in PORTAL_MAP:
                self._enter_portal(portal_id)

    def draw(self, surface: pygame.Surface) -> None:
        # Draw background at camera offset
        if self.background:
            bg_x, bg_y = self.camera.apply(0, 0)
            surface.blit(self.background, (bg_x, bg_y))
        else:
            surface.fill((139, 69, 19))
        
        # Draw portal regions for debugging
        if self.mask_system:
            for portal_id in self.mask_system.portal_regions:
                bounds = self.mask_system.get_portal_bounds(portal_id)
                if bounds:
                    px, py = self.camera.apply(bounds.x, bounds.y)
                    pygame.draw.rect(surface, (0, 128, 255), (px, py, bounds.width, bounds.height), 2)
                    # Label the portal
                    label = self.font.render(f"P{portal_id}", True, (0, 128, 255))
                    surface.blit(label, (px + 5, py + 5))
        
        # Draw player at camera-relative position
        player_screen_x, player_screen_y = self.camera.apply(self.player.x, self.player.y)
        temp_surface = pygame.Surface((self.player.sprite.get_width(), self.player.sprite.get_height()), pygame.SRCALPHA)
        self.player.sprite and temp_surface.blit(self.player.sprite, (0, 0))
        surface.blit(temp_surface, (player_screen_x, player_screen_y))
        
        # Draw player collision rect for debugging
        if hasattr(self.player, 'collision_rect'):
            coll_x, coll_y = self.camera.apply(
                self.player.collision_rect.x,
                self.player.collision_rect.y,
            )
            # Semi-transparent fill to make hitbox easy to see
            hb_surf = pygame.Surface((self.player.collision_rect.width, self.player.collision_rect.height), pygame.SRCALPHA)
            hb_surf.fill((0, 255, 0, 80))
            surface.blit(hb_surf, (coll_x, coll_y))
            pygame.draw.rect(surface, (0, 255, 0), (
                coll_x,
                coll_y,
                self.player.collision_rect.width,
                self.player.collision_rect.height,
            ), 2)
        
        surface.blit(self.font.render("Cat Cafe (ESC for inventory)", True, (255, 255, 255)), (8, 8))

    def _enter_portal(self, portal_id: int) -> None:
        portal_config = PORTAL_MAP.get(portal_id)
        if not portal_config:
            return
        
        target = portal_config.get("to_scene")
        spawn = portal_config.get("spawn", (self.world_width // 2, self.world_height // 2))
        
        if target == "cat_cafe_kitchen":
            from scenes.cat_cafe_kitchen_scene import CatCafeKitchenScene
            self.game.stack.pop()
            self.game.stack.push(CatCafeKitchenScene(self.game, spawn=spawn))
