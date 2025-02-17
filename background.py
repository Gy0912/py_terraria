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
            "under_ocean": pygame.image.load(IMAGES_PATH["under_ocean"]).convert(),
            "star": pygame.image.load(IMAGES_PATH["star"]).convert()
        }
        # set the background image
        self.current_bg = self.bg_images["forest"]
        self.width, self.height = self.current_bg.get_rect().size

    def update(self, biome):
        if biome in self.bg_images and self.current_bg != self.bg_images[biome]:
            self.current_bg = self.bg_images[biome]
            self.width, self.height = self.current_bg.get_rect().size

    def draw(self, camera_x):
        pos_x_tmp = (camera_x // self.slowing_rate) % self.width
        num_tiles = SCREEN_WIDTH // self.width + 2

        for i in range(-1, num_tiles):
            self.screen.blit(self.current_bg, (pos_x_tmp + i * self.width, 0))