import pygame
from .player import Player
from .platform import Platform
from .hazard import Hazard
from .sounds import SoundManager

# Game Engine

WHITE = (255, 255, 255)
BROWN = (150, 100, 60)
RED = (220, 60, 60)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)

# Difficulty settings: (gravity, jump strength)
DIFFICULTIES = {
    "Easy": (0.50, -12),
    "Medium": (0.60, -12),
    "Hard": (0.75, -11),
}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.difficulty = "Medium"
        self.gravity = DIFFICULTIES[self.difficulty][0]
        self.max_fall_speed = 20

        self.start_x, self.start_y = 40, height - 120
        self.player = Player(self.start_x, self.start_y)
        self.player.jump_strength = DIFFICULTIES[self.difficulty][1]

        # A simple hand-built level: platforms with gaps between them
        # (falling into a gap means falling off the bottom of the
        # screen), one hazard, and a goal near the right edge.
        ground_y = height - 40
        self.platforms = [
            Platform(0, ground_y, 160),
            Platform(220, ground_y, 140),
            Platform(420, ground_y - 60, 120),
            Platform(600, ground_y, 180),
        ]
        self.hazards = [Hazard(240, ground_y - 14, 100)]
        self.goal_x = 740

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over = False
        self.quit_requested = False
        self.sounds = SoundManager()
        self.big_font = pygame.font.SysFont("Arial", 56, bold=True)

    def start_game(self, difficulty):
        """(Re)start the game with the chosen difficulty."""
        self.difficulty = difficulty
        self.gravity, self.player.jump_strength = DIFFICULTIES[difficulty]
        self.player.reset(self.start_x, self.start_y)
        self.score = 0
        self.game_over = False

    def end_game(self):
        self.game_over = True
        self.sounds.play("die")

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.game_over:
            if event.key == pygame.K_1:
                self.start_game("Easy")
            elif event.key == pygame.K_2:
                self.start_game("Medium")
            elif event.key == pygame.K_3:
                self.start_game("Hard")
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.quit_requested = True
        elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            if self.player.jump():
                self.sounds.play("jump")

    def handle_input(self):
        if self.game_over:
            self.player.vx = 0
            return
        keys = pygame.key.get_pressed()
        self.player.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.vx = -self.player.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.vx = self.player.speed

    def update(self):
        if self.game_over:
            return

        player = self.player
        player.vy = min(player.vy + self.gravity, self.max_fall_speed)
        player.x = max(0, player.x + player.vx)

        # Swept collision: compare where the player's feet were BEFORE this
        # frame's move with where they are after it. If the feet crossed a
        # platform's top surface, land on it - no matter how fast we fell.
        prev_bottom = player.y + player.height
        player.y += player.vy
        new_bottom = player.y + player.height
        player.on_ground = False
        if player.vy >= 0:
            for platform in self.platforms:
                overlaps_x = (player.x < platform.x + platform.width
                              and player.x + player.width > platform.x)
                crossed_top = (prev_bottom <= platform.y + 0.01
                               and new_bottom >= platform.y)
                if overlaps_x and crossed_top:
                    player.y = platform.y - player.height
                    player.vy = 0
                    player.on_ground = True
                    break

        for hazard in self.hazards:
            if self.player.rect().colliderect(hazard.rect()):
                self.end_game()
                return

        if self.player.y > self.height:
            self.end_game()
            return

        if self.player.x >= self.goal_x:
            self.score += 1
            self.sounds.play("goal")
            self.player.x, self.player.y = self.start_x, self.start_y
            self.player.vy = 0

    def render(self, screen):
        for platform in self.platforms:
            pygame.draw.rect(screen, BROWN, platform.rect())
        for hazard in self.hazards:
            pygame.draw.rect(screen, RED, hazard.rect())

        goal_rect = pygame.Rect(self.goal_x, 0, 6, self.height)
        pygame.draw.rect(screen, GREEN, goal_rect)

        pygame.draw.rect(screen, WHITE, self.player.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            self.render_game_over(screen)

    def render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        lines = [
            (self.big_font, "GAME OVER", RED, 110),
            (self.font, f"Final Score: {self.score}", WHITE, 190),
            (self.font, "Play again - choose difficulty:", WHITE, 255),
            (self.font, "1 - Easy     2 - Medium     3 - Hard", WHITE, 300),
            (self.font, "Esc / Q - Exit", WHITE, 360),
        ]
        for font, text, color, y in lines:
            surf = font.render(text, True, color)
            screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))
