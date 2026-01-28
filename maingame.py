import pygame
import random
import sys
from typing import List
from class_function import GameState, Location, Animatronic, create_animatronics

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
NIGHT_LENGTH = 480  # 8 minutes in seconds (reduced for testing)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Five Nights at Blankas")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.state = GameState.MENU
        self.mouse_pos = (0, 0)
        self.reset_game()
    
    def reset_game(self):
        """Reset game state for new night"""
        self.power = 100.0
        self.time_elapsed = 0
        self.game_hour = 0  # 0-6 (12AM to 6AM)
        
        self.left_door_closed = False
        self.right_door_closed = False
        self.left_light_on = False
        self.right_light_on = False
        self.camera_open = False
        self.current_camera = Location.STAGE
        
        # Create animatronics with varying AI levels
        self.animatronics = create_animatronics()
        
        self.jumpscare_timer = 0
        self.jumpscare_animatronic = None
    
    def update_power(self, dt: float):
        """Update power consumption"""
        drain_rate = 0.1  # Base drain
        
        if self.left_door_closed:
            drain_rate += 0.5
        if self.right_door_closed:
            drain_rate += 0.5
        if self.left_light_on:
            drain_rate += 0.3
        if self.right_light_on:
            drain_rate += 0.3
        if self.camera_open:
            drain_rate += 0.2
        
        self.power -= drain_rate * dt
        self.power = max(0, self.power)
    
    def update_time(self, dt: float):
        """Update in-game time"""
        self.time_elapsed += dt
        self.game_hour = int((self.time_elapsed / NIGHT_LENGTH) * 6)
        
        if self.game_hour >= 6:
            self.state = GameState.WIN
    
    def update_animatronics(self, dt: float):
        """Update all animatronics"""
        for anim in self.animatronics:
            if anim.update(dt, self.game_hour):
                anim.move()
                
                # Check if animatronic reaches player
                if anim.location == Location.LEFT_DOOR and not self.left_door_closed:
                    if random.random() < 0.3:  # 30% chance to attack when at door
                        self.trigger_jumpscare(anim)
                elif anim.location == Location.RIGHT_DOOR and not self.right_door_closed:
                    if random.random() < 0.3:
                        self.trigger_jumpscare(anim)
    
    def trigger_jumpscare(self, animatronic: Animatronic):
        """Trigger game over with jumpscare"""
        self.jumpscare_animatronic = animatronic
        self.jumpscare_timer = 2.0
        self.state = GameState.GAME_OVER
    
    def check_power_out(self):
        """Check if power is depleted"""
        if self.power <= 0:
            self.trigger_jumpscare(self.animatronics[0])  # Freddy gets you
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill(BLACK)
        
        title = self.font.render("Five Nights at Blankas", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        start_text = self.font.render("Press SPACE to Start Night", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(start_text, start_rect)
        
        controls = [
            "Controls:",
            "A/D - Close Left/Right Door",
            "Q/E - Left/Right Light",
            "SPACE - Toggle Camera",
            "Arrow Keys - Switch Camera View"
        ]
        
        y = 500
        for line in controls:
            text = self.small_font.render(line, True, GRAY)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, rect)
            y += 30
    
    def draw_office(self):
        """Draw office view"""
        self.screen.fill(DARK_GRAY)
        
        # Draw office background (placeholder)
        pygame.draw.rect(self.screen, (50, 50, 50), (0, 300, SCREEN_WIDTH, 420))
        
        # Draw doors
        left_door_color = RED if self.left_door_closed else GREEN
        right_door_color = RED if self.right_door_closed else GREEN
        
        pygame.draw.rect(self.screen, left_door_color, (50, 350, 100, 250))
        pygame.draw.rect(self.screen, right_door_color, (SCREEN_WIDTH - 150, 350, 100, 250))
        
        # Draw door labels
        left_text = self.small_font.render("LEFT DOOR (A)", True, WHITE)
        self.screen.blit(left_text, (55, 620))
        
        right_text = self.small_font.render("RIGHT DOOR (D)", True, WHITE)
        self.screen.blit(right_text, (SCREEN_WIDTH - 145, 620))
        
        # Draw light indicators
        if self.left_light_on:
            pygame.draw.circle(self.screen, (255, 255, 100), (100, 300), 30)
            # Check if animatronic is at left door
            at_left = [a.name for a in self.animatronics if a.location == Location.LEFT_DOOR]
            if at_left:
                warning = self.font.render(f"{at_left[0]} AT DOOR!", True, RED)
                self.screen.blit(warning, (50, 250))
        
        if self.right_light_on:
            pygame.draw.circle(self.screen, (255, 255, 100), (SCREEN_WIDTH - 100, 300), 30)
            at_right = [a.name for a in self.animatronics if a.location == Location.RIGHT_DOOR]
            if at_right:
                warning = self.font.render(f"{at_right[0]} AT DOOR!", True, RED)
                self.screen.blit(warning, (SCREEN_WIDTH - 250, 250))
        
        # Draw HUD
        self.draw_hud()
    
    def draw_camera(self):
        """Draw camera view"""
        self.screen.fill(BLACK)
        
        # Camera static effect
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, (50, 50, 50), (x, y), 1)
        
        # Draw camera view area
        pygame.draw.rect(self.screen, (30, 30, 30), (100, 100, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 300))
        
        # Show current location
        location_names = {
            Location.STAGE: "Faculty Room",
            Location.DINING: "Dining Area",
            Location.HALLWAY: "Corridor",
            Location.LEFT_DOOR: "Left Door",
            Location.RIGHT_DOOR: "Right Door"
        }
        
        cam_text = self.font.render(f"Camera: {location_names[self.current_camera]}", True, GREEN)
        self.screen.blit(cam_text, (120, 120))
        
        # Show animatronics at current location
        at_location = [a for a in self.animatronics if a.location == self.current_camera]
        y = 200
        for anim in at_location:
            # Draw simple representation
            pygame.draw.circle(self.screen, RED, (SCREEN_WIDTH // 2, y), 40)
            name_text = self.small_font.render(anim.name, True, WHITE)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(name_text, name_rect)
            y += 100
        
        # Draw camera selection buttons
        cam_y = SCREEN_HEIGHT - 150
        cam_buttons = [
            ("1-Faculty Room", Location.STAGE),
            ("2-Dining", Location.DINING),
            ("3-Corridor", Location.HALLWAY),
            ("4-Left", Location.LEFT_DOOR),
            ("5-Right", Location.RIGHT_DOOR)
        ]
        
        x = 150
        for label, loc in cam_buttons:
            color = GREEN if loc == self.current_camera else GRAY
            text = self.small_font.render(label, True, color)
            self.screen.blit(text, (x, cam_y))
            x += 200
        
        # Draw HUD
        self.draw_hud()
        
        hint = self.small_font.render("Press SPACE to close camera", True, WHITE)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 50))
    
    def draw_hud(self):
        """Draw heads-up display"""
        # Power
        power_text = self.font.render(f"Power: {int(self.power)}%", True, WHITE if self.power > 20 else RED)
        self.screen.blit(power_text, (20, 20))
        
        # Time
        hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
        time_text = self.font.render(f"Time: {hours[min(self.game_hour, 6)]}", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(RED)
        
        if self.jumpscare_timer > 0:
            # Jumpscare animation
            text = self.font.render(self.jumpscare_animatronic.name.upper(), True, BLACK)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
        else:
            text = self.font.render("GAME OVER", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
            
            restart = self.small_font.render("Press SPACE to return to menu", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart, restart_rect)
    
    def draw_win(self):
        """Draw win screen"""
        self.screen.fill(GREEN)
        
        text = self.font.render("6 AM - You survived the night!", True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)
        
        restart = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(restart, restart_rect)
    
    def handle_input(self):
        """Handle keyboard input"""
        keys = pygame.key.get_pressed()
        
        if self.state == GameState.PLAYING:
            # Door controls
            if keys[pygame.K_a]:
                self.left_door_closed = True
            else:
                self.left_door_closed = False
            
            if keys[pygame.K_d]:
                self.right_door_closed = True
            else:
                self.right_door_closed = False
            
            # Light controls
            self.left_light_on = keys[pygame.K_q]
            self.right_light_on = keys[pygame.K_e]
        
        elif self.state == GameState.CAMERA:
            # Camera switching
            if keys[pygame.K_LEFT]:
                cam_list = list(Location)
                idx = cam_list.index(self.current_camera)
                self.current_camera = cam_list[(idx - 1) % len(cam_list)]
                pygame.time.wait(200)
            elif keys[pygame.K_RIGHT]:
                cam_list = list(Location)
                idx = cam_list.index(self.current_camera)
                self.current_camera = cam_list[(idx + 1) % len(cam_list)]
                pygame.time.wait(200)
    
    def handle_mouse_click(self, pos: tuple):
        """Handle mouse click events"""
        x, y = pos
        
        if self.state == GameState.MENU:
            # Click on start button area
            start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 380, 400, 40)
            if start_rect.collidepoint(x, y):
                self.reset_game()
                self.state = GameState.PLAYING
        
        elif self.state == GameState.PLAYING:
            # Click on left door
            left_door_rect = pygame.Rect(50, 350, 100, 250)
            if left_door_rect.collidepoint(x, y):
                self.left_door_closed = not self.left_door_closed
            
            # Click on right door
            right_door_rect = pygame.Rect(SCREEN_WIDTH - 150, 350, 100, 250)
            if right_door_rect.collidepoint(x, y):
                self.right_door_closed = not self.right_door_closed
            
            # Click on left light
            left_light_rect = pygame.Rect(70, 270, 60, 60)
            if left_light_rect.collidepoint(x, y):
                self.left_light_on = not self.left_light_on
            
            # Click on right light
            right_light_rect = pygame.Rect(SCREEN_WIDTH - 130, 270, 60, 60)
            if right_light_rect.collidepoint(x, y):
                self.right_light_on = not self.right_light_on
            
            # Click to open camera
            camera_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, 20, 100, 30)
            if camera_rect.collidepoint(x, y):
                self.camera_open = True
                self.state = GameState.CAMERA
        
        elif self.state == GameState.CAMERA:
            # Click on camera selection buttons
            cam_buttons = [
                ("1-Stage", Location.STAGE, 150),
                ("2-Dining", Location.DINING, 350),
                ("3-Hallway", Location.HALLWAY, 550),
                ("4-Left", Location.LEFT_DOOR, 750),
                ("5-Right", Location.RIGHT_DOOR, 950)
            ]
            
            cam_y = SCREEN_HEIGHT - 150
            for label, loc, btn_x in cam_buttons:
                btn_rect = pygame.Rect(btn_x - 50, cam_y - 10, 100, 30)
                if btn_rect.collidepoint(x, y):
                    self.current_camera = loc
            
            # Click to close camera
            close_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 50, 300, 30)
            if close_rect.collidepoint(x, y):
                self.camera_open = False
                self.state = GameState.PLAYING
        
        elif self.state in [GameState.GAME_OVER, GameState.WIN]:
            # Click to return to menu
            menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 40, 300, 40)
            if menu_rect.collidepoint(x, y):
                self.state = GameState.MENU
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.mouse_pos = pygame.mouse.get_pos()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_mouse_click(event.pos)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    if event.key == pygame.K_SPACE:
                        if self.state == GameState.MENU:
                            self.reset_game()
                            self.state = GameState.PLAYING
                        elif self.state == GameState.PLAYING:
                            self.camera_open = True
                            self.state = GameState.CAMERA
                        elif self.state == GameState.CAMERA:
                            self.camera_open = False
                            self.state = GameState.PLAYING
                        elif self.state in [GameState.GAME_OVER, GameState.WIN]:
                            self.state = GameState.MENU
            
            # Update
            self.handle_input()
            
            if self.state == GameState.PLAYING or self.state == GameState.CAMERA:
                self.update_time(dt)
                self.update_power(dt)
                self.update_animatronics(dt)
                self.check_power_out()
            
            if self.state == GameState.GAME_OVER and self.jumpscare_timer > 0:
                self.jumpscare_timer -= dt
            
            # Draw
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                self.draw_office()
            elif self.state == GameState.CAMERA:
                self.draw_camera()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            elif self.state == GameState.WIN:
                self.draw_win()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()