import pygame

from settings import *
from ui import get_font


class ManaBar:
    """Mana bar below the health bar; reads the player's current values."""

    def __init__(self):
        self.bar_width = 200
        self.bar_height = 16
        self.x = SCREEN_WIDTH - self.bar_width - 10
        self.y = 30
        self.font = get_font(13, bold=True)

    def draw(self, surface, mana, max_mana):
        ratio = max(0.0, mana / max_mana)
        pygame.draw.rect(surface, (0, 0, 80), (self.x, self.y, self.bar_width, self.bar_height))
        pygame.draw.rect(surface, (60, 110, 240), (self.x, self.y, int(self.bar_width * ratio), self.bar_height))
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.bar_width, self.bar_height), 1)
        text = self.font.render(f"魔力 {mana}/{max_mana}", True, WHITE)
        surface.blit(text, (self.x + 4, self.y))
