from settings import *


class Camera:
    """Viewport that follows the player, converting world coords to screen coords."""

    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, target_x, target_y):
        """Center the camera on a target pixel position, clamped to world bounds."""
        self.x = int(target_x - SCREEN_WIDTH // 2)
        self.y = int(target_y - SCREEN_HEIGHT // 2)
        self.x = max(0, min(self.x, MAP_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, MAP_HEIGHT - SCREEN_HEIGHT))

    def apply(self, world_x, world_y):
        """Convert world pixel coords to screen pixel coords."""
        return world_x - self.x, world_y - self.y
