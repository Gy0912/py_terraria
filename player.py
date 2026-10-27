import math

import pygame

from settings import *
from tiles import T, STICKY
from items import ITEMS, STARTING_ITEMS
from inventory import Inventory
from physics import move_x, move_y, rect_solid, rect_liquid, point_in_liquid, rect_touches

TS = TILE_SIZE
_WATER, _LAVA = T["water"], T["lava"]
EQUIP_SLOTS = ("head", "body", "legs", "acc0", "acc1", "acc2", "acc3", "acc4")

WALK_SPEED = 3.0
JUMP_SPEED = 7.2          # about 5.5 tiles with the jump key held
GRAVITY = 0.42
GRAVITY_HELD = 0.28
LAVA_HIT = 25
BURN_FRAMES = FPS * 7


class Player:
    W = 24
    H = 44

    def __init__(self, world):
        self.world = world
        self.inventory = Inventory()
        for name, count in STARTING_ITEMS:
            self.inventory.add(name, count)
        self.equip = {slot: None for slot in EQUIP_SLOTS}
        self.max_hp = 100
        self.base_max_mana = 40
        self.spawn_point = None   # bed anchor, if any
        self.cards = []           # card collection used as the deck in NPC card games
        self.journal = set()      # lore note ids that have been read
        self.facing = 1
        self.anim = 0.0
        self.recompute_stats()
        self.respawn()

    # -------------------- equipment --------------------

    def recompute_stats(self):
        st = {"defense": 0, "speed": 0.0, "jump": 0.0, "double_jump": 0, "breath": 1, "lava_immune": 0,
              "fall_immune": 0, "regen": 0, "magnet": 1.0, "luck": 0.0, "mana": 0, "light": 0, "kb_immune": 0,
              "mining": 0.0}
        for slot, name in self.equip.items():
            if not name:
                continue
            it = ITEMS[name]
            st["defense"] += it.defense
            for key, val in it.effects.items():
                if key in ("breath", "magnet"):
                    st[key] = max(st[key], val)
                else:
                    st[key] += val
        self.stats = st
        self.defense = st["defense"]
        self.max_mana = min(200, self.base_max_mana + st["mana"])
        self.breath_max = BREATH_MAX * st["breath"]
        if hasattr(self, "mana"):
            self.mana = min(self.mana, self.max_mana)
            self.breath = min(self.breath, self.breath_max)

    def can_equip(self, slot, name):
        if name is None:
            return True
        it = ITEMS[name]
        if slot.startswith("acc"):
            others = [n for s, n in self.equip.items() if s.startswith("acc") and s != slot]
            return it.slot == "accessory" and name not in others
        return it.slot == slot

    def look(self):
        return self.equip["head"], self.equip["body"], self.equip["legs"]

    # -------------------- lifecycle --------------------

    def spawn_tile(self):
        if self.spawn_point and self.world.objects.get(self.spawn_point) == T["bed"]:
            ax, ay = self.spawn_point
            return ax + 1, ay + 2
        self.spawn_point = None
        tx, ty = self.world.spawn_tx, self.world.spawn_ty
        while self.world.is_solid(tx, ty - 1) and ty > 0:
            ty -= 1
        return tx, ty

    def respawn(self):
        tx, ty = self.spawn_tile()
        self.x = float(tx * TS + (TS - self.W) / 2)
        self.y = float(ty * TS - self.H)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.fall_peak = self.y
        self.hp = self.max_hp
        self.mana = self.max_mana
        self.breath = self.breath_max
        self.alive = True
        self.invuln = 90
        self.knockback_timer = 0
        self.regen_delay = 0
        self.regen_tick = 0
        self.mana_tick = 0
        self.pending_damage = 0
        self.pending_invuln = 0
        self.dot_tick = 0
        self.burning = 0
        self.in_water = False
        self.in_lava = False
        self.head_under = False
        self.jump_held = False
        self.double_jump_ready = False
        self.double_jumped = False
        self.use_timer = 0
        self.use_total = 1
        self.use_item = None
        self.swing_hits = set()
        self.aim_angle = 0.0
        self.heal_cd = 0

    def teleport(self, tx, ty):
        self.x = float(tx * TS + (TS - self.W) / 2)
        self.y = float(ty * TS - self.H)
        self.vx = self.vy = 0.0
        self.fall_peak = self.y

    def center(self):
        return self.x + self.W / 2, self.y + self.H / 2

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    # -------------------- damage / healing --------------------

    def hurt(self, amount, from_x=None, ignore_defense=False):
        """Apply damage unless invulnerable. Returns damage dealt."""
        if not self.alive or self.invuln > 0 or amount <= 0:
            return 0
        if not ignore_defense:
            amount = max(1, amount - self.defense // 2)
        self.hp -= amount
        self.invuln = 40
        self.regen_delay = FPS * 5
        if from_x is not None and not self.stats["kb_immune"]:
            d = 1 if self.center()[0] >= from_x else -1
            self.vx = d * 5
            self.vy = -4.0
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
        st = self.stats
        self.in_water = rect_liquid(world, self.x, self.y + self.H * 0.4, self.W, self.H * 0.6, _WATER)
        self.in_lava = rect_liquid(world, self.x, self.y + self.H * 0.3, self.W, self.H * 0.7, _LAVA)
        self.head_under = point_in_liquid(world, self.x + self.W / 2, self.y + 8, _WATER)
        swimming = self.in_water or self.in_lava
        webbed = rect_touches(world, self.x, self.y, self.W, self.H, STICKY)

        move = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - \
               (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        jump = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        jump_pressed = jump and not self.jump_held
        self.jump_held = jump

        # horizontal
        speed = WALK_SPEED * (1 + st["speed"])
        if self.in_lava:
            speed *= 0.5
        elif self.in_water:
            speed *= 0.65
        if self.knockback_timer > 0:
            self.knockback_timer -= 1
        elif move:
            accel = 0.38 if self.on_ground else 0.26
            self.vx += max(-accel, min(accel, move * speed - self.vx))
            if self.use_timer == 0:
                self.facing = move
        else:
            self.vx *= 0.72 if self.on_ground else 0.94
            if abs(self.vx) < 0.05:
                self.vx = 0.0

        # vertical
        jump_v = JUMP_SPEED * (1 + st["jump"])
        if self.on_ground:
            self.double_jump_ready = bool(st["double_jump"])
            self.double_jumped = False
        if jump and self.on_ground:
            self.vy = -jump_v
            self.on_ground = False
        elif jump and swimming:
            self.vy = max(self.vy - 0.8, -4.0)
        elif jump_pressed and self.double_jump_ready:
            self.vy = -jump_v * 0.95
            self.double_jump_ready = False
            self.double_jumped = True
            self.fall_peak = self.y
        g = GRAVITY_HELD if (jump and self.vy < 0) else GRAVITY
        max_fall = 12.0
        if swimming:
            g *= 0.35
            max_fall = 3.0
        self.vy = min(self.vy + g, max_fall)
        if webbed:
            self.vx *= 0.35
            self.vy = max(-1.5, min(self.vy, 1.0))
            self.fall_peak = self.y

        # move x, stepping up single-tile ledges
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
            if not was_on_ground and not swimming and not st["fall_immune"]:
                fall_tiles = (self.y - self.fall_peak) / TS
                if fall_tiles > FALL_SAFE_TILES:
                    self.pending_damage += int((fall_tiles - FALL_SAFE_TILES) * 2)
            self.on_ground = True
            self.vy = 0.0
        else:
            self.on_ground = False
            if ceil:
                self.vy = 0.0
        if self.on_ground or swimming:
            self.fall_peak = self.y
        else:
            self.fall_peak = min(self.fall_peak, self.y)

        self._environment()

        if self.on_ground and abs(self.vx) > 0.3:
            self.anim += abs(self.vx) * 0.07
        else:
            self.anim = 0.0

        if self.invuln > 0:
            self.invuln -= 1
        if self.heal_cd > 0:
            self.heal_cd -= 1
        if self.regen_delay > 0:
            self.regen_delay -= 1 + st["regen"]
        else:
            self.regen_tick += 1 + st["regen"]
            if self.regen_tick >= 30 and self.hp < self.max_hp:
                self.regen_tick = 0
                self.hp += 1
        self.mana_tick += 1
        if self.mana_tick >= 12 and self.mana < self.max_mana:
            self.mana_tick = 0
            self.mana += 1

    def _environment(self):
        """Breath under water, lava contact and burning."""
        st = self.stats
        if self.head_under:
            self.breath = max(0, self.breath - 1)
        else:
            self.breath = min(self.breath_max, self.breath + 6)
        lava_ok = st["lava_immune"]
        if self.in_lava and not lava_ok:
            self.burning = BURN_FRAMES
            if self.invuln == 0:
                self.pending_damage += LAVA_HIT
                self.pending_invuln = 40
        if lava_ok:
            self.burning = 0
        elif self.burning > 0:
            self.burning -= 1
        self.dot_tick += 1
        if self.dot_tick >= 30:
            self.dot_tick = 0
            if self.breath == 0:
                self.pending_damage += 6
            if self.burning > 0:
                self.pending_damage += 4

    def take_pending_damage(self):
        dmg = self.pending_damage
        after = self.pending_invuln or 20
        self.pending_damage = 0
        self.pending_invuln = 0
        if dmg > 0:
            invuln = self.invuln
            self.invuln = 0
            dealt = self.hurt(dmg, ignore_defense=True)
            if self.alive:
                self.invuln = max(invuln, after)
            return dealt
        return 0

    # -------------------- draw --------------------

    def frame(self):
        if not self.on_ground and not (self.in_water or self.in_lava):
            return "jump"
        if abs(self.vx) > 0.3:
            return int(self.anim) % 4
        return "idle"

    def draw(self, surf, cam, assets):
        if not self.alive:
            return
        if self.invuln > 0 and (self.invuln // 4) % 2 == 0:
            return
        right, left = assets.player_look(*self.look())[self.frame()]
        img = right if self.facing > 0 else left
        if self.burning > 0 and (self.burning // 5) % 2 == 0:
            img = img.copy()
            img.fill((90, 30, 0), special_flags=pygame.BLEND_RGB_ADD)
        sx, sy = cam.apply(self.x, self.y)
        surf.blit(img, (sx + (self.W - img.get_width()) / 2, sy + self.H - img.get_height()))
        if self.use_item and self.use_timer > 0:
            self._draw_held(surf, cam, assets)
        if self.breath < self.breath_max:
            bubbles = math.ceil(self.breath / self.breath_max * 10)
            for i in range(10):
                bx = sx + self.W / 2 - 45 + i * 9
                if i < bubbles:
                    pygame.draw.circle(surf, (170, 220, 255), (int(bx), int(sy - 12)), 4)
                    pygame.draw.circle(surf, (255, 255, 255), (int(bx) - 1, int(sy - 13)), 1)
                else:
                    pygame.draw.circle(surf, (90, 110, 140), (int(bx), int(sy - 12)), 4, 1)

    def swing_angle(self):
        """Rotation (degrees, CCW) of the held item for the current swing frame."""
        progress = 1 - self.use_timer / self.use_total
        return 80 - 190 * progress

    def _draw_held(self, surf, cam, assets):
        it = ITEMS[self.use_item]
        icon = assets.icons[self.use_item]
        size = max(28, it.reach) if it.kind in ("tool", "weapon") else 26
        icon = pygame.transform.scale(icon, (size, size))
        cx, cy = self.center()
        shoulder = (cx + self.facing * 2, cy - 6)
        aimed = it.kind in ("ranged", "magic")
        if aimed:
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
            rot = pygame.transform.rotate(canvas, angle if aimed else -angle)
        sx, sy = cam.apply(*shoulder)
        surf.blit(rot, (sx - rot.get_width() / 2, sy - rot.get_height() / 2))
