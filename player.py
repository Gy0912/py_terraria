import math

import pygame

from settings import *
from tiles import T
from items import STARTING_ITEMS
from inventory import Inventory
from physics import move_x, move_y, rect_solid, rect_touches

TS = TILE_SIZE
_WATER = {T["water"]}
_LAVA = {T["lava"]}
FALL_SAFE_TILES = 12


class Player:
    W = 24
    H = 44

    def __init__(self, world):
        self.world = world
        self.inventory = Inventory()
        for name, count in STARTING_ITEMS:
            self.inventory.add(name, count)
        self.max_hp = 100
        self.max_mana = 40
        self.facing = 1
        self.anim = 0.0
        self.respawn()

    # -------------------- lifecycle --------------------

    def respawn(self):
        tx = self.world.spawn_tx
        ty = self.world.spawn_ty
        # stand on top of the first solid tile at the spawn column
        while self.world.is_solid(tx, ty - 1) and ty > 0:
            ty -= 1
        self.x = float(tx * TS + (TS - self.W) / 2)
        self.y = float(ty * TS - self.H)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.fall_peak = self.y
        self.hp = self.max_hp
        self.mana = self.max_mana
        self.alive = True
        self.invuln = 90
        self.knockback_timer = 0
        self.regen_delay = 0
        self.regen_tick = 0
        self.mana_tick = 0
        self.pending_damage = 0
        self.in_water = False
        # item use state
        self.use_timer = 0
        self.use_total = 1
        self.use_item = None
        self.swing_hits = set()
        self.aim_angle = 0.0
        self.heal_cd = 0

    def center(self):
        return self.x + self.W / 2, self.y + self.H / 2

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    # -------------------- damage / healing --------------------

    def hurt(self, amount, from_x=None):
        """Apply damage unless invulnerable. Returns damage dealt."""
        if not self.alive or self.invuln > 0 or amount <= 0:
            return 0
        self.hp -= amount
        self.invuln = 40
        self.regen_delay = FPS * 5
        if from_x is not None:
            d = 1 if self.center()[0] >= from_x else -1
            self.vx = d * 5
            self.vy = -4.5
            self.knockback_timer = 12
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return amount

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    # -------------------- update --------------------

    def update(self, keys):
        if not self.alive:
            return
        world = self.world
        self.in_water = rect_touches(world, self.x, self.y + self.H * 0.4, self.W, self.H * 0.6, _WATER)

        move = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - \
               (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        jump = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]

        # horizontal
        speed = 2.2 if self.in_water else 3.4
        if self.knockback_timer > 0:
            self.knockback_timer -= 1
        elif move:
            accel = 0.4 if self.on_ground else 0.28
            self.vx += max(-accel, min(accel, move * speed - self.vx))
            if self.use_timer == 0:
                self.facing = move
        else:
            self.vx *= 0.72 if self.on_ground else 0.94
            if abs(self.vx) < 0.05:
                self.vx = 0.0

        # vertical
        if jump and self.on_ground:
            self.vy = -10.5
            self.on_ground = False
        elif jump and self.in_water:
            self.vy = max(self.vy - 0.9, -4.5)
        g = 0.26 if (jump and self.vy < 0) else 0.45
        max_fall = 14.0
        if self.in_water:
            g *= 0.35
            max_fall = 3.5
        self.vy = min(self.vy + g, max_fall)

        # move x, stepping up single-tile ledges like Terraria
        old_x = self.x
        self.x, blocked = move_x(world, self.x, self.y, self.W, self.H, self.vx)
        if blocked and self.on_ground and move != 0:
            tx = old_x + self.vx
            if not rect_solid(world, tx, self.y - TS, self.W, self.H):
                self.x = tx
                self.y -= TS
                blocked = False
        if blocked:
            self.vx = 0.0
        self.x = max(0.0, min(self.x, MAP_WIDTH - self.W))

        # move y
        was_on_ground = self.on_ground
        self.y, landed, ceil = move_y(world, self.x, self.y, self.W, self.H, self.vy)
        if landed:
            if not was_on_ground and not self.in_water:
                fall_tiles = (self.y - self.fall_peak) / TS
                if fall_tiles > FALL_SAFE_TILES:
                    self.pending_damage += int((fall_tiles - FALL_SAFE_TILES) * 3)
            self.on_ground = True
            self.vy = 0.0
        else:
            self.on_ground = False
            if ceil:
                self.vy = 0.0
        # the fall height is measured from the highest point since we last stood on something
        if self.on_ground or self.in_water:
            self.fall_peak = self.y
        else:
            self.fall_peak = min(self.fall_peak, self.y)

        if rect_touches(world, self.x, self.y, self.W, self.H, _LAVA):
            self.pending_damage = max(self.pending_damage, 40)

        # animation
        if self.on_ground and abs(self.vx) > 0.3:
            self.anim += abs(self.vx) * 0.06
        else:
            self.anim = 0.0

        # timers and regeneration
        if self.invuln > 0:
            self.invuln -= 1
        if self.heal_cd > 0:
            self.heal_cd -= 1
        if self.regen_delay > 0:
            self.regen_delay -= 1
        else:
            self.regen_tick += 1
            if self.regen_tick >= 30 and self.hp < self.max_hp:
                self.regen_tick = 0
                self.hp += 1
        self.mana_tick += 1
        if self.mana_tick >= 12 and self.mana < self.max_mana:
            self.mana_tick = 0
            self.mana += 1

    def take_pending_damage(self):
        dmg = self.pending_damage
        self.pending_damage = 0
        if dmg > 0:
            invuln = self.invuln
            self.invuln = 0
            dealt = self.hurt(dmg)
            if self.alive:
                self.invuln = max(invuln, 30)
            return dealt
        return 0

    # -------------------- draw --------------------

    def frame(self):
        if not self.on_ground and not self.in_water:
            return "jump"
        if abs(self.vx) > 0.3:
            return int(self.anim) % 4
        return "idle"

    def draw(self, surf, cam, assets):
        if not self.alive:
            return
        if self.invuln > 0 and (self.invuln // 4) % 2 == 0:
            return
        right, left = assets.player[self.frame()]
        img = right if self.facing > 0 else left
        sx, sy = cam.apply(self.x, self.y)
        surf.blit(img, (sx + (self.W - img.get_width()) / 2, sy + self.H - img.get_height()))
        if self.use_item and self.use_timer > 0:
            self._draw_held(surf, cam, assets)

    def swing_angle(self):
        """Rotation (degrees, CCW) of the held item for the current swing frame."""
        progress = 1 - self.use_timer / self.use_total
        return 80 - 190 * progress

    def _draw_held(self, surf, cam, assets):
        from items import ITEMS
        it = ITEMS[self.use_item]
        icon = assets.icons[self.use_item]
        size = max(28, it.reach) if it.kind in ("tool", "weapon") else 28
        icon = pygame.transform.scale(icon, (size, size))
        cx, cy = self.center()
        shoulder = (cx + self.facing * 2, cy - 6)
        if it.kind in ("ranged", "magic"):
            angle = -math.degrees(self.aim_angle) - 45 if self.facing > 0 else \
                -math.degrees(self.aim_angle) + 225
        else:
            angle = self.swing_angle()
        canvas = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        if self.facing > 0:
            canvas.blit(icon, (size, 0))
            rot = pygame.transform.rotate(canvas, angle)
        else:
            canvas.blit(pygame.transform.flip(icon, True, False), (0, 0))
            rot = pygame.transform.rotate(canvas, -angle if it.kind not in ("ranged", "magic") else angle)
        sx, sy = cam.apply(*shoulder)
        surf.blit(rot, (sx - rot.get_width() / 2, sy - rot.get_height() / 2))
