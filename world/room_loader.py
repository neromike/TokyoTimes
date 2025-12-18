# Currently unused

import json
from pathlib import Path
from world.room import Room

class RoomLoader:
    def load(self, path: str) -> Room:
        p = Path("game/data") / path
        if not p.exists():
            return Room({"id": "empty"})
        data = json.loads(p.read_text())
        return Room(data)
