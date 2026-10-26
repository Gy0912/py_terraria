import pygame
import random
from settings import *


class Creature:
    """A basic enemy that walks on the surface and damages the player on contact."""

    def __init__(self, x, y, world):
        self.x = float(x)
        self.y = float(y)
        self.width = 28
        self.height = 32
        self.color = (200, 40, 40)
        self.world = world

        self.vx = random.choice([-1.5, 1.5])
        self.vy = 0.0
        self.gravity = 0.5
        self.max_fall = 10.0
        self.on_ground = False

        self.hp = 30
        self.damage = 8
        self.alive = True

        self.direction_timer = 0
        self.direction_interval = random.randint(60, 180)

    def _get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def _collides(self, rect):
        left_tx = int(rect.left) // TILE_SIZE
        right_tx = int(rect.right - 1) // TILE_SIZE
        top_ty = int(rect.top) // TILE_SIZE
        bottom_ty = int(rect.bottom - 1) // TILE_SIZE
        for tx in range(left_tx, right_tx + 1):
            for ty in range(top_ty, bottom_ty + 1):
                if self.world.get_tile(tx, ty) is not None:
                    return True
        return False

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def update(self):
        if not self.alive:
            return

        self.direction_timer += 1
        if self.direction_timer >= self.direction_interval:
            self.vx = -self.vx
            self.direction_timer = 0
            self.direction_interval = random.randint(60, 180)

        self.vy += self.gravity
        if self.vy > self.max_fall:
            self.vy = self.max_fall

        self.x += self.vx
        rect = self._get_rect()
        if self._collides(rect):
            self.x -= self.vx
            self.vx = -self.vx

        self.y += self.vy
        rect = self._get_rect()
        if self._collides(rect):
            if self.vy > 0:
                tile_ty = int(rect.bottom - 1) // TILE_SIZE
                self.y = tile_ty * TILE_SIZE - self.height
                self.on_ground = True
            else:
                tile_ty = int(rect.top) // TILE_SIZE
                self.y = (tile_ty + 1) * TILE_SIZE
            self.vy = 0
        else:
            self.on_ground = False

    def draw(self, surface, camera):
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        pygame.draw.rect(surface, self.color, (sx, sy, self.width, self.height))
        # HP bar above creature
        bar_w = self.width
        ratio = max(0, self.hp / 30)
        pygame.draw.rect(surface, (80, 0, 0), (sx, sy - 6, bar_w, 4))
        pygame.draw.rect(surface, RED, (sx, sy - 6, int(bar_w * ratio), 4))


class CreatureManager:
    """Manages spawning and updating creatures near the player."""

    def __init__(self, world):
        self.world = world
        self.creatures = []
        self.spawn_cooldown = 0
        self.max_creatures = 8

    def update(self, player_x, player_y):
        self.spawn_cooldown += 1
        if self.spawn_cooldown >= 300 and len(self.creatures) < self.max_creatures:
            self._try_spawn(player_x, player_y)
            self.spawn_cooldown = 0

        for c in self.creatures:
            c.update()

        self.creatures = [c for c in self.creatures if c.alive]

        # Despawn far creatures
        self.creatures = [
            c for c in self.creatures
            if abs(c.x - player_x) < SCREEN_WIDTH * 2
        ]

    def _try_spawn(self, player_x, player_y):
        offset = random.choice([-1, 1]) * random.randint(SCREEN_WIDTH // 2, SCREEN_WIDTH)
        spawn_x = player_x + offset
        spawn_tx = int(spawn_x) // TILE_SIZE
        if spawn_tx < 0 or spawn_tx >= ACTUAL_MAP_WIDTH:
            return

        surface_ty = self.world._surface_heights.get(spawn_tx)
        if surface_ty is None:
            return
        spawn_y = (surface_ty - 3) * TILE_SIZE
        self.creatures.append(Creature(spawn_x, spawn_y, self.world))

    def check_player_collision(self, player):
        prect = pygame.Rect(player.x, player.y, player.width, player.height)
        for c in self.creatures:
            if not c.alive:
                continue
            crect = c._get_rect()
            if prect.colliderect(crect):
                return c.damage
        return 0

    def draw(self, surface, camera):
        for c in self.creatures:
            c.draw(surface, camera)
