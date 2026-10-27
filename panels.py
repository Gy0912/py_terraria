"""Modal panels opened from the world: NPC dialogue (requests, cards, services), pylon
teleport list, lockpicking mini-game, lore reading, the journal and the housing report."""
import random

import pygame

from settings import *
from tiles import T
from ui import draw_text, panel, Button
from items import ITEMS
from quests import quest_text, MAX_ACTIVE
from story import NOTES, TOTAL_NOTES

_PYLON = T["pylon"]


class DialogPanel:
    def __init__(self, game, npc):
        self.game = game
        self.npc = npc
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 330, SCREEN_HEIGHT - 250, 660, 160)
        self.text = "救救我！我被困在这里很久了……" if npc.bound else npc.next_line()
        self.mode = "main"
        self.make_buttons()

    def heal_price(self):
        p = self.game.player
        return (p.max_hp - p.hp) + (5 if p.burning else 0)

    def make_buttons(self):
        g = self.game
        npc = self.npc
        options = []
        if self.mode == "quest":
            options = [("接受委托", "accept"), ("返回", "back")]
        elif npc.bound:
            options.append(("解救", "rescue"))
        else:
            options.append(("对话", "talk"))
            if npc.shop_items():
                options.append(("商店", "shop"))
            active = g.quests.from_giver(npc.kind)
            if active:
                options.append(("交付委托" if g.quests.ready(active, g.player) else "委托进度", "turn_in"))
            elif g.quests.offer(npc.kind):
                options.append(("委托", "quest"))
            if g.cards_unlocked() and npc.kind in g.card_decks():
                options.append(("打牌", "cards"))
            if npc.kind == "nurse":
                options.append((f"治疗（{self.heal_price()} 金币）", "heal"))
            if npc.kind == "traveler":
                options.append(("传送", "teleport"))
        options.append(("离开", "close"))
        self.buttons = []
        x = self.rect.x + 16
        for label, action in options:
            w = max(80, 22 + len(label) * 15)
            self.buttons.append((Button(label, (x + w // 2, self.rect.bottom - 30), (w, 34), 16), action))
            x += w + 10

    def show_offer(self):
        g = self.game
        q = g.quests.offer(self.npc.kind)
        extras = "、".join(f"{ITEMS[n].display}×{c}" for n, c in q["extras"])
        self.text = f"委托：{quest_text(q)}。报酬 {q['coins']} 金币" + (f" + {extras}" if extras else "")
        if len(g.quests.active) >= MAX_ACTIVE:
            self.text += f"（你已经接了 {MAX_ACTIVE} 个委托）"
        self.mode = "quest"
        self.make_buttons()

    def handle_event(self, event):
        """Returns True when the panel should close."""
        for b, action in self.buttons:
            if b.clicked(event):
                return self.game.dialog_action(self, action)
        return False

    def draw(self, surf):
        panel(surf, self.rect, 215)
        draw_text(surf, self.npc.name, (self.rect.x + 16, self.rect.y + 10), 20, (255, 240, 150), bold=True)
        if not self.npc.bound:
            draw_text(surf, f"生命 {self.npc.hp}/{self.npc.max_hp}", (self.rect.right - 140, self.rect.y + 14), 14,
                      (180, 255, 180))
        draw_text(surf, self.text, (self.rect.x + 16, self.rect.y + 46), 16)
        for b, _ in self.buttons:
            b.draw(surf)


class TeleportPanel:
    def __init__(self, game):
        self.game = game
        world = game.world
        pylons = sorted(a for a, tid in world.objects.items() if tid == _PYLON)
        self.buttons = []
        h = 70 + max(1, len(pylons)) * 44
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, max(40, SCREEN_HEIGHT // 2 - h // 2), 440, h)
        for i, (ax, ay) in enumerate(pylons):
            layer = LAYER_NAMES[world.layer_at(ax, ay)]
            biome = BIOME_NAMES.get(world.biome_at(ax, ay), "")
            label = f"{biome}{layer}晶塔  ({ax - world.spawn_tx:+d})"
            b = Button(label, (self.rect.centerx, self.rect.y + 60 + i * 44), (380, 36), 16)
            self.buttons.append((b, (ax, ay)))
        self.close_btn = Button("关闭", (self.rect.right - 50, self.rect.y + 22), (70, 28), 14)
        self.empty = not pylons

    def handle_event(self, event):
        if self.close_btn.clicked(event):
            return True
        for b, anchor in self.buttons:
            if b.clicked(event):
                self.game.teleport_to(anchor)
                return True
        return False

    def draw(self, surf):
        panel(surf, self.rect, 220)
        draw_text(surf, "传送晶塔网络", (self.rect.x + 16, self.rect.y + 12), 20, (150, 240, 255), bold=True)
        if self.empty:
            draw_text(surf, "还没有放置任何传送晶塔（可向传送师购买）", (self.rect.x + 16, self.rect.y + 50), 15)
        for b, _ in self.buttons:
            b.draw(surf)
        self.close_btn.draw(surf)


class LockpickPanel:
    """Three pins. A needle sweeps across the lock; press Space / click while it is inside
    the green zone. A miss snaps one lockpick. Each pin is narrower and faster."""
    PINS = 3
    pauses = True

    def __init__(self, game, anchor):
        self.game = game
        self.anchor = anchor
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 110, 440, 220)
        self.bar = pygame.Rect(self.rect.x + 40, self.rect.y + 110, 360, 22)
        self.pin = 0
        self.message = "按空格或左键：指针停在绿色区域时撬动锁销"
        self.shake = 0
        self._new_pin()

    def _new_pin(self):
        width = (70, 50, 34)[self.pin]
        self.zone = (random.randint(20, self.bar.w - width - 20), width)
        self.pos = 0.0
        self.speed = (3.2, 4.4, 5.6)[self.pin]

    def update(self):
        self.pos += self.speed
        if self.pos <= 0 or self.pos >= self.bar.w:
            self.speed = -self.speed
            self.pos = max(0, min(self.bar.w, self.pos))
        if self.shake:
            self.shake -= 1

    def handle_event(self, event):
        press = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        if not press:
            return False
        z0, zw = self.zone
        if z0 <= self.pos <= z0 + zw:
            self.pin += 1
            if self.pin >= self.PINS:
                self.game.unlock_chest(self.anchor)
                return True
            self.message = f"锁销 {self.pin}/{self.PINS} 已撬开"
            self._new_pin()
            return False
        inv = self.game.player.inventory
        inv.remove("lockpick", 1)
        self.shake = 12
        left = inv.count("lockpick")
        if left == 0:
            self.game.notify("撬锁器用完了")
            return True
        self.message = f"咔嚓！撬锁器折断了（剩余 {left}）"
        return False

    def draw(self, surf):
        r = self.rect.move(random.randint(-3, 3) if self.shake else 0, 0)
        panel(surf, r, 230)
        draw_text(surf, "撬锁", (r.x + 16, r.y + 12), 22, (255, 230, 140), bold=True)
        draw_text(surf, self.message, (r.x + 16, r.y + 52), 15)
        for i in range(self.PINS):
            col = (120, 255, 140) if i < self.pin else (90, 90, 110)
            pygame.draw.rect(surf, col, (r.x + 300 + i * 30, r.y + 16, 20, 30), border_radius=4)
        bar = self.bar.move(r.x - self.rect.x, 0)
        pygame.draw.rect(surf, (40, 40, 60), bar, border_radius=4)
        z0, zw = self.zone
        pygame.draw.rect(surf, (70, 200, 90), (bar.x + z0, bar.y, zw, bar.h), border_radius=4)
        pygame.draw.rect(surf, (230, 230, 255), bar, 1, border_radius=4)
        x = bar.x + int(self.pos)
        pygame.draw.line(surf, (255, 240, 120), (x, bar.y - 8), (x, bar.bottom + 8), 3)
        draw_text(surf, f"撬锁器 {self.game.player.inventory.count('lockpick')}   Esc 放弃",
                  (r.x + 16, r.bottom - 34), 14, (200, 200, 220))


class TextPanel:
    """Reading a lore tablet (or any titled text)."""
    pauses = True

    def update(self):
        pass

    def __init__(self, title, lines, footer=""):
        self.title = title
        self.lines = lines
        self.footer = footer
        h = 120 + len(lines) * 28
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 320, SCREEN_HEIGHT // 2 - h // 2, 640, h)
        self.close_btn = Button("关闭", (self.rect.right - 60, self.rect.bottom - 28), (90, 32), 15)

    def handle_event(self, event):
        return self.close_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE, pygame.K_RETURN))

    def draw(self, surf):
        panel(surf, self.rect, 235, border=(230, 210, 150))
        draw_text(surf, self.title, (self.rect.x + 20, self.rect.y + 14), 22, (255, 230, 150), bold=True)
        for i, line in enumerate(self.lines):
            draw_text(surf, line, (self.rect.x + 24, self.rect.y + 58 + i * 28), 16, (235, 230, 215))
        if self.footer:
            draw_text(surf, self.footer, (self.rect.x + 20, self.rect.bottom - 34), 14, (190, 200, 160))
        self.close_btn.draw(surf)


class JournalPanel:
    pauses = True

    def update(self):
        pass

    def __init__(self, game):
        self.game = game
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 380, 60, 760, 470)
        self.selected = min(game.player.journal) if game.player.journal else None
        self.close_btn = Button("关闭", (self.rect.right - 60, self.rect.y + 24), (90, 30), 15)

    def _entry_rect(self, i):
        return pygame.Rect(self.rect.x + 16, self.rect.y + 60 + i * 44, 220, 38)

    def handle_event(self, event):
        if self.close_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_l)):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, nid in enumerate(sorted(NOTES)):
                if self._entry_rect(i).collidepoint(event.pos) and nid in self.game.player.journal:
                    self.selected = nid
        return False

    def draw(self, surf):
        found = self.game.player.journal
        panel(surf, self.rect, 240, border=(230, 210, 150))
        draw_text(surf, f"远征队日志  {len(found)}/{TOTAL_NOTES}", (self.rect.x + 16, self.rect.y + 14), 22,
                  (255, 230, 150), bold=True)
        for i, nid in enumerate(sorted(NOTES)):
            r = self._entry_rect(i)
            have = nid in found
            pygame.draw.rect(surf, (80, 70, 50) if nid == self.selected else (40, 36, 30), r, border_radius=4)
            draw_text(surf, NOTES[nid][0] if have else "？？？", (r.x + 10, r.y + 9), 15,
                      (240, 230, 200) if have else (130, 120, 100))
        if self.selected:
            title, lines = NOTES[self.selected]
            draw_text(surf, title, (self.rect.x + 260, self.rect.y + 64), 19, (255, 230, 150))
            for i, line in enumerate(lines):
                draw_text(surf, line, (self.rect.x + 260, self.rect.y + 104 + i * 30), 15, (235, 230, 215))
        else:
            draw_text(surf, "还没有找到任何日志。去废弃的营地、瞭望塔和神殿看看吧。",
                      (self.rect.x + 260, self.rect.y + 64), 15)
        if len(found) == TOTAL_NOTES:
            draw_text(surf, "你拼凑出了远征队的全部故事。", (self.rect.x + 260, self.rect.bottom - 40), 15,
                      (150, 255, 170))
        self.close_btn.draw(surf)


class RoomReport:
    """Result of the housing query tool: highlights the room and lists every requirement."""

    def __init__(self, result, tenant=None):
        self.r = result
        self.tenant = tenant
        self.life = FPS * 8

    def lines(self):
        r = self.r
        out = [("✓ 适合居住" if r["ok"] else "✗ 还不能居住", (140, 255, 160) if r["ok"] else (255, 140, 140))]
        if r["size"]:
            checks = [(f"面积 {r['size']} 格（50–750）", 50 <= r["size"] <= 750),
                      (f"背景墙 {int(r['walls'] * 100)}%（≥90%）", r["walls"] >= 0.9),
                      ("光源", r["light"]), ("门", r["door"]), ("床", r["bed"] is not None)]
            out += [(("✓ " if ok else "✗ ") + text, (200, 255, 200) if ok else (255, 170, 170)) for text, ok in checks]
        else:
            out += [(text, (255, 170, 170)) for text in r["reasons"]]
        if self.tenant:
            out.append((f"住户：{self.tenant}", (255, 240, 150)))
        return out

    def draw(self, surf, cam):
        overlay = (60, 220, 90, 70) if self.r["ok"] else (230, 60, 60, 70)
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        tile.fill(overlay)
        if len(self.r["cells"]) <= 750:
            for x, y in self.r["cells"]:
                surf.blit(tile, cam.apply(x * TILE_SIZE, y * TILE_SIZE))
        lines = self.lines()
        box = pygame.Rect(SCREEN_WIDTH - 250, 250, 240, 22 * len(lines) + 34)
        panel(surf, box, 220)
        draw_text(surf, "房屋检测", (box.x + 10, box.y + 6), 16, (255, 230, 150))
        for i, (text, color) in enumerate(lines):
            draw_text(surf, text, (box.x + 10, box.y + 30 + i * 22), 14, color)
