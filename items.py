"""Item registry and crafting recipes."""
from dataclasses import dataclass, field


@dataclass
class ItemDef:
    name: str
    display: str
    kind: str                     # block, tool, weapon, ranged, magic, consumable, material, ammo
    icon: str                     # icon style used by textures.py
    color: tuple = (200, 200, 200)
    max_stack: int = 999
    place: str | None = None      # tile placed by this item
    pick: int = 0
    axe: int = 0
    damage: int = 0
    use_time: int = 20            # frames per use
    knockback: float = 4.0
    reach: int = 40               # melee swing size in pixels
    heal: int = 0
    mana_cost: int = 0
    max_hp_up: int = 0
    ammo: str | None = None
    proj: str | None = None       # projectile kind
    proj_speed: float = 0.0
    desc: str = ""


def _block(name, display, color, tile=None, **kw):
    return ItemDef(name, display, "block", "block", color, place=tile or name, use_time=8, **kw)


_ITEMS = [
    # placeable blocks
    _block("dirt", "泥土块", (139, 96, 64)),
    _block("stone", "石块", (125, 125, 130)),
    _block("sand", "沙块", (219, 196, 130)),
    _block("sandstone", "砂岩块", (196, 152, 96)),
    _block("snow", "雪块", (236, 242, 250)),
    _block("ice", "冰块", (160, 212, 240)),
    _block("mud", "泥浆块", (92, 68, 70)),
    _block("ash", "灰烬块", (78, 74, 80)),
    _block("wood", "木材", (168, 116, 66)),
    _block("copper_ore", "铜矿", (205, 120, 60)),
    _block("iron_ore", "铁矿", (180, 155, 140)),
    _block("gold_ore", "金矿", (235, 200, 60)),
    _block("hellstone", "狱石", (190, 60, 30)),
    _block("torch", "火把", (255, 200, 80), desc="照亮周围"),
    _block("workbench", "工作台", (150, 100, 55), max_stack=99, desc="制作站"),
    _block("furnace", "熔炉", (115, 105, 105), max_stack=99, desc="冶炼矿石"),
    _block("anvil", "铁砧", (90, 90, 100), max_stack=99, desc="锻造工具与武器"),
    # materials
    ItemDef("cactus", "仙人掌", "material", "cactus", (70, 150, 60)),
    ItemDef("gel", "凝胶", "material", "gel", (80, 150, 255), desc="史莱姆掉落"),
    ItemDef("lens", "晶状体", "material", "lens", (240, 240, 240), desc="恶魔眼掉落"),
    ItemDef("bone", "骨头", "material", "bone", (230, 225, 200), desc="骷髅掉落"),
    ItemDef("copper_bar", "铜锭", "material", "bar", (215, 125, 65)),
    ItemDef("iron_bar", "铁锭", "material", "bar", (190, 190, 200)),
    ItemDef("gold_bar", "金锭", "material", "bar", (245, 205, 70)),
    ItemDef("hellstone_bar", "狱石锭", "material", "bar", (230, 80, 30)),
    # consumables
    ItemDef("mushroom", "蘑菇", "consumable", "mushroom", (220, 60, 60), max_stack=99, heal=15,
            use_time=30, desc="恢复 15 生命"),
    ItemDef("healing_potion", "治疗药水", "consumable", "potion", (230, 40, 60), max_stack=30,
            heal=50, use_time=30, desc="恢复 50 生命"),
    ItemDef("life_crystal", "生命水晶", "consumable", "crystal", (240, 80, 120), max_stack=99,
            max_hp_up=20, use_time=30, desc="永久提升 20 生命上限（最高 200）"),
    # tools
    ItemDef("copper_pickaxe", "铜镐", "tool", "pickaxe", (205, 120, 60), max_stack=1, pick=35,
            damage=4, use_time=15, reach=34),
    ItemDef("iron_pickaxe", "铁镐", "tool", "pickaxe", (190, 190, 200), max_stack=1, pick=45,
            damage=5, use_time=13, reach=36),
    ItemDef("gold_pickaxe", "金镐", "tool", "pickaxe", (245, 205, 70), max_stack=1, pick=55,
            damage=6, use_time=11, reach=38, desc="可以开采狱石"),
    ItemDef("molten_pickaxe", "熔岩镐", "tool", "pickaxe", (240, 90, 30), max_stack=1, pick=70,
            damage=10, use_time=9, reach=42),
    ItemDef("copper_axe", "铜斧", "tool", "axe", (205, 120, 60), max_stack=1, axe=35, damage=5,
            use_time=18, reach=34),
    ItemDef("iron_axe", "铁斧", "tool", "axe", (190, 190, 200), max_stack=1, axe=50, damage=7,
            use_time=15, reach=36),
    # melee
    ItemDef("copper_sword", "铜短剑", "weapon", "sword", (205, 120, 60), max_stack=1, damage=9,
            use_time=18, reach=38),
    ItemDef("wooden_sword", "木剑", "weapon", "sword", (168, 116, 66), max_stack=1, damage=8,
            use_time=20, reach=40),
    ItemDef("iron_sword", "铁剑", "weapon", "sword", (190, 190, 200), max_stack=1, damage=13,
            use_time=18, reach=46),
    ItemDef("bone_sword", "骨剑", "weapon", "sword", (230, 225, 200), max_stack=1, damage=16,
            use_time=17, reach=48),
    ItemDef("gold_sword", "金剑", "weapon", "sword", (245, 205, 70), max_stack=1, damage=18,
            use_time=17, reach=50),
    ItemDef("fiery_greatsword", "炽焰巨剑", "weapon", "sword", (240, 90, 30), max_stack=1, damage=38,
            use_time=24, knockback=6.5, reach=64, desc="地狱之火凝成的巨剑"),
    # ranged / magic
    ItemDef("wooden_bow", "木弓", "ranged", "bow", (168, 116, 66), max_stack=1, damage=6, use_time=26,
            ammo="wood_arrow", proj="arrow", proj_speed=10.0, desc="消耗木箭"),
    ItemDef("wood_arrow", "木箭", "ammo", "arrow", (168, 116, 66), damage=5),
    ItemDef("magic_staff", "火花法杖", "magic", "staff", (255, 120, 40), max_stack=1, damage=20,
            use_time=22, mana_cost=6, proj="bolt", proj_speed=9.0, desc="消耗 6 魔力发射火球"),
]

ITEMS = {it.name: it for it in _ITEMS}


@dataclass
class Recipe:
    result: str
    count: int
    ingredients: dict = field(default_factory=dict)
    station: str | None = None


RECIPES = [
    Recipe("workbench", 1, {"wood": 10}),
    Recipe("torch", 3, {"wood": 1, "gel": 1}),
    Recipe("wooden_sword", 1, {"wood": 7}, "workbench"),
    Recipe("wooden_bow", 1, {"wood": 10}, "workbench"),
    Recipe("wood_arrow", 10, {"wood": 1, "stone": 1}, "workbench"),
    Recipe("healing_potion", 1, {"mushroom": 2, "gel": 2}, "workbench"),
    Recipe("bone_sword", 1, {"bone": 25}, "workbench"),
    Recipe("furnace", 1, {"stone": 20, "wood": 4, "torch": 3}, "workbench"),
    Recipe("anvil", 1, {"iron_bar": 5}, "workbench"),
    Recipe("copper_bar", 1, {"copper_ore": 3}, "furnace"),
    Recipe("iron_bar", 1, {"iron_ore": 3}, "furnace"),
    Recipe("gold_bar", 1, {"gold_ore": 4}, "furnace"),
    Recipe("hellstone_bar", 1, {"hellstone": 3}, "furnace"),
    Recipe("copper_pickaxe", 1, {"copper_bar": 12, "wood": 4}, "anvil"),
    Recipe("iron_pickaxe", 1, {"iron_bar": 10, "wood": 3}, "anvil"),
    Recipe("iron_axe", 1, {"iron_bar": 9, "wood": 3}, "anvil"),
    Recipe("iron_sword", 1, {"iron_bar": 8}, "anvil"),
    Recipe("gold_pickaxe", 1, {"gold_bar": 12, "wood": 4}, "anvil"),
    Recipe("gold_sword", 1, {"gold_bar": 10}, "anvil"),
    Recipe("magic_staff", 1, {"gold_bar": 8, "lens": 2}, "anvil"),
    Recipe("molten_pickaxe", 1, {"hellstone_bar": 15}, "anvil"),
    Recipe("fiery_greatsword", 1, {"hellstone_bar": 20}, "anvil"),
]

STATION_NAMES = {"workbench": "工作台", "furnace": "熔炉", "anvil": "铁砧"}

STARTING_ITEMS = [("copper_pickaxe", 1), ("copper_axe", 1), ("copper_sword", 1), ("torch", 10)]
