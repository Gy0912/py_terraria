import pygame
from settings import *
from player import Player
from world import World
from background import Background
from camera import Camera


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 22)

    # ------------------------------------------------------------------
    # New game
    # ------------------------------------------------------------------

    def new(self):
        self.world = World()
        self.background = Background(self.screen)
        self.player = Player(self.world)
        self.camera = Camera()
        self.run()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.camera.update(self.player.x, self.player.y)
        biome = self.world.get_biome(self.player.x, self.player.y)
        self.background.update(biome)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                world_x = mx + self.camera.x
                world_y = my + self.camera.y
                tx = world_x // TILE_SIZE
                ty = world_y // TILE_SIZE
                if event.button == 1:
                    removed = self.world.remove_tile(tx, ty)
                    if removed:
                        self.player.inventory[removed] = self.player.inventory.get(removed, 0) + 1
                elif event.button == 3:
                    if self.player.selected_block and self.player.inventory.get(self.player.selected_block, 0) > 0:
                        if self.world.get_tile(tx, ty) is None:
                            self.world.set_tile(tx, ty, self.player.selected_block)
                            self.player.inventory[self.player.selected_block] -= 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.player.selected_block = "dirt"
                elif event.key == pygame.K_2:
                    self.player.selected_block = "stone"
                elif event.key == pygame.K_3:
                    self.player.selected_block = "sand"
                elif event.key == pygame.K_4:
                    self.player.selected_block = "wood"
                elif event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.screen.fill(BLACK)
        self.background.draw(self.player.x, self.player.y)
        self._draw_tiles()
        self.player.draw(self.screen, self.camera)
        self._draw_hud()
        self._draw_cursor_highlight()
        pygame.display.flip()

    def _draw_tiles(self):
        """Render only tiles visible on screen."""
        cam_x, cam_y = self.camera.x, self.camera.y
        start_tx = max(cam_x // TILE_SIZE, 0)
        start_ty = max(cam_y // TILE_SIZE, 0)
        end_tx = min((cam_x + SCREEN_WIDTH) // TILE_SIZE + 1, ACTUAL_MAP_WIDTH)
        end_ty = min((cam_y + SCREEN_HEIGHT) // TILE_SIZE + 1, ACTUAL_MAP_HEIGHT)

        for tx in range(start_tx, end_tx):
            for ty in range(start_ty, end_ty):
                tile = self.world.get_tile(tx, ty)
                if tile is not None:
                    color = TILE_COLORS.get(tile, GRAY)
                    sx = tx * TILE_SIZE - cam_x
                    sy = ty * TILE_SIZE - cam_y
                    pygame.draw.rect(self.screen, color, (sx, sy, TILE_SIZE, TILE_SIZE))

    def _draw_hud(self):
        """Minimal HUD: coords, biome, inventory summary."""
        biome = self.world.get_biome(self.player.x, self.player.y)
        tx = int(self.player.x) // TILE_SIZE
        ty = int(self.player.y) // TILE_SIZE
        info = f"Pos: ({tx}, {ty})  Biome: {biome}  FPS: {int(self.clock.get_fps())}"
        surf = self.font.render(info, True, WHITE)
        self.screen.blit(surf, (8, 8))

        inv_parts = []
        for item, count in self.player.inventory.items():
            if count > 0:
                inv_parts.append(f"{item}:{count}")
        inv_text = "Inventory: " + "  ".join(inv_parts) if inv_parts else "Inventory: (empty)"
        inv_surf = self.font.render(inv_text, True, WHITE)
        self.screen.blit(inv_surf, (8, 28))

        sel = self.player.selected_block or "none"
        sel_surf = self.font.render(f"Selected [1-4]: {sel}", True, YELLOW)
        self.screen.blit(sel_surf, (8, 48))

    def _draw_cursor_highlight(self):
        """Highlight the tile under the mouse cursor."""
        mx, my = pygame.mouse.get_pos()
        world_x = mx + self.camera.x
        world_y = my + self.camera.y
        tx = world_x // TILE_SIZE
        ty = world_y // TILE_SIZE
        sx = tx * TILE_SIZE - self.camera.x
        sy = ty * TILE_SIZE - self.camera.y
        pygame.draw.rect(self.screen, WHITE, (sx, sy, TILE_SIZE, TILE_SIZE), 1)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------

    def show_start_screen(self):
        self.screen.fill(BLACK)
        waiting = True
        font = pygame.font.Font(None, 48)
        version_font = pygame.font.Font(None, 24)
        image = pygame.image.load(IMAGES_PATH["start_screen"]).convert()
        image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        enter_text = font.render("Press 'ENTER' to Start Game", True, WHITE)
        text_x = (SCREEN_WIDTH - enter_text.get_width()) // 2
        text_y = SCREEN_HEIGHT - 100
        version_text = version_font.render("Version 0.1.0", True, (200, 200, 200))
        show_text = True
        blink_time = 0
        blink_clock = pygame.time.Clock()
        while waiting:
            self.clock.tick(FPS)
            self.screen.blit(image, (0, 0))
            blink_time += blink_clock.tick(FPS)
            if blink_time >= 400:
                show_text = not show_text
                blink_time = 0
            if show_text:
                self.screen.blit(enter_text, (text_x, text_y))
            self.screen.blit(version_text, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                waiting = False

    def show_game_over_screen(self):
        pass

    def pause_screen(self):
        pass


if __name__ == '__main__':
    game = Game()
    game.show_start_screen()
    while game.running:
        game.new()
    pygame.quit()
