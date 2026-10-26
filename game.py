import pygame
from settings import *
from player import Player
from world import World
from background import Background
from camera import Camera
from healthbar import HealthBar
from manabar import ManaBar
from creatures import CreatureManager
from inventory import InventoryUI


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
        self.health_bar = HealthBar(100)
        self.mana_bar = ManaBar(50)
        self.creature_mgr = CreatureManager(self.world)
        self.inventory_ui = InventoryUI()
        self.damage_cooldown = 0
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
        # Apply fall damage
        if self.player.fall_damage > 0:
            self.health_bar.take_damage(self.player.fall_damage)
            self.player.fall_damage = 0
        # Track fall start when not on ground
        if not self.player.on_ground and self.player.vy <= 0:
            self.player.fall_start_y = self.player.y
        # Creatures
        self.creature_mgr.update(self.player.x, self.player.y)
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
        else:
            contact_dmg = self.creature_mgr.check_player_collision(self.player)
            if contact_dmg > 0:
                self.health_bar.take_damage(contact_dmg)
                self.damage_cooldown = 30  # invincibility frames
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
                world_x = int(mx + self.camera.x)
                world_y = int(my + self.camera.y)
                tx = world_x // TILE_SIZE
                ty = world_y // TILE_SIZE
                if event.button == 1:
                    # Attack creature first, then mine tile
                    hit_creature = False
                    click_rect = pygame.Rect(world_x - 4, world_y - 4, 8, 8)
                    for c in self.creature_mgr.creatures:
                        if c.alive and c._get_rect().colliderect(click_rect):
                            c.take_damage(15)
                            hit_creature = True
                            break
                    if not hit_creature:
                        removed = self.world.remove_tile(tx, ty)
                        if removed:
                            self.player.inventory[removed] = self.player.inventory.get(removed, 0) + 1
                elif event.button == 3:
                    selected = self.inventory_ui.get_selected_item()
                    if selected and self.player.inventory.get(selected, 0) > 0:
                        if self.world.get_tile(tx, ty) is None:
                            self.world.set_tile(tx, ty, selected)
                            self.player.inventory[selected] -= 1
            # Inventory UI handles key/scroll for slot selection
            if self.inventory_ui.handle_event(event):
                self.player.selected_block = self.inventory_ui.get_selected_item()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.screen.fill(BLACK)
        self.background.draw(self.player.x, self.player.y)
        self._draw_tiles()
        self.creature_mgr.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self._draw_hud()
        self._draw_cursor_highlight()
        self.health_bar.draw(self.screen)
        self.mana_bar.draw(self.screen)
        self.inventory_ui.draw(self.screen, self.player.inventory)
        pygame.display.flip()

    def _draw_tiles(self):
        """Render only tiles visible on screen."""
        cam_x, cam_y = int(self.camera.x), int(self.camera.y)
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
        """Minimal HUD: coords, biome, FPS."""
        biome = self.world.get_biome(self.player.x, self.player.y)
        tx = int(self.player.x) // TILE_SIZE
        ty = int(self.player.y) // TILE_SIZE
        info = f"Pos: ({tx}, {ty})  Biome: {biome}  FPS: {int(self.clock.get_fps())}"
        surf = self.font.render(info, True, WHITE)
        self.screen.blit(surf, (8, 8))

    def _draw_cursor_highlight(self):
        """Highlight the tile under the mouse cursor."""
        mx, my = pygame.mouse.get_pos()
        world_x = int(mx + self.camera.x)
        world_y = int(my + self.camera.y)
        tx = world_x // TILE_SIZE
        ty = world_y // TILE_SIZE
        sx = tx * TILE_SIZE - int(self.camera.x)
        sy = ty * TILE_SIZE - int(self.camera.y)
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
