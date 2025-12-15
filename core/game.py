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

        self.stack.push(TitleScene(self))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    top = self.stack.top()
                    if top:
                        top.handle_event(event)

            top = self.stack.top()
            if top:
                top.update(dt)

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
