import pygame
from settings import *


class HealthBar:
    """Simple health bar drawn at top-right of screen."""

    def __init__(self, max_hp=100):
        self.max_hp = max_hp
        self.hp = max_hp
        self.bar_width = 200
        self.bar_height = 16
        self.x = SCREEN_WIDTH - self.bar_width - 10
        self.y = 10
        self.font = pygame.font.Font(None, 20)

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def draw(self, surface):
        ratio = self.hp / self.max_hp
        # Background (dark red)
        pygame.draw.rect(surface, (80, 0, 0),
                         (self.x, self.y, self.bar_width, self.bar_height))
        # Foreground (red)
        pygame.draw.rect(surface, RED,
                         (self.x, self.y, int(self.bar_width * ratio), self.bar_height))
        # Border
        pygame.draw.rect(surface, WHITE,
                         (self.x, self.y, self.bar_width, self.bar_height), 1)
        # Text
        text = self.font.render(f"HP {self.hp}/{self.max_hp}", True, WHITE)
        surface.blit(text, (self.x + 4, self.y + 1))
