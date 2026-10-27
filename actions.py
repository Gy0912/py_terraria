"""Player item use: mining, chopping, hammering walls, placing tiles / objects / walls,
melee swings, shooting, consumables, buckets, bags, summons and right-click interaction."""
import math
import random

import pygame

from settings import *
from tiles import TILES, T, W, AIR, SOLID, LIQUID, IS_OBJECT, WALLS, WALL_HP
from items import ITEMS
from entities import Projectile
from bosses import open_bag

TS = TILE_SIZE
_TREE, _CACTUS = T["tree"], T["cactus"]
_CROP = {T["crop_0"], T["crop_1"], T["crop_2"]}
_SOIL = {T["dirt"], T["mud"], T["grass"], T["jungle_grass"]}
_TORCH, _MUSHROOM = T["torch"], T["mushroom"]
_NOTE = T["lore_note"]
_WATER, _LAVA = T["water"], T["lava"]
POT_LOOT = [("torch", 3, 8, 4), ("healing_potion", 1, 1, 2), ("wood_arrow", 8, 20, 3), ("gel", 1, 4, 2),
            ("mushroom", 1, 2, 2), ("coin", 2, 12, 5)]
HEAL_COOLDOWN = FPS * 10


def mouse_world(game):
    mx, my = pygame.mouse.get_pos()
    return mx + game.camera.x, my + game.camera.y


def mouse_tile(game):
    wx, wy = mouse_world(game)
    return int(wx) // TS, int(wy) // TS


def in_reach(player, tx, ty):
    cx, cy = player.center()
    return (abs((tx + 0.5) * TS - cx) <= PLAYER_REACH * TS
            and abs((ty + 0.5) * TS - cy) <= (PLAYER_REACH - 1) * TS)


def _start(player, item, frames):
    player.use_item = item.name
    player.use_timer = player.use_total = max(1, frames)
    player.swing_hits = set()


def try_use(game):
    p = game.player
    if not p.alive or p.use_timer > 0:
        return
    idx = game.inv_ui.selected
    stack = p.inventory.slots[idx]
    if not stack:
        return
    it = ITEMS[stack[0]]
    wx, wy = mouse_world(game)
    cx, cy = p.center()
    p.facing = 1 if wx >= cx else -1
    p.aim_angle = math.atan2(wy - cy, wx - cx)
    tx, ty = int(wx) // TS, int(wy) // TS
    kind = it.kind

    if kind == "seed":
        if plant(game, tx, ty):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "block":
        if place_tile(game, it, tx, ty):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "wall":
        if place_wall(game, it, tx, ty):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "consumable":
        if consume(game, it):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "bag":
        p.inventory.consume_slot(idx)
        open_bag(game, it.bag)
        _start(p, it, it.use_time)
    elif kind == "cardpack":
        p.inventory.consume_slot(idx)
        game.open_card_pack()
        _start(p, it, it.use_time)
    elif kind == "map":
        if game.start_treasure_hunt():
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "summon":
        if use_summon(game, it):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif kind == "mirror":
        _start(p, it, it.use_time)
        game.burst(*p.center(), (180, 220, 255), 20, speed=3)
        p.teleport(*p.spawn_tile())
        game.burst(*p.center(), (180, 220, 255), 20, speed=3)
    elif kind == "bucket":
        if use_bucket(game, it, idx, tx, ty):
            _start(p, it, it.use_time)
    elif kind == "ranged":
        if p.inventory.remove(it.ammo, 1):
            _shoot(game, "arrow", it.damage + ITEMS[it.ammo].damage, it.knockback, it.proj_speed)
            _start(p, it, it.use_time)
        else:
            game.notify(f"没有{ITEMS[it.ammo].display}了")
    elif kind == "magic":
        if p.mana >= it.mana_cost:
            p.mana -= it.mana_cost
            _shoot(game, "bolt", it.damage, it.knockback, it.proj_speed)
            _start(p, it, it.use_time)
        else:
            game.notify("魔力不足")
    elif kind in ("tool", "weapon"):
        _start(p, it, it.use_time)
        if kind == "tool" and in_reach(p, tx, ty):
            if it.hammer:
                hit_wall(game, it, tx, ty)
            else:
                hit_tile(game, it, tx, ty)


def _shoot(game, kind, damage, knockback, speed):
    p = game.player
    cx, cy = p.center()
    a = p.aim_angle
    game.projectiles.append(Projectile(kind, cx + math.cos(a) * 14, cy - 6 + math.sin(a) * 14,
                                       math.cos(a) * speed, math.sin(a) * speed, damage, knockback))


# ----------------------------------------------------------------------
# swings
# ----------------------------------------------------------------------

def swing_hitbox(p, it):
    cx, cy = p.center()
    r = it.reach
    if p.facing > 0:
        return pygame.Rect(cx - 6, cy - r - 4, r + 14, r * 2)
    return pygame.Rect(cx - r - 8, cy - r - 4, r + 14, r * 2)


def update_use(game):
    p = game.player
    if p.use_timer <= 0:
        return
    p.use_timer -= 1
    it = ITEMS[p.use_item]
    if it.kind in ("tool", "weapon") and it.damage > 0:
        box = swing_hitbox(p, it)
        for c in game.creatures.creatures:
            if id(c) in p.swing_hits or not c.alive:
                continue
            if box.colliderect(c.rect()):
                p.swing_hits.add(id(c))
                game.on_creature_hit(c, c.hit(it.damage, p.center()[0], it.knockback, attacker=p))
    if p.use_timer == 0:
        p.use_item = None


# ----------------------------------------------------------------------
# mining
# ----------------------------------------------------------------------

def hit_tile(game, it, tx, ty):
    world = game.world
    tid = world.get_tile(tx, ty)
    if tid == AIR or LIQUID[tid]:
        return
    td = TILES[tid]
    if td.tool == "axe":
        power = it.axe
    elif td.tool == "pick":
        power = it.pick
        if power and power < td.min_power:
            game.notify(f"需要更强的镐（{td.display} 需要 {td.min_power}% 镐力）")
            return
    elif td.tool == "any":
        power = max(it.pick, it.axe, 1)
    else:
        return
    if not power:
        if td.tool == "axe":
            game.notify("需要用斧头砍伐")
        return
    anchor = world.object_at(tx, ty) if IS_OBJECT[tid] else None
    if anchor in world.locked:
        game.notify("上锁的金箱无法破坏，右键用撬锁器打开")
        return
    key = anchor or (tx, ty)
    dmg = world.damage_tile(*key, int(power * (1 + game.player.stats["mining"])))
    game.burst((tx + 0.5) * TS, (ty + 0.5) * TS, td.color, 3, speed=1.8)
    if dmg >= td.hp:
        if anchor:
            break_object(game, anchor)
        else:
            break_tile(game, tx, ty)


def break_tile(game, tx, ty):
    world = game.world
    tid = world.get_tile(tx, ty)
    if IS_OBJECT[tid]:
        anchor = world.object_at(tx, ty)
        if anchor:
            break_object(game, anchor)
        else:
            world.set_tile(tx, ty, AIR)
        return
    td = TILES[tid]
    px, py = (tx + 0.5) * TS, (ty + 0.5) * TS
    if tid in (_TREE, _CACTUS):
        n = world.remove_tree(tx, ty)
        game.drop_item_at(td.drop, n, px, py)
        game.burst(px, py - TS * 4, (60, 150, 50), 16, speed=3.0)
    elif tid in _CROP:
        world.set_tile(tx, ty, AIR)
        if tid == T["crop_2"]:
            game.drop_item_at("wheat", 2, px, py)
            game.drop_item_at("seeds", 1, px, py)
        else:
            game.drop_item_at("seeds", 1, px, py)
    else:
        world.set_tile(tx, ty, AIR)
        if td.drop:
            game.drop_item_at(td.drop, 1, px, py)
    game.burst(px, py, td.color, 8, speed=2.5)
    _check_support(game, tx, ty)


def break_object(game, anchor):
    world = game.world
    tid, contents = world.remove_object(anchor)
    if tid is None:
        return
    td = TILES[tid]
    w, h = td.size
    px, py = (anchor[0] + w / 2) * TS, (anchor[1] + h / 2) * TS
    if td.kind == "pot":
        for _ in range(random.randint(1, 3)):
            name, lo, hi, _ = random.choices(POT_LOOT, [e[3] for e in POT_LOOT])[0]
            game.drop_item_at(name, random.randint(lo, hi), px, py)
    elif td.drop:
        game.drop_item_at(td.drop, 1, px, py)
    for stack in contents or ():
        if stack:
            game.drop_item_at(stack[0], stack[1], px, py)
    if game.inv_ui.container and game.inv_ui.container[0] == anchor:
        game.inv_ui.close(game)
    game.burst(px, py, td.color, 12, speed=3.0)
    for x in range(anchor[0], anchor[0] + w):
        _check_support(game, x, anchor[1] + h - 1)


def _check_support(game, tx, ty):
    """Break things that rested on or hung from the removed cell (tx, ty)."""
    world = game.world
    above = world.get_tile(tx, ty - 1)
    if above in (_TREE, _CACTUS, _MUSHROOM):
        break_tile(game, tx, ty - 1)
    for x, y in ((tx, ty - 1), (tx, ty + 1)):
        anchor = world.object_at(x, y)
        if not anchor:
            continue
        td = TILES[world.objects[anchor]]
        w, h = td.size
        bottom, top = anchor[1] + h - 1, anchor[1]
        if (td.support == "below" and y == bottom == ty - 1) or \
                (td.support == "frame" and (y == bottom == ty - 1 or y == top == ty + 1)):
            break_object(game, anchor)
    for nx, ny in ((tx - 1, ty), (tx + 1, ty), (tx, ty - 1)):
        if world.get_tile(nx, ny) == _TORCH and not _torch_supported(world, nx, ny):
            break_tile(game, nx, ny)


def _torch_supported(world, x, y):
    return (world.is_solid(x - 1, y) or world.is_solid(x + 1, y) or world.is_solid(x, y + 1)
            or world.get_wall(x, y) != 0)


def hit_wall(game, it, tx, ty):
    world = game.world
    wid = world.get_wall(tx, ty)
    if not wid:
        return
    if world.is_solid(tx, ty):
        game.notify("先挖掉前面的方块")
        return
    dmg = world.damage_tile(tx, ty, it.hammer, walls=True)
    color = TILES[T[WALLS[wid].tile]].color
    game.burst((tx + 0.5) * TS, (ty + 0.5) * TS, color, 3, speed=1.5)
    if dmg >= WALL_HP:
        world.set_wall(tx, ty, 0)
        game.drop_item_at(WALLS[wid].name, 1, (tx + 0.5) * TS, (ty + 0.5) * TS)
        if world.get_tile(tx, ty) == _TORCH and not _torch_supported(world, tx, ty):
            break_tile(game, tx, ty)


# ----------------------------------------------------------------------
# placing
# ----------------------------------------------------------------------

def plant(game, tx, ty):
    world = game.world
    if not in_reach(game.player, tx, ty) or world.get_tile(tx, ty) != AIR:
        return False
    if world.get_tile(tx, ty + 1) not in _SOIL:
        game.notify("麦种需要种在泥土或泥浆上")
        return False
    world.set_tile(tx, ty, T["crop_0"])
    return True


def place_tile(game, it, tx, ty):
    world = game.world
    p = game.player
    if not in_reach(p, tx, ty) or not (0 <= tx < WORLD_W and 0 <= ty < WORLD_H):
        return False
    tid = T[it.place]
    td = TILES[tid]
    if td.size != (1, 1):
        return place_object(game, tid, tx, ty)
    cur = world.get_tile(tx, ty)
    if cur != AIR and not LIQUID[cur]:
        return False
    if td.solid:
        r = pygame.Rect(tx * TS, ty * TS, TS, TS)
        if r.colliderect(p.rect()) or any(r.colliderect(c.rect()) for c in game.creatures.creatures):
            return False
    if td.support == "side":
        if not _torch_supported(world, tx, ty):
            return False
    else:
        neighbours = [world.get_tile(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if all(n == AIR or LIQUID[n] for n in neighbours) and not world.get_wall(tx, ty):
            return False
    world.set_tile(tx, ty, tid)
    return True


def place_object(game, tid, tx, ty):
    """Place a multi-tile object with the mouse at its bottom-middle cell."""
    world = game.world
    w, h = TILES[tid].size
    ax, ay = tx - (w - 1) // 2, ty - (h - 1)
    for dx in range(w):
        for dy in range(h):
            t = world.get_tile(ax + dx, ay + dy)
            if t != AIR and not LIQUID[t]:
                return False
    support = TILES[tid].support
    if support == "below" and not all(world.is_solid(ax + dx, ay + h) for dx in range(w)):
        game.notify(f"{TILES[tid].display} 需要放在平整的地面上")
        return False
    if support == "frame" and not (world.is_solid(ax, ay - 1) and world.is_solid(ax, ay + h)):
        game.notify("门需要上下都有方块")
        return False
    world.place_object(tid, ax, ay)
    return True


def place_wall(game, it, tx, ty):
    world = game.world
    if not in_reach(game.player, tx, ty) or world.get_wall(tx, ty):
        return False
    near = [(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    if not any(world.get_wall(x, y) or world.is_solid(x, y) for x, y in near) and not world.is_solid(tx, ty):
        return False
    world.set_wall(tx, ty, W[it.wall])
    return True


def use_bucket(game, it, idx, tx, ty):
    world = game.world
    p = game.player
    if not in_reach(p, tx, ty):
        return False
    if it.liquid is None:
        t = world.get_tile(tx, ty)
        if t not in (_WATER, _LAVA) or world.liquid_level(tx, ty) < 4:
            return False
        world.set_tile(tx, ty, AIR)
        p.inventory.consume_slot(idx)
        filled = "water_bucket" if t == _WATER else "lava_bucket"
        if p.inventory.add(filled, 1):
            game.drop_item(filled, 1)
        return True
    if world.get_tile(tx, ty) != AIR:
        return False
    world.place_liquid(tx, ty, _WATER if it.liquid == "water" else _LAVA)
    p.inventory.slots[idx] = ["bucket", 1]
    return True


# ----------------------------------------------------------------------
# right-click interaction
# ----------------------------------------------------------------------

def interact(game, tx, ty):
    """Right-click on the world. Returns True if something reacted."""
    world = game.world
    p = game.player
    if not in_reach(p, tx, ty):
        return False
    if world.get_tile(tx, ty) == _NOTE:
        game.read_note(tx, ty)
        return True
    anchor = world.object_at(tx, ty)
    if not anchor:
        return False
    td = TILES[world.objects[anchor]]
    if td.kind == "container":
        if anchor in world.locked:
            game.start_lockpick(anchor)
        else:
            game.open_chest(anchor, td.display)
        return True
    if td.kind == "furnace":
        game.inv_ui.open_container(anchor, world.containers[anchor], td.display)
        return True
    if td.kind == "bed":
        game.use_bed(anchor)
        return True
    if td.kind == "pylon":
        game.open_teleport()
        return True
    return False


# ----------------------------------------------------------------------
# consumables
# ----------------------------------------------------------------------

def consume(game, it):
    p = game.player
    if it.max_hp_up:
        if p.max_hp >= 200:
            game.notify("生命上限已达到 200")
            return False
        p.max_hp += it.max_hp_up
        p.heal(it.max_hp_up)
        game.add_text(f"生命上限 +{it.max_hp_up}", (255, 120, 170))
        return True
    if it.max_mana_up:
        if p.base_max_mana >= 200:
            game.notify("魔力上限已达到 200")
            return False
        p.base_max_mana += it.max_mana_up
        p.recompute_stats()
        p.mana = p.max_mana
        game.add_text(f"魔力上限 +{it.max_mana_up}", (120, 160, 255))
        return True
    if it.heal:
        if p.heal_cd > 0:
            game.notify(f"治疗冷却中（{p.heal_cd // FPS + 1} 秒）")
            return False
        if p.hp >= p.max_hp:
            return False
        healed = p.heal(it.heal)
        p.heal_cd = HEAL_COOLDOWN
        game.add_text(f"+{healed}", (90, 255, 90))
        return True
    return False


def use_summon(game, it):
    if it.summon == "eye" and not game.is_night():
        game.notify("只能在夜晚使用")
        return False
    if game.bosses.active():
        game.notify("已经有 Boss 在场")
        return False
    return game.bosses.summon(it.summon, delay=60)


def quick_heal(game):
    p = game.player
    for name in ("healing_potion", "mushroom"):
        for i, s in enumerate(p.inventory.slots):
            if s and s[0] == name:
                if consume(game, ITEMS[name]):
                    p.inventory.consume_slot(i)
                return
    game.notify("没有治疗物品")
