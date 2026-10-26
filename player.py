import pygame
from settings import *


class Player:
    def __init__(self, world):
        self.width = 24
        self.height = 48
        self.color = (0, 200, 80)

        self.world = world

        # spawn near centre of map, at ground surface
        spawn_tx = ACTUAL_MAP_WIDTH // 2
        spawn_ty = ACTUAL_GROUND_HEIGHT - 3
        self.x = float(spawn_tx * TILE_SIZE)
        self.y = float(spawn_ty * TILE_SIZE)

        self.vx = 0.0
        self.vy = 0.0

        self.speed = 4.0
        self.jump_power = -10.0
        self.gravity = 0.5
        self.max_fall = 12.0
        self.on_ground = False

        self.inventory = {}
        self.selected_block = "dirt"

    # ------------------------------------------------------------------
    # Collision helpers
    # ------------------------------------------------------------------

    def _get_rect(self, x=None, y=None):
        return pygame.Rect(x or self.x, y or self.y, self.width, self.height)

    def _collides_with_world(self, rect):
        """Check if *rect* overlaps any solid tile."""
        left_tx = int(rect.left) // TILE_SIZE
        right_tx = int(rect.right - 1) // TILE_SIZE
        top_ty = int(rect.top) // TILE_SIZE
        bottom_ty = int(rect.bottom - 1) // TILE_SIZE
        for tx in range(left_tx, right_tx + 1):
            for ty in range(top_ty, bottom_ty + 1):
                if self.world.get_tile(tx, ty) is not None:
                    return True
        return False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, keys):
        # Horizontal input
        self.vx = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = self.speed

        # Jump
        if self.on_ground and (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]):
            self.vy = self.jump_power
            self.on_ground = False

        # Gravity
        self.vy += self.gravity
        if self.vy > self.max_fall:
            self.vy = self.max_fall

        # Move X then resolve
        self.x += self.vx
        self._clamp_x()
        player_rect = self._get_rect()
        if self._collides_with_world(player_rect):
            # undo and nudge
            self.x -= self.vx
            player_rect = self._get_rect()

        # Move Y then resolve
        self.y += self.vy
        self._clamp_y()
        player_rect = self._get_rect()
        if self._collides_with_world(player_rect):
            if self.vy > 0:
                # snap to top of tile
                tile_ty = int(player_rect.bottom - 1) // TILE_SIZE
                self.y = tile_ty * TILE_SIZE - self.height
                self.on_ground = True
            else:
                tile_ty = int(player_rect.top) // TILE_SIZE
                self.y = (tile_ty + 1) * TILE_SIZE
            self.vy = 0
        else:
            self.on_ground = False

    def _clamp_x(self):
        self.x = max(0, min(self.x, MAP_WIDTH - self.width))

    def _clamp_y(self):
        self.y = max(0, min(self.y, MAP_HEIGHT - self.height))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface, camera):
        sx, sy = camera.apply(self.x, self.y)
        pygame.draw.rect(surface, self.color, (sx, sy, self.width, self.height))
