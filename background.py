import pygame
from settings import *

class Background:
    def __init__(self, screen):
        self.screen = screen
        self.slowing_rate = 3
        self.bg_images = {
            "forest": pygame.image.load(IMAGES_PATH["forest"]).convert(),
            "desert": pygame.image.load(IMAGES_PATH["desert"]).convert(),
            "snow": pygame.image.load(IMAGES_PATH["snow"]).convert(),
            "jungle": pygame.image.load(IMAGES_PATH["jungle"]).convert(),
            "ocean": pygame.image.load(IMAGES_PATH["ocean"]).convert(),
            "hell": pygame.image.load(IMAGES_PATH["hell"]).convert(),
            "space": pygame.image.load(IMAGES_PATH["space"]).convert(),
            "cave": pygame.image.load(IMAGES_PATH["cave"]).convert(),
            "under_ground": pygame.image.load(IMAGES_PATH["under_ground"]).convert(),
            "under_snow": pygame.image.load(IMAGES_PATH["under_snow"]).convert(),
            "under_jungle": pygame.image.load(IMAGES_PATH["under_jungle"]).convert(),
            "under_ocean": pygame.image.load(IMAGES_PATH["under_ocean"]).convert()
        }
        # set the background image
        self.current_bg = self.bg_images["forest"]
        self.width, self.height = self.current_bg.get_rect().size

    def update(self, biome):
        if biome in self.bg_images and self.current_bg != self.bg_images[biome]:
            self.current_bg = self.bg_images[biome]
            self.width, self.height = self.current_bg.get_rect().size

    def draw(self, camera_x, camera_y):
        pos_x = (camera_x // self.slowing_rate) % self.width
        pos_y = (camera_y // self.slowing_rate) % self.height
        num_tiles_x = SCREEN_WIDTH // self.width + 2
        num_tiles_y = SCREEN_HEIGHT // self.height + 2

        for i in range(-1, num_tiles_x):
            for j in range(-1, num_tiles_y):
                self.screen.blit(self.current_bg, (i * self.width - pos_x, j * self.height - pos_y))