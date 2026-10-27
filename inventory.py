"""Inventory data and the inventory screen: hotbar, bag grid, equipment, crafting,
containers (chest / shipping bin / auto smelter) and NPC shops."""
import pygame

from items import ITEMS, RECIPES, STATION_NAMES
from ui import get_font, panel, tooltip, draw_text

SLOT = 40
PAD = 4
COLS = 10
ROWS = 4
ORIGIN = (10, 10)
EQUIP_X = ORIGIN[0] + COLS * (SLOT + PAD) + 14
EQUIP_LABELS = {"head": "头", "body": "身", "legs": "腿"}


class Inventory:
    def __init__(self, size=COLS * ROWS):
        self.slots = [None] * size   # each slot: [item_name, count] or None

    def add(self, name, count):
        """Add items; returns the count that did not fit."""
        return add_to_slots(self.slots, name, count)

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


def add_to_slots(slots, name, count):
    max_stack = ITEMS[name].max_stack
    for slot in slots:
        if slot and slot[0] == name and slot[1] < max_stack:
            moved = min(max_stack - slot[1], count)
            slot[1] += moved
            count -= moved
            if count == 0:
                return 0
    for i, slot in enumerate(slots):
        if slot is None:
            moved = min(max_stack, count)
            slots[i] = [name, moved]
            count -= moved
            if count == 0:
                return 0
    return count


def can_craft(inv, recipe):
    return all(inv.count(n) >= c for n, c in recipe.ingredients.items())


def available_recipes(stations):
    return [r for r in RECIPES if r.station is None or r.station in stations]


def item_tooltip(name, count=None):
    it = ITEMS[name]
    lines = [(it.display + (f" ({count})" if count and count > 1 else ""), (255, 255, 255))]
    if it.damage and it.kind in ("weapon", "ranged", "magic", "tool"):
        lines.append((f"{it.damage} 点伤害", (220, 220, 220)))
    for key, label in (("pick", "镐力"), ("axe", "斧力"), ("hammer", "锤力")):
        if getattr(it, key):
            lines.append((f"{label} {getattr(it, key)}%", (220, 220, 220)))
    if it.defense:
        lines.append((f"{it.defense} 点防御", (220, 220, 220)))
    if it.slot:
        lines.append(({"head": "头部装备", "body": "身体装备", "legs": "腿部装备"}.get(it.slot, "饰品"),
                      (200, 200, 255)))
    if it.mana_cost:
        lines.append((f"消耗 {it.mana_cost} 魔力", (150, 180, 255)))
    if it.kind in ("block", "wall"):
        lines.append(("可放置", (200, 200, 200)))
    if it.kind == "material":
        lines.append(("材料", (200, 200, 200)))
    if it.kind == "ammo":
        lines.append(("弹药", (200, 200, 200)))
    if it.desc:
        lines.append((it.desc, (180, 230, 180)))
    if it.value:
        lines.append((f"售价 {it.value} 金币", (250, 215, 90)))
    return lines


class InventoryUI:
    def __init__(self, player, assets):
        self.player = player
        self.inv = player.inventory
        self.assets = assets
        self.selected = 0
        self.open = False
        self.cursor = None            # [item_name, count] held by the mouse
        self.stations = set()
        self.recipe_scroll = 0
        self.container = None         # (anchor, slots, title)
        self.shop = None              # npc offering a shop
        self.font = get_font(13, bold=True)
        self._recipe_rects = []
        self._shop_rects = []
        self._button_rects = []

    # -------------------- geometry --------------------

    def slot_rect(self, i):
        row, col = divmod(i, COLS)
        return pygame.Rect(ORIGIN[0] + col * (SLOT + PAD), ORIGIN[1] + row * (SLOT + PAD), SLOT, SLOT)

    def equip_rect(self, slot):
        if slot in ("head", "body", "legs"):
            col, row = 0, ("head", "body", "legs").index(slot)
        else:
            col, row = 1, int(slot[3])
        return pygame.Rect(EQUIP_X + col * (SLOT + PAD), ORIGIN[1] + row * (SLOT + PAD), SLOT, SLOT)

    def inv_rect(self):
        rows = ROWS if self.open else 1
        return pygame.Rect(ORIGIN[0] - 4, ORIGIN[1] - 4, COLS * (SLOT + PAD) + 4, rows * (SLOT + PAD) + 4)

    def equip_panel_rect(self):
        return pygame.Rect(EQUIP_X - 4, ORIGIN[1] - 4, 2 * (SLOT + PAD) + 4, 5 * (SLOT + PAD) + 26)

    def lower_rect(self):
        y = ORIGIN[1] + ROWS * (SLOT + PAD) + 34
        return pygame.Rect(ORIGIN[0] - 4, y, COLS * (SLOT + PAD) + 4, 3 * (SLOT + PAD) + 36)

    def over_ui(self, pos):
        if self.inv_rect().collidepoint(pos):
            return True
        return self.open and (self.lower_rect().collidepoint(pos) or self.equip_panel_rect().collidepoint(pos))

    def selected_item(self):
        s = self.inv.slots[self.selected]
        return s[0] if s else None

    # -------------------- open / close --------------------

    def open_container(self, anchor, slots, title):
        self.open = True
        self.shop = None
        self.container = (anchor, slots, title)

    def open_shop(self, npc):
        self.open = True
        self.container = None
        self.shop = npc

    def close(self, game):
        self.open = False
        self.container = None
        self.shop = None
        if self.cursor:
            left = self.inv.add(*self.cursor)
            if left:
                game.drop_item(self.cursor[0], left)
            self.cursor = None

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
        if self.open and self.lower_rect().collidepoint(mouse_pos) and not (self.container or self.shop):
            rows = (len(available_recipes(self.stations)) + COLS - 1) // COLS
            self.recipe_scroll = max(0, min(max(0, rows - 3), self.recipe_scroll - dy))
        else:
            self.selected = (self.selected - dy) % COLS

    def handle_click(self, pos, button, game):
        """Returns True if the click was consumed by the UI."""
        shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
        n_slots = COLS * ROWS if self.open else COLS
        for i in range(n_slots):
            if self.slot_rect(i).collidepoint(pos):
                if not self.open:
                    self.selected = i
                elif shift and button == 1 and self.inv.slots[i]:
                    self._quick_move(i, game)
                else:
                    self._click_slot(self.inv.slots, i, button)
                return True
        if not self.open:
            return False
        for slot in self.player.equip:
            if self.equip_rect(slot).collidepoint(pos):
                self._click_equip(slot)
                return True
        for rect, action in self._button_rects:
            if rect.collidepoint(pos):
                action(game)
                return True
        if self.shop:
            for rect, (name, price) in self._shop_rects:
                if rect.collidepoint(pos):
                    game.buy(name, price)
                    return True
            if self.lower_rect().collidepoint(pos) and self.cursor:
                game.sell(*self.cursor)
                self.cursor = None
            return self.lower_rect().collidepoint(pos)
        if self.container:
            slots = self.container[1]
            for i in range(len(slots)):
                if self._container_rect(i).collidepoint(pos):
                    if shift and button == 1 and slots[i]:
                        left = self.inv.add(*slots[i])
                        slots[i] = None if not left else [slots[i][0], left]
                    else:
                        self._click_slot(slots, i, button)
                    return True
            return self.lower_rect().collidepoint(pos)
        for rect, recipe in self._recipe_rects:
            if rect.collidepoint(pos):
                if button == 1 and can_craft(self.inv, recipe):
                    self._craft(recipe, game)
                return True
        return self.lower_rect().collidepoint(pos) or self.equip_panel_rect().collidepoint(pos)

    def _quick_move(self, i, game):
        stack = self.inv.slots[i]
        if self.shop:
            game.sell(*stack)
            self.inv.slots[i] = None
        elif self.container:
            left = add_to_slots(self.container[1], *stack)
            self.inv.slots[i] = None if not left else [stack[0], left]
        elif ITEMS[stack[0]].slot:
            self.cursor, self.inv.slots[i] = stack, None
            for slot in self.player.equip:
                if self.player.can_equip(slot, stack[0]) and (not slot.startswith("acc") or
                                                               self.player.equip[slot] is None):
                    self._click_equip(slot)
                    break
            if self.cursor:
                self.inv.slots[i], self.cursor = self.cursor, None

    def _click_slot(self, slots, i, button):
        slot = slots[i]
        cur = self.cursor
        if button == 3:
            if slot is None:
                return
            if cur is None:
                self.cursor = [slot[0], 1]
            elif cur[0] == slot[0] and cur[1] < ITEMS[slot[0]].max_stack:
                cur[1] += 1
            else:
                return
            slot[1] -= 1
            if slot[1] <= 0:
                slots[i] = None
            return
        if cur is None:
            self.cursor, slots[i] = slot, None
        elif slot is None:
            slots[i], self.cursor = cur, None
        elif slot[0] == cur[0]:
            moved = min(ITEMS[slot[0]].max_stack - slot[1], cur[1])
            slot[1] += moved
            cur[1] -= moved
            if cur[1] == 0:
                self.cursor = None
        else:
            slots[i], self.cursor = cur, slot

    def _click_equip(self, slot):
        p = self.player
        held = self.cursor[0] if self.cursor else None
        if held is not None and (self.cursor[1] != 1 or not p.can_equip(slot, held)):
            return
        old = p.equip[slot]
        p.equip[slot] = held
        self.cursor = [old, 1] if old else None
        p.recompute_stats()

    def _craft(self, recipe, game):
        for name, count in recipe.ingredients.items():
            self.inv.remove(name, count)
        left = self.inv.add(recipe.result, recipe.count)
        if left:
            game.drop_item(recipe.result, left)
        game.add_text(f"制作了 {ITEMS[recipe.result].display}", (255, 240, 150))

    def _deposit_all(self, game):
        slots = self.container[1]
        for i in range(COLS, len(self.inv.slots)):
            s = self.inv.slots[i]
            if s:
                left = add_to_slots(slots, *s)
                self.inv.slots[i] = None if not left else [s[0], left]

    def _loot_all(self, game):
        slots = self.container[1]
        for i, s in enumerate(slots):
            if s:
                left = self.inv.add(*s)
                slots[i] = None if not left else [s[0], left]

    # -------------------- drawing --------------------

    def _draw_slot(self, surf, rect, stack, highlight=False, dim=False, label=None):
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
        elif label:
            draw_text(surf, label, rect.center, 14, (140, 150, 200), shadow=False, center=True)

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
                if self.open and self.shop:
                    hover_lines.append(("Shift+左键 出售", (250, 215, 90)))
                elif self.open and self.container:
                    hover_lines.append(("Shift+左键 存入", (200, 220, 255)))

        sel = self.selected_item()
        coins = self.inv.count("coin")
        if not self.open:
            if sel:
                draw_text(surf, ITEMS[sel].display, (ORIGIN[0], ORIGIN[1] + SLOT + 6), 15)
            draw_text(surf, f"金币 {coins}", (ORIGIN[0] + 330, ORIGIN[1] + SLOT + 6), 15, (250, 215, 90))

        self._recipe_rects = []
        self._shop_rects = []
        self._button_rects = []
        if self.open:
            hover_lines = self._draw_equipment(surf, mouse) or hover_lines
            draw_text(surf, f"金币 {coins}", (EQUIP_X, self.equip_panel_rect().bottom + 4), 15, (250, 215, 90))
            if self.shop:
                hover_lines = self._draw_shop(surf, mouse) or hover_lines
            elif self.container:
                hover_lines = self._draw_container(surf, mouse) or hover_lines
            else:
                hover_lines = self._draw_crafting(surf, mouse) or hover_lines

        if self.cursor:
            surf.blit(self.assets.icons[self.cursor[0]], (mouse[0] - 8, mouse[1] - 8))
            if self.cursor[1] > 1:
                draw_text(surf, str(self.cursor[1]), (mouse[0] - 6, mouse[1] + 12), 13)
        elif hover_lines:
            tooltip(surf, hover_lines, mouse)

    def _draw_equipment(self, surf, mouse):
        p = self.player
        panel(surf, self.equip_panel_rect(), 120)
        hover = None
        for slot, name in p.equip.items():
            rect = self.equip_rect(slot)
            label = EQUIP_LABELS.get(slot, "饰")
            self._draw_slot(surf, rect, [name, 1] if name else None, label=label)
            if name and rect.collidepoint(mouse) and self.cursor is None:
                hover = item_tooltip(name)
        r = self.equip_panel_rect()
        draw_text(surf, f"防御 {p.defense}", (r.x + 6, r.bottom - 22), 15, (200, 220, 255))
        return hover

    def _panel_title(self, surf, text):
        rect = self.lower_rect()
        draw_text(surf, text, (rect.x + 4, rect.y - 24), 15, (255, 240, 150))
        panel(surf, rect, 150)
        return rect

    def _button(self, surf, rect, text, action):
        pygame.draw.rect(surf, (60, 80, 170), rect, border_radius=4)
        pygame.draw.rect(surf, (220, 220, 255), rect, 1, border_radius=4)
        draw_text(surf, text, rect.center, 14, center=True)
        self._button_rects.append((rect, action))

    def _is_furnace(self):
        from tiles import TILES
        return bool(self.container) and TILES[self.player.world.objects.get(self.container[0], 0)].kind == "furnace"

    def _container_rect(self, i):
        rect = self.lower_rect()
        if self._is_furnace():
            x, y = ((rect.x + 60, rect.y + 16), (rect.x + 60, rect.y + 84), (rect.x + 260, rect.y + 50))[i]
            return pygame.Rect(x, y, SLOT, SLOT)
        row, col = divmod(i, COLS)
        return pygame.Rect(rect.x + 4 + col * (SLOT + PAD), rect.y + 4 + row * (SLOT + PAD), SLOT, SLOT)

    def _draw_container(self, surf, mouse):
        anchor, slots, title = self.container
        rect = self._panel_title(surf, title)
        hover = None
        furnace = self._is_furnace()
        labels = ("原料", "燃料", "产出") if furnace else ()
        for i, stack in enumerate(slots):
            r = self._container_rect(i)
            self._draw_slot(surf, r, stack, label=labels[i] if furnace else None)
            if stack and r.collidepoint(mouse) and self.cursor is None:
                hover = item_tooltip(stack[0], stack[1]) + [("Shift+左键 取出", (200, 220, 255))]
        if furnace:
            self._draw_furnace_state(surf, rect, anchor, slots)
            return hover
        by = rect.bottom - 30
        self._button(surf, pygame.Rect(rect.x + 6, by, 110, 24), "全部存入", self._deposit_all)
        self._button(surf, pygame.Rect(rect.x + 124, by, 110, 24), "全部取出", self._loot_all)
        hint = self.container_hint()
        if hint:
            draw_text(surf, hint, (rect.x + 244, by + 3), 13, (220, 220, 220))
        return hover

    def _draw_furnace_state(self, surf, rect, anchor, slots):
        from items import SMELTING, FUEL
        progress, fuel_left = self.player.world.furnaces.get(anchor, [0, 0])
        src = slots[0][0] if slots[0] else None
        total = SMELTING[src][2] if src in SMELTING else 1
        bar = pygame.Rect(rect.x + 120, rect.y + 64, 120, 12)
        pygame.draw.rect(surf, (40, 40, 60), bar, border_radius=3)
        pygame.draw.rect(surf, (255, 170, 60), (bar.x, bar.y, int(bar.w * min(1, progress / total)), bar.h),
                         border_radius=3)
        pygame.draw.rect(surf, (220, 220, 255), bar, 1, border_radius=3)
        draw_text(surf, f"燃料剩余 {fuel_left} 次" if fuel_left else "无燃料", (rect.x + 120, rect.y + 90), 13,
                  (255, 200, 120) if fuel_left else (200, 200, 200))
        if src in SMELTING:
            need, out, _ = SMELTING[src]
            info = f"{need} {ITEMS[src].display} → 1 {ITEMS[out].display}"
        else:
            info = "可烧炼：矿石→锭、石块/砂岩/泥浆/黑曜石→砖、生肉→烤肉"
        draw_text(surf, info, (rect.x + 12, rect.bottom - 28), 13, (220, 220, 220))
        draw_text(surf, "燃料：" + "、".join(f"{ITEMS[n].display}({v}次)" for n, v in FUEL.items()),
                  (rect.x + 320, rect.y + 16), 13, (220, 200, 160))

    def container_hint(self):
        from tiles import TILES
        anchor, slots, _ = self.container
        name = TILES[self.player.world.objects.get(anchor, 0)].name
        if name == "shipping_bin":
            total = sum(ITEMS[s[0]].value * s[1] for s in slots if s)
            return f"早上 6:00 自动售出，预计 {total} 金币"
        return ""

    def _draw_shop(self, surf, mouse):
        npc = self.shop
        rect = self._panel_title(surf, f"{npc.name} 的商店（把物品拖到这里或 Shift+左键 出售）")
        hover = None
        for k, (name, price) in enumerate(npc.shop_items()):
            row, col = divmod(k, COLS)
            r = pygame.Rect(rect.x + 4 + col * (SLOT + PAD), rect.y + 4 + row * (SLOT + PAD + 12), SLOT, SLOT)
            self._draw_slot(surf, r, [name, 1])
            draw_text(surf, str(price), (r.centerx, r.bottom + 6), 12, (250, 215, 90), center=True)
            self._shop_rects.append((r, (name, price)))
            if r.collidepoint(mouse) and self.cursor is None:
                hover = item_tooltip(name) + [(f"购买价 {price} 金币（左键购买）", (250, 215, 90))]
        return hover

    def _draw_crafting(self, surf, mouse):
        names = "、".join(STATION_NAMES[s] for s in sorted(self.stations)) or "无"
        rect = self._panel_title(surf, f"制作（附近制作站：{names}）")
        recipes = available_recipes(self.stations)
        recipes.sort(key=lambda r: not can_craft(self.inv, r))
        start = self.recipe_scroll * COLS
        hover = None
        for k, recipe in enumerate(recipes[start:start + COLS * 3]):
            row, col = divmod(k, COLS)
            r = pygame.Rect(rect.x + 4 + col * (SLOT + PAD), rect.y + 4 + row * (SLOT + PAD), SLOT, SLOT)
            ok = can_craft(self.inv, recipe)
            self._draw_slot(surf, r, [recipe.result, recipe.count], dim=not ok)
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
        if len(recipes) > COLS * 3:
            draw_text(surf, f"滚轮翻页（{len(recipes)} 个配方）", (rect.right - 170, rect.bottom - 22), 13,
                      (200, 200, 200))
        return hover
