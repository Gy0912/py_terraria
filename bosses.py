"""Boss encounters: the Bloodshot Eye (night, summoned or natural) and King Slime
(summoned or triggered by a slime rain). Bosses live in the creature list so all
hit / contact code treats them like other creatures."""
import math
import random

import pygame

from settings import *
from items import BAG_LOOT, ITEMS
from creatures import Creature
from physics import move_x, move_y, rect_solid

TS = TILE_SIZE

BOSS_INFO = {
    "eye": dict(name="血瞳巨眼", hp=1600, defense=8, dmg=20, size=(60, 44), bag="eye_bag"),
    "king_slime": dict(name="史莱姆之王", hp=1300, defense=6, dmg=24, size=(90, 60), bag="slime_bag"),
}


class Boss:
    is_boss = True

    def __init__(self, kind, x, y, game):
        info = BOSS_INFO[kind]
        self.kind = kind
        self.game = game
        self.world = game.world
        self.name = info["name"]
        self.w, self.h = info["size"]
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.hp = self.max_hp = info["hp"]
        self.t = {"dmg": info["dmg"], "defense": info["defense"], "drops": [], "ai": "boss",
                  "name": self.name}
        self.alive = True
        self.fled = False
        self.flash = 0
        self.anim = 0
        self.facing = 1

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def hit(self, damage, from_x, knockback):
        dealt = max(1, damage - self.t["defense"] // 2)
        self.hp -= dealt
        self.flash = 6
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return dealt

    def flee(self, message):
        self.fled = True
        self.alive = False
        self.game.announce(message, (200, 200, 255))

    def _tinted(self, img):
        if self.flash > 0:
            img = img.copy()
            img.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
        return img


class EyeBoss(Boss):
    def __init__(self, x, y, game):
        super().__init__("eye", x, y, game)
        self.state = "hover"
        self.timer = 120
        self.dashes = 0
        self.spawn_timer = 90
        self.phase = 1
        self.angle = 0.0

    def update(self, player):
        self.anim += 1
        if self.flash:
            self.flash -= 1
        if not player.alive:
            self.flee(f"{self.name} 离开了……")
            return
        if not self.game.is_night():
            self.flee(f"{self.name} 在黎明前逃走了")
            return
        if self.phase == 1 and self.hp < self.max_hp * 0.5:
            self.phase = 2
            self.t["dmg"] = 28
            self.t["defense"] = 2
            self.game.announce(f"{self.name} 张开了血盆大口！", (255, 90, 90))
            self.game.burst(*self.center(), (200, 40, 40), 30, speed=5)
        px, py = player.center()
        cx, cy = self.center()
        if self.state == "hover":
            tx, ty = px - cx, py - 220 - cy
            dist = max(1.0, math.hypot(tx, ty))
            speed = 5.0 if self.phase == 1 else 6.5
            self.vx += (tx / dist * speed - self.vx) * 0.06
            self.vy += (ty / dist * speed - self.vy) * 0.06
            self.angle = math.atan2(py - cy, px - cx)
            self.timer -= 1
            if self.phase == 1:
                self.spawn_timer -= 1
                minions = sum(1 for c in self.game.creatures.creatures if c.kind == "servant_eye")
                if self.spawn_timer <= 0 and minions < 5:
                    self.spawn_timer = 100
                    self.game.creatures.creatures.append(Creature("servant_eye", cx, cy, self.world))
            if self.timer <= 0:
                self.state = "dash"
                self.dashes = 3 if self.phase == 1 else 5
                self._start_dash(px, py)
        elif self.state == "dash":
            self.timer -= 1
            if self.timer < 14:
                self.vx *= 0.9
                self.vy *= 0.9
            if self.timer <= 0:
                self.dashes -= 1
                if self.dashes > 0:
                    self._start_dash(px, py)
                else:
                    self.state = "hover"
                    self.timer = 150 if self.phase == 1 else 100
        self.x += self.vx
        self.y += self.vy

    def _start_dash(self, px, py):
        cx, cy = self.center()
        a = math.atan2(py - cy, px - cx)
        speed = 10.0 if self.phase == 1 else 13.0
        self.vx, self.vy = math.cos(a) * speed, math.sin(a) * speed
        self.angle = a
        self.timer = 42 if self.phase == 1 else 34

    def draw(self, surf, cam, assets):
        frames = assets.bosses["eye"][self.phase]
        img = self._tinted(frames[(self.anim // 8) % 2][0])
        rot = pygame.transform.rotate(img, -math.degrees(self.angle))
        sx, sy = cam.apply(*self.center())
        surf.blit(rot, (sx - rot.get_width() / 2, sy - rot.get_height() / 2))


class KingSlime(Boss):
    def __init__(self, x, y, game):
        super().__init__("king_slime", x, y, game)
        self.timer = 60
        self.on_ground = False
        self.next_split = 0.9
        self.teleport = 0
        self.stuck = 0

    def hit(self, damage, from_x, knockback):
        dealt = super().hit(damage, from_x, knockback)
        while self.alive and self.hp < self.max_hp * self.next_split:
            self.next_split -= 0.08
            cx, cy = self.center()
            kind = random.choice(("blue_slime", "green_slime"))
            self.game.creatures.creatures.append(
                Creature(kind, cx + random.randint(-30, 30), self.y + self.h - 24, self.world))
        return dealt

    def update(self, player):
        self.anim += 1
        if self.flash:
            self.flash -= 1
        if not player.alive:
            self.flee(f"{self.name} 离开了……")
            return
        px, py = player.center()
        cx, cy = self.center()
        if self.teleport > 0:
            self.teleport -= 1
            if self.teleport == 30:
                self._teleport_near(player)
            return
        if math.hypot(px - cx, py - cy) > 60 * TS or self.stuck > 300:
            self.teleport = 60
            self.stuck = 0
            return
        if rect_solid(self.world, self.x, self.y, self.w, self.h, creature=True):
            # embedded in terrain after a cramped teleport: drift toward the player until free
            d = max(1.0, math.hypot(px - cx, py - cy))
            self.x += (px - cx) / d * 2.5
            self.y += (py - cy) / d * 2.5
            self.on_ground = False
            return
        if self.on_ground:
            self.vx *= 0.8
            self.timer -= 1
            if self.timer <= 0:
                big = random.random() < 0.35
                self.vy = -12.5 if big else -8.5
                self.vx = (1 if px > cx else -1) * (4.5 if big else 3.0)
                self.facing = 1 if self.vx > 0 else -1
                self.timer = random.randint(40, 70)
        self.vy = min(self.vy + 0.4, 12)
        old = (self.x, self.y)
        self.x, blocked = move_x(self.world, self.x, self.y, self.w, self.h, self.vx, creature=True)
        if blocked:
            self.vx = -self.vx * 0.3
        self.y, landed, ceil = move_y(self.world, self.x, self.y, self.w, self.h, self.vy, creature=True)
        if landed or ceil:
            self.vy = 0.0
        self.on_ground = landed
        self.stuck = self.stuck + 1 if abs(self.x - old[0]) + abs(self.y - old[1]) < 0.5 else 0

    def _teleport_near(self, player):
        """Land on open ground near the player; if there is none, drop onto the player and
        phase through terrain until free (see update)."""
        ptx = int(player.center()[0]) // TS
        pty = int(player.y + player.H) // TS
        tw, th = -(-self.w // TS), -(-self.h // TS)
        spot = None
        for dist in range(4, 30):
            for side in random.sample((-1, 1), 2):
                tx = ptx + side * dist
                for ty in range(pty - 12, pty + 13):
                    x, y = tx * TS, (ty - th) * TS
                    if not rect_solid(self.world, x, y, self.w, self.h, creature=True) and \
                            all(self.world.blocks_creature(tx + dx, ty) for dx in range(tw)):
                        spot = (x, y)
                        break
                if spot:
                    break
            if spot:
                break
        if spot is None:
            spot = (player.center()[0] - self.w / 2, player.y + player.H - self.h)
        self.x, self.y = spot
        self.vx = self.vy = 0.0
        self.game.burst(*self.center(), (90, 150, 255), 25, speed=4)

    def draw(self, surf, cam, assets):
        frames = assets.bosses["king_slime"]
        squish = self.on_ground and self.timer < 12
        img = self._tinted(frames[1 if squish else 0][0])
        if self.teleport > 0:
            k = abs(self.teleport - 30) / 30
            img = pygame.transform.scale(img, (max(1, int(img.get_width() * k)), max(1, int(img.get_height() * k))))
        sx, sy = cam.apply(self.x, self.y)
        surf.blit(img, (sx + (self.w - img.get_width()) / 2, sy + self.h - img.get_height()))


class BossManager:
    def __init__(self, game):
        self.game = game
        self.pending = None   # (kind, frames until spawn)

    def active(self):
        return next((c for c in self.game.creatures.creatures if getattr(c, "is_boss", False)), None)

    def summon(self, kind, delay=0, message=None):
        if self.active() or self.pending:
            return False
        if message:
            self.game.announce(message, (255, 120, 120))
        self.pending = (kind, delay)
        return True

    def update(self):
        if self.pending:
            kind, delay = self.pending
            if delay > 0:
                self.pending = (kind, delay - 1)
            else:
                self.pending = None
                self._spawn(kind)

    def _spawn(self, kind):
        g = self.game
        p = g.player
        if not p.alive:
            return
        px, py = p.center()
        if kind == "eye":
            boss = EyeBoss(px + random.choice((-1, 1)) * 500, py - 400, g)
        else:
            boss = KingSlime(px + random.choice((-1, 1)) * 300, py - 300, g)
            boss._teleport_near(p)
        g.creatures.creatures.append(boss)
        g.announce(f"{boss.name} 已苏醒！", (255, 80, 80))

    def on_defeat(self, boss):
        g = self.game
        cx, cy = boss.center()
        g.world.flags[f"{boss.kind}_defeated"] = True
        g.announce(f"{boss.name} 已被打败！", (120, 255, 140))
        g.burst(cx, cy, (230, 230, 230), 40, speed=6)
        g.drop_item_at(BOSS_INFO[boss.kind]["bag"], 1, cx, cy)
        g.drop_item_at("healing_potion", random.randint(3, 6), cx, cy)
        if boss.kind == "eye":
            for c in g.creatures.creatures:
                if c.kind == "servant_eye":
                    c.alive = False
        if boss.kind == "king_slime":
            g.creatures.slime_rain = False

    def draw_bar(self, surf):
        boss = self.active()
        if not boss:
            return
        from ui import draw_text
        w = 420
        x = (SCREEN_WIDTH - w) // 2
        y = SCREEN_HEIGHT - 58
        pygame.draw.rect(surf, (40, 0, 0), (x, y, w, 16), border_radius=4)
        pygame.draw.rect(surf, (220, 40, 50), (x, y, int(w * boss.hp / boss.max_hp), 16), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255), (x, y, w, 16), 1, border_radius=4)
        draw_text(surf, f"{boss.name}  {boss.hp}/{boss.max_hp}", (SCREEN_WIDTH // 2, y + 8), 14, center=True)


def open_bag(game, bag):
    for name, lo, hi, chance in BAG_LOOT[bag]:
        if random.random() < chance:
            count = random.randint(lo, hi)
            left = game.player.inventory.add(name, count)
            if left:
                game.drop_item(name, left)
            game.add_text(f"+{count} {ITEMS[name].display}", (255, 240, 150))
