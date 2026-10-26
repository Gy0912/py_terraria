"""Lightweight world entities: dropped items, projectiles, particles and floating text."""
import math
import random

import pygame

from settings import *
from items import ITEMS
from physics import move_x, move_y, rect_solid


class ItemDrop:
    W = H = 16

    def __init__(self, name, count, x, y, vx=None, vy=None, pickup_delay=20):
        self.name = name
        self.count = count
        self.x = x - self.W / 2
        self.y = y - self.H / 2
        self.vx = random.uniform(-1.5, 1.5) if vx is None else vx
        self.vy = random.uniform(-3.5, -2.0) if vy is None else vy
        self.pickup_delay = pickup_delay
        self.age = 0
        self.alive = True
        self.magnet = False

    def center(self):
        return self.x + self.W / 2, self.y + self.H / 2

    def update(self, world, player):
        self.age += 1
        if self.pickup_delay > 0:
            self.pickup_delay -= 1
        if self.age > FPS * 300:
            self.alive = False
            return
        px, py = player.center()
        cx, cy = self.center()
        dist = math.hypot(px - cx, py - cy)
        radius = MAGNET_RADIUS * player.stats["magnet"]
        self.magnet = (player.alive and self.pickup_delay == 0 and dist < radius
                       and player.inventory.can_accept(self.name))
        if self.magnet:
            # fly straight to the player, ignoring tiles
            speed = min(9.0, 2.0 + (radius - dist) * 0.08)
            self.vx += ((px - cx) / max(dist, 1) * speed - self.vx) * 0.3
            self.vy += ((py - cy) / max(dist, 1) * speed - self.vy) * 0.3
            self.x += self.vx
            self.y += self.vy
            return
        self.vy = min(self.vy + 0.3, 8)
        self.x, blocked = move_x(world, self.x, self.y, self.W, self.H, self.vx)
        if blocked:
            self.vx = 0
        self.y, landed, ceil = move_y(world, self.x, self.y, self.W, self.H, self.vy)
        if landed:
            self.vy = 0
            self.vx *= 0.8
        elif ceil:
            self.vy = 0

    def draw(self, surf, cam, assets):
        icon = assets.icons_small.get(self.name)
        bob = math.sin(self.age * 0.08) * 2 if not self.magnet else 0
        sx, sy = cam.apply(self.x - 2, self.y - 4 + bob)
        surf.blit(icon, (sx, sy))


class Projectile:
    def __init__(self, kind, x, y, vx, vy, damage, knockback):
        self.kind = kind
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.knockback = knockback
        self.life = 180
        self.alive = True
        self.size = 6 if kind == "arrow" else 10

    def rect(self):
        h = self.size / 2
        return pygame.Rect(self.x - h, self.y - h, self.size, self.size)

    def update(self, world, game):
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        if self.kind == "arrow":
            self.vy = min(self.vy + 0.15, 12)
        else:
            if random.random() < 0.7:
                game.particles.append(Particle(self.x, self.y, random.uniform(-0.5, 0.5),
                                               random.uniform(-0.5, 0.5),
                                               random.choice(((255, 200, 60), (255, 120, 30))),
                                               life=18, gravity=0, size=3))
        self.x += self.vx
        self.y += self.vy
        h = self.size / 2
        if rect_solid(world, self.x - h, self.y - h, self.size, self.size):
            self.alive = False
            if self.kind == "arrow" and random.random() < 0.3:
                game.drops.append(ItemDrop("wood_arrow", 1, self.x - self.vx, self.y - self.vy, 0, 0))
            else:
                game.burst(self.x, self.y, (255, 150, 40) if self.kind == "bolt" else (170, 140, 100), 6)

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        if self.kind == "arrow":
            ang = math.atan2(self.vy, self.vx)
            dx, dy = math.cos(ang) * 10, math.sin(ang) * 10
            pygame.draw.line(surf, (140, 95, 50), (sx - dx, sy - dy), (sx + dx, sy + dy), 2)
            pygame.draw.circle(surf, (190, 190, 195), (int(sx + dx), int(sy + dy)), 2)
        else:
            pygame.draw.circle(surf, (255, 120, 30), (int(sx), int(sy)), 6)
            pygame.draw.circle(surf, (255, 230, 120), (int(sx), int(sy)), 3)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "life", "max_life", "gravity", "size")

    def __init__(self, x, y, vx, vy, color, life=30, gravity=0.25, size=4):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color = color
        self.life = self.max_life = life
        self.gravity = gravity
        self.size = size

    def update(self):
        self.life -= 1
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        s = max(1, int(self.size * self.life / self.max_life + 1))
        surf.fill(self.color, (sx, sy, s, s))


class FloatingText:
    def __init__(self, text, x, y, color, font):
        self.surf = font.render(text, True, color)
        self.shadow = font.render(text, True, (0, 0, 0))
        self.x, self.y = x - self.surf.get_width() / 2, y
        self.life = 60

    def update(self):
        self.life -= 1
        self.y -= 0.7

    def draw(self, surf, cam):
        sx, sy = cam.apply(self.x, self.y)
        alpha = min(255, self.life * 8)
        self.surf.set_alpha(alpha)
        self.shadow.set_alpha(alpha)
        surf.blit(self.shadow, (sx + 1, sy + 1))
        surf.blit(self.surf, (sx, sy))
