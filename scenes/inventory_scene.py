import pygame
from typing import Any

class InventoryScene:
    def __init__(self, game: Any):
        self.game = game
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.item_font = pygame.font.Font(None, 24)
        self.options = ["Resume", "Return to Title"]
        self.selected = 0
        self.option_rects = []  # Store menu option rects for click detection
        self.item_rects = []  # Store item rects for click detection
        self.selected_item = None  # Currently selected item index

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.stack.pop()
            elif event.key == pygame.K_d:
                # Drop selected item
                if self.selected_item is not None:
                    self._drop_item(self.selected_item)
        elif event.type == pygame.MOUSEMOTION:
            # Check if mouse is over any menu option
            mouse_pos = event.pos
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected = i
                    break
            # Check if mouse is over any item
            for i, rect in enumerate(self.item_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_item = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected = i
                        self._activate_option()
                        break
                # Check if clicking an item
                for i, rect in enumerate(self.item_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_item = i
                        break
            elif event.button == 3:  # Right click to drop
                mouse_pos = event.pos
                for i, rect in enumerate(self.item_rects):
                    if rect.collidepoint(mouse_pos):
                        self._drop_item(i)
                        break

    def _activate_option(self) -> None:
        choice = self.options[self.selected].lower()
        if choice == "resume":
            self.game.stack.pop()
        elif choice == "return to title":
            # Pop all scenes to get back to title
            while len(self.game.stack._stack) > 1:
                self.game.stack.pop()

    def _drop_item(self, item_index: int) -> None:
        """Drop an item from inventory at player's feet position."""
        # Find the player and active scene
        player = None
        active_scene = None
        for scene in self.game.stack._stack:
            if hasattr(scene, 'player'):
                player = scene.player
                active_scene = scene
                break
        
        if not player or not active_scene:
            print("Warning: Cannot drop item - no active scene or player")
            return
        
        if not hasattr(player, 'inventory'):
            return
        
        inventory_items = player.inventory.items
        if item_index < 0 or item_index >= len(inventory_items):
            return
        
        item = inventory_items[item_index]
        
        # Remove from inventory
        player.inventory.items.pop(item_index)
        self.selected_item = None
        
        # Spawn the item prop at player's feet position
        if hasattr(active_scene, '_spawn_dropped_item'):
            active_scene._spawn_dropped_item(item, player)
        
        print(f"Dropped: {item.get('name', 'unknown')}")

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        rect = surface.get_rect()
        title = self.title_font.render("Inventory", True, (200, 255, 200))
        title_pos = (rect.centerx - title.get_width() // 2, rect.top + 20)
        surface.blit(title, title_pos)

        # Draw inventory items
        items_y = title_pos[1] + title.get_height() + 20
        player = None
        # Find the player from the scene stack
        for scene in self.game.stack._stack:
            if hasattr(scene, 'player'):
                player = scene.player
                break
        
        if player and hasattr(player, 'inventory'):
            inventory_items = player.inventory.items
            if inventory_items:
                items_title = self.item_font.render("Items: (Right-click or press D to drop)", True, (200, 200, 200))
                surface.blit(items_title, (50, items_y))
                items_y += items_title.get_height() + 10
                
                self.item_rects = []  # Clear and rebuild each frame
                item_x = 50
                item_y = items_y
                max_width = rect.width - 100
                current_row_height = 0
                
                for idx, item in enumerate(inventory_items):
                    item_name = item.get("name", "Unknown")
                    sprite_path = item.get("sprite")
                    
                    # Load and display item sprite
                    item_sprite = None
                    if sprite_path and self.game and hasattr(self.game, 'assets'):
                        try:
                            item_sprite = self.game.assets.image(sprite_path)
                            # Scale down for inventory display
                            scale = 0.3
                            scaled_w = max(1, int(item_sprite.get_width() * scale))
                            scaled_h = max(1, int(item_sprite.get_height() * scale))
                            item_sprite = pygame.transform.scale(item_sprite, (scaled_w, scaled_h))
                        except Exception as e:
                            print(f"Warning: Could not load item sprite {sprite_path}: {e}")
                            item_sprite = None
                    
                    # Check if we need to wrap to next row
                    item_display_width = (item_sprite.get_width() if item_sprite else 60) + 150
                    if item_x + item_display_width > max_width and item_x > 50:
                        item_x = 50
                        item_y += current_row_height + 15
                        current_row_height = 0
                    
                    # Store starting position for this item
                    item_start_x = item_x
                    
                    # Highlight if selected
                    is_selected = (idx == self.selected_item)
                    
                    # Draw item sprite
                    if item_sprite:
                        surface.blit(item_sprite, (item_x, item_y))
                        item_width = item_sprite.get_width()
                        item_height = item_sprite.get_height()
                        item_x += item_width + 10
                        current_row_height = max(current_row_height, item_height)
                    else:
                        # Fallback: draw colored box
                        pygame.draw.rect(surface, (100, 100, 100), (item_x, item_y, 50, 50))
                        item_width = 50
                        item_height = 50
                        item_x += 60
                        current_row_height = max(current_row_height, 50)
                    
                    # Draw item name next to sprite
                    name_color = (255, 255, 100) if is_selected else (200, 200, 200)
                    name_text = self.item_font.render(item_name, True, name_color)
                    surface.blit(name_text, (item_x, item_y + item_height // 2 - name_text.get_height() // 2))
                    
                    # Store clickable rect for this item
                    item_rect = pygame.Rect(item_start_x, item_y, item_x - item_start_x + name_text.get_width(), current_row_height)
                    self.item_rects.append(item_rect)
                    
                    # Draw selection border if selected
                    if is_selected:
                        pygame.draw.rect(surface, (255, 255, 100), item_rect, 2)
                    
                    item_x += name_text.get_width() + 30
            else:
                empty_text = self.item_font.render("(empty)", True, (150, 150, 150))
                surface.blit(empty_text, (50, items_y))
                items_y += empty_text.get_height() + 20

        # Draw menu options below items
        start_y = items_y + 40
        self.option_rects = []  # Clear and rebuild each frame
        for i, opt in enumerate(self.options):
            sel = (i == self.selected)
            color = (255, 255, 0) if sel else (200, 200, 200)
            marker = "> " if sel else "  "
            text = self.menu_font.render(f"{marker}{opt}", True, color)
            x = rect.centerx - text.get_width() // 2
            y = start_y + i * 40
            surface.blit(text, (x, y))
            
            # Store clickable rect for this option
            self.option_rects.append(pygame.Rect(x, y, text.get_width(), text.get_height()))
