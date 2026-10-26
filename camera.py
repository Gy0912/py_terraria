import pygame
from settings import *

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.speed = 10
        self.max_x = MAP_WIDTH - SCREEN_WIDTH
        self.max_y = MAP_HEIGHT - SCREEN_HEIGHT

    def handle_input(self):
        keys = pygame.key.get_pressed()
        old_x, old_y = self.x, self.y
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
        
        self.x = max(0, min(self.x, self.max_x))
        self.y = max(0, min(self.y, self.max_y))