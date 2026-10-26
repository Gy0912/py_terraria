"""Tile registry: every block type in the world, indexed by a small integer id."""
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
    light: tuple | None = None    # (radius_tiles, intensity 0..1)
    liquid: bool = False
    color: tuple = (128, 128, 128)
    station: bool = False
    support: str | None = None    # "below" or "side": what a placed tile needs next to it
    id: int = 0


_DEFS = [
    TileDef("air", "空气", solid=False, hp=0, tool="none", color=(0, 0, 0)),
    TileDef("dirt", "泥土", hp=75, drop="dirt", color=(139, 96, 64)),
    TileDef("grass", "草地", hp=75, drop="dirt", color=(76, 160, 60)),
    TileDef("stone", "石块", hp=140, drop="stone", color=(125, 125, 130)),
    TileDef("sand", "沙子", hp=60, drop="sand", color=(219, 196, 130)),
    TileDef("sandstone", "砂岩", hp=130, drop="sandstone", color=(196, 152, 96)),
    TileDef("snow", "雪块", hp=60, drop="snow", color=(236, 242, 250)),
    TileDef("ice", "冰块", hp=110, drop="ice", color=(160, 212, 240)),
    TileDef("mud", "泥浆", hp=75, drop="mud", color=(92, 68, 70)),
    TileDef("jungle_grass", "丛林草", hp=75, drop="mud", color=(110, 200, 40)),
    TileDef("ash", "灰烬", hp=100, drop="ash", color=(78, 74, 80)),
    TileDef("copper_ore", "铜矿", hp=170, drop="copper_ore", color=(205, 120, 60)),
    TileDef("iron_ore", "铁矿", hp=210, drop="iron_ore", color=(180, 155, 140)),
    TileDef("gold_ore", "金矿", hp=260, min_power=35, drop="gold_ore", color=(235, 200, 60)),
    TileDef("hellstone", "狱石", hp=380, min_power=55, drop="hellstone", color=(190, 60, 30),
            light=(3, 0.55)),
    TileDef("wood", "木材", hp=100, drop="wood", color=(168, 116, 66)),
    TileDef("tree", "树干", solid=False, hp=140, tool="axe", drop="wood", color=(110, 75, 40)),
    TileDef("leaves", "树叶", solid=False, hp=10, tool="any", color=(60, 150, 50)),
    TileDef("jungle_leaves", "丛林树叶", solid=False, hp=10, tool="any", color=(40, 175, 60)),
    TileDef("boreal_leaves", "针叶", solid=False, hp=10, tool="any", color=(60, 115, 95)),
    TileDef("cactus", "仙人掌", solid=False, hp=60, tool="axe", drop="cactus", color=(70, 150, 60)),
    TileDef("torch", "火把", solid=False, hp=1, tool="any", drop="torch", color=(255, 200, 80),
            light=(9, 1.0), support="side"),
    TileDef("workbench", "工作台", solid=False, hp=30, tool="any", drop="workbench",
            color=(150, 100, 55), station=True, support="below"),
    TileDef("furnace", "熔炉", solid=False, hp=60, tool="any", drop="furnace", color=(115, 105, 105),
            station=True, support="below", light=(3, 0.5)),
    TileDef("anvil", "铁砧", solid=False, hp=60, tool="any", drop="anvil", color=(90, 90, 100),
            station=True, support="below"),
    TileDef("mushroom", "蘑菇", solid=False, hp=1, tool="any", drop="mushroom", color=(220, 60, 60)),
    TileDef("life_crystal", "生命水晶", solid=False, hp=120, tool="pick", drop="life_crystal",
            color=(240, 80, 120), light=(3, 0.6)),
    TileDef("pot", "陶罐", solid=False, hp=1, tool="any", color=(150, 90, 60)),
    TileDef("water", "水", solid=False, hp=0, tool="none", liquid=True, color=(40, 100, 210)),
    TileDef("lava", "岩浆", solid=False, hp=0, tool="none", liquid=True, color=(240, 100, 20),
            light=(5, 0.9)),
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
EMITS_LIGHT = [d.light is not None for d in TILES]
TREE_PARTS = {T["tree"], T["leaves"], T["jungle_leaves"], T["boreal_leaves"], T["cactus"]}
