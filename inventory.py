"""Inventory data, hotbar / inventory grid UI and the crafting panel."""
import pygame

from items import ITEMS, RECIPES, STATION_NAMES
from ui import get_font, panel, tooltip, draw_text

SLOT = 40
PAD = 4
COLS = 10
ROWS = 4
ORIGIN = (10, 10)


class Inventory:
    def __init__(self, size=COLS * ROWS):
        self.slots = [None] * size   # each slot: [item_name, count] or None

    def add(self, name, count):
        """Add items; returns the count that did not fit."""
        max_stack = ITEMS[name].max_stack
        for slot in self.slots:
            if slot and slot[0] == name and slot[1] < max_stack:
                room = max_stack - slot[1]
                moved = min(room, count)
                slot[1] += moved
                count -= moved
                if count == 0:
                    return 0
        for i, slot in enumerate(self.slots):
            if slot is None:
                moved = min(max_stack, count)
                self.slots[i] = [name, moved]
                count -= moved
                if count == 0:
                    return 0
        return count

    def can_accept(self, name):
        max_stack = ITEMS[name].max_stack
        return any(s is None or (s[0] == name and s[1] < max_stack) for s in self.slots)

    def count(self, name):
        return sum(s[1] for s in self.slots if s and s[0] == name)

    def remove(self, name, count):
        if self.count(name) < count:
            return False
        for i in range(len(self.slots) - 1, -1, -1):
            s = self.slots[i]
            if s and s[0] == name:
                taken = min(s[1], count)
                s[1] -= taken
                count -= taken
                if s[1] == 0:
                    self.slots[i] = None
                if count == 0:
                    break
        return True

    def consume_slot(self, index, count=1):
        s = self.slots[index]
        if s:
            s[1] -= count
            if s[1] <= 0:
                self.slots[index] = None


def can_craft(inv, recipe):
    return all(inv.count(n) >= c for n, c in recipe.ingredients.items())


def available_recipes(stations):
    return [r for r in RECIPES if r.station is None or r.station in stations]


def item_tooltip(name, count=None):
    it = ITEMS[name]
    lines = [(it.display + (f" ({count})" if count and count > 1 else ""), (255, 255, 255))]
    if it.damage and it.kind in ("weapon", "ranged", "magic", "tool"):
        lines.append((f"{it.damage} 点伤害", (220, 220, 220)))
    if it.pick:
        lines.append((f"镐力 {it.pick}%", (220, 220, 220)))
    if it.axe:
        lines.append((f"斧力 {it.axe}%", (220, 220, 220)))
    if it.mana_cost:
        lines.append((f"消耗 {it.mana_cost} 魔力", (150, 180, 255)))
    if it.kind == "block":
        lines.append(("可放置", (200, 200, 200)))
    if it.kind == "material":
        lines.append(("材料", (200, 200, 200)))
    if it.kind == "ammo":
        lines.append(("弹药", (200, 200, 200)))
    if it.desc:
        lines.append((it.desc, (180, 230, 180)))
    return lines


class InventoryUI:
    def __init__(self, inventory, assets):
        self.inv = inventory
        self.assets = assets
        self.selected = 0
        self.open = False
        self.cursor = None            # [item_name, count] held by the mouse
        self.stations = set()
        self.recipe_scroll = 0
        self.font = get_font(13, bold=True)
        self._recipe_rects = []

    # -------------------- geometry --------------------

    def slot_rect(self, i):
        row, col = divmod(i, COLS)
        return pygame.Rect(ORIGIN[0] + col * (SLOT + PAD), ORIGIN[1] + row * (SLOT + PAD), SLOT, SLOT)

    def inv_rect(self):
        rows = ROWS if self.open else 1
        return pygame.Rect(ORIGIN[0] - 4, ORIGIN[1] - 4, COLS * (SLOT + PAD) + 4, rows * (SLOT + PAD) + 4)

    def craft_rect(self):
        y = ORIGIN[1] + ROWS * (SLOT + PAD) + 34
        return pygame.Rect(ORIGIN[0] - 4, y, 8 * (SLOT + PAD) + 4, 3 * (SLOT + PAD) + 8)

    def over_ui(self, pos):
        if self.inv_rect().collidepoint(pos):
            return True
        return self.open and self.craft_rect().collidepoint(pos)

    def selected_item(self):
        s = self.inv.slots[self.selected]
        return s[0] if s else None

    # -------------------- input --------------------

    def handle_key(self, key):
        if pygame.K_1 <= key <= pygame.K_9:
            self.selected = key - pygame.K_1
            return True
        if key == pygame.K_0:
            self.selected = 9
            return True
        return False

    def handle_wheel(self, dy, mouse_pos):
        if self.open and self.craft_rect().collidepoint(mouse_pos):
            rows = (len(available_recipes(self.stations)) + 7) // 8
            self.recipe_scroll = max(0, min(max(0, rows - 3), self.recipe_scroll - dy))
        else:
            self.selected = (self.selected - dy) % COLS

    def handle_click(self, pos, button, game):
        """Returns True if the click was consumed by the UI."""
        n_slots = COLS * ROWS if self.open else COLS
        for i in range(n_slots):
            if self.slot_rect(i).collidepoint(pos):
                if not self.open:
                    self.selected = i
                elif button == 1:
                    self._left_slot(i)
                elif button == 3:
                    self._right_slot(i)
                return True
        if self.open:
            for rect, recipe in self._recipe_rects:
                if rect.collidepoint(pos):
                    if button == 1 and can_craft(self.inv, recipe):
                        self._craft(recipe, game)
                    return True
            if self.craft_rect().collidepoint(pos):
                return True
        return False

    def _left_slot(self, i):
        slot = self.inv.slots[i]
        cur = self.cursor
        if cur is None:
            self.cursor, self.inv.slots[i] = slot, None
        elif slot is None:
            self.inv.slots[i], self.cursor = cur, None
        elif slot[0] == cur[0]:
            room = ITEMS[slot[0]].max_stack - slot[1]
            moved = min(room, cur[1])
            slot[1] += moved
            cur[1] -= moved
            if cur[1] == 0:
                self.cursor = None
        else:
            self.inv.slots[i], self.cursor = cur, slot

    def _right_slot(self, i):
        slot = self.inv.slots[i]
        if slot is None:
            return
        if self.cursor is None:
            self.cursor = [slot[0], 1]
        elif self.cursor[0] == slot[0] and self.cursor[1] < ITEMS[slot[0]].max_stack:
            self.cursor[1] += 1
        else:
            return
        self.inv.consume_slot(i)

    def _craft(self, recipe, game):
        for name, count in recipe.ingredients.items():
            self.inv.remove(name, count)
        left = self.inv.add(recipe.result, recipe.count)
        if left:
            game.drop_item(recipe.result, left)
        game.add_text(f"制作了 {ITEMS[recipe.result].display}", (255, 240, 150))

    def close(self, game):
        self.open = False
        if self.cursor:
            left = self.inv.add(*self.cursor)
            if left:
                game.drop_item(self.cursor[0], left)
            self.cursor = None

    # -------------------- drawing --------------------

    def _draw_slot(self, surf, rect, stack, highlight=False, dim=False):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((60, 80, 170, 200) if highlight else (35, 45, 110, 170))
        surf.blit(bg, rect.topleft)
        pygame.draw.rect(surf, (255, 230, 120) if highlight else (150, 160, 220), rect, 2 if highlight else 1,
                         border_radius=4)
        if stack:
            icon = self.assets.icons[stack[0]]
            if dim:
                icon = icon.copy()
                icon.set_alpha(90)
            surf.blit(icon, (rect.x + (SLOT - 32) // 2, rect.y + (SLOT - 32) // 2))
            if stack[1] > 1:
                txt = self.font.render(str(stack[1]), True, (255, 255, 255))
                sh = self.font.render(str(stack[1]), True, (0, 0, 0))
                surf.blit(sh, (rect.x + 4, rect.bottom - 16))
                surf.blit(txt, (rect.x + 3, rect.bottom - 17))

    def draw(self, surf):
        mouse = pygame.mouse.get_pos()
        hover_lines = None
        n_slots = COLS * ROWS if self.open else COLS
        for i in range(n_slots):
            rect = self.slot_rect(i)
            stack = self.inv.slots[i]
            self._draw_slot(surf, rect, stack, highlight=(i == self.selected))
            if i < COLS:
                num = self.font.render(str((i + 1) % 10), True, (230, 230, 230))
                surf.blit(num, (rect.right - 10, rect.y + 2))
            if stack and rect.collidepoint(mouse) and self.cursor is None:
                hover_lines = item_tooltip(stack[0], stack[1])

        sel = self.selected_item()
        if sel and not self.open:
            draw_text(surf, ITEMS[sel].display, (ORIGIN[0], ORIGIN[1] + SLOT + 6), 15)

        self._recipe_rects = []
        if self.open:
            hover_lines = self._draw_crafting(surf, mouse) or hover_lines

        if self.cursor:
            surf.blit(self.assets.icons[self.cursor[0]], (mouse[0] - 8, mouse[1] - 8))
            if self.cursor[1] > 1:
                draw_text(surf, str(self.cursor[1]), (mouse[0] - 6, mouse[1] + 12), 13)
        elif hover_lines:
            tooltip(surf, hover_lines, mouse)

    def _draw_crafting(self, surf, mouse):
        rect = self.craft_rect()
        names = "、".join(STATION_NAMES[s] for s in sorted(self.stations)) or "无"
        draw_text(surf, f"制作（附近制作站：{names}）", (rect.x + 4, rect.y - 24), 15, (255, 240, 150))
        panel(surf, rect, 150)
        recipes = available_recipes(self.stations)
        recipes.sort(key=lambda r: not can_craft(self.inv, r))
        start = self.recipe_scroll * 8
        hover = None
        for k, recipe in enumerate(recipes[start:start + 24]):
            row, col = divmod(k, 8)
            r = pygame.Rect(rect.x + 4 + col * (SLOT + PAD), rect.y + 4 + row * (SLOT + PAD), SLOT, SLOT)
            ok = can_craft(self.inv, recipe)
            self._draw_slot(surf, r, [recipe.result, recipe.count], highlight=False, dim=not ok)
            self._recipe_rects.append((r, recipe))
            if r.collidepoint(mouse):
                lines = item_tooltip(recipe.result, recipe.count)
                lines.append(("需要材料：", (255, 240, 150)))
                for n, c in recipe.ingredients.items():
                    have = self.inv.count(n)
                    lines.append((f"  {ITEMS[n].display} {have}/{c}",
                                  (180, 255, 180) if have >= c else (255, 140, 140)))
                if recipe.station:
                    lines.append((f"制作站：{STATION_NAMES[recipe.station]}", (200, 200, 255)))
                lines.append(("左键制作" if ok else "材料不足", (255, 255, 255) if ok else (255, 140, 140)))
                hover = lines
        if len(recipes) > 24:
            draw_text(surf, "滚轮翻页", (rect.right - 70, rect.bottom + 2), 13, (200, 200, 200))
        return hover
