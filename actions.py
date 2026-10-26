"""Player item use: mining, chopping, placing, melee swings, shooting and consumables."""
import math
import random

import pygame

from settings import *
from tiles import TILES, T, AIR, SOLID, LIQUID
from items import ITEMS
from entities import Projectile

TS = TILE_SIZE
_TREE, _CACTUS, _POT = T["tree"], T["cactus"], T["pot"]
# tiles that disappear when the block under them is removed
_NEEDS_BELOW = {T["workbench"], T["furnace"], T["anvil"], T["mushroom"], T["pot"], T["life_crystal"]}
_TORCH = T["torch"]
POT_LOOT = [("torch", 3, 8, 4), ("healing_potion", 1, 1, 2), ("wood_arrow", 8, 20, 3), ("gel", 1, 4, 2),
            ("mushroom", 1, 2, 2)]
HEAL_COOLDOWN = FPS * 10


def mouse_world(game):
    mx, my = pygame.mouse.get_pos()
    return mx + game.camera.x, my + game.camera.y


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

    if it.kind == "block":
        if place_tile(game, it, tx, ty):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif it.kind == "consumable":
        if consume(game, it):
            p.inventory.consume_slot(idx)
            _start(p, it, it.use_time)
    elif it.kind == "ranged":
        if p.inventory.remove(it.ammo, 1):
            _shoot(game, "arrow", it.damage + ITEMS[it.ammo].damage, it.knockback, it.proj_speed)
            _start(p, it, it.use_time)
        else:
            game.notify(f"没有{ITEMS[it.ammo].display}了")
    elif it.kind == "magic":
        if p.mana >= it.mana_cost:
            p.mana -= it.mana_cost
            _shoot(game, "bolt", it.damage, it.knockback, it.proj_speed)
            _start(p, it, it.use_time)
        else:
            game.notify("魔力不足")
    elif it.kind in ("tool", "weapon"):
        _start(p, it, it.use_time)
        if it.kind == "tool" and in_reach(p, tx, ty):
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
                game.on_creature_hit(c, c.hit(it.damage, p.center()[0], it.knockback))
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
    dmg = world.damage_tile(tx, ty, power)
    px, py = (tx + 0.5) * TS, (ty + 0.5) * TS
    game.burst(px, py, td.color, 4, speed=2.0)
    if dmg >= td.hp:
        break_tile(game, tx, ty)


def break_tile(game, tx, ty):
    world = game.world
    tid = world.get_tile(tx, ty)
    td = TILES[tid]
    px, py = (tx + 0.5) * TS, (ty + 0.5) * TS
    if tid in (_TREE, _CACTUS):
        n = world.remove_tree(tx, ty)
        game.drop_item_at(td.drop, n, px, py)
        game.burst(px, py - TS * 2, (60, 150, 50), 14, speed=3.0)
    elif tid == _POT:
        world.set_tile(tx, ty, AIR)
        for _ in range(random.randint(1, 2)):
            name, lo, hi, _ = random.choices(POT_LOOT, [w for *_, w in POT_LOOT])[0]
            game.drop_item_at(name, random.randint(lo, hi), px, py)
    else:
        world.set_tile(tx, ty, AIR)
        if td.drop:
            game.drop_item_at(td.drop, 1, px, py)
    game.burst(px, py, td.color, 10, speed=3.0)
    _check_support(game, tx, ty)


def _check_support(game, tx, ty):
    """Break things that were resting on or attached to the removed tile."""
    world = game.world
    above = world.get_tile(tx, ty - 1)
    if above in _NEEDS_BELOW or above in (_TREE, _CACTUS):
        break_tile(game, tx, ty - 1)
    for nx, ny in ((tx - 1, ty), (tx + 1, ty), (tx, ty - 1)):
        if world.get_tile(nx, ny) == _TORCH and not (
                world.is_solid(nx - 1, ny) or world.is_solid(nx + 1, ny) or world.is_solid(nx, ny + 1)):
            break_tile(game, nx, ny)


# ----------------------------------------------------------------------
# placing
# ----------------------------------------------------------------------

def place_tile(game, it, tx, ty):
    world = game.world
    p = game.player
    if not in_reach(p, tx, ty) or not (0 <= tx < WORLD_W and 0 <= ty < WORLD_H):
        return False
    cur = world.get_tile(tx, ty)
    if cur != AIR and not LIQUID[cur]:
        return False
    tid = T[it.place]
    td = TILES[tid]
    if td.solid:
        r = pygame.Rect(tx * TS, ty * TS, TS, TS)
        if r.colliderect(p.rect()) or any(r.colliderect(c.rect()) for c in game.creatures.creatures):
            return False
    solid = world.is_solid
    if td.support == "below":
        if not solid(tx, ty + 1):
            return False
    elif td.support == "side":
        if not (solid(tx - 1, ty) or solid(tx + 1, ty) or solid(tx, ty + 1)):
            return False
    else:
        neighbours = [world.get_tile(tx + dx, ty + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if all(n == AIR or LIQUID[n] for n in neighbours):
            return False
    world.set_tile(tx, ty, tid)
    return True


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


def quick_heal(game):
    p = game.player
    for name in ("healing_potion", "mushroom"):
        for i, s in enumerate(p.inventory.slots):
            if s and s[0] == name:
                if consume(game, ITEMS[name]):
                    p.inventory.consume_slot(i)
                return
    game.notify("没有治疗物品")
