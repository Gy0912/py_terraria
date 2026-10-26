import math
import random
import time

import pygame

from settings import *
from tiles import T, TILES
from items import ITEMS, SMELTING
from world import World
from player import Player
from camera import Camera
from background import Background
from creatures import CreatureManager
from bosses import BossManager
from npc import NPCManager, NPC, check_house
from inventory import InventoryUI, add_to_slots
from entities import ItemDrop, Particle, FloatingText
from physics import rect_solid
from textures import Assets
from render import WorldRenderer
from lighting import Lighting
from minimap import Minimap
from healthbar import HealthBar
from manabar import ManaBar
from panels import DialogPanel, TeleportPanel
from ui import get_font, draw_text, Button
import actions
import menus
import save

STATION_IDS = {T["workbench"]: "workbench", T["furnace"]: "furnace", T["anvil"]: "anvil"}
_SHIPPING, _SMELTER = T["shipping_bin"], T["auto_smelter"]
CONTROLS = ("A/D 移动  空格 跳跃(可二段跳)  左键 使用  右键 交互/对话  1-0/滚轮 切换  E 背包  H 治疗  "
            "M 小地图  Esc 暂停")


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
        self.small_font = get_font(13, bold=True)
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
        draw_text(self.screen, CONTROLS, (cx, SCREEN_HEIGHT - 40), 13, (220, 220, 220), center=True)
        draw_text(self.screen, f"Version {VERSION}", (SCREEN_WIDTH - 110, SCREEN_HEIGHT - 20), 13, (200, 200, 200))

    def choose_world(self):
        """World selection; returns True when a session is ready to run."""
        choice = menus.world_select(self)
        if choice is None:
            return False
        if choice[0] == "new":
            _, slot, name, seed = choice
            self.setup(seed=seed, slot=slot, name=name)
        else:
            self.load(choice[1])
        return True

    # ------------------------------------------------------------------
    # Session setup / save / load
    # ------------------------------------------------------------------

    def _loading(self, text):
        self.screen.fill(BLACK)
        draw_text(self.screen, text, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 28, center=True)
        pygame.display.flip()

    def setup(self, seed=None, slot=0, name="世界", world=None):
        if world is None:
            self._loading("正在生成世界……")
            world = World(random.randrange(1 << 30) if seed is None else seed)
        self.world = world
        self.slot = slot
        self.world_name = name
        self.created = time.strftime("%Y-%m-%d %H:%M")
        self.playtime = 0.0
        self.session_start = time.time()
        self.player = Player(self.world)
        self.camera = Camera()
        self.creatures = CreatureManager(self.world)
        self.bosses = BossManager(self)
        self.npcs = NPCManager(self)
        self.inv_ui = InventoryUI(self.player, self.assets)
        self.renderer = WorldRenderer(self.world, self.assets)
        self.lighting = Lighting()
        self.minimap = Minimap(self.world, (SCREEN_WIDTH - 210, 72, 200, 130))
        self.drops = []
        self.projectiles = []
        self.particles = []
        self.texts = []
        self.notices = {}
        self.banners = []
        self.ticks = int(START_HOUR / 24 * DAY_LENGTH)
        self.day_count = 1
        self.slime_kills = 0
        self.state = "playing"
        self.panel = None
        self.sleep_timer = 0
        self.autosave_timer = AUTOSAVE_SECONDS * FPS
        self.mouse_blocked = False
        self.pause_buttons = [Button("继续游戏", (SCREEN_WIDTH // 2, 290)),
                              Button("保存并返回主菜单", (SCREEN_WIDTH // 2, 360)),
                              Button("保存并退出游戏", (SCREEN_WIDTH // 2, 430))]
        self.death_buttons = [Button("复活", (SCREEN_WIDTH // 2, 330)),
                              Button("返回主菜单", (SCREEN_WIDTH // 2, 400))]
        self.camera.update(*self.player.center())
        self.npcs.check_arrivals()

    def load(self, slot):
        self._loading("正在读取存档……")
        data = save.load_data(slot)
        world = World(data["meta"]["seed"])
        save.apply_world(world, data)
        self.setup(slot=slot, name=data["meta"]["name"], world=world)
        self.created = data["meta"]["created"] if "created" in data["meta"] else self.created
        self.playtime = data["meta"]["playtime"]
        pd = data["player"]
        p = self.player
        p.inventory.slots = [s if s else None for s in pd["inventory"]]
        p.equip.update(pd["equip"])
        p.max_hp = pd["max_hp"]
        p.base_max_mana = pd["base_max_mana"]
        p.spawn_point = tuple(pd["spawn_point"]) if pd["spawn_point"] else None
        p.recompute_stats()
        p.x, p.y = pd["x"], pd["y"]
        p.hp, p.mana = pd["hp"], min(pd["mana"], p.max_mana)
        p.fall_peak = p.y
        self.npcs.npcs = []
        for nd in data["npcs"]:
            n = NPC(nd["kind"], nd["x"], nd["y"], bound=nd["bound"])
            n.home = tuple(nd["home"]) if nd["home"] else None
            self.npcs.npcs.append(n)
        gd = data["game"]
        self.ticks = gd["ticks"]
        self.day_count = gd["day_count"]
        self.creatures.slime_rain = gd["slime_rain"]
        self.slime_kills = gd["slime_kills"]
        self.camera.update(*p.center())

    def save(self, quiet=False):
        try:
            save.save_game(self)
            if not quiet:
                self.announce("已保存", (180, 255, 180))
        except OSError as e:
            self.announce(f"保存失败：{e}", (255, 120, 120))

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

    def _advance_time(self, frames=1):
        before = self.hour()
        self.ticks += frames
        after = self.hour()
        if before < 6.0 <= after or (after < before and after >= 6.0):
            self.on_dawn()
        if before < 19.5 <= after:
            self.on_dusk()
        if before < 18.0 <= after and self.creatures.slime_rain:
            self.creatures.slime_rain = False
            self.announce("史莱姆雨停了", (180, 220, 255))

    def on_dawn(self):
        self.day_count += 1
        total = items = 0
        for anchor, tid in list(self.world.objects.items()):
            if tid != _SHIPPING:
                continue
            slots = self.world.containers.get(anchor, [])
            for i, s in enumerate(slots):
                if s:
                    total += ITEMS[s[0]].value * s[1]
                    items += s[1]
                    slots[i] = None
        if items:
            self.give("coin", total)
            self.announce(f"出货箱售出 {items} 件物品，获得 {total} 金币", (250, 215, 90))
        if self.day_count >= 2 and random.random() < 0.2:
            self.creatures.slime_rain = True
            self.slime_kills = 0
            self.announce("史莱姆雨来了！", (120, 180, 255))
        self.npcs.check_arrivals()

    def on_dusk(self):
        p = self.player
        if (not self.world.flags.get("eye_defeated") and p.max_hp >= 140 and p.defense >= 6
                and random.random() < 0.33):
            self.bosses.summon("eye", delay=FPS * 8, message="你感到一股邪恶的目光正注视着你……")

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
                self.save(quiet=True)
                self.playing = False
                self.running = False
                return
            if self.state == "paused":
                self._pause_event(event)
                continue
            if self.state == "dead":
                self._death_event(event)
                continue
            if self.panel:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.panel = None
                elif self.panel.handle_event(event):
                    self.panel = None
                    self.mouse_blocked = True
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
                elif event.button == 3:
                    self.right_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_blocked = False

    def right_click(self, pos):
        wx, wy = pos[0] + self.camera.x, pos[1] + self.camera.y
        npc = self.npcs.npc_at(wx, wy)
        p = self.player
        if npc and math.hypot(npc.center()[0] - p.center()[0], npc.center()[1] - p.center()[1]) < 8 * TILE_SIZE:
            self.inv_ui.close(self)
            self.panel = DialogPanel(self, npc)
            return
        if actions.interact(self, int(wx) // TILE_SIZE, int(wy) // TILE_SIZE):
            self.mouse_blocked = True

    def _pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "playing"
        resume, menu, quit_ = self.pause_buttons
        if resume.clicked(event):
            self.state = "playing"
        elif menu.clicked(event):
            self.save(quiet=True)
            self.playing = False
        elif quit_.clicked(event):
            self.save(quiet=True)
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
            self.save(quiet=True)
            self.playing = False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        if self.sleep_timer:
            self._update_sleep()
            return
        self._advance_time()
        p = self.player
        keys = pygame.key.get_pressed()

        mouse = pygame.mouse.get_pos()
        if (pygame.mouse.get_pressed()[0] and not self.mouse_blocked and not self.panel
                and not self.inv_ui.over_ui(mouse) and not self.inv_ui.cursor):
            actions.try_use(self)

        p.update(keys)
        dmg = p.take_pending_damage()
        if dmg:
            self.add_text(f"-{dmg}", (255, 80, 80))
        if p.double_jumped:
            p.double_jumped = False
            self.burst(p.center()[0], p.y + p.H, (235, 240, 255), 10, speed=2)
        if p.burning and self.ticks % 4 == 0:
            self.particles.append(Particle(p.x + random.random() * p.W, p.y + random.random() * p.H,
                                           0, -1.2, random.choice(((255, 140, 30), (255, 210, 80))), 20, 0, 3))
        actions.update_use(self)

        self.bosses.update()
        self.creatures.update(p, self.is_night())
        if p.alive:
            for c in self.creatures.creatures:
                if c.rect().colliderect(p.rect()):
                    dealt = p.hurt(c.t["dmg"], c.center()[0])
                    if dealt:
                        self.add_text(f"-{dealt}", (255, 80, 80))
                        self.burst(*p.center(), (200, 30, 30), 6)
                    break
        self.npcs.update()

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
        self.banners = [[t, c, life - 1] for t, c, life in self.banners if life > 1]

        if self.ticks % 2 == 0:
            self.world.update_liquids(500)
        self.world.tick_damage()
        if self.ticks % 15 == 0:
            self.inv_ui.stations = self.nearby_stations()
        if self.ticks % 240 == 0:
            self._run_smelters()
        if self.inv_ui.container and self.inv_ui.container[0] not in self.world.objects:
            self.inv_ui.close(self)

        self.camera.update(*p.center())
        self.background.update(self.world.get_biome(*p.center()))
        self.minimap.update(p)

        self.autosave_timer -= 1
        if self.autosave_timer <= 0:
            self.autosave_timer = AUTOSAVE_SECONDS * FPS
            self.save(quiet=True)
            self.announce("已自动保存", (180, 255, 180))

        if not p.alive:
            self._on_death()

    def _on_death(self):
        p = self.player
        self.state = "dead"
        self.burst(*p.center(), (200, 30, 30), 30, speed=5)
        self.inv_ui.close(self)
        self.panel = None
        coins = p.inventory.count("coin")
        lost = coins // 2
        if lost:
            p.inventory.remove("coin", lost)
            cx, cy = p.center()
            self.drops.append(ItemDrop("coin", lost, cx, cy, 0, -2, pickup_delay=30))
            self.death_note = f"掉落了 {lost} 金币（可以回去捡回）"
        else:
            self.death_note = ""

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
        self.drops = [d for d in self.drops if d.alive][-400:]

    def _run_smelters(self):
        """Automation: every auto smelter turns one batch of ore into a bar."""
        for anchor, tid in self.world.objects.items():
            if tid != _SMELTER:
                continue
            slots = self.world.containers.get(anchor)
            if not slots:
                continue
            for i, s in enumerate(slots):
                if s and s[0] in SMELTING and s[1] >= SMELTING[s[0]][0]:
                    need, bar = SMELTING[s[0]]
                    test = [list(x) if x else None for x in slots]
                    test[i][1] -= need
                    if test[i][1] == 0:
                        test[i] = None
                    if add_to_slots(test, bar, 1) == 0:
                        slots[:] = test
                        break

    def nearby_stations(self):
        cx, cy = self.player.center()
        tx, ty = int(cx) // TILE_SIZE, int(cy) // TILE_SIZE
        found = set()
        for y in range(ty - 4, ty + 5):
            for x in range(tx - 6, tx + 7):
                name = STATION_IDS.get(self.world.get_tile(x, y))
                if name:
                    found.add(name)
        return found

    # ------------------------------------------------------------------
    # Beds, sleep, teleport, NPC services
    # ------------------------------------------------------------------

    def use_bed(self, anchor):
        p = self.player
        p.spawn_point = anchor
        ok, reason = check_house(self.world, anchor)
        self.announce(f"重生点已设置。房屋检测：{reason}", (180, 255, 180) if ok else (255, 220, 140))
        if self.is_night():
            hostile = any(math.hypot(c.center()[0] - p.center()[0], c.center()[1] - p.center()[1]) < 400
                          for c in self.creatures.creatures)
            if self.bosses.active() or hostile:
                self.notify("附近有敌人，无法入睡")
            else:
                self.sleep_timer = 90

    def _update_sleep(self):
        self.sleep_timer -= 1
        if self.sleep_timer == 45:
            h = self.hour()
            hours = (6 - h) % 24
            self._advance_time(int(hours / 24 * DAY_LENGTH) + 1)
            self.player.hp = self.player.max_hp
            self.announce("你一觉睡到了天亮", (255, 240, 180))

    def open_teleport(self):
        self.inv_ui.close(self)
        self.panel = TeleportPanel(self)

    def teleport_to(self, anchor):
        p = self.player
        self.burst(*p.center(), (120, 230, 255), 20, speed=3)
        p.teleport(anchor[0] + 3, anchor[1] + 3)
        self.burst(*p.center(), (120, 230, 255), 20, speed=3)

    def dialog_action(self, panel, action):
        npc = panel.npc
        p = self.player
        if action == "close":
            return True
        if action == "talk":
            panel.text = npc.next_line()
        elif action == "rescue":
            self.npcs.rescue(npc)
            return True
        elif action == "shop":
            self.inv_ui.open_shop(npc)
            return True
        elif action == "heal":
            price = panel.heal_price()
            if price <= 0:
                panel.text = "你看起来很健康。"
            elif p.inventory.count("coin") < price:
                panel.text = f"治疗需要 {price} 金币，你的钱不够。"
            else:
                p.inventory.remove("coin", price)
                p.hp = p.max_hp
                p.burning = 0
                panel.text = "好了，下次小心点。"
            panel._make_buttons()
        elif action == "teleport":
            self.panel = TeleportPanel(self)
            return False
        return False

    def buy(self, name, price):
        p = self.player
        if p.inventory.count("coin") < price:
            self.notify("金币不足")
            return
        if not p.inventory.can_accept(name):
            self.notify("背包已满")
            return
        p.inventory.remove("coin", price)
        p.inventory.add(name, 1)
        self.add_text(f"购买了 {ITEMS[name].display}", (250, 215, 90))

    def sell(self, name, count):
        if name == "coin":
            self.give("coin", count)
            return
        value = ITEMS[name].value * count
        self.give("coin", value)
        self.add_text(f"出售 {ITEMS[name].display} x{count}，+{value} 金币", (250, 215, 90))

    def give(self, name, count):
        if count <= 0:
            return
        left = self.player.inventory.add(name, count)
        if left:
            self.drop_item(name, left)

    # ------------------------------------------------------------------
    # Helpers used by actions / inventory / bosses
    # ------------------------------------------------------------------

    def on_creature_hit(self, c, dealt):
        cx, cy = c.center()
        self.add_text(str(dealt), (255, 210, 80), (cx, c.y - 10))
        self.burst(cx, cy, (200, 40, 40) if "slime" not in c.kind else (120, 200, 255), 5)
        if c.alive:
            return
        self.burst(cx, cy, (230, 230, 230), 14, speed=3.5)
        if getattr(c, "is_boss", False):
            self.bosses.on_defeat(c)
            return
        luck = 1 + self.player.stats["luck"]
        for name, lo, hi, chance in c.t["drops"]:
            if random.random() < chance * luck:
                self.drop_item_at(name, random.randint(lo, hi), cx, cy)
        if c.kind != "servant_eye" and random.random() < 0.8:
            self.drop_item_at("coin", random.randint(1, max(1, c.max_hp // 8)), cx, cy)
        if self.creatures.slime_rain and "slime" in c.kind:
            self.slime_kills += 1
            if self.slime_kills == 40:
                self.bosses.summon("king_slime", delay=FPS * 2, message="大地在震动……")

    def drop_item_at(self, name, count, x, y):
        if name and count > 0:
            for _ in range(60):
                if not rect_solid(self.world, x - 8, y - 8, 16, 16):
                    break
                y -= TILE_SIZE
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
                                           life=random.randint(18, 35), size=3))

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

    def announce(self, text, color=(255, 255, 255)):
        """Banner at the top of the screen for world events."""
        self.banners.append([text, color, FPS * 5])
        self.banners = self.banners[-4:]

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
        self.renderer.draw_objects(screen, cam)
        self.renderer.draw_cracks(screen, cam)
        for d in self.drops:
            d.draw(screen, cam, self.assets)
        self.npcs.draw(screen, cam, self.assets, self.small_font)
        self.creatures.draw(screen, cam, self.assets)
        for pr in self.projectiles:
            pr.draw(screen, cam)
        p.draw(screen, cam, self.assets)
        self.renderer.draw_liquids(screen, cam)
        for pt in self.particles:
            pt.draw(screen, cam)

        lights = []
        if p.alive:
            lights.append((*p.center(), 3, 0.55))
            if p.stats["light"]:
                lights.append((*p.center(), p.stats["light"], 0.95))
        for pr in self.projectiles:
            if pr.kind == "bolt":
                lights.append((pr.x, pr.y, 3, 0.9))
        for c in self.creatures.creatures:
            if "light" in c.t:
                lights.append((*c.center(), *c.t["light"]))
        self.lighting.render(screen, self.world, cam, self.daylight(), lights)

        self._draw_cursor()
        for t in self.texts:
            t.draw(screen, cam)
        self._draw_hud()
        if self.panel:
            self.panel.draw(screen)
        if self.sleep_timer:
            k = 1 - abs(self.sleep_timer - 45) / 45
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((0, 0, 0, int(255 * k)))
            screen.blit(fade, (0, 0))
        if self.state == "paused":
            self._draw_overlay("已暂停", (0, 0, 30, 160), self.pause_buttons)
            draw_text(screen, CONTROLS, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40), 13, center=True)
        elif self.state == "dead":
            self._draw_overlay("你死了", (60, 0, 0, 150), self.death_buttons, (255, 90, 90))
            if self.death_note:
                draw_text(screen, self.death_note, (SCREEN_WIDTH // 2, 262), 16, (255, 220, 140), center=True)

    def _draw_cursor(self):
        p = self.player
        item = self.inv_ui.selected_item()
        if not p.alive or not item or ITEMS[item].kind not in ("tool", "block", "wall", "bucket") or \
                self.inv_ui.over_ui(pygame.mouse.get_pos()) or self.panel:
            return
        tx, ty = actions.mouse_tile(self)
        if actions.in_reach(p, tx, ty):
            it = ITEMS[item]
            w, h = (1, 1)
            if it.kind == "block":
                w, h = TILES[T[it.place]].size
            ax, ay = tx - (w - 1) // 2, ty - (h - 1)
            sx, sy = self.camera.apply(ax * TILE_SIZE, ay * TILE_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 255), (sx, sy, w * TILE_SIZE, h * TILE_SIZE), 1)

    def _draw_hud(self):
        screen = self.screen
        p = self.player
        self.health_bar.draw(screen, p.hp, p.max_hp)
        self.mana_bar.draw(screen, p.mana, p.max_mana)
        status = [f"防御 {p.defense}"]
        if p.burning:
            status.append("燃烧中")
        if p.breath == 0:
            status.append("窒息！")
        if self.creatures.slime_rain:
            status.append(f"史莱姆雨 {self.slime_kills}/40")
        draw_text(screen, "  ".join(status), (SCREEN_WIDTH - 210, 49), 14,
                  (255, 140, 120) if (p.burning or p.breath == 0) else (200, 220, 255))
        self.minimap.draw(screen, p, self.creatures.creatures, self.npcs.npcs)
        acc = [n for s, n in p.equip.items() if s.startswith("acc") and n]
        for i, name in enumerate(acc):
            screen.blit(self.assets.icons_small[name], (SCREEN_WIDTH - 210 + i * 22, 206))

        cx, cy = p.center()
        tx, ty = int(cx) // TILE_SIZE, int(cy) // TILE_SIZE
        layer = self.world.layer_at(tx, ty)
        if layer == "hell":
            place = LAYER_NAMES[layer]
        else:
            place = f"{BIOME_NAMES[self.world.biome_at(tx, ty)]} · {LAYER_NAMES[layer]}"
        h = self.hour()
        clock = f"第 {self.day_count} 天 {int(h):02d}:{int(h % 1 * 60):02d} {'夜晚' if self.is_night() else '白天'}"
        info = (f"{place}   坐标 {tx - self.world.spawn_tx:+d}  深度 {ty - SURFACE_LEVEL}   {clock}   "
                f"FPS {int(self.clock.get_fps())}")
        draw_text(screen, info, (10, SCREEN_HEIGHT - 26), 15)
        if p.heal_cd > 0:
            draw_text(screen, f"治疗冷却 {p.heal_cd // FPS + 1}s", (SCREEN_WIDTH - 210, 230), 14, (255, 160, 160))
        for i, (text, color, _) in enumerate(self.banners):
            draw_text(screen, text, (SCREEN_WIDTH // 2 + 120, 74 + i * 24), 16, color, center=True)
        self.bosses.draw_bar(screen)
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
        if not game.choose_world():
            continue
        game.run()
    pygame.quit()
