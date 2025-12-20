import pygame
from typing import Any
from pathlib import Path


class LoadGameScene:
    """Scene for selecting and loading a saved game."""
    
    def __init__(self, game: Any):
        self.game = game
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Get list of save files
        self.save_slots = self._get_save_slots()
        self.selected = 0
        self.slot_rects = []  # Store clickable rects for each save slot
    
    def _get_save_slots(self) -> list[dict]:
        """Get list of available save files with metadata."""
        # Use the same directory the SaveSystem writes to
        saves_dir = getattr(getattr(self.game, "saves", None), "base", Path("saves"))
        saves_dir.mkdir(parents=True, exist_ok=True)
        
        save_slots = []
        # Look for .sav files
        for save_file in sorted(saves_dir.glob("*.sav")):
            slot_name = save_file.stem
            try:
                import json
                data = json.loads(save_file.read_text())
                run_state = data.get("run", {})
                # Extract useful info for display
                room = run_state.get("room", "Unknown")
                save_slots.append({
                    "slot": slot_name,
                    "file": save_file,
                    "room": room,
                    "data": data
                })
            except Exception as e:
                print(f"Warning: Could not load save file {save_file}: {e}")
                save_slots.append({
                    "slot": slot_name,
                    "file": save_file,
                    "room": "Corrupted",
                    "data": None
                })
        
        # Add empty slots up to 3 total
        while len(save_slots) < 3:
            slot_num = len(save_slots) + 1
            save_slots.append({
                "slot": f"slot{slot_num}",
                "file": saves_dir / f"slot{slot_num}.sav",
                "room": "Empty",
                "data": None
            })
        
        return save_slots

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.save_slots)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.save_slots)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._load_selected()
            elif event.key == pygame.K_ESCAPE:
                self.game.stack.pop()  # Return to title
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for i, rect in enumerate(self.slot_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected = i
                        self._load_selected()
                        break

    def _load_selected(self) -> None:
        """Load the selected save slot."""
        slot = self.save_slots[self.selected]
        
        # Only load if not empty
        if slot["data"] is None:
            return
        
        # Load the save
        run_state, knowledge_state = slot["data"].get("run", {}), slot["data"].get("knowledge", {})
        
        # Determine target scene
        room = run_state.get("scene", run_state.get("room", "cat_cafe"))
        
        # Reset to a clean state, apply world/global data, then start the scene
        if hasattr(self.game, "reset_run_state"):
            self.game.reset_run_state()
        self.game.saves.apply_run_state(self.game, run_state)

        # Clear stack and load target scene fresh
        self.game.stack._stack = []
        from scenes.scene_registry import get_scene_class
        from scenes.generic_scene import GenericScene
        scene_class = get_scene_class(room)
        if scene_class is None:
            # Fallback to cat_cafe if scene not found
            scene_class = get_scene_class("cat_cafe")
            if scene_class is None:
                # Ultimate fallback: create GenericScene directly
                self.game.stack.push(GenericScene(self.game, scene_name="cat_cafe"))
                return

        self.game.stack.push(scene_class(self.game))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        rect = surface.get_rect()
        
        # Fill background to cover any underlying scenes
        surface.fill((20, 20, 40))
        
        # Draw title
        title = self.title_font.render("Load Game", True, (255, 255, 255))
        title_pos = (rect.centerx - title.get_width() // 2, rect.top + 40)
        surface.blit(title, title_pos)
        
        # Draw save slots
        start_y = title_pos[1] + title.get_height() + 60
        self.slot_rects = []  # Clear and rebuild each frame
        
        for i, slot in enumerate(self.save_slots):
            is_selected = (i == self.selected)
            is_empty = slot["data"] is None
            
            # Draw slot background if selected
            if is_selected:
                bg_rect = pygame.Rect(rect.centerx - 300, start_y + i * 80, 600, 70)
                pygame.draw.rect(surface, (50, 50, 80), bg_rect)
                pygame.draw.rect(surface, (100, 150, 255), bg_rect, 2)
            
            # Draw slot label
            color = (255, 255, 0) if is_selected else (200, 200, 200)
            marker = "> " if is_selected else "  "
            slot_text = self.menu_font.render(f"{marker}{slot['slot'].upper()}", True, color)
            x = rect.centerx - 250
            y = start_y + i * 80 + 5
            surface.blit(slot_text, (x, y))
            
            # Draw room info
            if is_empty:
                info_text = self.small_font.render("(Empty)", True, (150, 150, 150))
            else:
                info_text = self.small_font.render(f"Room: {slot['room']}", True, (180, 180, 180))
            surface.blit(info_text, (x + 20, y + 35))
            
            # Store clickable rect
            slot_rect = pygame.Rect(rect.centerx - 300, start_y + i * 80, 600, 70)
            self.slot_rects.append(slot_rect)
        
        # Draw instructions
        instructions = self.small_font.render("Press SPACE/ENTER to load, ESC to cancel", True, (150, 150, 150))
        instructions_pos = (rect.centerx - instructions.get_width() // 2, rect.bottom - 40)
        surface.blit(instructions, instructions_pos)
