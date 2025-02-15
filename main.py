import pygame
from settings import *
from player import *
from world import *
from creatures import *

class Game:
    def __init__(self):
        # Initialize game window, etc.
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False

    def new(self):
        # Start a new game
        generate()
        self.grid = {}
        # create player, background, creatures
        self.player = Player()
        self.background = Background()
        self.creatures = Creatures()
        # create world
        self.world = World()

        self.run()

    def run(self):
        # Game loop
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def update(self):
        # Game loop - update
        self.player.update()
        self.background.update()
        self.creatures.update()
        self.world.update()

    def events(self):
        # Game loop - events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
    
    def draw(self):
        # Game loop - draw
        self.screen.fill(BLACK)
        self.background.draw()
        self.creatures.draw()
        self.player.draw()
        self.world.draw()
        pygame.display.flip()

    def show_start_screen(self):
        # Show start screen
        self.screen.fill(BLACK)
        waiting = True
        # text font
        font = pygame.font.Font(None, 48)
        version_font = pygame.font.Font(None, 24)
        # image path
        image = pygame.image.load(IMAGES_PATH["start_screen"]).convert()
        image = pygame.transform.scale(image, (WIDTH, HEIGHT))
        # basic text infos
        enter_text = font.render("Press 'ENTER' to Start Game", True, WHITE)
        text_x = (self.screen.get_width() - enter_text.get_width()) // 2
        text_y = self.screen.get_height() - 100
        version_text = version_font.render("Version 0.0.1", True, (200, 200, 200))
        # text blink
        show_text = True
        blink_time = 0
        clock = pygame.time.Clock()
        while waiting:
            self.clock.tick(FPS)
            self.screen.blit(image, (0, 0))
            # show text
            blink_time += clock.tick(FPS)
            if blink_time >= 400:
                show_text = not show_text
                blink_time = 0
            if show_text:
                self.screen.blit(enter_text, (text_x, text_y))
            self.screen.blit(version_text, (self.screen.get_width() - 100, self.screen.get_height() - 30))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                waiting = False
    
    def show_game_over_screen(self):
        # Show game over screen
        pass

    def pause_screen(self):
        # Pause game
        pass

if __name__ == '__main__':
    game = Game()
    game.show_start_screen()
    while game.running:
        game.new()
    pygame.quit()