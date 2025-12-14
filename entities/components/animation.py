import pygame

class Spritesheet:
    """Handles spritesheet parsing and frame extraction."""
    def __init__(self, image: pygame.Surface, frame_width: int, frame_height: int):
        self.image = image
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frames = self._parse_frames()

    def _parse_frames(self) -> list[pygame.Surface]:
        """Extract all frames from the spritesheet."""
        frames = []
        cols = self.image.get_width() // self.frame_width
        rows = self.image.get_height() // self.frame_height
        
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    col * self.frame_width,
                    row * self.frame_height,
                    self.frame_width,
                    self.frame_height
                )
                frames.append(self.image.subsurface(rect).copy())
        
        return frames

    def get_frame(self, index: int) -> pygame.Surface:
        """Get a frame by index."""
        return self.frames[index % len(self.frames)] if self.frames else None


class Animation:
    """Handles sprite animation playback."""
    def __init__(self, spritesheet: Spritesheet, fps: int = 10, scale: float = 1.0):
        self.spritesheet = spritesheet
        self.fps = fps
        self.frame_time = 1.0 / fps
        self.current_frame = 0
        self.elapsed = 0.0
        self.frame_indices = None  # Optional: specific frame sequence
        self.mirrored = False  # Optional: flip horizontally
        self.scale = scale  # Scale factor for frames
        self.scaled_frame_cache = {}  # Cache scaled frames

    def update(self, dt: float) -> None:
        """Update animation frame."""
        self.elapsed += dt
        if self.elapsed >= self.frame_time:
            frame_count = len(self.frame_indices) if self.frame_indices else len(self.spritesheet.frames)
            self.current_frame = (self.current_frame + 1) % frame_count
            self.elapsed = 0.0

    def get_current_frame(self) -> pygame.Surface:
        """Get the current animation frame."""
        if self.frame_indices:
            idx = self.frame_indices[self.current_frame]
        else:
            idx = self.current_frame
        
        frame = self.spritesheet.get_frame(idx) if self.spritesheet.frames else None
        
        if frame is None:
            return None
        
        # Apply scaling if needed
        if self.scale and self.scale != 1.0:
            cache_key = (id(frame), self.scale, self.mirrored)
            if cache_key not in self.scaled_frame_cache:
                new_width = int(frame.get_width() * self.scale)
                new_height = int(frame.get_height() * self.scale)
                scaled = pygame.transform.scale(frame, (new_width, new_height))
                if self.mirrored:
                    scaled = pygame.transform.flip(scaled, True, False)
                self.scaled_frame_cache[cache_key] = scaled
            return self.scaled_frame_cache[cache_key]
        elif self.mirrored:
            cache_key = (id(frame), self.mirrored)
            if cache_key not in self.scaled_frame_cache:
                self.scaled_frame_cache[cache_key] = pygame.transform.flip(frame, True, False)
            return self.scaled_frame_cache[cache_key]
        
        return frame
