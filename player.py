import pygame
from settings import *

class Player:
    def __init__(self):
        self.width = 32
        self.height = 48
        self.color = (0, 255, 0)
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.speed = 32
        self.max_x = MAP_WIDTH - SCREEN_WIDTH
        self.max_y = MAP_HEIGHT - SCREEN_HEIGHT

    def handle_input(self, keys=None):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed

        self.x = max(0, min(self.x, self.max_x))
        self.y = max(0, min(self.y, self.max_y))

    def update(self, keys=None):
        self.handle_input(keys)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
