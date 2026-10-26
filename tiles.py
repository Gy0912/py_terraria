"""Tile and wall registries. Tiles are indexed by a small integer id stored in chunk bytearrays."""
from dataclasses import dataclass


@dataclass
class TileDef:
    name: str
    display: str
    solid: bool = True
    hp: int = 50                  # damage needed to break
    min_power: int = 0            # minimum pickaxe power
    tool: str = "pick"            # "pick", "axe", "any", "none"
    drop: str | None = None       # item name dropped when broken
    light: tuple | None = None    # (radius in light cells, intensity 0..1)
    liquid: bool = False
    color: tuple = (128, 128, 128)
    station: bool = False
    support: str | None = None    # "below", "side" or "frame" (door: needs solid above and below)
    size: tuple = (1, 1)          # multi-tile objects (width, height) in tiles
    kind: str | None = None       # container / bed / door / pylon / pot / crystal
    blocks_creatures: bool = False
    id: int = 0


_DEFS = [
    TileDef("air", "空气", solid=False, hp=0, tool="none", color=(0, 0, 0)),
    TileDef("dirt", "泥土", hp=60, drop="dirt", color=(139, 96, 64)),
    TileDef("grass", "草地", hp=60, drop="dirt", color=(76, 160, 60)),
    TileDef("stone", "石块", hp=90, drop="stone", color=(125, 125, 130)),
    TileDef("sand", "沙子", hp=50, drop="sand", color=(219, 196, 130)),
    TileDef("sandstone", "砂岩", hp=90, drop="sandstone", color=(196, 152, 96)),
    TileDef("snow", "雪块", hp=45, drop="snow", color=(236, 242, 250)),
    TileDef("ice", "冰块", hp=80, drop="ice", color=(160, 212, 240)),
    TileDef("mud", "泥浆", hp=60, drop="mud", color=(92, 68, 70)),
    TileDef("jungle_grass", "丛林草", hp=60, drop="mud", color=(110, 200, 40)),
    TileDef("ash", "灰烬", hp=80, drop="ash", color=(78, 74, 80)),
    TileDef("copper_ore", "铜矿", hp=110, drop="copper_ore", color=(205, 120, 60)),
    TileDef("iron_ore", "铁矿", hp=140, drop="iron_ore", color=(180, 155, 140)),
    TileDef("gold_ore", "金矿", hp=180, min_power=35, drop="gold_ore", color=(235, 200, 60)),
    TileDef("hellstone", "狱石", hp=260, min_power=55, drop="hellstone", color=(190, 60, 30),
            light=(3, 0.55)),
    TileDef("obsidian", "黑曜石", hp=220, min_power=55, drop="obsidian", color=(55, 40, 80)),
    TileDef("wood", "木材", hp=80, drop="wood", color=(168, 116, 66)),
    TileDef("stone_brick", "石砖", hp=110, drop="stone_brick", color=(140, 140, 150)),
    TileDef("sandstone_brick", "砂岩砖", hp=110, drop="sandstone_brick", color=(210, 170, 110)),
    TileDef("snow_brick", "雪砖", hp=70, drop="snow_brick", color=(215, 230, 245)),
    TileDef("mud_brick", "泥砖", hp=90, drop="mud_brick", color=(120, 85, 80)),
    TileDef("obsidian_brick", "黑曜石砖", hp=240, min_power=55, drop="obsidian_brick", color=(70, 50, 95)),
    TileDef("cloud", "云块", hp=40, drop="cloud", color=(240, 245, 255)),
    TileDef("tree", "树干", solid=False, hp=120, tool="axe", drop="wood", color=(110, 75, 40)),
    TileDef("leaves", "树叶", solid=False, hp=10, tool="any", color=(60, 150, 50)),
    TileDef("jungle_leaves", "丛林树叶", solid=False, hp=10, tool="any", color=(40, 175, 60)),
    TileDef("boreal_leaves", "针叶", solid=False, hp=10, tool="any", color=(60, 115, 95)),
    TileDef("cactus", "仙人掌", solid=False, hp=60, tool="axe", drop="cactus", color=(70, 150, 60)),
    TileDef("torch", "火把", solid=False, hp=1, tool="any", drop="torch", color=(255, 200, 80),
            light=(9, 1.0), support="side"),
    TileDef("mushroom", "蘑菇", solid=False, hp=1, tool="any", drop="mushroom", color=(220, 60, 60)),
    TileDef("water", "水", solid=False, hp=0, tool="none", liquid=True, color=(40, 100, 210)),
    TileDef("lava", "岩浆", solid=False, hp=0, tool="none", liquid=True, color=(240, 100, 20),
            light=(5, 0.9)),
    # multi-tile objects (anchor = top-left cell)
    TileDef("workbench", "工作台", solid=False, hp=30, tool="any", drop="workbench", color=(150, 100, 55),
            station=True, support="below", size=(2, 1)),
    TileDef("furnace", "熔炉", solid=False, hp=60, tool="any", drop="furnace", color=(115, 105, 105),
            station=True, support="below", size=(3, 2), light=(3, 0.5)),
    TileDef("anvil", "铁砧", solid=False, hp=60, tool="any", drop="anvil", color=(90, 90, 100),
            station=True, support="below", size=(2, 1)),
    TileDef("chest", "箱子", solid=False, hp=40, tool="any", drop="chest", color=(160, 110, 50),
            support="below", size=(2, 2), kind="container"),
    TileDef("bed", "床", solid=False, hp=30, tool="any", drop="bed", color=(170, 60, 60),
            support="below", size=(4, 2), kind="bed"),
    TileDef("door", "门", solid=False, hp=30, tool="any", drop="door", color=(140, 95, 50),
            support="frame", size=(1, 3), kind="door", blocks_creatures=True),
    TileDef("pot", "陶罐", solid=False, hp=1, tool="any", color=(150, 90, 60), support="below",
            size=(2, 2), kind="pot"),
    TileDef("life_crystal", "生命水晶", solid=False, hp=100, tool="pick", drop="life_crystal",
            color=(240, 80, 120), light=(3, 0.6), support="below", size=(2, 2)),
    TileDef("pylon", "传送晶塔", solid=False, hp=40, tool="any", drop="pylon", color=(90, 220, 230),
            light=(6, 0.8), support="below", size=(2, 3), kind="pylon"),
    TileDef("shipping_bin", "出货箱", solid=False, hp=40, tool="any", drop="shipping_bin",
            color=(150, 110, 70), support="below", size=(2, 2), kind="container"),
    TileDef("auto_smelter", "自动熔炉", solid=False, hp=60, tool="any", drop="auto_smelter",
            color=(150, 140, 140), support="below", size=(3, 2), kind="container", light=(4, 0.6)),
]

TILES = []
T = {}
for _i, _d in enumerate(_DEFS):
    _d.id = _i
    TILES.append(_d)
    T[_d.name] = _i

AIR = T["air"]
SOLID = [d.solid for d in TILES]
LIQUID = [d.liquid for d in TILES]
BLOCKS_CREATURES = [d.solid or d.blocks_creatures for d in TILES]
EMITS_LIGHT = [d.light is not None for d in TILES]
IS_OBJECT = [d.size != (1, 1) for d in TILES]
TREE_PARTS = {T["tree"], T["leaves"], T["jungle_leaves"], T["boreal_leaves"], T["cactus"]}
LEAF_TILES = {T["leaves"], T["jungle_leaves"], T["boreal_leaves"]}


@dataclass
class WallDef:
    name: str
    display: str
    tile: str          # tile whose texture (darkened) is used for the wall
    natural: bool = False
    id: int = 0


_WALL_DEFS = [
    WallDef("none", "无", "air"),
    WallDef("dirt_wall", "泥土墙", "dirt", natural=True),
    WallDef("stone_wall", "石墙", "stone", natural=True),
    WallDef("sand_wall", "沙墙", "sand", natural=True),
    WallDef("snow_wall", "雪墙", "snow", natural=True),
    WallDef("mud_wall", "泥浆墙", "mud", natural=True),
    WallDef("wood_wall", "木墙", "wood"),
    WallDef("stone_brick_wall", "石砖墙", "stone_brick"),
    WallDef("sandstone_brick_wall", "砂岩砖墙", "sandstone_brick"),
    WallDef("snow_brick_wall", "雪砖墙", "snow_brick"),
    WallDef("mud_brick_wall", "泥砖墙", "mud_brick"),
    WallDef("obsidian_brick_wall", "黑曜石砖墙", "obsidian_brick"),
]
WALLS = []
W = {}
for _i, _d in enumerate(_WALL_DEFS):
    _d.id = _i
    WALLS.append(_d)
    W[_d.name] = _i
NO_WALL = 0
WALL_HP = 40
