"""World selection screen shown after "开始游戏": save slots, create, load and delete."""
import random
import time

import pygame

from settings import *
from ui import draw_text, panel, Button
import save


def _fmt_time(seconds):
    h, rem = divmod(int(seconds), 3600)
    return f"{h} 小时 {rem // 60} 分" if h else f"{rem // 60} 分 {rem % 60} 秒"


class TextBox:
    def __init__(self, rect, text="", digits=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.digits = digits
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif self.active and event.type == pygame.TEXTINPUT:
            add = "".join(c for c in event.text if c.isdigit()) if self.digits else event.text
            self.text = (self.text + add)[:16]
        elif self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]

    def draw(self, surf, label):
        draw_text(surf, label, (self.rect.x, self.rect.y - 24), 16)
        pygame.draw.rect(surf, (20, 25, 50), self.rect, border_radius=4)
        pygame.draw.rect(surf, (255, 230, 120) if self.active else (180, 180, 220), self.rect, 2, border_radius=4)
        caret = "|" if self.active and (pygame.time.get_ticks() // 500) % 2 else ""
        draw_text(surf, self.text + caret, (self.rect.x + 10, self.rect.y + 8), 18, shadow=False)


def world_select(game):
    """Returns ("new", slot, name, seed), ("load", slot) or None to go back."""
    screen = game.screen
    cx = SCREEN_WIDTH // 2
    confirm = {}            # slot -> time of first delete click
    creating = None         # slot being created
    name_box = TextBox((cx - 180, 260, 360, 40))
    seed_box = TextBox((cx - 180, 340, 360, 40), digits=True)
    back = Button("返回", (cx, SCREEN_HEIGHT - 50), (180, 44), 20)
    pygame.key.start_text_input()
    try:
        while True:
            game.clock.tick(FPS)
            slots = save.list_slots()
            cards = []
            for i in range(SAVE_SLOTS):
                rect = pygame.Rect(cx - 330, 110 + i * 140, 660, 120)
                if slots[i]:
                    enter = Button("进入游戏", (rect.right - 190, rect.centery), (130, 40), 18)
                    label = "确认删除？" if time.time() - confirm.get(i, 0) < 3 else "删除"
                    delete = Button(label, (rect.right - 60, rect.centery), (100, 40), 16)
                    cards.append((rect, slots[i], [(enter, "enter"), (delete, "delete")]))
                else:
                    new = Button("新建世界", (rect.right - 110, rect.centery), (160, 40), 18)
                    cards.append((rect, None, [(new, "new")]))
            create_btn = Button("创建", (cx - 70, 430), (120, 44), 20)
            cancel_btn = Button("取消", (cx + 70, 430), (120, 44), 20)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.running = False
                    return None
                if creating is not None:
                    name_box.handle(event)
                    seed_box.handle(event)
                    if create_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
                        seed = int(seed_box.text) if seed_box.text else random.randrange(1 << 30)
                        return ("new", creating, name_box.text.strip() or f"世界 {creating + 1}", seed)
                    if cancel_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        creating = None
                    continue
                if back.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return None
                for i, (rect, meta, buttons) in enumerate(cards):
                    for b, action in buttons:
                        if not b.clicked(event):
                            continue
                        if action == "enter":
                            return ("load", i)
                        if action == "new":
                            creating = i
                            name_box.text = f"世界 {i + 1}"
                            seed_box.text = ""
                            name_box.active = True
                        if action == "delete":
                            if time.time() - confirm.get(i, 0) < 3:
                                save.delete_slot(i)
                                confirm.pop(i, None)
                            else:
                                confirm[i] = time.time()

            screen.blit(game.start_image, (0, 0))
            dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 20, 170))
            screen.blit(dim, (0, 0))
            draw_text(screen, "选择世界", (cx, 60), 34, (255, 235, 140), center=True, bold=True)
            if creating is not None:
                box = pygame.Rect(cx - 220, 190, 440, 280)
                panel(screen, box, 230)
                draw_text(screen, f"新建世界（存档 {creating + 1}）", (box.x + 20, box.y + 12), 20, (255, 240, 150))
                name_box.draw(screen, "世界名称")
                seed_box.draw(screen, "种子（留空则随机）")
                create_btn.draw(screen)
                cancel_btn.draw(screen)
            else:
                for i, (rect, meta, buttons) in enumerate(cards):
                    panel(screen, rect, 200)
                    if meta:
                        draw_text(screen, f"{i + 1}. {meta['name']}", (rect.x + 20, rect.y + 14), 22,
                                  (255, 240, 150), bold=True)
                        draw_text(screen, f"第 {meta['day']} 天 · 游玩 {_fmt_time(meta['playtime'])} · "
                                          f"已击败 {len(meta.get('bosses', []))} 个 Boss",
                                  (rect.x + 20, rect.y + 52), 15)
                        draw_text(screen, f"上次保存 {meta['saved']} · 种子 {meta['seed']}",
                                  (rect.x + 20, rect.y + 80), 14, (200, 200, 220))
                    else:
                        draw_text(screen, f"{i + 1}. 空存档", (rect.x + 20, rect.y + 44), 22, (180, 180, 200))
                    for b, _ in buttons:
                        b.draw(screen)
                back.draw(screen)
            pygame.display.flip()
    finally:
        pygame.key.stop_text_input()
