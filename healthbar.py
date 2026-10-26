import pygame

from settings import *
from ui import get_font


class HealthBar:
    """Health bar at the top-right of the screen; reads the player's current values."""

    def __init__(self):
        self.bar_width = 200
        self.bar_height = 16
        self.x = SCREEN_WIDTH - self.bar_width - 10
        self.y = 10
        self.font = get_font(13, bold=True)

    def draw(self, surface, hp, max_hp):
        ratio = max(0.0, hp / max_hp)
        pygame.draw.rect(surface, (80, 0, 0), (self.x, self.y, self.bar_width, self.bar_height))
        pygame.draw.rect(surface, (225, 40, 50), (self.x, self.y, int(self.bar_width * ratio), self.bar_height))
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.bar_width, self.bar_height), 1)
        text = self.font.render(f"生命 {hp}/{max_hp}", True, WHITE)
        surface.blit(text, (self.x + 4, self.y))
