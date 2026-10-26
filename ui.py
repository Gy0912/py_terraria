"""Shared UI helpers: CJK-capable fonts, text, buttons, panels and tooltips."""
import os

import pygame

from settings import FONT_CANDIDATES, FONT_FILES

_fonts = {}
_font_path = None


def _find_font_path():
    font_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in FONT_FILES:
        path = os.path.join(font_dir, name)
        if os.path.exists(path):
            return path
    # pygame's registry scan can raise on some Windows installs, so it is only a fallback
    for name in FONT_CANDIDATES:
        try:
            path = pygame.font.match_font(name)
        except Exception:
            return None
        if path:
            return path
    return None


def get_font(size, bold=False):
    global _font_path
    key = (size, bold)
    if key not in _fonts:
        if _font_path is None:
            _font_path = _find_font_path() or ""
        if _font_path:
            font = pygame.font.Font(_font_path, size)
            font.set_bold(bold)
        else:
            font = pygame.font.Font(None, size + 4)
        _fonts[key] = font
    return _fonts[key]


def draw_text(surf, text, pos, size=16, color=(255, 255, 255), shadow=True, center=False, bold=False):
    font = get_font(size, bold)
    img = font.render(text, True, color)
    x, y = pos
    if center:
        x -= img.get_width() // 2
        y -= img.get_height() // 2
    if shadow:
        surf.blit(font.render(text, True, (0, 0, 0)), (x + 2, y + 2))
    surf.blit(img, (x, y))
    return img.get_width()


def panel(surf, rect, alpha=170, border=(220, 220, 255)):
    box = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    box.fill((20, 25, 60, alpha))
    surf.blit(box, rect[:2])
    pygame.draw.rect(surf, border, rect, 1, border_radius=4)


def tooltip(surf, lines, pos):
    """lines: list of (text, color)."""
    font = get_font(15)
    imgs = [font.render(t, True, c) for t, c in lines]
    w = max(i.get_width() for i in imgs) + 14
    h = sum(i.get_height() for i in imgs) + 10
    x, y = pos[0] + 16, pos[1] + 16
    sw, sh = surf.get_size()
    x = min(x, sw - w - 4)
    y = min(y, sh - h - 4)
    panel(surf, (x, y, w, h), 220)
    yy = y + 5
    for img in imgs:
        surf.blit(img, (x + 7, yy))
        yy += img.get_height()


class Button:
    def __init__(self, text, center, size=(240, 52), font_size=24):
        self.text = text
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.font_size = font_size

    def hovered(self, mouse_pos=None):
        return self.rect.collidepoint(mouse_pos or pygame.mouse.get_pos())

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surf):
        hover = self.hovered()
        box = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        box.fill((70, 90, 170, 230) if hover else (30, 40, 90, 200))
        surf.blit(box, self.rect.topleft)
        pygame.draw.rect(surf, (255, 230, 120) if hover else (200, 200, 240), self.rect, 2, border_radius=6)
        draw_text(surf, self.text, self.rect.center, self.font_size,
                  (255, 240, 150) if hover else (255, 255, 255), center=True)
