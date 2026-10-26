import pygame
from settings import *


class InventoryUI:
    """Visual inventory bar at the bottom of the screen."""

    SLOT_SIZE = 40
    PADDING = 4
    SLOTS = 9

    def __init__(self):
        self.selected_slot = 0
        self.slot_items = ["dirt", "stone", "sand", "wood", "leaves",
                           None, None, None, None]
        self.font = pygame.font.Font(None, 18)
        self.bar_width = self.SLOTS * (self.SLOT_SIZE + self.PADDING) + self.PADDING
        self.bar_x = (SCREEN_WIDTH - self.bar_width) // 2
        self.bar_y = SCREEN_HEIGHT - self.SLOT_SIZE - self.PADDING * 2

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_9:
                self.selected_slot = event.key - pygame.K_1
                return True
        elif event.type == pygame.MOUSEWHEEL:
            self.selected_slot = (self.selected_slot - event.y) % self.SLOTS
            return True
        return False

    def get_selected_item(self):
        return self.slot_items[self.selected_slot]

    def draw(self, surface, player_inventory):
        for i in range(self.SLOTS):
            x = self.bar_x + i * (self.SLOT_SIZE + self.PADDING) + self.PADDING
            y = self.bar_y

            # Slot background
            color = (60, 60, 60) if i != self.selected_slot else (100, 100, 40)
            pygame.draw.rect(surface, color, (x, y, self.SLOT_SIZE, self.SLOT_SIZE))
            pygame.draw.rect(surface, WHITE, (x, y, self.SLOT_SIZE, self.SLOT_SIZE), 1)

            item = self.slot_items[i]
            if item:
                tile_color = TILE_COLORS.get(item, GRAY)
                inner = 8
                pygame.draw.rect(surface, tile_color,
                                 (x + inner, y + inner,
                                  self.SLOT_SIZE - inner * 2, self.SLOT_SIZE - inner * 2))
                count = player_inventory.get(item, 0)
                if count > 0:
                    count_text = self.font.render(str(count), True, WHITE)
                    surface.blit(count_text, (x + 2, y + self.SLOT_SIZE - 16))
