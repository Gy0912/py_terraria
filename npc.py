"""Town NPCs: arrival conditions, housing checks, wandering, fighting hostile creatures,
taking damage, dialogue and services."""
import math
import random
from collections import deque

import pygame

from settings import *
from tiles import TILES, T, SOLID, EMITS_LIGHT
from physics import move_x, move_y, rect_solid
from entities import Projectile

TS = TILE_SIZE
_DOOR = T["door"]
_BED = T["bed"]
HOUSE_MIN, HOUSE_MAX = 50, 750

# attack: (style, damage, cooldown frames, range px). Damage per second stays well below the player's.
NPC_TYPES = {
    "guide": dict(name="向导", hp=200, attack=("arrow", 7, 50, 360), lines=[
        "用斧头砍树，10 个木材就能做一张工作台。",
        "想让人搬来住？按 J 或者点快捷栏旁边的房屋按钮，检测房间还缺什么。",
        "在水下待太久会窒息，头顶的气泡就是你剩余的氧气。",
        "熔炉不能直接合成，要放进矿石和燃料慢慢烧。煤炭比木材耐烧得多。",
        "镇上住满三个人以后，大家晚上会打打牌。你也可以来一局。",
        "废墟里散落着一支远征队的日志，按 L 可以翻看你找到的部分。",
        "上锁的金箱需要撬锁器。手要稳，时机要准。",
    ]),
    "merchant": dict(name="商人", hp=200, attack=("knife", 6, 55, 300),
                     shop=[("torch", 5), ("seeds", 2), ("healing_potion", 30), ("wood_arrow", 1), ("mushroom", 8),
                           ("bucket", 40), ("mining_helmet", 80), ("magnet_ring", 200), ("bed", 30),
                           ("chest", 25), ("card_pack", 50), ("lockpick", 15)],
                     lines=["有钱就是大爷！看看我的货吧。", "出货箱是个好东西，第二天早上就能拿到钱。",
                            "卡包里偶尔能开出稀有牌，要不要试试手气？", "我手上有个活儿，你要不要接？"]),
    "nurse": dict(name="护士", hp=180, attack=("heal", 6, 120, 220),
                  lines=["受伤了？我可以帮你治疗，不过要收点费用。", "别总是往岩浆里跳。",
                         "镇上打起来的时候，我会尽量给大家包扎。"]),
    "traveler": dict(name="传送师", hp=220, attack=("bolt", 9, 60, 420),
                     shop=[("pylon", 120), ("magic_mirror", 350), ("mana_crystal", 150), ("treasure_map", 120)],
                     lines=["谢谢你救了我！在不同的地方放置传送晶塔，就可以在它们之间穿梭。",
                            "我当年是灰烬远征队的人。队长的日志散落在各处的废墟里。",
                            "藏宝图上的宝藏埋在地下，跟着地图上的红叉挖下去就行。"]),
    "blacksmith": dict(name="铁匠", hp=280, attack=("melee", 12, 45, 34),
                       shop=[("copper_bar", 10), ("iron_bar", 15), ("gold_bar", 25), ("coal", 3),
                             ("iron_hammer", 80), ("lockpick", 12)],
                       lines=["打败了那个怪物？了不起！我来帮你打造装备。",
                              "金属锭要在熔炉里炼：原料放上面，燃料放下面。",
                              "有怪物敢进镇子，我的锤子可不答应。"]),
}
ARRIVAL_HINTS = {
    "merchant": "持有 50 金币以上",
    "nurse": "生命上限达到 120 且商人已入住",
    "traveler": "在沙漠金字塔中解救",
    "blacksmith": "击败任意一个 Boss",
}


def check_room(world, tx, ty):
    """Flood-fill the room containing (tx, ty) and report every housing requirement."""
    result = {"ok": False, "cells": set(), "reasons": [], "size": 0, "walls": 0.0,
              "light": False, "door": False, "bed": None}
    t0 = world.get_tile(tx, ty)
    if SOLID[t0] or t0 == _DOOR:
        result["reasons"].append("请点击房间内部的空地")
        return result
    seen = {(tx, ty)}
    queue = deque([(tx, ty)])
    walls = 0
    open_room = False
    while queue:
        x, y = queue.popleft()
        t = world.get_tile(x, y)
        if EMITS_LIGHT[t]:
            result["light"] = True
        if t == _BED and result["bed"] is None:
            result["bed"] = world.object_at(x, y)
        if world.get_wall(x, y):
            walls += 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in seen:
                continue
            nt = world.get_tile(nx, ny)
            if nt == _DOOR:
                result["door"] = True
                continue
            if SOLID[nt]:
                continue
            seen.add((nx, ny))
            if len(seen) > HOUSE_MAX:
                open_room = True
                queue.clear()
                break
            queue.append((nx, ny))
    result["cells"] = seen
    result["size"] = len(seen)
    result["walls"] = walls / max(1, len(seen))
    reasons = result["reasons"]
    if open_room:
        reasons.append("房间不封闭或太大（最多 750 格）")
    else:
        if len(seen) < HOUSE_MIN:
            reasons.append(f"房间太小（{len(seen)}/{HOUSE_MIN} 格）")
        if result["walls"] < 0.9:
            reasons.append(f"背景墙不足（{int(result['walls'] * 100)}%/90%）")
        if not result["light"]:
            reasons.append("缺少光源（火把）")
        if not result["door"]:
            reasons.append("缺少门")
        if result["bed"] is None:
            reasons.append("缺少床")
    result["ok"] = not reasons
    return result


def check_house(world, anchor):
    """Validate the room around a bed. Returns (ok, first reason or success text)."""
    r = check_room(world, anchor[0] + 1, anchor[1])
    return r["ok"], (r["reasons"][0] if r["reasons"] else "这个房屋适合 NPC 居住")


class NPC:
    W, H = 22, 44
    DEFENSE = 4

    def __init__(self, kind, x, y, bound=False):
        self.kind = kind
        self.info = NPC_TYPES[kind]
        self.name = self.info["name"]
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.home = None
        self.bound = bound
        self.facing = 1
        self.anim = 0.0
        self.target = None
        self.timer = 0
        self.on_ground = False
        self.line = 0
        self.hp = self.max_hp = self.info["hp"]
        self.alive = True
        self.invuln = 0
        self.attack_cd = random.randint(0, 30)
        self.calm = 0          # frames since last hurt (regeneration starts after 5 s)
        self.flash = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def center(self):
        return self.x + self.W / 2, self.y + self.H / 2

    def shop_items(self):
        return self.info.get("shop", [])

    def next_line(self):
        lines = self.info["lines"]
        text = lines[self.line % len(lines)]
        self.line += 1
        return text

    def hurt(self, amount, from_x=None):
        if self.invuln > 0 or self.bound or not self.alive:
            return 0
        dealt = max(1, amount - self.DEFENSE // 2)
        self.hp -= dealt
        self.invuln = 30
        self.calm = 0
        self.flash = 8
        if from_x is not None:
            d = 1 if self.center()[0] >= from_x else -1
            self.vx = d * 3.5
            self.vy = -3.0
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return dealt

    # -------------------- behaviour --------------------

    def update(self, world, night, spawn_x):
        if self.bound:
            return
        if self.invuln > 0:
            self.invuln -= 1
        if self.flash > 0:
            self.flash -= 1
        self.calm += 1
        if self.calm > FPS * 5 and self.hp < self.max_hp and self.calm % 30 == 0:
            self.hp += 1
        cx = self.center()[0]
        home_x = (self.home[0] + 2) * TS if self.home else spawn_x
        self.timer -= 1
        if self.hp < self.max_hp * 0.35 and self.calm < FPS * 3:
            self.target = home_x                         # badly hurt: run home
        elif night and self.home:
            self.target = home_x
        elif self.timer <= 0:
            self.timer = random.randint(120, 300)
            self.target = None if random.random() < 0.4 else home_x + random.randint(-14, 14) * TS
        move = 0
        if self.target is not None and abs(self.target - cx) > 6:
            move = 1 if self.target > cx else -1
        self.vx += (move * 1.1 - self.vx) * 0.2
        if move:
            self.facing = move
        self.vy = min(self.vy + 0.42, 10)
        old_x = self.x
        self.x, blocked = move_x(world, self.x, self.y, self.W, self.H, self.vx)
        if blocked and self.on_ground:
            if not rect_solid(world, old_x + self.vx, self.y - TS, self.W, self.H):
                self.x = old_x + self.vx
                self.y -= TS
            else:
                self.vy = -6.5
                if random.random() < 0.02:
                    self.target = None
        self.y, landed, ceil = move_y(world, self.x, self.y, self.W, self.H, self.vy)
        if landed or ceil:
            self.vy = 0.0
        self.on_ground = landed
        self.anim = self.anim + abs(self.vx) * 0.07 if abs(self.vx) > 0.2 else 0.0

    def fight(self, game):
        """Attack the nearest hostile creature in range (the nurse heals instead)."""
        if self.bound:
            return
        if self.attack_cd > 0:
            self.attack_cd -= 1
            return
        style, dmg, cooldown, reach = self.info["attack"]
        cx, cy = self.center()
        if style == "heal":
            patients = [game.player] + [n for n in game.npcs.npcs if not n.bound]
            for p in patients:
                if p.alive and p.hp < p.max_hp and math.hypot(p.center()[0] - cx, p.center()[1] - cy) < reach:
                    p.hp = min(p.max_hp, p.hp + dmg)
                    game.burst(*p.center(), (120, 255, 140), 6, speed=1.5)
                    self.attack_cd = cooldown
            return
        foes = [c for c in game.creatures.creatures if c.alive and c.hostile]
        target = min(foes, key=lambda c: math.hypot(c.center()[0] - cx, c.center()[1] - cy), default=None)
        if target is None:
            return
        tx, ty = target.center()
        dist = math.hypot(tx - cx, ty - cy)
        if dist > reach:
            if style == "melee" and dist < 9 * TS and self.home and abs(tx - (self.home[0] + 2) * TS) < 20 * TS:
                self.target = tx
            return
        self.facing = 1 if tx > cx else -1
        self.attack_cd = cooldown
        if style == "melee":
            game.on_creature_hit(target, target.hit(dmg, cx, 4, attacker=self))
            game.burst(tx, ty, (230, 230, 230), 4)
            return
        a = math.atan2(ty - cy, tx - cx)
        speed = 8.0 if style == "bolt" else 9.0
        kind = "bolt" if style == "bolt" else "arrow"
        if kind == "arrow":
            a -= 0.08 * dist / 300            # aim a little high to cancel the arrow drop
        game.projectiles.append(Projectile(kind, cx, cy - 6, math.cos(a) * speed, math.sin(a) * speed,
                                           dmg, 2, owner=self))

    def draw(self, surf, cam, assets, font):
        frames = assets.npcs[self.kind]
        frame = int(self.anim) % 4 if self.anim else "idle"
        right, left = frames[frame]
        img = right if self.facing > 0 else left
        if self.flash > 0:
            img = img.copy()
            img.fill((150, 60, 60), special_flags=pygame.BLEND_RGB_ADD)
        sx, sy = cam.apply(self.x, self.y)
        surf.blit(img, (sx + (self.W - img.get_width()) / 2, sy + self.H - img.get_height()))
        label = f"{self.name}（被困）" if self.bound else self.name
        txt = font.render(label, True, (255, 240, 170) if self.bound else (230, 255, 230))
        surf.blit(txt, (sx + self.W / 2 - txt.get_width() / 2, sy - 18))
        if self.hp < self.max_hp:
            pygame.draw.rect(surf, (40, 0, 0), (sx - 2, sy - 24, self.W + 4, 4))
            pygame.draw.rect(surf, (90, 220, 90), (sx - 2, sy - 24, (self.W + 4) * self.hp / self.max_hp, 4))


class NPCManager:
    def __init__(self, game):
        self.game = game
        self.npcs = []
        self.check_timer = 60

    def by_kind(self, kind):
        return next((n for n in self.npcs if n.kind == kind), None)

    def housed(self):
        return [n for n in self.npcs if n.home and not n.bound]

    def npc_at(self, wx, wy):
        for n in self.npcs:
            if n.rect().inflate(8, 8).collidepoint(wx, wy):
                return n
        return None

    def update(self):
        g = self.game
        world = g.world
        night = g.is_night()
        spawn_x = world.spawn_tx * TS
        for n in self.npcs:
            n.update(world, night, spawn_x)
            n.fight(g)
        for n in [n for n in self.npcs if not n.alive]:
            self.npcs.remove(n)
            world.flags[f"npc_dead_{n.kind}"] = g.day_count
            g.announce(f"{n.name} 被杀死了！明天会有人接替", (255, 120, 120))
        self._spawn_bound()
        self.check_timer -= 1
        if self.check_timer <= 0:
            self.check_timer = FPS * 10
            self.check_arrivals()

    def _spawn_bound(self):
        world = self.game.world
        for entry in list(world.pending_npcs):
            kind, tx, ty = entry
            if world.is_generated(tx // CHUNK_SIZE, ty // CHUNK_SIZE):
                world.pending_npcs.remove(entry)
                if not self.by_kind(kind):
                    self.npcs.append(NPC(kind, tx * TS, (ty + 1) * TS - NPC.H, bound=True))

    def rescue(self, npc):
        npc.bound = False
        self.game.world.flags[f"{npc.kind}_rescued"] = True
        self.game.announce(f"你解救了 {npc.name}！为他准备一间房屋吧。", (140, 255, 160))

    def houses(self):
        """Beds near the player in generated chunks, nearest first."""
        world = self.game.world
        px = self.game.player.center()[0] / TS
        py = self.game.player.center()[1] / TS
        beds = [a for a, tid in world.objects.items() if tid == _BED
                and world.is_generated(a[0] // CHUNK_SIZE, a[1] // CHUNK_SIZE)
                and abs(a[0] - px) < 200 and abs(a[1] - py) < 120]
        return sorted(beds, key=lambda a: abs(a[0] - px) + abs(a[1] - py))

    @staticmethod
    def move_in(npc, home):
        npc.home = home
        npc.x = (home[0] + 1) * TS
        npc.y = (home[1] + 2) * TS - NPC.H
        npc.vx = npc.vy = 0.0

    def check_arrivals(self):
        g = self.game
        world = g.world
        p = g.player
        taken = {n.home for n in self.npcs if n.home}
        for n in self.npcs:
            if n.home and (world.objects.get(n.home) != _BED or not check_house(world, n.home)[0]):
                taken.discard(n.home)
                n.home = None
                g.announce(f"{n.name} 失去了住所", (255, 200, 120))
        free = [h for h in self.houses() if h not in taken and check_house(world, h)[0]]
        for n in self.npcs:
            if not n.home and not n.bound and free:
                self.move_in(n, free.pop(0))
                g.announce(f"{n.name} 搬进了新家", (140, 255, 160))
        conditions = {
            "guide": True,
            "merchant": p.inventory.count("coin") >= 50,
            "nurse": p.max_hp >= 120 and self.by_kind("merchant") is not None,
            "blacksmith": world.flags.get("eye_defeated") or world.flags.get("king_slime_defeated"),
            "traveler": world.flags.get("traveler_rescued"),
        }
        for kind, ok in conditions.items():
            if not ok or self.by_kind(kind) or world.flags.get(f"npc_dead_{kind}") == g.day_count:
                continue
            if kind == "guide" and not free:
                tx = world.spawn_tx + 3
                self.npcs.append(NPC(kind, tx * TS, (world.surface_at(tx) - 4) * TS))
                continue
            if not free:
                continue
            npc = NPC(kind, 0, 0)
            self.move_in(npc, free.pop(0))
            self.npcs.append(npc)
            g.announce(f"{npc.name} 已经到来！", (140, 255, 160))

    def draw(self, surf, cam, assets, font):
        for n in self.npcs:
            n.draw(surf, cam, assets, font)
