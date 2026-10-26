"""Town NPCs: arrival conditions, housing checks, wandering AI, dialogue and services."""
import random
from collections import deque

import pygame

from settings import *
from tiles import TILES, T, SOLID, EMITS_LIGHT
from physics import move_x, move_y, rect_solid

TS = TILE_SIZE
_DOOR = T["door"]
_BED = T["bed"]
HOUSE_MIN, HOUSE_MAX = 50, 750

NPC_TYPES = {
    "guide": dict(name="向导", lines=[
        "用斧头砍树，10 个木材就能做一张工作台。",
        "地下越深越黑，记得多带火把。",
        "想让人搬来住？用墙围出房间，放床、门和火把，再用木锤敲掉不要的墙。",
        "右键点击床可以设置重生点，晚上还能睡觉跳过黑夜。",
        "在水下待太久会窒息，头顶的气泡就是你剩余的氧气。",
        "岩浆会让你持续燃烧。黑曜石护符能保护你——水和岩浆相遇就会生成黑曜石。",
        "用六个晶状体能在工作台做出可疑眼球，晚上使用它……如果你够勇敢的话。",
        "听说沙漠的金字塔里困着一位会传送的旅人。",
    ]),
    "merchant": dict(name="商人", shop=[("torch", 5), ("healing_potion", 30), ("wood_arrow", 1),
                                       ("mushroom", 8), ("bucket", 40), ("mining_helmet", 80),
                                       ("magnet_ring", 200), ("bed", 30), ("chest", 25)],
                     lines=["有钱就是大爷！看看我的货吧。", "出货箱是个好东西，第二天早上就能拿到钱。",
                            "地下的箱子里总有些稀奇古怪的宝贝。"]),
    "nurse": dict(name="护士", lines=["受伤了？我可以帮你治疗，不过要收点费用。",
                                     "别总是往岩浆里跳。"]),
    "traveler": dict(name="传送师", shop=[("pylon", 120), ("magic_mirror", 350), ("mana_crystal", 150)],
                     lines=["谢谢你救了我！在不同的地方放置传送晶塔，就可以在它们之间穿梭。",
                            "魔镜能让你瞬间回到重生点。"]),
    "blacksmith": dict(name="铁匠", shop=[("copper_bar", 10), ("iron_bar", 15), ("gold_bar", 25),
                                         ("auto_smelter", 350), ("iron_hammer", 80)],
                       lines=["打败了那个怪物？了不起！我来帮你打造装备。",
                              "自动熔炉能把矿石自己炼成锭，懒人必备。"]),
}
ARRIVAL_HINTS = {
    "merchant": "持有 50 金币以上",
    "nurse": "生命上限达到 120 且商人已入住",
    "traveler": "在沙漠金字塔中解救",
    "blacksmith": "击败任意一个 Boss",
}


def check_house(world, anchor):
    """Validate the room around a bed. Returns (ok, reason)."""
    ax, ay = anchor
    start = (ax + 1, ay)
    seen = {start}
    queue = deque([start])
    door = light = False
    walls = 0
    while queue:
        x, y = queue.popleft()
        t = world.get_tile(x, y)
        if EMITS_LIGHT[t]:
            light = True
        if world.get_wall(x, y):
            walls += 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in seen:
                continue
            nt = world.get_tile(nx, ny)
            if nt == _DOOR:
                door = True
                continue
            if SOLID[nt]:
                continue
            seen.add((nx, ny))
            if len(seen) > HOUSE_MAX:
                return False, "房间不封闭或太大"
            queue.append((nx, ny))
    if len(seen) < HOUSE_MIN:
        return False, "房间太小"
    if walls < len(seen) * 0.9:
        return False, "缺少背景墙"
    if not light:
        return False, "需要光源（火把）"
    if not door:
        return False, "需要一扇门"
    return True, "这个房屋适合 NPC 居住"


class NPC:
    W, H = 22, 44

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

    def update(self, world, night, spawn_x):
        if self.bound:
            return
        cx = self.center()[0]
        home_x = (self.home[0] + 2) * TS if self.home else spawn_x
        self.timer -= 1
        if night and self.home:
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

    def draw(self, surf, cam, assets, font):
        frames = assets.npcs[self.kind]
        frame = int(self.anim) % 4 if self.anim else "idle"
        right, left = frames[frame]
        img = right if self.facing > 0 else left
        sx, sy = cam.apply(self.x, self.y)
        surf.blit(img, (sx + (self.W - img.get_width()) / 2, sy + self.H - img.get_height()))
        label = f"{self.name}（被困）" if self.bound else self.name
        txt = font.render(label, True, (255, 240, 170) if self.bound else (230, 255, 230))
        surf.blit(txt, (sx + self.W / 2 - txt.get_width() / 2, sy - 18))


class NPCManager:
    def __init__(self, game):
        self.game = game
        self.npcs = []
        self.check_timer = 60

    def by_kind(self, kind):
        return next((n for n in self.npcs if n.kind == kind), None)

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
        }
        for kind, ok in conditions.items():
            if not ok or self.by_kind(kind):
                continue
            if kind == "guide":
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
