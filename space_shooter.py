"""
Space Shooter Game
A simple 2D space shooter built with Pygame where the player controls a spaceship,
shoots lasers at falling meteors, and tries to survive as long as possible.

Features:
- Player movement and shooting mechanics
- Meteor spawning with random movement patterns
- Collision detection and explosion animations
- Scoring system based on survival time and meteor destruction
- Level progression system with increasing difficulty
- Lives/heart system
- Game over screen with final score
"""

import pygame
import random
import sys

# Initialize pygame
pygame.init()

# --------------------------------
# GAME CONSTANTS AND CONFIGURATIONS
# --------------------------------
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
FPS = 120  # Frames per second cap
BACKGROUND_COLOR = "#0F111A"  # Dark purple background
UI_TEXT_COLOR = "#ECF0F1"

# Player settings
PLAYER_SPEED = 600
INITIAL_LASER_COOLDOWN = 400  # Milliseconds between shots (will increase with levels)

# Scoring system
SURVIVAL_POINTS_PER_SECOND = 10  # Points gained per second of survival
METEOR_DESTRUCTION_POINTS = 20  # Points gained for destroying a meteor

# Level system thresholds
LEVEL_THRESHOLDS = [0, 300, 600, 900, 1200, 1500, 1800, 2100]  # Score thresholds for levels 1-8
MAX_LEVEL = len(LEVEL_THRESHOLDS)  # Maximum level (based on threshold list length)

# Difficulty scaling
BASE_METEOR_SPAWN_RATE = 700  # Milliseconds between meteor spawns at level 1
METEOR_SPAWN_RATE_DECREASE = 100  # How much spawn time decreases per level
MIN_METEOR_SPAWN_RATE = 0  # Minimum spawn time (milliseconds)

LASER_COOLDOWN_INCREASE_LEVEL = 3  # Level at which laser cooldown starts increasing
LASER_COOLDOWN_INCREASE = 100  # How much cooldown increases per level
MAX_LASER_COOLDOWN = 800  # Maximum laser cooldown (milliseconds)

# Life system
INITIAL_LIVES = 3  # Number of hearts/lives at game start

# Display setup
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()

# ------------------------
# ASSET LOADING
# ------------------------
# Images
try:
    # Player and projectiles
    player_surf = pygame.image.load("images/player.png").convert_alpha()
    laser_surf = pygame.image.load("images/laser.png").convert_alpha()

    # Environment
    star_surf = pygame.image.load("images/star.png").convert_alpha()
    meteor_surf = pygame.image.load("images/meteor.png").convert_alpha()

    # UI elements
    heart_full_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.polygon(heart_full_surf, (255, 0, 0), [(15, 5), (25, 15), (15, 25), (5, 15)])
    heart_empty_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.polygon(heart_empty_surf, (100, 100, 100), [(15, 5), (25, 15), (15, 25), (5, 15)], 2)

    # Animation frames
    explosion_frames = [
        pygame.image.load(f"images/explosion/{i}.png").convert_alpha()
        for i in range(21)
    ]
except pygame.error as e:
    print(f"Error loading game assets: {e}")
    print("Please make sure all required image files exist in the correct paths.")
    pygame.quit()
    sys.exit()

# Fonts
try:
    main_font = pygame.font.Font("images/Frank.ttf", 32)
    game_over_font = pygame.font.Font("images/GameBuble.otf", 64)
    # Fallback to system font if custom font not found
except pygame.error:
    print("Custom font not found, using system default.")
    main_font = pygame.font.SysFont("arial", 32)
    game_over_font = pygame.font.SysFont("arial", 64)

# Audio
try:
    laser_sound = pygame.mixer.Sound("audio/laser.wav")
    laser_sound.set_volume(0.1)

    explosion_sound = pygame.mixer.Sound("audio/explosion.wav")
    explosion_sound.set_volume(0.1)

    damage_sound = pygame.mixer.Sound("audio/damage.ogg")
    damage_sound.set_volume(0.2)

    game_over_sound = pygame.mixer.Sound("audio/game_over.wav")
    game_over_sound.set_volume(0.3)

    game_music = pygame.mixer.Sound("audio/game_music.wav")
    game_music.set_volume(0.05)
    game_music.play(loops=-1)
except pygame.error as e:
    print(f"Error loading audio: {e}")
    print("Game will continue without sound.")


# ------------------------
# SPRITE CLASSES
# ------------------------

class Player(pygame.sprite.Sprite):
    """Player spaceship that can move and shoot lasers"""

    def __init__(self):
        super().__init__()
        # Visual and positioning
        self.image = player_surf
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.mask = pygame.mask.from_surface(self.image)  # For pixel-perfect collision

        # Movement
        self.direction = pygame.math.Vector2()
        self.speed = PLAYER_SPEED

        # Shooting mechanics
        self.can_shoot = True
        self.laser_cooldown = INITIAL_LASER_COOLDOWN
        self.laser_shoot_time = 0

        # Player stats
        self.lives = INITIAL_LIVES
        self.alive = True

    def input(self):
        """Process keyboard input for movement"""
        keys = pygame.key.get_pressed()

        # Horizontal movement: D (right) - A (left)
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])

        # Vertical movement: S (down) - W (up)
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])

        # Normalize for consistent diagonal speed
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()

    def move(self, dt):
        """Move the player based on current direction and delta time"""
        # Move horizontally
        self.rect.centerx += self.direction.x * self.speed * dt

        # Move vertically
        self.rect.centery += self.direction.y * self.speed * dt

        # Keep player within screen bounds
        self.rect.clamp_ip(pygame.FRect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

    def shoot_laser(self):
        """Create a new laser if cooldown has expired"""
        recent_keys = pygame.key.get_just_pressed()

        if recent_keys[pygame.K_SPACE] and self.can_shoot:
            # Create new laser at player's position
            Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))

            # Play sound effect
            laser_sound.play()

            # Start cooldown
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()

    def laser_timer(self):
        """Manage cooldown timer for shooting lasers"""
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            # Check if cooldown period has passed
            if current_time - self.laser_shoot_time >= self.laser_cooldown:
                self.can_shoot = True

    def take_damage(self):
        """Reduce player lives when hit by a meteor"""
        self.lives -= 1
        damage_sound.play()

        # Check if player has run out of lives
        if self.lives <= 0:
            self.alive = False
            game_over_sound.play()

    def update_laser_cooldown(self, current_level):
        """Update laser cooldown based on current level"""
        # Only increase cooldown after reaching specified level
        if current_level >= LASER_COOLDOWN_INCREASE_LEVEL:
            level_factor = current_level - LASER_COOLDOWN_INCREASE_LEVEL + 1
            new_cooldown = INITIAL_LASER_COOLDOWN + (level_factor * LASER_COOLDOWN_INCREASE)

            # Cap cooldown at maximum value
            self.laser_cooldown = min(new_cooldown, MAX_LASER_COOLDOWN)
            # print(f"Laser cooldown: {self.laser_cooldown}")

    def update(self, dt, current_level):
        """Update player state for the current frame"""
        self.input()
        self.move(dt)
        self.shoot_laser()
        self.laser_timer()
        self.update_laser_cooldown(current_level)


class Star(pygame.sprite.Sprite):
    """Background star decoration"""

    def __init__(self, surf, groups):
        super().__init__(groups)
        self.image = surf

        # Random position within the screen
        self.rect = self.image.get_frect(center=(
            random.randint(0, WINDOW_WIDTH),
            random.randint(0, WINDOW_HEIGHT)
        ))

        # Stars remain stationary so no update logic needed

    def update(self, dt):
        """Stars don't move, but this is required for sprite group compatibility"""
        pass


class Laser(pygame.sprite.Sprite):
    """Player projectile that moves upward and damages meteors"""

    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom=pos)
        self.speed = 700
        self.mask = pygame.mask.from_surface(self.image)  # For pixel-perfect collision

    def update(self, dt):
        """Move laser upward and destroy if off-screen"""
        # Move upward
        self.rect.centery -= self.speed * dt

        # Remove if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()


class Meteor(pygame.sprite.Sprite):
    """Enemy object that falls from the top of the screen"""

    def __init__(self, surf, groups, speed_multiplier=1.0):
        super().__init__(groups)
        # Store original surface for rotation without quality loss
        self.original_surf = surf
        self.image = self.original_surf

        # Position meteor randomly above the visible screen
        self.rect = self.image.get_frect(center=(
            random.randint(0, WINDOW_WIDTH - self.image.get_width()),
            random.randint(-200, -50)  # Start above the screen
        ))

        # Movement parameters
        self.speed = 500 * speed_multiplier  # Base speed modified by difficulty
        self.direction = pygame.math.Vector2(
            random.uniform(-0.5, 0.5),  # Random horizontal drift
            1  # Always moving downward
        )

        # Rotation parameters
        self.rotation_speed = random.randint(50, 300)  # Degrees per second
        self.rotation = 0  # Current rotation angle

        # Time tracking
        self.creation_time = pygame.time.get_ticks()

        # Collision detection
        self.mask = pygame.mask.from_surface(self.image)  # For pixel-perfect collision

    def update(self, dt):
        """Update meteor position, rotation, and destroy if off-screen too long"""
        # Move based on direction, speed and time
        self.rect.center += self.direction * self.speed * dt

        # Rotate the meteor
        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)

        # Update mask for the rotated image
        self.mask = pygame.mask.from_surface(self.image)

        # Keep the rect centered at the same position after rotation
        old_center = self.rect.center
        self.rect = self.image.get_frect(center=old_center)

        # Check if meteor has been alive too long or is far below screen
        current_time = pygame.time.get_ticks()
        if current_time - self.creation_time >= 5000 or self.rect.top > WINDOW_HEIGHT + 100:
            self.kill()


class AnimatedExplosion(pygame.sprite.Sprite):
    """Explosion animation played when a meteor is destroyed"""

    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames  # List of animation frame images
        self.index = 0  # Current frame index
        self.image = self.frames[self.index]
        self.rect = self.image.get_frect(center=pos)
        self.animation_speed = 30  # Frames per second

        # Play explosion sound
        explosion_sound.play()

    def update(self, dt):
        """Advance animation frames based on time elapsed"""
        # Increment frame index
        self.index += self.animation_speed * dt

        # Check if animation should continue
        if self.index < len(self.frames):
            # Show current frame
            self.image = self.frames[int(self.index)]
        else:
            # End animation when all frames are shown
            self.kill()


# -----------------------
# GAME MANAGEMENT FUNCTIONS
# -----------------------

def spawn_stars(count=20):
    """Create initial background stars"""
    for _ in range(count):
        Star(star_surf, all_sprites)


def get_current_level(score):
    """Determine current level based on score"""
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if score < threshold:
            return i  # Return level index (0-based)

    # If score exceeds all thresholds, return max level
    return len(LEVEL_THRESHOLDS)


def calculate_meteor_spawn_time(level):
    """Calculate meteor spawn interval based on current level"""
    # Decrease spawn time as level increases
    spawn_time = BASE_METEOR_SPAWN_RATE - (level * METEOR_SPAWN_RATE_DECREASE)

    # Ensure spawn time doesn't go below minimum
    # print(f"Meteor Spawn rate = {max(spawn_time, MIN_METEOR_SPAWN_RATE)}")
    return max(spawn_time, MIN_METEOR_SPAWN_RATE)


def check_collisions(player, score):
    """Handle all collision detection and responses"""
    # Player-meteor collision
    if pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask):
        player.take_damage()

    # Laser-meteor collisions
    for laser in laser_sprites:
        meteors_hit = pygame.sprite.spritecollide(laser, meteor_sprites, True, pygame.sprite.collide_mask)
        if meteors_hit:
            # Create explosion animation at collision position
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)

            # Remove the laser
            laser.kill()

            # Award points for destroying meteor
            score += METEOR_DESTRUCTION_POINTS

    return score


def display_ui(surface, score, level, lives):
    """Draw all UI elements (score, level indicator, and hearts)"""
    # Display score at bottom center
    score_surf = main_font.render(f"Score: {score}", True, UI_TEXT_COLOR)
    score_rect = score_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
    surface.blit(score_surf, score_rect)

    # Add decorative background for score
    pygame.draw.rect(surface, '#aaaaaa', score_rect.inflate(50, 20), 2, 10)

    # Display level at top left
    level_surf = main_font.render(f"Level: {level}", True, UI_TEXT_COLOR)
    level_rect = level_surf.get_frect(topleft=(20, 20))
    surface.blit(level_surf, level_rect)

    # Display hearts at top right
    heart_spacing = 40  # Pixels between hearts
    for i in range(INITIAL_LIVES):
        # Choose heart image based on current lives
        heart_surf = heart_full_surf if i < lives else heart_empty_surf

        # Position hearts right-aligned with spacing
        heart_x = WINDOW_WIDTH - (heart_spacing * (INITIAL_LIVES - i))
        heart_y = 20
        heart_rect = heart_surf.get_frect(topright=(heart_x, heart_y))

        # Draw heart
        surface.blit(heart_surf, heart_rect)


def show_game_over_screen(surface, final_score):
    """Display game over screen with final score"""
    # Create semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Black with alpha
    surface.blit(overlay, (0, 0))

    # Game over text
    game_over_surf = game_over_font.render("GAME OVER", True, "#ff3333")
    game_over_rect = game_over_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    surface.blit(game_over_surf, game_over_rect)

    # Final score text
    score_surf = main_font.render(f"Final Score: {final_score}", True, "#ffffff")
    score_rect = score_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
    surface.blit(score_surf, score_rect)

    # Restart instructions
    restart_surf = main_font.render("Press SPACE to Play Again or ESC to Quit", True, "#cccccc")
    restart_rect = restart_surf.get_frect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))
    surface.blit(restart_surf, restart_rect)


def run_game():
    """Main game loop function"""
    # Create sprite groups
    global all_sprites, meteor_sprites, laser_sprites
    all_sprites = pygame.sprite.Group()
    meteor_sprites = pygame.sprite.Group()
    laser_sprites = pygame.sprite.Group()

    # Create player
    player = Player()

    # Create background stars
    spawn_stars(20)

    # Game state variables
    score = 0
    level = 1
    last_score_update = pygame.time.get_ticks()

    # Initial meteor spawn timer
    meteor_spawn_rate = calculate_meteor_spawn_time(level)
    meteor_timer = pygame.time.get_ticks()

    # Game loop
    running = True
    game_over = False

    while running:
        # Time management
        dt = clock.tick(FPS) / 1000  # Convert milliseconds to seconds
        current_time = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Game over screen controls
            if game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    # Restart the game
                    return True  # Signal to restart
                if keys[pygame.K_ESCAPE]:
                    return False  # Signal to quit

        # Skip game logic if game is over
        if game_over:
            # Draw all sprites (background elements)
            display_surface.fill(BACKGROUND_COLOR)
            all_sprites.draw(display_surface)
            display_surface.blit(player.image, player.rect)

            # Show game over screen
            show_game_over_screen(display_surface, score)
            pygame.display.update()
            continue
        # Clear screen
        display_surface.fill(BACKGROUND_COLOR)

        # Update current level based on score
        level = get_current_level(score)  # +1 because levels are 1-based for display

        # Passive score increase (survival points)
        if current_time - last_score_update >= 1000:  # Every second
            score += SURVIVAL_POINTS_PER_SECOND
            last_score_update = current_time

        # Spawn meteors on timer
        if current_time - meteor_timer >= meteor_spawn_rate:
            # Calculate speed multiplier based on level (more speed at higher levels)
            speed_multiplier = 1.0 + (level - 1) * 0.1  # 10% increase per level

            # Create new meteor
            Meteor(meteor_surf, (all_sprites, meteor_sprites), speed_multiplier)

            # Reset timer
            meteor_timer = current_time

            # Update spawn rate based on current level
            meteor_spawn_rate = calculate_meteor_spawn_time(level)

        # Update all sprites
        player.update(dt, level)  # Pass current level to player for laser cooldown adjustment
        all_sprites.update(dt)

        # Handle collisions and update score
        score = check_collisions(player, score)

        # Check if player is still alive
        if not player.alive:
            game_over = True

        # Draw everything
        all_sprites.draw(display_surface)
        display_surface.blit(player.image, player.rect)
        display_ui(display_surface, score, level, player.lives)

        # Update display
        pygame.display.update()

    return False  # Signal to quit


# ------------------------
# MAIN PROGRAM EXECUTION
# ------------------------

def main():
    """Program entry point"""
    # Start game loop with restart option
    restart = True
    while restart:
        restart = run_game()

    # Clean up and exit
    pygame.quit()
    sys.exit()


main()
