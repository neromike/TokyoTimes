import json
from pathlib import Path


class SaveSystem:
    def __init__(self, base: Path):
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)

    def capture_run_state(self, game) -> dict:
        """Snapshot the current run state for saving."""
        current_scene = "unknown"
        player = None
        for scene in game.stack._stack:
            if hasattr(scene, "scene_name") and scene.scene_name:
                current_scene = scene.scene_name
            if hasattr(scene, "player") and scene.player:
                player = scene.player
                break

        player_state = {}
        if player:
            player_state = {
                "x": getattr(player, "x", 0),
                "y": getattr(player, "y", 0),
                "direction": getattr(player, "direction", "down"),
                "inventory": list(getattr(getattr(player, "inventory", None), "items", [])),
            }

        # Capture persistent world objects
        from world import world_registry

        world_state = world_registry.snapshot_world_state()

        return {
            "scene": current_scene,
            "room": current_scene,  # Kept for compatibility with load UI
            "player": player_state,
            "world": world_state,
            "dropped_items": game.dropped_items,
            "picked_up_items": list(getattr(game, "picked_up_items", set())),
        }

    def apply_run_state(self, game, run_state: dict) -> None:
        """Restore parts of the run state onto the live game objects."""
        if not run_state:
            return

        # Restore global item tracking
        game.dropped_items = run_state.get("dropped_items", {})
        game.picked_up_items = set(run_state.get("picked_up_items", []))

        from world import world_registry

        world_registry.apply_world_state(run_state.get("world", {}), game)

        # Restore player basics if present
        player_state = run_state.get("player", {})
        if player_state:
            applied = False
            for scene in game.stack._stack:
                if hasattr(scene, "player") and scene.player:
                    self.apply_player_state(scene.player, player_state)
                    applied = True
                    break
            if not applied:
                # Store for later application after a new scene creates the player
                game.pending_player_state = player_state

    def apply_player_state(self, player, player_state: dict) -> None:
        """Apply player-specific state onto an existing player instance."""
        if not player_state or not player:
            return
        player.x = player_state.get("x", getattr(player, "x", 0))
        player.y = player_state.get("y", getattr(player, "y", 0))
        player.direction = player_state.get("direction", getattr(player, "direction", "down"))
        if hasattr(player, "inventory") and "inventory" in player_state:
            player.inventory.items = list(player_state.get("inventory", []))

    def save(self, slot: str, run_state: dict, knowledge_state: dict) -> None:
        payload = {"run": run_state, "knowledge": knowledge_state}
        (self.base / f"{slot}.sav").write_text(json.dumps(payload, indent=2))

    def load(self, slot: str) -> tuple[dict, dict]:
        p = self.base / f"{slot}.sav"
        if not p.exists():
            return {}, {}
        data = json.loads(p.read_text())
        return data.get("run", {}), data.get("knowledge", {})
