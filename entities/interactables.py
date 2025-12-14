import pygame


class Interactable:
    def __init__(self, rect):
        self.rect = rect

    def interact(self, actor):
        pass


class Prop:
    """Generic prop with sprite + mask.
    Black pixels in mask = walkable; transparent/other = blocked (collision handled in player).
    """

    def __init__(self, x: float, y: float, sprite_path: str, mask_path: str = None, game=None, name: str = None, variants: int = 1, variant_index: int = 0, scale: float = 1.0, is_item: bool = False, item_data: dict = None, item_id: str = None):
        self.x = x
        self.y = y
        self.name = name
        self.game = game
        self.scale = max(0.1, float(scale))
        self.sprite = None
        self._sheet = None
        self.variants = max(1, int(variants))
        self.variant_index = max(0, int(variant_index))
        self.is_item = bool(is_item)
        self.item_data = item_data or {}
        self.item_id = item_id  # Unique identifier for tracking across scenes
        self.picked_up = False
        self.mask = None
        self._mask_sheet = None

        if game and sprite_path:
            try:
                self._sheet = game.assets.image(sprite_path)
            except Exception as e:
                print(f"Warning: Could not load prop sprite {sprite_path}: {e}")
                self._sheet = pygame.Surface((64, 64))
                self._sheet.fill((120, 120, 120))

        if game and mask_path:
            try:
                self._mask_sheet = game.assets.image(mask_path)
            except Exception as e:
                print(f"Warning: Could not load prop mask {mask_path}: {e}")
                self._mask_sheet = None

        # Slice the requested variant from the sheets
        if self._sheet:
            self._rebuild_variant_surface()
            self.rect = self.sprite.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 64, 64)

    def _rebuild_variant_surface(self):
        if not self._sheet:
            return
        sheet_w = self._sheet.get_width()
        sheet_h = self._sheet.get_height()
        frame_w = sheet_w // self.variants if self.variants > 0 else sheet_w
        frame_h = sheet_h
        index = max(0, min(self.variant_index, self.variants - 1))
        src_rect = pygame.Rect(index * frame_w, 0, frame_w, frame_h)
        # Create a surface for the sprite frame and blit
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(self._sheet, (0, 0), src_rect)
        self.sprite = frame
        # Also slice the mask variant if a mask sheet exists
        if self._mask_sheet:
            mask_w = self._mask_sheet.get_width()
            mask_h = self._mask_sheet.get_height()
            mask_frame_w = mask_w // self.variants if self.variants > 0 else mask_w
            mask_frame_h = mask_h
            mask_src_rect = pygame.Rect(index * mask_frame_w, 0, mask_frame_w, mask_frame_h)
            mask_frame = pygame.Surface((mask_frame_w, mask_frame_h), pygame.SRCALPHA)
            mask_frame.blit(self._mask_sheet, (0, 0), mask_src_rect)
            self.mask = mask_frame

    def set_variant(self, index: int):
        """Switch to a different variant sprite and mask."""
        self.variant_index = int(index)
        self._rebuild_variant_surface()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        if self.sprite:
            if camera:
                screen_x, screen_y = camera.apply(self.x, self.y)
            else:
                screen_x, screen_y = self.x, self.y
            # Scale the sprite if needed
            if self.scale != 1.0:
                scaled_width = int(self.sprite.get_width() * self.scale)
                scaled_height = int(self.sprite.get_height() * self.scale)
                scaled_sprite = pygame.transform.scale(self.sprite, (scaled_width, scaled_height))
                surface.blit(scaled_sprite, (screen_x, screen_y))
            else:
                surface.blit(self.sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, (120, 120, 120), self.rect)

    def depth(self) -> float:
        """Return depth (y) used for sorting. Uses visible sprite bounds to ignore transparent extensions."""
        if self.sprite:
            # bounding_rect is relative to surface; bottom gives visible height ignoring full transparency
            bbox = self.sprite.get_bounding_rect(min_alpha=1)
            # Account for scaling when calculating depth
            return self.y + bbox.bottom * self.scale
        elif self.rect:
            return self.rect.bottom * self.scale
        return self.y
