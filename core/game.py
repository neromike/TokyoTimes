import pygame
from pathlib import Path
from typing import Optional

from core.scene_stack import SceneStack
from core.input import Input
from core.assets import Assets
from core.events import EventBus
from settings import FPS, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, BG_COLOR
from scenes.title_scene import TitleScene
from core.save_system import SaveSystem

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.stack = SceneStack()
        self.input = Input()
        self.assets = Assets()
        self.events = EventBus()
        # Use shared saves directory so UI and save system align
        self.saves = SaveSystem(Path("saves"))
        self.running = True

        # Initialize a fresh run state (player/world/collections)
        self.reset_run_state()
        
        # Game clock: 8am to 10pm (14 hours = 840 minutes) in 15 real minutes
        # Time advances in 15-minute game increments (56 total increments)
        # Time per increment: 15 real minutes / 56 increments ≈ 16.07 seconds
        self.game_time = 8 * 60  # Start at 8:00 AM (in game minutes since midnight)
        self.game_time_increment = 15  # Jump 15 game minutes per update
        self.time_until_next_increment = 900 / 56  # ~16.07 seconds until next increment
        self.time_accumulator = 0.0  # Accumulate real time
        
        # Precache all scene masks for off-screen NPC wandering
        from world.mask_cache import precache_all_masks
        precache_all_masks(self)

        self.stack.push(TitleScene(self))
    
    @property
    def hour(self) -> int:
        """Current game hour (0-23)."""
        return self.game_time // 60
    
    @property
    def minute(self) -> int:
        """Current game minute (0-59)."""
        return self.game_time % 60

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                        # Debug: force all NPCs to travel on next state change
                        try:
                            from world.world_registry import get_all_npcs
                            for npc in get_all_npcs():
                                npc.force_travel_next = True
                        except Exception:
                            pass
                    top = self.stack.top()
                    if top:
                        top.handle_event(event)

            top = self.stack.top()
            if top:
                top.update(dt)

            # Update game clock (advance time in 15-minute increments)
            self.time_accumulator += dt
            if self.time_accumulator >= self.time_until_next_increment:
                self.game_time += self.game_time_increment
                self.time_accumulator = 0.0
                # Clamp to 8am-10pm range, reset at 10pm
                if self.game_time >= 22 * 60:  # 10pm or beyond
                    self.game_time = 8 * 60  # Reset to 8am

            # Update NPCs globally so they continue advancing state across scenes
            from world.world_registry import update_all_npcs
            update_all_npcs(dt, self)

            self.screen.fill(BG_COLOR)
            self.stack.draw(self.screen)
            pygame.display.flip()

    def quit(self):
        self.running = False

    def reset_run_state(self) -> None:
        """Reset world, player, and item tracking to their starting values."""
        # Clear per-run tracking
        self.picked_up_items = set()
        self.dropped_items = {}

        # Force a fresh player to be created by the next scene
        self.player = None

        # Rebuild world registry state (NPCs/props at defaults)
        from world.world_registry import initialize_world
        initialize_world(self)
        
        # Build complete portal map from all registered scenes
        from world.scene_graph import populate_scene_graph_from_registry
        populate_scene_graph_from_registry()
