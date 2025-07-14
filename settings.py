# game settings
TITLE = "PyTerraria"
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
FPS = 60

# world properties
TILE_SIZE = 32
MAP_WIDTH = 160000
MAP_HEIGHT = 32000
SKY_HEIGHT = 4800
GROUND_HEIGHT = 16000
CAVE_HEIGHT = 17600
HELL_HEIGHT = 27200
ACTUAL_MAP_WIDTH = MAP_WIDTH // TILE_SIZE
ACTUAL_MAP_HEIGHT = MAP_HEIGHT // TILE_SIZE
ACTUAL_SKY_HEIGHT = SKY_HEIGHT // TILE_SIZE
ACTUAL_GROUND_HEIGHT = GROUND_HEIGHT // TILE_SIZE
ACTUAL_CAVE_HEIGHT = CAVE_HEIGHT // TILE_SIZE
ACTUAL_HELL_HEIGHT = HELL_HEIGHT // TILE_SIZE

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHTBLUE = (0, 155, 155)
GRAY = (125, 125, 125)

# Images path
SCREEN_IMAGES = "images/screen_pics/"
BACKGROUND_IMAGES = "images/background_pics/"

# Images
IMAGES_PATH = {
    # start screen
    "start_screen": SCREEN_IMAGES + "start_screen.jpg",
    # background
    "forest": BACKGROUND_IMAGES + "forest.jpg",
    "desert": BACKGROUND_IMAGES + "desert.jpg",
    "snow": BACKGROUND_IMAGES + "snow.jpg",
    "jungle": BACKGROUND_IMAGES + "jungle.jpg",
    "ocean": BACKGROUND_IMAGES + "ocean.jpg",
    "hell": BACKGROUND_IMAGES + "hell.jpg",
    "space": BACKGROUND_IMAGES + "space.jpg",
    "cave": BACKGROUND_IMAGES + "cave.jpg",
    "under_ground": BACKGROUND_IMAGES + "under_ground.jpg",
    "under_snow": BACKGROUND_IMAGES + "under_snow.jpg",
    "under_jungle": BACKGROUND_IMAGES + "under_jungle.jpg",
    "under_ocean": BACKGROUND_IMAGES + "under_ocean.jpg"
}