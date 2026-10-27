"""Item registry, crafting recipes, sell values and loot tables."""
from dataclasses import dataclass, field


@dataclass
class ItemDef:
    name: str
    display: str
    kind: str                     # block wall tool weapon ranged magic consumable material ammo
    #                               armor accessory bag summon mirror bucket coin
    icon: str                     # icon style used by textures.py
    color: tuple = (200, 200, 200)
    max_stack: int = 999
    place: str | None = None      # tile placed by this item
    wall: str | None = None       # wall placed by this item
    pick: int = 0
    axe: int = 0
    hammer: int = 0
    damage: int = 0
    use_time: int = 20            # frames per use
    knockback: float = 4.0
    reach: int = 40               # melee swing size in pixels
    heal: int = 0
    mana_cost: int = 0
    max_hp_up: int = 0
    max_mana_up: int = 0
    ammo: str | None = None
    proj: str | None = None
    proj_speed: float = 0.0
    slot: str | None = None       # head / body / legs / accessory
    defense: int = 0
    effects: dict = field(default_factory=dict)
    summon: str | None = None
    bag: str | None = None
    liquid: str | None = None     # bucket contents
    value: int | None = None      # sell price in coins (computed for crafted items when None)
    desc: str = ""


def _block(name, display, color, tile=None, **kw):
    return ItemDef(name, display, "block", "block", color, place=tile or name, use_time=6, **kw)


def _wall(name, display, color):
    return ItemDef(name, display, "wall", "wall", color, wall=name, use_time=5, value=0)


def _armor(name, display, slot, color, defense, **kw):
    icon = {"head": "helmet", "body": "chestplate", "legs": "greaves"}[slot]
    return ItemDef(name, display, "armor", icon, color, max_stack=1, slot=slot, defense=defense, **kw)


def _acc(name, display, icon, color, effects, desc, value):
    return ItemDef(name, display, "accessory", icon, color, max_stack=1, slot="accessory",
                   effects=effects, desc=desc, value=value)


_COPPER, _IRON, _GOLD, _MOLTEN = (205, 120, 60), (190, 190, 200), (245, 205, 70), (240, 90, 30)

_ITEMS = [
    # placeable blocks
    _block("dirt", "泥土块", (139, 96, 64), value=0),
    _block("stone", "石块", (125, 125, 130), value=0),
    _block("sand", "沙块", (219, 196, 130), value=0),
    _block("sandstone", "砂岩块", (196, 152, 96), value=0),
    _block("snow", "雪块", (236, 242, 250), value=0),
    _block("ice", "冰块", (160, 212, 240), value=0),
    _block("mud", "泥浆块", (92, 68, 70), value=0),
    _block("ash", "灰烬块", (78, 74, 80), value=0),
    _block("cloud", "云块", (240, 245, 255), value=1),
    _block("wood", "木材", (168, 116, 66), value=1),
    _block("copper_ore", "铜矿", (205, 120, 60), value=2),
    _block("iron_ore", "铁矿", (180, 155, 140), value=3),
    _block("gold_ore", "金矿", (235, 200, 60), value=6),
    _block("hellstone", "狱石", (190, 60, 30), value=8),
    _block("obsidian", "黑曜石", (55, 40, 80), value=3, desc="水与岩浆相遇时形成"),
    _block("stone_brick", "石砖", (140, 140, 150), value=1),
    _block("sandstone_brick", "砂岩砖", (210, 170, 110), value=1),
    _block("snow_brick", "雪砖", (215, 230, 245), value=1),
    _block("mud_brick", "泥砖", (120, 85, 80), value=1),
    _block("obsidian_brick", "黑曜石砖", (70, 50, 95), value=6),
    _block("torch", "火把", (255, 200, 80), desc="照亮周围；房屋需要光源"),
    _block("workbench", "工作台", (150, 100, 55), max_stack=99, desc="制作站"),
    _block("furnace", "熔炉", (115, 105, 105), max_stack=99, desc="右键打开：放入原料和燃料，慢慢烧炼"),
    _block("anvil", "铁砧", (90, 90, 100), max_stack=99, desc="锻造工具、武器与盔甲"),
    _block("chest", "箱子", (160, 110, 50), max_stack=99, desc="右键打开，可存放 20 组物品"),
    _block("bed", "床", (170, 60, 60), max_stack=99, desc="右键设为重生点；夜晚可睡觉跳过；NPC 住房必需"),
    _block("door", "门", (140, 95, 50), max_stack=99, desc="玩家可通过，怪物无法通过"),
    _block("pylon", "传送晶塔", (90, 220, 230), max_stack=99, value=40, desc="右键在晶塔之间传送"),
    _block("shipping_bin", "出货箱", (150, 110, 70), max_stack=99,
           desc="放入的物品会在第二天早上 6:00 自动售出"),
    # walls
    _wall("dirt_wall", "泥土墙", (100, 70, 48)),
    _wall("stone_wall", "石墙", (90, 90, 95)),
    _wall("sand_wall", "沙墙", (160, 140, 95)),
    _wall("snow_wall", "雪墙", (170, 180, 195)),
    _wall("mud_wall", "泥浆墙", (70, 52, 54)),
    _wall("wood_wall", "木墙", (120, 84, 48)),
    _wall("stone_brick_wall", "石砖墙", (100, 100, 110)),
    _wall("sandstone_brick_wall", "砂岩砖墙", (150, 120, 80)),
    _wall("snow_brick_wall", "雪砖墙", (155, 165, 180)),
    _wall("mud_brick_wall", "泥砖墙", (88, 62, 58)),
    _wall("obsidian_brick_wall", "黑曜石砖墙", (52, 38, 70)),
    # materials
    ItemDef("cactus", "仙人掌", "material", "cactus", (70, 150, 60), value=1),
    ItemDef("gel", "凝胶", "material", "gel", (80, 150, 255), value=1, desc="史莱姆掉落"),
    ItemDef("lens", "晶状体", "material", "lens", (240, 240, 240), value=5, desc="恶魔眼掉落"),
    ItemDef("bone", "骨头", "material", "bone", (230, 225, 200), value=2, desc="骷髅掉落"),
    ItemDef("copper_bar", "铜锭", "material", "bar", _COPPER, value=8, desc="熔炉烧炼铜矿得到"),
    ItemDef("iron_bar", "铁锭", "material", "bar", _IRON, value=12, desc="熔炉烧炼铁矿得到"),
    ItemDef("gold_bar", "金锭", "material", "bar", _GOLD, value=25, desc="熔炉烧炼金矿得到"),
    ItemDef("hellstone_bar", "狱石锭", "material", "bar", (230, 80, 30), value=30, desc="熔炉烧炼狱石得到"),
    ItemDef("coin", "金币", "coin", "coin", (250, 210, 60), max_stack=9999, value=1, desc="货币"),
    ItemDef("coal", "煤炭", "material", "coal", (40, 40, 46), value=1, desc="熔炉燃料，可烧炼 4 次"),
    ItemDef("lockpick", "撬锁器", "material", "lockpick", (190, 190, 200), max_stack=50, value=4,
            desc="右键上锁的藏宝金箱时使用，失败会折断"),
    ItemDef("treasure_map", "藏宝图", "map", "map", (220, 200, 150), max_stack=10, use_time=30, value=60,
            desc="使用后在地图上标出一处埋藏的宝藏"),
    ItemDef("card_pack", "卡包", "cardpack", "cardpack", (120, 80, 200), max_stack=20, use_time=20,
            value=30, desc="使用后获得 3 张随机牌（用于和 NPC 打牌）"),
    ItemDef("raw_meat", "生肉", "consumable", "meat", (200, 90, 90), max_stack=99, heal=5, use_time=30,
            value=2, desc="放进熔炉可以烤熟"),
    ItemDef("cooked_meat", "烤肉", "consumable", "meat", (170, 100, 50), max_stack=99, heal=30, use_time=30,
            value=8, desc="恢复 30 生命"),
    # consumables
    ItemDef("mushroom", "蘑菇", "consumable", "mushroom", (220, 60, 60), max_stack=99, heal=15,
            use_time=30, value=2, desc="恢复 15 生命"),
    ItemDef("healing_potion", "治疗药水", "consumable", "potion", (230, 40, 60), max_stack=30,
            heal=50, use_time=30, desc="恢复 50 生命"),
    ItemDef("life_crystal", "生命水晶", "consumable", "crystal", (240, 80, 120), max_stack=99,
            max_hp_up=20, use_time=30, value=30, desc="永久提升 20 生命上限（最高 200）"),
    ItemDef("mana_crystal", "魔力水晶", "consumable", "star", (90, 140, 255), max_stack=99,
            max_mana_up=20, use_time=30, value=25, desc="永久提升 20 魔力上限（最高 200）"),
    ItemDef("magic_mirror", "魔镜", "mirror", "mirror", (180, 220, 255), max_stack=1, use_time=60,
            value=100, desc="凝视镜子即可返回重生点"),
    ItemDef("eye_summon", "可疑眼球", "summon", "eye_summon", (220, 60, 60), max_stack=20, use_time=30,
            summon="eye", desc="夜晚使用，召唤血瞳巨眼"),
    ItemDef("slime_crown", "史莱姆王冠", "summon", "crown", (90, 150, 255), max_stack=20, use_time=30,
            summon="king_slime", desc="召唤史莱姆之王"),
    ItemDef("eye_bag", "宝藏袋（血瞳巨眼）", "bag", "bag", (200, 60, 70), max_stack=99, use_time=20,
            bag="eye", value=50, desc="左键打开"),
    ItemDef("slime_bag", "宝藏袋（史莱姆之王）", "bag", "bag", (80, 140, 240), max_stack=99,
            use_time=20, bag="king_slime", value=50, desc="左键打开"),
    ItemDef("bucket", "空桶", "bucket", "bucket", (170, 170, 180), max_stack=10, use_time=12,
            desc="舀起一格水或岩浆"),
    ItemDef("water_bucket", "水桶", "bucket", "bucket", (60, 120, 230), max_stack=1, use_time=12,
            liquid="water", desc="倒出一格水"),
    ItemDef("lava_bucket", "岩浆桶", "bucket", "bucket", (240, 100, 20), max_stack=1, use_time=12,
            liquid="lava", desc="倒出一格岩浆"),
    # tools
    ItemDef("copper_pickaxe", "铜镐", "tool", "pickaxe", _COPPER, max_stack=1, pick=35,
            damage=4, use_time=13, reach=34),
    ItemDef("iron_pickaxe", "铁镐", "tool", "pickaxe", _IRON, max_stack=1, pick=45,
            damage=5, use_time=12, reach=36),
    ItemDef("gold_pickaxe", "金镐", "tool", "pickaxe", _GOLD, max_stack=1, pick=55,
            damage=6, use_time=10, reach=38, desc="可以开采狱石与黑曜石"),
    ItemDef("molten_pickaxe", "熔岩镐", "tool", "pickaxe", _MOLTEN, max_stack=1, pick=70,
            damage=10, use_time=8, reach=42),
    ItemDef("copper_axe", "铜斧", "tool", "axe", _COPPER, max_stack=1, axe=35, damage=5,
            use_time=16, reach=34),
    ItemDef("iron_axe", "铁斧", "tool", "axe", _IRON, max_stack=1, axe=50, damage=7,
            use_time=14, reach=36),
    ItemDef("wooden_hammer", "木锤", "tool", "hammer", (168, 116, 66), max_stack=1, hammer=25,
            damage=4, use_time=18, reach=34, desc="敲掉背景墙"),
    ItemDef("iron_hammer", "铁锤", "tool", "hammer", _IRON, max_stack=1, hammer=45, damage=8,
            use_time=14, reach=38, desc="敲掉背景墙"),
    # melee
    ItemDef("copper_sword", "铜短剑", "weapon", "sword", _COPPER, max_stack=1, damage=9,
            use_time=18, reach=38),
    ItemDef("wooden_sword", "木剑", "weapon", "sword", (168, 116, 66), max_stack=1, damage=8,
            use_time=20, reach=40),
    ItemDef("iron_sword", "铁剑", "weapon", "sword", _IRON, max_stack=1, damage=13,
            use_time=18, reach=46),
    ItemDef("bone_sword", "骨剑", "weapon", "sword", (230, 225, 200), max_stack=1, damage=16,
            use_time=17, reach=48),
    ItemDef("gold_sword", "金剑", "weapon", "sword", _GOLD, max_stack=1, damage=18,
            use_time=17, reach=50),
    ItemDef("fiery_greatsword", "炽焰巨剑", "weapon", "sword", _MOLTEN, max_stack=1, damage=38,
            use_time=24, knockback=6.5, reach=64, desc="地狱之火凝成的巨剑"),
    # ranged / magic
    ItemDef("wooden_bow", "木弓", "ranged", "bow", (168, 116, 66), max_stack=1, damage=6, use_time=26,
            ammo="wood_arrow", proj="arrow", proj_speed=10.0, desc="消耗木箭"),
    ItemDef("wood_arrow", "木箭", "ammo", "arrow", (168, 116, 66), damage=5),
    ItemDef("magic_staff", "火花法杖", "magic", "staff", (255, 120, 40), max_stack=1, damage=20,
            use_time=22, mana_cost=6, proj="bolt", proj_speed=9.0, desc="消耗 6 魔力发射火球"),
    # armor
    _armor("mining_helmet", "矿工头盔", "head", (230, 200, 60), 1, effects={"light": 6}, value=60,
           desc="头灯照亮周围"),
    _armor("copper_helmet", "铜头盔", "head", _COPPER, 1),
    _armor("copper_chainmail", "铜锁甲", "body", _COPPER, 2),
    _armor("copper_greaves", "铜护胫", "legs", _COPPER, 1),
    _armor("iron_helmet", "铁头盔", "head", _IRON, 2),
    _armor("iron_chainmail", "铁锁甲", "body", _IRON, 3),
    _armor("iron_greaves", "铁护胫", "legs", _IRON, 2),
    _armor("gold_helmet", "金头盔", "head", _GOLD, 3),
    _armor("gold_chainmail", "金锁甲", "body", _GOLD, 4),
    _armor("gold_greaves", "金护胫", "legs", _GOLD, 3),
    _armor("molten_helmet", "熔岩头盔", "head", _MOLTEN, 6),
    _armor("molten_breastplate", "熔岩胸甲", "body", _MOLTEN, 8),
    _armor("molten_greaves", "熔岩护胫", "legs", _MOLTEN, 6),
    # accessories
    _acc("hermes_boots", "疾风靴", "boots", (90, 180, 230), {"speed": 0.35}, "移动速度 +35%", 120),
    _acc("cloud_bottle", "云中瓶", "bottle", (230, 240, 255), {"double_jump": 1}, "可以二段跳", 120),
    _acc("diving_mask", "潜水面罩", "mask", (80, 160, 200), {"breath": 3}, "水下呼吸时间 ×3", 80),
    _acc("obsidian_charm", "黑曜石护符", "charm", (90, 60, 130), {"lava_immune": 1}, "免疫岩浆与燃烧",
         None),
    _acc("regen_band", "再生手环", "band", (230, 80, 90), {"regen": 1}, "生命恢复速度加快", 100),
    _acc("magnet_ring", "磁力戒指", "ring", (200, 60, 60), {"magnet": 2.0}, "拾取范围 ×2", 80),
    _acc("lucky_charm", "幸运符", "horseshoe", (250, 210, 80), {"luck": 0.5}, "怪物掉落更多物品", 120),
    _acc("star_band", "星辰手环", "band", (110, 140, 255), {"mana": 20}, "魔力上限 +20", 100),
    _acc("eye_shield", "巨眼盾牌", "shield", (200, 60, 70), {"defense": 4, "kb_immune": 1},
         "防御 +4，免疫击退", 150),
    _acc("slime_boots", "弹力胶鞋", "boots", (80, 140, 240), {"fall_immune": 1, "jump": 0.15},
         "免疫跌落伤害，跳跃 +15%", 150),
    _acc("expedition_badge", "远征队徽章", "badge", (200, 170, 90), {"mining": 0.25},
         "挖掘速度 +25%。灰烬矿业远征队的遗物", 200),
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
    Recipe("torch", 4, {"wood": 1, "coal": 1}),
    Recipe("wooden_sword", 1, {"wood": 7}, "workbench"),
    Recipe("wooden_bow", 1, {"wood": 10}, "workbench"),
    Recipe("wooden_hammer", 1, {"wood": 8}, "workbench"),
    Recipe("wood_arrow", 10, {"wood": 1, "stone": 1}, "workbench"),
    Recipe("healing_potion", 1, {"mushroom": 2, "gel": 2}, "workbench"),
    Recipe("bone_sword", 1, {"bone": 25}, "workbench"),
    Recipe("door", 1, {"wood": 6}, "workbench"),
    Recipe("bed", 1, {"wood": 15}, "workbench"),
    Recipe("chest", 1, {"wood": 8, "iron_bar": 2}, "workbench"),
    Recipe("shipping_bin", 1, {"wood": 20, "iron_bar": 1}, "workbench"),
    Recipe("eye_summon", 1, {"lens": 6}, "workbench"),
    Recipe("slime_crown", 1, {"gel": 30, "gold_bar": 3}, "workbench"),
    Recipe("snow_brick", 1, {"snow": 2}, "workbench"),
    Recipe("furnace", 1, {"stone": 20, "wood": 4, "torch": 3}, "workbench"),
    Recipe("anvil", 1, {"iron_bar": 5}, "workbench"),
    Recipe("bucket", 1, {"iron_bar": 3}, "anvil"),
    Recipe("lockpick", 3, {"iron_bar": 1}, "anvil"),
    Recipe("copper_pickaxe", 1, {"copper_bar": 12, "wood": 4}, "anvil"),
    Recipe("iron_pickaxe", 1, {"iron_bar": 10, "wood": 3}, "anvil"),
    Recipe("iron_axe", 1, {"iron_bar": 9, "wood": 3}, "anvil"),
    Recipe("iron_hammer", 1, {"iron_bar": 8, "wood": 3}, "anvil"),
    Recipe("iron_sword", 1, {"iron_bar": 8}, "anvil"),
    Recipe("gold_pickaxe", 1, {"gold_bar": 12, "wood": 4}, "anvil"),
    Recipe("gold_sword", 1, {"gold_bar": 10}, "anvil"),
    Recipe("magic_staff", 1, {"gold_bar": 8, "lens": 2}, "anvil"),
    Recipe("molten_pickaxe", 1, {"hellstone_bar": 15}, "anvil"),
    Recipe("fiery_greatsword", 1, {"hellstone_bar": 20}, "anvil"),
    Recipe("obsidian_charm", 1, {"obsidian": 20, "hellstone_bar": 3}, "anvil"),
    Recipe("copper_helmet", 1, {"copper_bar": 10}, "anvil"),
    Recipe("copper_chainmail", 1, {"copper_bar": 15}, "anvil"),
    Recipe("copper_greaves", 1, {"copper_bar": 12}, "anvil"),
    Recipe("iron_helmet", 1, {"iron_bar": 12}, "anvil"),
    Recipe("iron_chainmail", 1, {"iron_bar": 18}, "anvil"),
    Recipe("iron_greaves", 1, {"iron_bar": 15}, "anvil"),
    Recipe("gold_helmet", 1, {"gold_bar": 15}, "anvil"),
    Recipe("gold_chainmail", 1, {"gold_bar": 22}, "anvil"),
    Recipe("gold_greaves", 1, {"gold_bar": 18}, "anvil"),
    Recipe("molten_helmet", 1, {"hellstone_bar": 10}, "anvil"),
    Recipe("molten_breastplate", 1, {"hellstone_bar": 15}, "anvil"),
    Recipe("molten_greaves", 1, {"hellstone_bar": 12}, "anvil"),
]
for _base in ("dirt", "stone", "sand", "snow", "mud", "wood", "stone_brick", "sandstone_brick",
              "snow_brick", "mud_brick", "obsidian_brick"):
    RECIPES.append(Recipe(_base + "_wall", 4, {_base: 1}, "workbench"))

STATION_NAMES = {"workbench": "工作台", "anvil": "铁砧"}

STARTING_ITEMS = [("copper_pickaxe", 1), ("copper_axe", 1), ("copper_sword", 1), ("torch", 15),
                  ("wooden_hammer", 1)]

# furnace smelting: input -> (amount consumed, output, frames per batch)
SMELTING = {
    "copper_ore": (3, "copper_bar", 150),
    "iron_ore": (3, "iron_bar", 180),
    "gold_ore": (4, "gold_bar", 210),
    "hellstone": (3, "hellstone_bar", 300),
    "stone": (2, "stone_brick", 90),
    "sandstone": (2, "sandstone_brick", 90),
    "mud": (2, "mud_brick", 90),
    "obsidian": (2, "obsidian_brick", 150),
    "raw_meat": (1, "cooked_meat", 120),
}
# fuel item -> number of batches it burns for
FUEL = {"wood": 1, "coal": 4, "cactus": 1}


def _compute_values():
    """Crafted items without an explicit price sell for slightly more than their ingredients."""
    explicit = {name for name, it in ITEMS.items() if it.value is not None}
    for _ in range(6):
        for r in RECIPES:
            if r.result in explicit:
                continue
            total = sum((ITEMS[n].value or 0) * c for n, c in r.ingredients.items())
            ITEMS[r.result].value = max(1, int(total * 1.2 / r.count))
    for it in ITEMS.values():
        if it.value is None:
            it.value = 10


_compute_values()


# ----------------------------------------------------------------------
# loot tables: list of (item, min, max, chance)
# ----------------------------------------------------------------------

LOOT = {
    "surface_cabin": [("coin", 10, 30, 1.0), ("healing_potion", 1, 3, 0.7), ("torch", 5, 15, 0.8),
                      ("wood_arrow", 20, 40, 0.5), ("card_pack", 1, 1, 0.4)],
    "underground_cabin": [("coin", 20, 60, 1.0), ("healing_potion", 2, 4, 0.8), ("iron_bar", 4, 10, 0.5),
                          ("gold_bar", 3, 6, 0.3), ("mana_crystal", 1, 1, 0.2), ("lockpick", 2, 4, 0.4)],
    "mineshaft": [("coin", 15, 40, 1.0), ("coal", 10, 25, 0.8), ("iron_ore", 10, 20, 0.6),
                  ("gold_ore", 8, 20, 0.4), ("torch", 10, 25, 1.0), ("treasure_map", 1, 1, 0.15)],
    "miner_camp": [("coin", 20, 50, 1.0), ("coal", 15, 30, 0.8), ("cooked_meat", 2, 5, 0.6),
                   ("lockpick", 2, 5, 0.6), ("treasure_map", 1, 1, 0.3)],
    "watchtower": [("coin", 30, 70, 1.0), ("wood_arrow", 30, 60, 0.8), ("treasure_map", 1, 1, 0.4),
                   ("card_pack", 1, 2, 0.5)],
    "temple": [("coin", 150, 300, 1.0), ("gold_bar", 10, 20, 0.8), ("life_crystal", 1, 2, 0.6),
               ("card_pack", 1, 3, 0.8)],
    "pyramid": [("coin", 80, 150, 1.0), ("gold_bar", 8, 15, 0.8), ("healing_potion", 3, 5, 1.0)],
    "igloo": [("coin", 20, 50, 1.0), ("ice", 20, 40, 0.5), ("healing_potion", 2, 3, 0.8)],
    "jungle_ruins": [("coin", 30, 80, 1.0), ("mud_brick", 20, 40, 0.5), ("life_crystal", 1, 1, 0.4),
                     ("card_pack", 1, 1, 0.5)],
    "shipwreck": [("coin", 40, 90, 1.0), ("healing_potion", 2, 4, 0.8), ("treasure_map", 1, 1, 0.6)],
    "sky_island": [("coin", 60, 120, 1.0), ("cloud", 20, 50, 0.8), ("mana_crystal", 1, 1, 0.5)],
    "hell_tower": [("coin", 100, 200, 1.0), ("hellstone_bar", 5, 12, 0.8), ("obsidian", 10, 25, 0.6),
                   ("healing_potion", 3, 6, 1.0)],
    "treasure": [("coin", 150, 400, 1.0), ("gold_bar", 5, 12, 0.7), ("card_pack", 1, 2, 0.8),
                 ("life_crystal", 1, 1, 0.3)],
}
# one guaranteed special item per structure chest
SPECIAL_LOOT = {
    "surface_cabin": ["wooden_bow", "magnet_ring", "mining_helmet"],
    "underground_cabin": ["hermes_boots", "cloud_bottle", "regen_band", "magic_mirror"],
    "mineshaft": ["mining_helmet", "iron_hammer", "bucket"],
    "miner_camp": ["mining_helmet", "iron_hammer", "lucky_charm"],
    "watchtower": ["wooden_bow", "magnet_ring", "hermes_boots"],
    "temple": ["star_band", "lucky_charm", "magic_staff", "cloud_bottle"],
    "pyramid": ["magic_mirror", "star_band", "hermes_boots"],
    "igloo": ["hermes_boots", "regen_band"],
    "jungle_ruins": ["star_band", "regen_band"],
    "shipwreck": ["diving_mask"],
    "sky_island": ["cloud_bottle", "lucky_charm"],
    "hell_tower": ["lucky_charm", "fiery_greatsword", "obsidian_charm"],
    "treasure": ["hermes_boots", "cloud_bottle", "regen_band", "star_band", "lucky_charm", "magnet_ring"],
}
# "card:<name>" entries add a card to the player's collection instead of an item
BAG_LOOT = {
    "eye": [("coin", 150, 250, 1.0), ("healing_potion", 3, 5, 1.0), ("gold_ore", 20, 40, 1.0),
            ("eye_shield", 1, 1, 1.0), ("lens", 3, 6, 1.0), ("card:血瞳巨眼", 1, 1, 1.0)],
    "king_slime": [("coin", 100, 200, 1.0), ("gel", 30, 60, 1.0), ("slime_boots", 1, 1, 1.0),
                   ("healing_potion", 2, 4, 1.0), ("card:史莱姆之王", 1, 1, 1.0)],
}
