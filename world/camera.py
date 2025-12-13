class Camera:
    def __init__(self, screen_width: int, screen_height: int):
        self.x = 0
        self.y = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def follow(self, target_x: float, target_y: float, world_width: int, world_height: int) -> None:
        # Center camera on target
        self.x = target_x - self.screen_width // 2
        self.y = target_y - self.screen_height // 2
        
        # Clamp camera to world bounds
        self.x = max(0, min(self.x, world_width - self.screen_width))
        self.y = max(0, min(self.y, world_height - self.screen_height))
    
    def apply(self, x: float, y: float) -> tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        return x - self.x, y - self.y
