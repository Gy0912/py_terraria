import pygame
from settings import *


class ManaBar:
    """Simple mana bar drawn below the health bar."""

    def __init__(self, max_mana=50):
        self.max_mana = max_mana
        self.mana = max_mana
        self.bar_width = 200
        self.bar_height = 16
        self.x = SCREEN_WIDTH - self.bar_width - 10
        self.y = 30
        self.font = pygame.font.Font(None, 20)

    def use(self, amount):
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False

    def recover(self, amount):
        self.mana = min(self.max_mana, self.mana + amount)

    def draw(self, surface):
        ratio = self.mana / self.max_mana
        pygame.draw.rect(surface, (0, 0, 80),
                         (self.x, self.y, self.bar_width, self.bar_height))
        pygame.draw.rect(surface, BLUE,
                         (self.x, self.y, int(self.bar_width * ratio), self.bar_height))
        pygame.draw.rect(surface, WHITE,
                         (self.x, self.y, self.bar_width, self.bar_height), 1)
        text = self.font.render(f"MP {self.mana}/{self.max_mana}", True, WHITE)
        surface.blit(text, (self.x + 4, self.y + 1))
