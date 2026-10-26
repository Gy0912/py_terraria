import math
import random

import pygame

from settings import *
from tiles import T
from items import ITEMS
from world import World
from player import Player
from camera import Camera
from background import Background
from creatures import CreatureManager
from inventory import InventoryUI
from entities import ItemDrop, Particle, FloatingText
from textures import Assets
from render import WorldRenderer
from lighting import Lighting
from minimap import Minimap
from healthbar import HealthBar
from manabar import ManaBar
from ui import get_font, draw_text, Button
import actions

STATION_IDS = {T["workbench"]: "workbench", T["furnace"]: "furnace", T["anvil"]: "anvil"}
CONTROLS = "A/D 移动  空格 跳跃  左键 使用物品  1-0/滚轮 切换  E 背包与制作  H 快速治疗  M 小地图缩放  Esc 暂停"


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.playing = False
        self.assets = Assets()
        self.assets.load()
        self.background = Background(self.screen)
        img = pygame.image.load(IMAGES_PATH["start_screen"]).convert()
        self.start_image = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.text_font = get_font(16, bold=True)
        self.health_bar = HealthBar()
        self.mana_bar = ManaBar()
        self.menu_buttons = [Button("开始游戏", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)),
                             Button("退出游戏", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))]

    # ------------------------------------------------------------------
    # Start screen
    # ------------------------------------------------------------------

    def show_start_screen(self):
        """Returns True to start a game, False to quit."""
        start_btn, quit_btn = self.menu_buttons
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or quit_btn.clicked(event):
                    self.running = False
                    return False
                if start_btn.clicked(event):
                    return True
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return True
            self.draw_start_screen()
            pygame.display.flip()

    def draw_start_screen(self):
        cx = SCREEN_WIDTH // 2
        self.screen.blit(self.start_image, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 20, 90))
        self.screen.blit(shade, (0, 0))
        draw_text(self.screen, f"{TITLE} · 2D 沙盒生存冒险", (cx, SCREEN_HEIGHT // 2 - 10), 26,
                  (255, 235, 140), center=True, bold=True)
        for b in self.menu_buttons:
            b.draw(self.screen)
        draw_text(self.screen, CONTROLS, (cx, SCREEN_HEIGHT - 40), 14, (220, 220, 220), center=True)
        draw_text(self.screen, f"Version {VERSION}", (SCREEN_WIDTH - 110, SCREEN_HEIGHT - 20), 13, (200, 200, 200))

    # ------------------------------------------------------------------
    # New game
    # ------------------------------------------------------------------

    def new(self):
        self.setup()
        self.run()

    def setup(self, seed=None):
        self.screen.fill(BLACK)
        draw_text(self.screen, "正在生成世界……", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 28, center=True)
        pygame.display.flip()

        self.world = World(random.randrange(1 << 30) if seed is None else seed)
        self.player = Player(self.world)
        self.camera = Camera()
        self.creatures = CreatureManager(self.world)
        self.inv_ui = InventoryUI(self.player.inventory, self.assets)
        self.renderer = WorldRenderer(self.world, self.assets)
        self.lighting = Lighting()
        self.minimap = Minimap(self.world, (SCREEN_WIDTH - 210, 54, 200, 140))
        self.drops = []
        self.projectiles = []
        self.particles = []
        self.texts = []
        self.notices = {}
        self.ticks = int(START_HOUR / 24 * DAY_LENGTH)
        self.state = "playing"
        self.mouse_blocked = False
        self.pause_buttons = [Button("继续游戏", (SCREEN_WIDTH // 2, 290)),
                              Button("返回主菜单", (SCREEN_WIDTH // 2, 360)),
                              Button("退出游戏", (SCREEN_WIDTH // 2, 430))]
        self.death_buttons = [Button("复活", (SCREEN_WIDTH // 2, 330)),
                              Button("返回主菜单", (SCREEN_WIDTH // 2, 400))]
        self.camera.update(*self.player.center())

    # ------------------------------------------------------------------
    # Time of day
    # ------------------------------------------------------------------

    def hour(self):
        return (self.ticks % DAY_LENGTH) / DAY_LENGTH * 24

    def is_night(self):
        h = self.hour()
        return h >= 19.5 or h < 4.5

    def daylight(self):
        h = self.hour()
        if 6 <= h < 18:
            return 1.0
        if 18 <= h < 19.5:
            return 1.0 - (h - 18) / 1.5 * 0.78
        if 4.5 <= h < 6:
            return 0.22 + (h - 4.5) / 1.5 * 0.78
        return 0.22

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            if not self.playing:
                break
            if self.state == "playing":
                self.update()
            self.draw()
            pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False
                return
            if self.state == "paused":
                self._pause_event(event)
                continue
            if self.state == "dead":
                self._death_event(event)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.inv_ui.open:
                        self.inv_ui.close(self)
                    else:
                        self.state = "paused"
                elif event.key in (pygame.K_e, pygame.K_TAB):
                    if self.inv_ui.open:
                        self.inv_ui.close(self)
                    else:
                        self.inv_ui.open = True
                elif event.key == pygame.K_h:
                    actions.quick_heal(self)
                elif event.key == pygame.K_m:
                    self.minimap.toggle_zoom()
                else:
                    self.inv_ui.handle_key(event.key)
            elif event.type == pygame.MOUSEWHEEL:
                self.inv_ui.handle_wheel(event.y, pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                if self.inv_ui.over_ui(event.pos):
                    self.inv_ui.handle_click(event.pos, event.button, self)
                    self.mouse_blocked = True
                elif self.inv_ui.cursor:
                    name, count = self.inv_ui.cursor
                    self.inv_ui.cursor = None
                    self.drop_item(name, count)
                    self.mouse_blocked = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_blocked = False

    def _pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "playing"
        resume, menu, quit_ = self.pause_buttons
        if resume.clicked(event):
            self.state = "playing"
        elif menu.clicked(event):
            self.playing = False
        elif quit_.clicked(event):
            self.playing = False
            self.running = False

    def _death_event(self, event):
        respawn, menu = self.death_buttons
        if respawn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            self.player.respawn()
            self.creatures.clear()
            self.state = "playing"
            self.mouse_blocked = True
        elif menu.clicked(event):
            self.playing = False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        self.ticks += 1
        p = self.player
        keys = pygame.key.get_pressed()

        mouse = pygame.mouse.get_pos()
        if (pygame.mouse.get_pressed()[0] and not self.mouse_blocked
                and not self.inv_ui.over_ui(mouse) and not self.inv_ui.cursor):
            actions.try_use(self)

        p.update(keys)
        dmg = p.take_pending_damage()
        if dmg:
            self.add_text(f"-{dmg}", (255, 80, 80))
        actions.update_use(self)

        self.creatures.update(p, self.is_night())
        if p.alive:
            for c in self.creatures.creatures:
                if c.rect().colliderect(p.rect()):
                    dealt = p.hurt(c.t["dmg"], c.center()[0])
                    if dealt:
                        self.add_text(f"-{dealt}", (255, 80, 80))
                        self.burst(*p.center(), (200, 30, 30), 6)
                    break

        for pr in self.projectiles:
            pr.update(self.world, self)
            if not pr.alive:
                continue
            r = pr.rect()
            for c in self.creatures.creatures:
                if c.alive and r.colliderect(c.rect()):
                    self.on_creature_hit(c, c.hit(pr.damage, pr.x - pr.vx, pr.knockback))
                    pr.alive = False
                    break
        self.projectiles = [pr for pr in self.projectiles if pr.alive]

        self._update_drops()

        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles if pt.life > 0][-500:]
        for t in self.texts:
            t.update()
        self.texts = [t for t in self.texts if t.life > 0]
        for key in list(self.notices):
            self.notices[key] -= 1
            if self.notices[key] <= 0:
                del self.notices[key]

        self.world.tick_damage()
        if self.ticks % 15 == 0:
            self.inv_ui.stations = self.nearby_stations()

        self.camera.update(*p.center())
        self.background.update(self.world.get_biome(*p.center()))
        self.minimap.update(p)

        if not p.alive:
            self.state = "dead"
            self.burst(*p.center(), (200, 30, 30), 30, speed=5)
            self.inv_ui.close(self)

    def _update_drops(self):
        p = self.player
        px, py = p.center()
        for d in self.drops:
            d.update(self.world, p)
            if not d.alive or d.pickup_delay > 0 or not p.alive:
                continue
            cx, cy = d.center()
            if math.hypot(px - cx, py - cy) < PICKUP_RADIUS:
                left = p.inventory.add(d.name, d.count)
                picked = d.count - left
                if picked:
                    self.add_text(f"+{picked} {ITEMS[d.name].display}", (255, 255, 255))
                d.count = left
                if left == 0:
                    d.alive = False
        self.drops = [d for d in self.drops if d.alive]

    def nearby_stations(self):
        cx, cy = self.player.center()
        tx, ty = int(cx) // TILE_SIZE, int(cy) // TILE_SIZE
        found = set()
        for y in range(ty - 3, ty + 4):
            for x in range(tx - 5, tx + 6):
                name = STATION_IDS.get(self.world.get_tile(x, y))
                if name:
                    found.add(name)
        return found

    # ------------------------------------------------------------------
    # Helpers used by actions / inventory
    # ------------------------------------------------------------------

    def on_creature_hit(self, c, dealt):
        cx, cy = c.center()
        self.add_text(str(dealt), (255, 210, 80), (cx, c.y - 10))
        self.burst(cx, cy, (200, 40, 40) if "slime" not in c.kind else (120, 200, 255), 5)
        if not c.alive:
            self.burst(cx, cy, (230, 230, 230), 14, speed=3.5)
            for name, lo, hi, chance in c.t["drops"]:
                if random.random() < chance:
                    self.drop_item_at(name, random.randint(lo, hi), cx, cy)

    def drop_item_at(self, name, count, x, y):
        if name and count > 0:
            self.drops.append(ItemDrop(name, count, x, y))

    def drop_item(self, name, count):
        """Throw an item from the player in the facing direction."""
        p = self.player
        cx, cy = p.center()
        self.drops.append(ItemDrop(name, count, cx + p.facing * 10, cy - 10,
                                   vx=p.facing * 4.0, vy=-3.0, pickup_delay=90))

    def burst(self, x, y, color, n, speed=2.5):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.5, speed)
            col = tuple(max(0, min(255, int(c * random.uniform(0.75, 1.15)))) for c in color[:3])
            self.particles.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v - 1.0, col,
                                           life=random.randint(18, 35)))

    def add_text(self, text, color, pos=None):
        if pos is None:
            cx, _ = self.player.center()
            pos = (cx, self.player.y - 12)
        self.texts.append(FloatingText(text, pos[0], pos[1], color, self.text_font))

    def notify(self, text):
        """Floating message above the player, throttled so holding the mouse doesn't spam it."""
        if text not in self.notices:
            self.notices[text] = 90
            self.add_text(text, (255, 220, 120))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        screen = self.screen
        cam = self.camera
        p = self.player
        screen.fill(BLACK)
        self.background.draw(p.x, p.y)
        self.renderer.draw(screen, cam)
        self.renderer.draw_cracks(screen, cam)
        for d in self.drops:
            d.draw(screen, cam, self.assets)
        self.creatures.draw(screen, cam, self.assets)
        for pr in self.projectiles:
            pr.draw(screen, cam)
        p.draw(screen, cam, self.assets)
        for pt in self.particles:
            pt.draw(screen, cam)

        lights = []
        if p.alive:
            lights.append((*p.center(), 4, 0.6))
        for pr in self.projectiles:
            if pr.kind == "bolt":
                lights.append((pr.x, pr.y, 4, 0.9))
        for c in self.creatures.creatures:
            if "light" in c.t:
                lights.append((*c.center(), *c.t["light"]))
        self.lighting.render(screen, self.world, cam, self.daylight(), lights)

        self._draw_cursor()
        for t in self.texts:
            t.draw(screen, cam)
        self._draw_hud()
        if self.state == "paused":
            self._draw_overlay("已暂停", (0, 0, 30, 160), self.pause_buttons)
            draw_text(screen, CONTROLS, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40), 14, center=True)
        elif self.state == "dead":
            self._draw_overlay("你死了", (60, 0, 0, 150), self.death_buttons, (255, 90, 90))

    def _draw_cursor(self):
        p = self.player
        item = self.inv_ui.selected_item()
        if not p.alive or not item or ITEMS[item].kind not in ("tool", "block") or self.inv_ui.over_ui(
                pygame.mouse.get_pos()):
            return
        wx, wy = actions.mouse_world(self)
        tx, ty = int(wx) // TILE_SIZE, int(wy) // TILE_SIZE
        if actions.in_reach(p, tx, ty):
            sx, sy = self.camera.apply(tx * TILE_SIZE, ty * TILE_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 255), (sx, sy, TILE_SIZE, TILE_SIZE), 1)

    def _draw_hud(self):
        screen = self.screen
        p = self.player
        self.health_bar.draw(screen, p.hp, p.max_hp)
        self.mana_bar.draw(screen, p.mana, p.max_mana)
        self.minimap.draw(screen, p, self.creatures.creatures)

        cx, cy = p.center()
        tx, ty = int(cx) // TILE_SIZE, int(cy) // TILE_SIZE
        layer = self.world.layer_at(tx, ty)
        if layer in ("space", "hell"):
            place = LAYER_NAMES[layer]
        else:
            place = f"{BIOME_NAMES[self.world.biome_at(tx, ty)]} · {LAYER_NAMES[layer]}"
        h = self.hour()
        clock = f"{int(h):02d}:{int(h % 1 * 60):02d} {'夜晚' if self.is_night() else '白天'}"
        info = (f"{place}   坐标 {tx}  深度 {ty - SURFACE_LEVEL}   {clock}   "
                f"FPS {int(self.clock.get_fps())}")
        draw_text(screen, info, (10, SCREEN_HEIGHT - 26), 15)
        if p.heal_cd > 0:
            draw_text(screen, f"治疗冷却 {p.heal_cd // FPS + 1}s", (SCREEN_WIDTH - 210, 198), 14,
                      (255, 160, 160))
        self.inv_ui.draw(screen)

    def _draw_overlay(self, title, color, buttons, title_color=(255, 255, 255)):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill(color)
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, title, (SCREEN_WIDTH // 2, 200), 56, title_color, center=True, bold=True)
        for b in buttons:
            b.draw(self.screen)


if __name__ == '__main__':
    game = Game()
    while game.running:
        if not game.show_start_screen():
            break
        game.new()
    pygame.quit()
