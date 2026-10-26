"""Modal panels opened from the world: NPC dialogue and pylon teleport list."""
import pygame

from settings import *
from tiles import T
from ui import draw_text, panel, Button

_PYLON = T["pylon"]


class DialogPanel:
    def __init__(self, game, npc):
        self.game = game
        self.npc = npc
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 250, 600, 160)
        self.text = "救救我！我被困在这里很久了……" if npc.bound else npc.next_line()
        self._make_buttons()

    def _make_buttons(self):
        npc = self.npc
        options = []
        if npc.bound:
            options.append(("解救", "rescue"))
        else:
            options.append(("对话", "talk"))
            if npc.shop_items():
                options.append(("商店", "shop"))
            if npc.kind == "nurse":
                options.append((f"治疗（{self.heal_price()} 金币）", "heal"))
            if npc.kind == "traveler":
                options.append(("传送", "teleport"))
        options.append(("离开", "close"))
        self.buttons = []
        x = self.rect.x + 20
        for label, action in options:
            w = max(90, 22 + len(label) * 15)
            b = Button(label, (x + w // 2, self.rect.bottom - 30), (w, 34), 16)
            self.buttons.append((b, action))
            x += w + 12

    def heal_price(self):
        p = self.game.player
        return (p.max_hp - p.hp) + (5 if p.burning else 0)

    def handle_event(self, event):
        """Returns True when the panel should close."""
        for b, action in self.buttons:
            if b.clicked(event):
                return self.game.dialog_action(self, action)
        return False

    def draw(self, surf):
        panel(surf, self.rect, 215)
        draw_text(surf, self.npc.name, (self.rect.x + 16, self.rect.y + 10), 20, (255, 240, 150), bold=True)
        draw_text(surf, self.text, (self.rect.x + 16, self.rect.y + 44), 16)
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
