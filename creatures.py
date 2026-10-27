"""Creatures: hostile monsters, neutral animals (fight back when attacked) and friendly critters.

AI styles: slime / walker / flyer for fighters, critter / critter_fly for harmless animals.
Spawning is a once-per-second probability roll whose odds depend on layer, biome, time of
day and how close the player is to a settled town.
"""
import math
import random

import pygame

from settings import *
from tiles import SOLID, LIQUID
from physics import move_x, move_y

TS = TILE_SIZE

# drops: (item, min, max, chance). faction: hostile (default) / neutral / friendly
CREATURE_TYPES = {
    "green_slime": dict(ai="slime", name="绿史莱姆", size=(30, 22), hp=14, dmg=6, defense=0, speed=2.0,
                        jump=7.0, drops=[("gel", 1, 2, 1.0)]),
    "blue_slime": dict(ai="slime", name="蓝史莱姆", size=(30, 22), hp=25, dmg=7, defense=2, speed=2.2,
                       jump=7.5, drops=[("gel", 1, 3, 1.0)]),
    "sand_slime": dict(ai="slime", name="沙史莱姆", size=(30, 22), hp=30, dmg=10, defense=4, speed=2.4,
                       jump=8.0, drops=[("gel", 1, 3, 1.0), ("sand", 2, 5, 0.5)]),
    "ice_slime": dict(ai="slime", name="冰史莱姆", size=(30, 22), hp=40, dmg=12, defense=6, speed=2.4,
                      jump=8.0, drops=[("gel", 1, 3, 1.0), ("ice", 1, 3, 0.4)]),
    "jungle_slime": dict(ai="slime", name="丛林史莱姆", size=(32, 24), hp=60, dmg=18, defense=6, speed=2.6,
                         jump=8.5, drops=[("gel", 2, 4, 1.0), ("mud", 2, 4, 0.4)]),
    "lava_slime": dict(ai="slime", name="岩浆史莱姆", size=(32, 24), hp=70, dmg=26, defense=10, speed=2.8,
                       jump=9.0, drops=[("gel", 2, 4, 1.0), ("hellstone", 1, 2, 0.5)], light=(4, 0.7)),
    "zombie": dict(ai="walker", name="僵尸", size=(22, 42), hp=45, dmg=14, defense=6, speed=1.2,
                   drops=[("gel", 1, 1, 0.2)]),
    "frozen_zombie": dict(ai="walker", name="冰冻僵尸", size=(22, 42), hp=55, dmg=16, defense=8, speed=1.3,
                          drops=[("ice", 1, 3, 0.5)]),
    "skeleton": dict(ai="walker", name="骷髅", size=(22, 42), hp=70, dmg=20, defense=8, speed=1.6,
                     drops=[("bone", 1, 3, 1.0)]),
    "crab": dict(ai="walker", name="螃蟹", size=(30, 20), hp=40, dmg=14, defense=8, speed=1.0, drops=[]),
    "demon_eye": dict(ai="flyer", name="恶魔眼", size=(30, 20), hp=50, dmg=18, defense=2, speed=2.6,
                      drops=[("lens", 1, 1, 0.5)]),
    "cave_bat": dict(ai="flyer", name="洞穴蝙蝠", size=(30, 18), hp=20, dmg=12, defense=2, speed=3.0,
                     drops=[]),
    "jungle_bat": dict(ai="flyer", name="丛林蝙蝠", size=(30, 18), hp=35, dmg=18, defense=4, speed=3.2,
                       drops=[]),
    "ice_bat": dict(ai="flyer", name="冰蝙蝠", size=(30, 18), hp=30, dmg=15, defense=4, speed=3.0,
                    drops=[("ice", 1, 2, 0.3)]),
    "hornet": dict(ai="flyer", name="黄蜂", size=(28, 24), hp=45, dmg=22, defense=6, speed=2.4, drops=[]),
    "hellbat": dict(ai="flyer", name="地狱蝙蝠", size=(30, 18), hp=50, dmg=30, defense=8, speed=3.6,
                    drops=[("hellstone", 1, 1, 0.3)], light=(3, 0.6)),
    "servant_eye": dict(ai="flyer", name="巨眼仆从", size=(22, 15), hp=12, dmg=12, defense=0, speed=4.0,
                        drops=[]),
    # neutral: ignore you until hurt
    "boar": dict(ai="walker", faction="neutral", name="野猪", size=(32, 20), hp=60, dmg=14, defense=4,
                 speed=2.4, drops=[("raw_meat", 1, 2, 1.0)]),
    "snow_wolf": dict(ai="walker", faction="neutral", pack=True, name="雪狼", size=(34, 20), hp=65, dmg=16,
                      defense=4, speed=2.8, drops=[("raw_meat", 1, 1, 0.8)]),
    "scorpion": dict(ai="walker", faction="neutral", name="沙蝎", size=(26, 14), hp=40, dmg=12, defense=6,
                     speed=1.5, drops=[]),
    # friendly critters
    "bunny": dict(ai="critter", faction="friendly", name="兔子", size=(16, 14), hp=8, dmg=0, defense=0,
                  speed=1.8, drops=[("raw_meat", 1, 1, 0.6)]),
    "penguin": dict(ai="critter", faction="friendly", name="企鹅", size=(16, 20), hp=10, dmg=0, defense=0,
                    speed=1.1, drops=[("raw_meat", 1, 1, 0.5)]),
    "bird": dict(ai="critter_fly", faction="friendly", name="小鸟", size=(14, 10), hp=5, dmg=0, defense=0,
                 speed=2.2, drops=[]),
    "firefly": dict(ai="critter_fly", faction="friendly", name="萤火虫", size=(6, 6), hp=1, dmg=0, defense=0,
                    speed=0.8, drops=[], light=(2, 0.55)),
}

# chance per one-second roll that a hostile creature appears
SPAWN_CHANCE = {"surface_day": 0.07, "surface_night": 0.22, "underground": 0.14, "cavern": 0.18,
                "hell": 0.24, "space": 0.05}
SPAWN_CAP = {"surface_day": 4, "surface_night": 8, "underground": 6, "cavern": 8, "hell": 9, "space": 3}
BIOME_FACTOR = {"forest": 1.0, "desert": 0.9, "snow": 1.0, "jungle": 1.35, "ocean": 0.8}
TOWN_FACTOR = 0.3
PASSIVE_CHANCE, PASSIVE_CAP = 0.25, 6


def spawn_table(layer, biome, night):
    """Weighted hostile creature list for an environment."""
    if layer == "hell":
        return [("lava_slime", 4), ("hellbat", 5)]
    if layer == "surface":
        day = {
            "forest": [("green_slime", 6), ("blue_slime", 3)],
            "desert": [("sand_slime", 5)],
            "snow": [("ice_slime", 4), ("blue_slime", 1)],
            "jungle": [("jungle_slime", 4), ("hornet", 2)],
            "ocean": [("crab", 5), ("blue_slime", 1)],
        }[biome]
        if not night:
            return day
        return {
            "forest": [("zombie", 6), ("demon_eye", 4), ("blue_slime", 1)],
            "desert": [("zombie", 4), ("demon_eye", 2), ("sand_slime", 2)],
            "snow": [("frozen_zombie", 5), ("demon_eye", 2)],
            "jungle": [("zombie", 3), ("jungle_slime", 3), ("hornet", 2), ("demon_eye", 1)],
            "ocean": [("crab", 4), ("zombie", 2)],
        }[biome]
    if layer in ("underground", "cavern"):
        deep = layer == "cavern"
        table = {
            "snow": [("ice_slime", 4), ("ice_bat", 4), ("skeleton", 2 if deep else 0)],
            "jungle": [("jungle_slime", 4), ("jungle_bat", 4), ("hornet", 2)],
            "desert": [("sand_slime", 3), ("cave_bat", 3), ("skeleton", 3 if deep else 1)],
        }.get(biome, [("cave_bat", 4), ("blue_slime", 2), ("skeleton", 4 if deep else 1)])
        return [e for e in table if e[1] > 0]
    return []


def passive_table(biome, night):
    """Friendly and neutral animals on the surface."""
    if night:
        return {"forest": [("firefly", 5), ("bunny", 1)], "jungle": [("firefly", 5)],
                "snow": [("snow_wolf", 2), ("penguin", 1)], "desert": [("scorpion", 2)],
                "ocean": [("firefly", 1)]}[biome]
    return {"forest": [("bunny", 5), ("bird", 3), ("boar", 1)], "jungle": [("bird", 4), ("boar", 2)],
            "snow": [("penguin", 4), ("snow_wolf", 2), ("bird", 1)], "desert": [("scorpion", 3), ("bird", 1)],
            "ocean": [("bird", 3)]}[biome]


class Creature:
    def __init__(self, kind, x, y, world):
        self.kind = kind
        self.t = CREATURE_TYPES[kind]
        self.faction = self.t.get("faction", "hostile")
        self.world = world
        self.w, self.h = self.t["size"]
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.hp = self.max_hp = self.t["hp"]
        self.on_ground = False
        self.alive = True
        self.provoked = False
        self.provoker = None
        self.facing = random.choice((-1, 1))
        self.timer = random.randint(20, 80)
        self.flash = 0
        self.anim = random.randint(0, 100)
        self.stuck = 0
        self.wander = random.choice((-1, 1))

    @property
    def hostile(self):
        return self.faction == "hostile" or self.provoked

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def hit(self, damage, from_x, knockback, attacker=None):
        dealt = max(1, damage - self.t["defense"] // 2)
        self.hp -= dealt
        self.flash = 8
        d = 1 if self.center()[0] >= from_x else -1
        resist = 0.4 if self.t["ai"] == "slime" else 0.0
        self.vx = d * knockback * (1 - resist)
        self.vy = -3.0 * (1 - resist)
        self.timer = max(self.timer, 15)
        if self.faction == "neutral":
            self.provoke(attacker)
        if self.hp <= 0:
            self.alive = False
        return dealt

    def provoke(self, attacker):
        self.provoked = True
        if attacker is not None:
            self.provoker = attacker

    # -------------------- AI --------------------

    def _pick_target(self, targets):
        """Nearest living target (player or NPC) for hostile creatures."""
        cx, cy = self.center()
        if self.faction == "neutral":
            t = self.provoker
            return t if t is not None and t.alive else (targets[0] if targets else None)
        best, best_d = None, 1e9
        for t in targets:
            if not t.alive:
                continue
            tx, ty = t.center()
            d = abs(tx - cx) + abs(ty - cy) * 1.5
            if d < best_d:
                best, best_d = t, d
        return best

    def update(self, player, targets=None):
        self.anim += 1
        if self.flash > 0:
            self.flash -= 1
        ai = self.t["ai"]
        cx, cy = self.center()
        if ai in ("critter", "critter_fly"):
            near = [t for t in (targets or [player]) if t.alive]
            threat = min(near, key=lambda t: abs(t.center()[0] - cx) + abs(t.center()[1] - cy), default=None)
            if ai == "critter":
                self._critter(threat)
            else:
                self._critter_fly(threat)
            return
        if not self.hostile:
            self._idle_walk()
            return
        target = self._pick_target(targets or [player])
        if target is None:
            self._idle_walk()
            return
        tx, ty = target.center()
        dx = tx - cx
        near = abs(dx) < 900 and abs(ty - cy) < 600
        if ai == "slime":
            self._slime(dx, near)
        elif ai == "walker":
            self._walker(dx, near)
        else:
            self._flyer(tx - cx, ty - cy, near)

    def _physics(self, gravity=0.4, max_fall=10.0):
        in_liquid = LIQUID[self.world.get_tile(int(self.x + self.w / 2) // TS, int(self.y + self.h / 2) // TS)]
        if in_liquid:
            gravity *= 0.4
            max_fall = 3.0
        self.vy = min(self.vy + gravity, max_fall)
        self.x, blocked = move_x(self.world, self.x, self.y, self.w, self.h, self.vx, creature=True)
        self.y, landed, ceil = move_y(self.world, self.x, self.y, self.w, self.h, self.vy, creature=True)
        if landed or ceil:
            self.vy = 0.0
        self.on_ground = landed
        return blocked

    def _idle_walk(self):
        """Unprovoked neutral animals amble around."""
        self.timer -= 1
        if self.timer <= 0:
            self.timer = random.randint(60, 200)
            self.wander = random.choice((-1, 0, 0, 1))
        self.vx += (self.wander * self.t["speed"] * 0.35 - self.vx) * 0.1
        if self.wander:
            self.facing = self.wander
        if self._physics() and self.on_ground:
            self.vy = -6.0

    def _critter(self, threat):
        cx = self.center()[0]
        fleeing = threat is not None and math.hypot(threat.center()[0] - cx, threat.center()[1] - self.center()[1]) < 110
        if fleeing:
            d = -1 if threat.center()[0] > cx else 1
            self.vx += (d * self.t["speed"] * 1.6 - self.vx) * 0.25
            self.facing = d
            if self.on_ground and self.kind == "bunny" and self.anim % 18 == 0:
                self.vy = -5.0
        else:
            self._idle_walk()
            return
        if self._physics() and self.on_ground:
            self.vy = -6.0

    def _critter_fly(self, threat):
        if self.kind == "firefly":
            self.vx += (math.sin(self.anim * 0.03) * 0.6 - self.vx) * 0.05
            self.vy += (math.cos(self.anim * 0.025) * 0.4 - self.vy) * 0.05
        else:
            cx, cy = self.center()
            if threat is not None and math.hypot(threat.center()[0] - cx, threat.center()[1] - cy) < 140:
                d = -1 if threat.center()[0] > cx else 1
                self.vx += (d * self.t["speed"] * 1.5 - self.vx) * 0.1
                self.vy += (-1.6 - self.vy) * 0.1
            else:
                self.vx += (self.wander * self.t["speed"] * 0.5 - self.vx) * 0.05
                self.vy += (math.sin(self.anim * 0.05) * 0.8 - self.vy) * 0.05
                if random.random() < 0.005:
                    self.wander = -self.wander
        self._fly_move()

    def _fly_move(self):
        self.x, bx = move_x(self.world, self.x, self.y, self.w, self.h, self.vx, creature="flyer")
        if bx:
            self.vx = -self.vx * 0.7
            self.wander = -self.wander
        self.y, landed, ceil = move_y(self.world, self.x, self.y, self.w, self.h, self.vy, creature="flyer")
        if landed or ceil:
            self.vy = -self.vy * 0.7
        if abs(self.vx) > 0.2:
            self.facing = 1 if self.vx > 0 else -1

    def _slime(self, dx, near):
        if self.on_ground:
            self.vx *= 0.75
            self.timer -= 1
            if self.timer <= 0:
                d = (1 if dx > 0 else -1) if near else self.wander
                if not near and random.random() < 0.3:
                    self.wander = -self.wander
                self.facing = d
                self.vy = -self.t["jump"] * random.uniform(0.75, 1.05)
                self.vx = d * self.t["speed"]
                self.timer = random.randint(35, 70) if near else random.randint(80, 150)
        blocked = self._physics()
        if blocked:
            self.vx = -self.vx * 0.5

    def _walker(self, dx, near):
        d = (1 if dx > 0 else -1) if near else self.wander
        self.facing = d
        target = d * self.t["speed"]
        self.vx += max(-0.15, min(0.15, target - self.vx))
        old_x = self.x
        blocked = self._physics()
        if blocked and self.on_ground:
            self.vy = -8.0
        if abs(self.x - old_x) < 0.1:
            self.stuck += 1
            if self.stuck > 90:
                self.wander = -self.wander
                self.stuck = 0
        else:
            self.stuck = 0
        if not near and random.random() < 0.004:
            self.wander = -self.wander

    def _flyer(self, dx, dy, near):
        speed = self.t["speed"]
        if near:
            dist = max(1.0, math.hypot(dx, dy))
            tx, ty = dx / dist * speed, dy / dist * speed
        else:
            tx, ty = self.wander * speed * 0.5, math.sin(self.anim * 0.03) * speed * 0.4
        wobble = math.sin(self.anim * 0.15) * 0.8 if "bat" in self.kind else 0.0
        self.vx += (tx - self.vx) * 0.04
        self.vy += (ty + wobble - self.vy) * 0.04
        self._fly_move()

    # -------------------- draw --------------------

    def draw(self, surf, cam, assets):
        frames = assets.creatures[self.kind]
        ai = self.t["ai"]
        if ai == "slime":
            idx = 1 if (self.on_ground and self.timer < 12) else 0
        elif ai in ("walker", "critter"):
            idx = (self.anim // 8) % len(frames) if abs(self.vx) > 0.2 else 0
        else:
            idx = (self.anim // 6) % len(frames)
        right, left = frames[idx]
        img = right if self.facing > 0 else left
        sx, sy = cam.apply(self.x, self.y)
        pos = (sx + (self.w - img.get_width()) / 2, sy + self.h - img.get_height())
        if self.flash > 0:
            img = img.copy()
            img.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(img, pos)
        if self.hp < self.max_hp:
            bw = max(self.w, 26)
            bx = sx + (self.w - bw) / 2
            pygame.draw.rect(surf, (40, 0, 0), (bx, sy - 8, bw, 4))
            pygame.draw.rect(surf, (230, 40, 40), (bx, sy - 8, bw * self.hp / self.max_hp, 4))


SLIME_RAIN = [("green_slime", 5), ("blue_slime", 4), ("sand_slime", 1), ("jungle_slime", 1)]


class CreatureManager:
    def __init__(self, world):
        self.world = world
        self.creatures = []       # also holds active bosses and their minions
        self.roll_timer = 60
        self.slime_rain = False

    def clear(self):
        self.creatures = [c for c in self.creatures if getattr(c, "is_boss", False)]

    def count(self, hostile):
        return sum(1 for c in self.creatures
                   if not getattr(c, "is_boss", False) and (c.faction == "hostile") == hostile)

    def update(self, player, night, npcs=()):
        targets = [player] + [n for n in npcs if not n.bound]
        if player.alive:
            self._spawn_roll(player, night, npcs)
        for c in self.creatures:
            if getattr(c, "is_boss", False):
                c.update(player)
            else:
                c.update(player, targets)
                if c.kind == "firefly" and not night:
                    c.alive = False
        px, py = player.center()
        self.creatures = [c for c in self.creatures if c.alive and (
            getattr(c, "is_boss", False) or (abs(c.x - px) < SCREEN_WIDTH * 2.5 and abs(c.y - py) < SCREEN_HEIGHT * 3))]

    def spawn_context(self, player, night, npcs):
        """(key, chance, cap) of the hostile spawn roll at the player's position."""
        ptx = int(player.center()[0]) // TS
        pty = int(player.center()[1]) // TS
        layer = self.world.layer_at(ptx, pty)
        key = f"surface_{'night' if night else 'day'}" if layer == "surface" else layer
        chance = SPAWN_CHANCE[key] * BIOME_FACTOR.get(self.world.biome_at(ptx, pty), 1.0)
        town = sum(1 for n in npcs if not n.bound and abs(n.center()[0] - player.center()[0]) < 60 * TS
                   and abs(n.center()[1] - player.center()[1]) < 30 * TS)
        if town >= 2:
            chance *= TOWN_FACTOR
        if self.slime_rain and layer == "surface":
            return "slime_rain", 0.6, 14
        return key, chance, SPAWN_CAP[key]

    def _spawn_roll(self, player, night, npcs):
        self.roll_timer -= 1
        if self.roll_timer > 0:
            return
        self.roll_timer = FPS
        ptx = int(player.center()[0]) // TS
        pty = int(player.center()[1]) // TS
        key, chance, cap = self.spawn_context(player, night, npcs)
        if self.count(True) < cap and random.random() < chance:
            self._try_spawn(ptx, pty, night, rain=key == "slime_rain")
        layer = self.world.layer_at(ptx, pty)
        if layer == "surface" and self.count(False) < PASSIVE_CAP and random.random() < PASSIVE_CHANCE:
            self._try_spawn(ptx, pty, night, passive=True)

    def _try_spawn(self, ptx, pty, night, rain=False, passive=False):
        world = self.world
        half = SCREEN_WIDTH // TS // 2
        for _ in range(8):
            tx = ptx + random.choice((-1, 1)) * random.randint(half + 3, half + 26)
            if not (2 <= tx < WORLD_W - 3):
                continue
            for ty in sorted(range(pty - 24, pty + 25), key=lambda y: abs(y - pty) + random.random() * 10):
                if not (2 <= ty < WORLD_H - 4):
                    continue
                layer = world.layer_at(tx, ty)
                biome = world.biome_at(tx, ty)
                if rain:
                    table = SLIME_RAIN
                elif passive:
                    if layer != "surface":
                        continue
                    table = passive_table(biome, night)
                else:
                    table = spawn_table("surface" if layer == "space" else layer, biome, night)
                if not table:
                    continue
                kind = random.choices([k for k, _ in table], [w for _, w in table])[0]
                ai = CREATURE_TYPES[kind]["ai"]
                w, h = CREATURE_TYPES[kind]["size"]
                flying = ai in ("flyer", "critter_fly")
                if not self._fits(tx, ty, flying, w, h):
                    continue
                x = tx * TS + (TS - w) / 2
                y = ty * TS if flying else (ty + 1) * TS - h
                self.creatures.append(Creature(kind, x, y, world))
                return

    def _fits(self, tx, ty, flying, w, h):
        """Room for a w x h creature whose feet rest on row ty (flyers just need open air)."""
        g = self.world.peek_tile
        tw, th = -(-w // TS), -(-h // TS)
        for dx in range(tw):
            for dy in range(th):
                t = g(tx + dx, ty - dy)
                if t is None or SOLID[t] or LIQUID[t]:
                    return False
        if flying:
            return True
        return all(g(tx + dx, ty + 1) is not None and SOLID[g(tx + dx, ty + 1)] for dx in range(tw))

    def draw(self, surf, cam, assets):
        for c in self.creatures:
            c.draw(surf, cam, assets)
