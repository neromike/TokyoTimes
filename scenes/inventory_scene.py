import pygame
from typing import Any, Optional, Tuple

class InventoryScene:
    def __init__(self, game: Any):
        self.game = game
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.item_font = pygame.font.Font(None, 24)
        
        # Layout constants
        self.QUICK_SLOT_SIZE = 60
        self.QUICK_SLOT_PADDING = 8
        self.BACKPACK_SLOT_SIZE = 50
        self.BACKPACK_SLOT_PADDING = 6
        # Centered horizontally: (1280 - (5*60 + 4*8)) / 2 = (1280 - 332) / 2 = 474
        self.QUICK_SLOTS_X = 474
        self.QUICK_SLOTS_Y = 100
        self.BACKPACK_COLS = 5
        self.BACKPACK_ROWS = 5
        # Centered horizontally: (1280 - (5*50 + 4*6)) / 2 = (1280 - 274) / 2 = 503
        self.BACKPACK_START_X = 503
        self.BACKPACK_START_Y = 200  # Moved down to avoid overlapping with quick slots
        
        # Drag state
        self.dragging_item: Optional[Tuple[str, int]] = None  # (source_type, index) where source_type is "quick" or "backpack"
        self.drag_offset: Tuple[int, int] = (0, 0)
        self.drag_start_pos: Tuple[int, int] = (0, 0)
        self.drag_moved: bool = False
        
        # Menu state
        self.show_menu = False
        self.menu_options = ["Resume", "Save Game", "Return to Title"]
        self.menu_selected = 0
        self.menu_rects = []
        self.save_message = ""
        self.save_message_timer = 0
        self.save_slot_selection = False
        self.save_slot_selected = 1
        self.slot_rects = []

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.save_slot_selection:
                self._handle_save_slot_selection(event)
            elif self.show_menu:
                self._handle_menu_input(event)
            else:
                # Inventory screen input
                if event.key == pygame.K_ESCAPE:
                    self.game.stack.pop()
                elif event.key == pygame.K_TAB:
                    self.show_menu = True
                    self.menu_selected = 0
                elif event.key == pygame.K_DELETE and self.dragging_item:
                    # Drop the dragged item
                    self._drop_dragged_item()
                    self.dragging_item = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_item and not self.show_menu:
                # Track movement to distinguish click vs drag
                if not self.drag_moved:
                    dx = event.pos[0] - self.drag_start_pos[0]
                    dy = event.pos[1] - self.drag_start_pos[1]
                    if abs(dx) > 4 or abs(dy) > 4:
                        self.drag_moved = True
                self.drag_offset = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.save_slot_selection:
                    self._handle_save_slot_click(event.pos)
                elif self.show_menu:
                    self._handle_menu_click(event.pos)
                else:
                    self._handle_inventory_click(event.pos)
        elif event.type == pygame.KEYDOWN and not self.show_menu and not self.save_slot_selection:
            # Mirror main HUD hotkeys: 1-5 selects active quick slot
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
                selected_slot = event.key - pygame.K_1
                active_scene = self._get_scene_with_selected_slot()
                if active_scene:
                    active_scene.selected_inventory_slot = selected_slot
                return
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item and not self.show_menu:  # Left mouse release
                # Drop without changing active slot
                self._try_drop_on_slot(event.pos)

    def _handle_save_slot_selection(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
            self.save_slot_selected = min(3, self.save_slot_selected + 1)
        elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
            self.save_slot_selected = max(1, self.save_slot_selected - 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._save_game(self.save_slot_selected)
            self.save_slot_selection = False
        elif event.key == pygame.K_ESCAPE:
            self.save_slot_selection = False

    def _handle_save_slot_click(self, pos: Tuple[int, int]) -> None:
        for i, rect in enumerate(self.slot_rects):
            if rect.collidepoint(pos):
                self.save_slot_selected = i + 1
                self._save_game(self.save_slot_selected)
                self.save_slot_selection = False
                break

    def _handle_menu_input(self, event: pygame.event.Event) -> None:
        if event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate_menu_option()
        elif event.key == pygame.K_ESCAPE:
            self.show_menu = False

    def _handle_menu_click(self, pos: Tuple[int, int]) -> None:
        for i, rect in enumerate(self.menu_rects):
            if rect.collidepoint(pos):
                self.menu_selected = i
                self._activate_menu_option()
                break

    def _activate_menu_option(self) -> None:
        choice = self.menu_options[self.menu_selected].lower()
        if choice == "resume":
            self.show_menu = False
        elif choice == "save game":
            self.save_slot_selection = True
            self.save_slot_selected = 1
        elif choice == "return to title":
            from scenes.title_scene import TitleScene
            if hasattr(self.game, "reset_run_state"):
                self.game.reset_run_state()
            self.game.stack._stack = []
            self.game.stack.push(TitleScene(self.game))

    def _handle_inventory_click(self, pos: Tuple[int, int]) -> None:
        """Handle clicking on inventory slots to start dragging."""
        # Check quick slots
        for i in range(5):
            rect = self._get_quick_slot_rect(i)
            if rect.collidepoint(pos):
                self.dragging_item = ("quick", i)
                self.drag_offset = pos
                self.drag_start_pos = pos
                self.drag_moved = False
                return
        
        # Check backpack slots
        for row in range(self.BACKPACK_ROWS):
            for col in range(self.BACKPACK_COLS):
                rect = self._get_backpack_slot_rect(row, col)
                if rect.collidepoint(pos):
                    index = row * self.BACKPACK_COLS + col
                    self.dragging_item = ("backpack", index)
                    self.drag_offset = pos
                    self.drag_start_pos = pos
                    self.drag_moved = False
                    return

    def _get_quick_slot_rect(self, slot: int) -> pygame.Rect:
        """Get the rect for a quick slot (0-4)."""
        x = self.QUICK_SLOTS_X + slot * (self.QUICK_SLOT_SIZE + self.QUICK_SLOT_PADDING)
        y = self.QUICK_SLOTS_Y
        return pygame.Rect(x, y, self.QUICK_SLOT_SIZE, self.QUICK_SLOT_SIZE)

    def _get_backpack_slot_rect(self, row: int, col: int) -> pygame.Rect:
        """Get the rect for a backpack slot."""
        x = self.BACKPACK_START_X + col * (self.BACKPACK_SLOT_SIZE + self.BACKPACK_SLOT_PADDING)
        y = self.BACKPACK_START_Y + row * (self.BACKPACK_SLOT_SIZE + self.BACKPACK_SLOT_PADDING)
        return pygame.Rect(x, y, self.BACKPACK_SLOT_SIZE, self.BACKPACK_SLOT_SIZE)

    def _get_player(self):
        """Get the player from the scene stack."""
        for scene in self.game.stack._stack:
            if hasattr(scene, 'player') and scene.player:
                return scene.player
        return None

    def _get_scene_with_selected_slot(self):
        """Get the active scene that tracks selected_inventory_slot."""
        for scene in self.game.stack._stack:
            if hasattr(scene, 'selected_inventory_slot'):
                return scene
        return None

    def _get_selected_slot(self) -> int:
        scene = self._get_scene_with_selected_slot()
        if scene:
            return getattr(scene, 'selected_inventory_slot', 0)
        return 0

    def _drop_dragged_item(self) -> None:
        """Drop the currently dragged item into the world."""
        if not self.dragging_item:
            return
        
        player = self._get_player()
        active_scene = None
        for scene in self.game.stack._stack:
            if hasattr(scene, 'player') and scene.player:
                active_scene = scene
                break
        
        if not player or not active_scene or not hasattr(player, 'inventory'):
            return
        
        source_type, index = self.dragging_item
        inventory_items = player.inventory.items
        
        # Get the item
        if source_type == "quick":
            if index < len(inventory_items) and inventory_items[index] is not None:
                item = inventory_items[index]
                inventory_items.pop(index)
                if hasattr(active_scene, '_spawn_dropped_item'):
                    active_scene._spawn_dropped_item(item, player)
        elif source_type == "backpack":
            # Backpack slots start after quick slots
            backpack_index = index + 5
            if backpack_index < len(inventory_items) and inventory_items[backpack_index] is not None:
                item = inventory_items[backpack_index]
                inventory_items.pop(backpack_index)
                if hasattr(active_scene, '_spawn_dropped_item'):
                    active_scene._spawn_dropped_item(item, player)

    def _handle_drop(self, target_type: str, target_index: int) -> None:
        """Handle dropping an item onto a target slot - swaps items."""
        if not self.dragging_item:
            return
        
        player = self._get_player()
        if not player or not hasattr(player, 'inventory'):
            self.dragging_item = None
            return
        
        inventory_items = player.inventory.items
        source_type, source_index = self.dragging_item
        
        # Ensure inventory is large enough
        max_index_needed = max(source_index, target_index)
        if source_type == "backpack":
            max_index_needed += 5
        if target_type == "backpack":
            max_index_needed += 5
        
        while len(inventory_items) <= max_index_needed:
            inventory_items.append(None)
        
        # Get source and target indices in the inventory list
        source_inv_index = source_index + (5 if source_type == "backpack" else 0)
        target_inv_index = target_index + (5 if target_type == "backpack" else 0)
        
        # Swap items
        inventory_items[source_inv_index], inventory_items[target_inv_index] = \
            inventory_items[target_inv_index], inventory_items[source_inv_index]
        
        self.dragging_item = None

    def _try_drop_on_slot(self, pos: Tuple[int, int]) -> Optional[Tuple[str, int]]:
        """Try to drop the dragged item on a target slot. Returns (type, index) if dropped, else None."""
        if not self.dragging_item:
            return None
        
        player = self._get_player()
        if not player or not hasattr(player, 'inventory'):
            self.dragging_item = None
            return None
        
        target: Optional[Tuple[str, int]] = None
        # Check if dropped on quick slots
        for i in range(5):
            rect = self._get_quick_slot_rect(i)
            if rect.collidepoint(pos):
                target = ("quick", i)
                break
        
        # Check if dropped on backpack slots
        if target is None:
            for row in range(self.BACKPACK_ROWS):
                for col in range(self.BACKPACK_COLS):
                    rect = self._get_backpack_slot_rect(row, col)
                    if rect.collidepoint(pos):
                        slot_index = row * self.BACKPACK_COLS + col
                        target = ("backpack", slot_index)
                        break
                if target:
                    break

        if target:
            self._handle_drop(target[0], target[1])
            return target

        # No valid drop target - just clear the dragging state
        self.dragging_item = None
        return None

    def update(self, dt: float) -> None:
        if self.save_message_timer > 0:
            self.save_message_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        if self.save_slot_selection:
            self._draw_save_slot_selection(surface)
            return
        
        if self.show_menu:
            self._draw_menu(surface)
            return
        
        # Draw backpack screen
        self._draw_backpack(surface)

    def _draw_backpack(self, surface: pygame.Surface) -> None:
        """Draw the main backpack interface with quick slots and backpack grid."""
        # Title
        title = self.title_font.render("Backpack", True, (200, 255, 200))
        title_pos = (20, 20)
        surface.blit(title, title_pos)

        player = self._get_player()
        if not player or not hasattr(player, 'inventory'):
            return
        
        inventory_items = player.inventory.items

        # Draw quick slots label and slots
        quick_label = self.menu_font.render("Quick Slots", True, (200, 200, 200))
        surface.blit(quick_label, (self.QUICK_SLOTS_X, self.QUICK_SLOTS_Y - 30))
        
        selected_slot = self._get_selected_slot()
        for slot in range(5):
            rect = self._get_quick_slot_rect(slot)
            item = inventory_items[slot] if slot < len(inventory_items) else None
            self._draw_slot(surface, rect, item, slot, "quick", selected_slot)

        # Draw backpack label and grid
        backpack_label = self.menu_font.render("Backpack", True, (200, 200, 200))
        surface.blit(backpack_label, (self.BACKPACK_START_X, self.BACKPACK_START_Y - 30))
        
        for row in range(self.BACKPACK_ROWS):
            for col in range(self.BACKPACK_COLS):
                slot_index = row * self.BACKPACK_COLS + col
                inv_index = slot_index + 5  # Backpack starts after quick slots
                item = inventory_items[inv_index] if inv_index < len(inventory_items) else None
                rect = self._get_backpack_slot_rect(row, col)
                self._draw_slot(surface, rect, item, slot_index, "backpack", selected_slot)

        # Draw dragging item if any
        if self.dragging_item:
            self._draw_dragged_item(surface)

        # Draw instructions
        instructions = self.item_font.render("Drag items to move | TAB for menu | ESC to close", True, (150, 150, 150))
        surface.blit(instructions, (20, surface.get_height() - 30))

    def _draw_slot(self, surface: pygame.Surface, rect: pygame.Rect, item: Any, slot_index: int, slot_type: str, selected_slot: int) -> None:
        """Draw a single inventory slot."""
        is_dragging_this = (self.dragging_item and 
                           self.dragging_item[0] == slot_type and 
                           self.dragging_item[1] == slot_index)
        
        # Draw background and border
        bg_color = (50, 50, 50) if not is_dragging_this else (40, 40, 40)
        pygame.draw.rect(surface, bg_color, rect)
        
        is_selected_quick = slot_type == "quick" and slot_index == selected_slot
        border_color = (255, 200, 0) if is_selected_quick else ((150, 150, 150) if not is_dragging_this else (100, 100, 100))
        border_width = 3 if is_selected_quick else (2 if not is_dragging_this else 1)
        pygame.draw.rect(surface, border_color, rect, border_width)

        if item is not None:
            # Draw item sprite
            item_sprite = self._get_item_sprite(item)
            if item_sprite:
                if slot_type == "quick":
                    scale_factor = min((rect.width - 4) / item_sprite.get_width(),
                                     (rect.height - 4) / item_sprite.get_height())
                else:
                    scale_factor = min((rect.width - 4) / item_sprite.get_width(),
                                     (rect.height - 4) / item_sprite.get_height())
                
                scaled_width = int(item_sprite.get_width() * scale_factor)
                scaled_height = int(item_sprite.get_height() * scale_factor)
                scaled_sprite = pygame.transform.scale(item_sprite, (scaled_width, scaled_height))
                
                item_x = rect.centerx - scaled_width // 2
                item_y = rect.centery - scaled_height // 2
                surface.blit(scaled_sprite, (item_x, item_y))
            else:
                # Fallback colored box
                inner_padding = 2
                pygame.draw.rect(surface, (150, 150, 100),
                               (rect.x + inner_padding, rect.y + inner_padding,
                                rect.width - 2*inner_padding, rect.height - 2*inner_padding))
            
            # Draw quantity if > 1
            if isinstance(item, dict) and item.get('quantity', 1) > 1:
                qty_text = self.item_font.render(str(item['quantity']), True, (255, 255, 255))
                qty_x = rect.right - qty_text.get_width() - 2
                qty_y = rect.bottom - qty_text.get_height() - 2
                surface.blit(qty_text, (qty_x, qty_y))

    def _get_item_sprite(self, item: Any) -> Optional[pygame.Surface]:
        """Get the sprite for an item."""
        if not isinstance(item, dict):
            return None
        
        sprite_data = item.get('sprite')
        if not isinstance(sprite_data, str) or not self.game or not hasattr(self.game, 'assets'):
            return None
        
        try:
            from core.sprites import SpriteLoader
            full_sheet = self.game.assets.image(sprite_data)
            loader = SpriteLoader(self.game.assets)
            variants = item.get('variants', 1)
            variant_index = item.get('variant_index', 0)
            return loader.slice_variant(full_sheet, variants, variant_index)
        except:
            return None

    def _draw_dragged_item(self, surface: pygame.Surface) -> None:
        """Draw the item being dragged under the mouse cursor."""
        if not self.dragging_item:
            return
        
        player = self._get_player()
        if not player or not hasattr(player, 'inventory'):
            return
        
        inventory_items = player.inventory.items
        source_type, source_index = self.dragging_item
        source_inv_index = source_index + (5 if source_type == "backpack" else 0)
        
        if source_inv_index >= len(inventory_items) or inventory_items[source_inv_index] is None:
            return
        
        item = inventory_items[source_inv_index]
        item_sprite = self._get_item_sprite(item)
        
        if item_sprite:
            # Scale for dragging - larger so it's visible
            scale = 1.0
            scaled_w = int(item_sprite.get_width() * scale)
            scaled_h = int(item_sprite.get_height() * scale)
            scaled_sprite = pygame.transform.scale(item_sprite, (scaled_w, scaled_h))
            
            # Draw at mouse position with offset
            mouse_x, mouse_y = self.drag_offset
            surface.blit(scaled_sprite, (mouse_x - scaled_w // 2, mouse_y - scaled_h // 2))

    def _draw_menu(self, surface: pygame.Surface) -> None:
        """Draw the menu overlay."""
        # Semi-transparent menu background
        menu_bg = pygame.Surface((300, 300))
        menu_bg.fill((40, 40, 60))
        menu_bg.set_alpha(220)
        menu_x = surface.get_width() // 2 - 150
        menu_y = surface.get_height() // 2 - 150
        surface.blit(menu_bg, (menu_x, menu_y))

        # Menu title
        title = self.title_font.render("Menu", True, (200, 255, 200))
        title_pos = (menu_x + 150 - title.get_width() // 2, menu_y + 20)
        surface.blit(title, title_pos)

        # Menu options
        self.menu_rects = []
        start_y = menu_y + 100
        for i, opt in enumerate(self.menu_options):
            is_selected = (i == self.menu_selected)
            color = (255, 255, 0) if is_selected else (200, 200, 200)
            marker = "> " if is_selected else "  "
            text = self.menu_font.render(f"{marker}{opt}", True, color)
            x = menu_x + 150 - text.get_width() // 2
            y = start_y + i * 50
            surface.blit(text, (x, y))
            self.menu_rects.append(pygame.Rect(x - 20, y, text.get_width() + 40, text.get_height()))

    def _draw_save_slot_selection(self, surface: pygame.Surface) -> None:
        """Draw the save slot selection UI."""
        rect = surface.get_rect()
        
        # Draw title
        title = self.title_font.render("Choose Save Slot", True, (255, 200, 100))
        title_pos = (rect.centerx - title.get_width() // 2, rect.centery - 150)
        surface.blit(title, title_pos)
        
        # Draw save slot options
        self.slot_rects = []
        slot_y = rect.centery - 50
        
        for i in range(1, 4):
            is_selected = (i == self.save_slot_selected)
            
            # Draw slot background if selected
            if is_selected:
                bg_rect = pygame.Rect(rect.centerx - 150, slot_y, 300, 50)
                pygame.draw.rect(surface, (50, 50, 100), bg_rect)
                pygame.draw.rect(surface, (100, 150, 255), bg_rect, 2)
            
            # Draw slot text
            color = (255, 255, 0) if is_selected else (200, 200, 200)
            marker = "> " if is_selected else "  "
            slot_text = self.menu_font.render(f"{marker}Slot {i}", True, color)
            x = rect.centerx - slot_text.get_width() // 2
            surface.blit(slot_text, (x, slot_y + 10))
            
            # Store clickable rect
            slot_rect = pygame.Rect(rect.centerx - 150, slot_y, 300, 50)
            self.slot_rects.append(slot_rect)
            
            slot_y += 70
        
        # Draw instructions
        instructions = self.item_font.render("Press LEFT/RIGHT/UP/DOWN or click to select, SPACE/ENTER to save, ESC to cancel", True, (150, 150, 150))
        instructions_pos = (rect.centerx - instructions.get_width() // 2, rect.bottom - 40)
        surface.blit(instructions, instructions_pos)

    def _save_game(self, slot: int = 1) -> None:
        """Save the current game state."""
        try:
            slot_name = f"slot{slot}"
            run_state = self.game.saves.capture_run_state(self.game)
            knowledge_state = {"seen_intro": True}
            self.game.saves.save(slot_name, run_state, knowledge_state)
            self.save_message = f"Game saved to Slot {slot}!"
            self.save_message_timer = 2.0
        except Exception as e:
            self.save_message = f"Save failed: {str(e)}"
            self.save_message_timer = 2.0
