# Currently unused

import pygame
from typing import Protocol

class Scene(Protocol):
    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    def update(self, dt: float) -> None:
        ...

    def draw(self, surface: pygame.Surface) -> None:
        ...
