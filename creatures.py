"""Creatures with three AI styles (slime / walker / flyer) and biome-aware spawning."""
import math
import random

import pygame

from settings import *
from tiles import SOLID, LIQUID
from physics import move_x, move_y

TS = TILE_SIZE

# drops: (item, min, max, chance)
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
}


def spawn_table(layer, biome, night):
    """Weighted creature list for an environment."""
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


class Creature:
    def __init__(self, kind, x, y, world):
        self.kind = kind
        self.t = CREATURE_TYPES[kind]
        self.world = world
        self.w, self.h = self.t["size"]
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.hp = self.max_hp = self.t["hp"]
        self.on_ground = False
        self.alive = True
        self.facing = random.choice((-1, 1))
        self.timer = random.randint(20, 80)
        self.flash = 0
        self.anim = 0
        self.stuck = 0
        self.wander = random.choice((-1, 1))

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def hit(self, damage, from_x, knockback):
        dealt = max(1, damage - self.t["defense"] // 2)
        self.hp -= dealt
        self.flash = 8
        d = 1 if self.center()[0] >= from_x else -1
        resist = 0.4 if self.t["ai"] == "slime" else 0.0
        self.vx = d * knockback * (1 - resist)
        self.vy = -3.0 * (1 - resist)
        self.timer = max(self.timer, 15)
        if self.hp <= 0:
            self.alive = False
        return dealt

    # -------------------- AI --------------------

    def update(self, player):
        self.anim += 1
        if self.flash > 0:
            self.flash -= 1
        px, py = player.center()
        cx, cy = self.center()
        dx = px - cx
        near = player.alive and abs(dx) < 900 and abs(py - cy) < 600
        ai = self.t["ai"]
        if ai == "slime":
            self._slime(dx, near)
        elif ai == "walker":
            self._walker(dx, near)
        else:
            self._flyer(px - cx, py - cy, near)

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
        self.x, bx = move_x(self.world, self.x, self.y, self.w, self.h, self.vx, creature=True)
        if bx:
            self.vx = -self.vx * 0.7
            self.wander = -self.wander
        self.y, landed, ceil = move_y(self.world, self.x, self.y, self.w, self.h, self.vy, creature=True)
        if landed or ceil:
            self.vy = -self.vy * 0.7
        if abs(self.vx) > 0.2:
            self.facing = 1 if self.vx > 0 else -1

    # -------------------- draw --------------------

    def draw(self, surf, cam, assets):
        frames = assets.creatures[self.kind]
        ai = self.t["ai"]
        if ai == "slime":
            idx = 1 if (self.on_ground and self.timer < 12) else 0
        elif ai == "walker":
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
        self.cooldown = 120
        self.slime_rain = False

    def clear(self):
        self.creatures = [c for c in self.creatures if getattr(c, "is_boss", False)]

    def normal_count(self):
        return sum(1 for c in self.creatures if not getattr(c, "is_boss", False))

    def update(self, player, night):
        if player.alive:
            self._spawn_tick(player, night)
        for c in self.creatures:
            c.update(player)
        px, py = player.center()
        self.creatures = [c for c in self.creatures if c.alive and (
            getattr(c, "is_boss", False) or (abs(c.x - px) < SCREEN_WIDTH * 2.5 and abs(c.y - py) < SCREEN_HEIGHT * 3))]

    def _spawn_tick(self, player, night):
        self.cooldown -= 1
        if self.cooldown > 0:
            return
        ptx = int(player.center()[0]) // TS
        pty = int(player.center()[1]) // TS
        layer = self.world.layer_at(ptx, pty)
        rain = self.slime_rain and layer == "surface"
        if rain:
            interval, cap = 70, 14
        elif layer == "surface":
            interval, cap = (150, 9) if night else (260, 5)
        elif layer == "hell":
            interval, cap = 150, 10
        elif layer == "space":
            interval, cap = 300, 3
        else:
            interval, cap = 180, 8
        self.cooldown = interval + random.randint(-20, 20)
        if self.normal_count() >= cap:
            return
        self._try_spawn(ptx, pty, night, rain)

    def _try_spawn(self, ptx, pty, night, rain=False):
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
                if rain:
                    table = SLIME_RAIN
                else:
                    table = spawn_table("surface" if layer == "space" else layer, world.biome_at(tx, ty), night)
                if not table:
                    continue
                kind = random.choices([k for k, _ in table], [w for _, w in table])[0]
                ai = CREATURE_TYPES[kind]["ai"]
                w, h = CREATURE_TYPES[kind]["size"]
                if not self._fits(tx, ty, ai, w, h):
                    continue
                x = tx * TS + (TS - w) / 2
                y = (ty + 1) * TS - h if ai != "flyer" else ty * TS
                self.creatures.append(Creature(kind, x, y, world))
                return

    def _fits(self, tx, ty, ai, w, h):
        """Room for a w x h creature whose feet rest on row ty (flyers just need open air)."""
        g = self.world.peek_tile
        tw, th = -(-w // TS), -(-h // TS)
        for dx in range(tw):
            for dy in range(th):
                t = g(tx + dx, ty - dy)
                if t is None or SOLID[t] or LIQUID[t]:
                    return False
        if ai == "flyer":
            return True
        return all(g(tx + dx, ty + 1) is not None and SOLID[g(tx + dx, ty + 1)] for dx in range(tw))

    def draw(self, surf, cam, assets):
        for c in self.creatures:
            c.draw(surf, cam, assets)
