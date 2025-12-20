# Currently unused

import pygame
from world.room import Room
from world.room_loader import RoomLoader

class World:
    def __init__(self):
        self.loader = RoomLoader()
        self.current_room: Room = self.loader.load("rooms/room_001.json")

    def update(self, dt: float) -> None:
        self.current_room.update(dt)

    def draw(self, surface: pygame.Surface, camera) -> None:
        self.current_room.draw(surface, camera)
