# game settings
TITLE = "PyTerraria"
VERSION = "0.2.0"
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 655
FPS = 60

# world properties (in tiles unless noted)
TILE_SIZE = 32
CHUNK_SIZE = 16
WORLD_W = 5000
WORLD_H = 1000
MAP_WIDTH = WORLD_W * TILE_SIZE    # pixels
MAP_HEIGHT = WORLD_H * TILE_SIZE   # pixels

SPACE_LINE = 80            # rows above this are "space"
SURFACE_LEVEL = 300        # mean surface row
SEA_LEVEL = 304            # ocean water fills down from this row
SURFACE_LAYER_DEPTH = 18   # rows below the local surface still counted as surface layer
CAVERN_LINE = 480
HELL_LINE = 850
LAVA_LINE = 955

# day / night: frames per full 24h cycle
DAY_LENGTH = FPS * 60 * 6
START_HOUR = 8.0

# player
PLAYER_REACH = 6           # tiles
MAGNET_RADIUS = 96         # pixels
PICKUP_RADIUS = 22         # pixels

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHTBLUE = (0, 155, 155)
GRAY = (125, 125, 125)

# fonts able to render Chinese; first file found in %WINDIR%\Fonts is used, then system font names
FONT_FILES = ["msyh.ttc", "msyh.ttf", "Deng.ttf", "simhei.ttf", "simsun.ttc"]
FONT_CANDIDATES = ["microsoftyaheiui", "microsoftyahei", "dengxian", "simhei", "simsun", "notosanscjksc"]

# Images path
SCREEN_IMAGES = "images/screen_pics/"
BACKGROUND_IMAGES = "images/background_pics/"
# optional PNG overrides for procedural textures: images/textures/tiles/<name>.png, items/<name>.png
TEXTURE_OVERRIDE_DIR = "images/textures/"

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

BIOME_NAMES = {
    "forest": "森林", "desert": "沙漠", "snow": "雪原", "jungle": "丛林", "ocean": "海洋",
    "space": "太空", "under_ground": "地下", "under_snow": "地下雪原", "under_jungle": "地下丛林",
    "under_ocean": "地下", "cave": "洞穴层", "hell": "地狱",
}
LAYER_NAMES = {"space": "太空", "surface": "地表", "underground": "地下", "cavern": "洞穴", "hell": "地狱"}
