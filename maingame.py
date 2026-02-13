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
NIGHT_LENGTH = 120  # 2 minuter per match

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
MONITOR_COLOR = (30, 80, 30)  # CRT monitor 

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
            drain_rate += 0.4
        if self.right_door_closed:
            drain_rate += 0.4
        if self.left_light_on:
            drain_rate += 0.2
        if self.right_light_on:
            drain_rate += 0.2
        if self.camera_open:
            drain_rate += 0.1
        
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
                # Check if animatronic is at a door
                if anim.location == Location.LEFT_DOOR:
                    # Pass door state and dt to check for retreat
                    anim.move(door_blocked=self.left_door_closed, dt=dt)
                    # Only attack if door is open 
                    if not self.left_door_closed:
                        attack_chance = 0.8 + (anim.ai_level * 0.05) + (self.game_hour * 0.05)
                        if random.random() < attack_chance:
                            self.trigger_jumpscare(anim)
                elif anim.location == Location.RIGHT_DOOR:
                    anim.move(door_blocked=self.right_door_closed, dt=dt)
                    # Only attack if door is open
                    if not self.right_door_closed:
                        attack_chance = 0.8 + (anim.ai_level * 0.05) + (self.game_hour * 0.05)
                        if random.random() < attack_chance:
                            self.trigger_jumpscare(anim)
                else:
                    anim.move(door_blocked=False, dt=dt)
    
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
        
        # Draw decorative lines
        pygame.draw.line(self.screen, GRAY, (0, 150), (SCREEN_WIDTH, 150), 2)
        pygame.draw.line(self.screen, GRAY, (0, SCREEN_HEIGHT - 150), (SCREEN_WIDTH, SCREEN_HEIGHT - 150), 2)
        
        title = self.font.render("FIVE NIGHTS AT BLANKAS", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.small_font.render("Can you survive until 6 AM?", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Start button
        start_text = self.font.render("Press SPACE to Start", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(start_text, start_rect)
        
        # Draw controls
        controls = [
            "━━━ CONTROLS ━━━",
            "A - Close Left Door",
            "D - Close Right Door",
            "Q - Turn On Left Light",
            "E - Turn On Right Light",
            "SPACE - Open/Close Camera",
            "ARROW KEYS - Switch Camera View",
            "",
            "━━━ OBJECTIVE ━━━",
            "Survive from 12 AM to 6 AM",
            "Manage your power carefully",
            "Use doors to block animatronics",
            "Use lights to see who's there"
        ]
        
        y = 350
        for line in controls:
            if "CONTROLS" in line or "OBJECTIVE" in line:
                text = self.small_font.render(line, True, RED)
            elif line == "":
                y += 10
                continue
            else:
                text = self.small_font.render(line, True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, rect)
            y += 20
    
    def draw_office(self):
        """Draw office view - FNAF style"""
        # Dark office background
        self.screen.fill(BLACK)
        
        # Draw office interior (desk area)
        pygame.draw.rect(self.screen, (40, 40, 40), (0, 400, SCREEN_WIDTH, 320))
        pygame.draw.rect(self.screen, (60, 60, 60), (100, 380, SCREEN_WIDTH - 200, 340), 3)
        
        # Draw left side panel
        pygame.draw.rect(self.screen, (50, 50, 50), (0, 350, 200, 370))
        pygame.draw.rect(self.screen, GRAY, (0, 350, 200, 370), 2)
        
        # Draw right side panel  
        pygame.draw.rect(self.screen, (50, 50, 50), (SCREEN_WIDTH - 200, 350, 200, 370))
        pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH - 200, 350, 200, 370), 2)
        
        # Draw doors with status
        left_door_color = RED if self.left_door_closed else GREEN
        right_door_color = RED if self.right_door_closed else GREEN
        
        # Left door visual
        pygame.draw.rect(self.screen, left_door_color, (30, 400, 120, 280))
        pygame.draw.rect(self.screen, WHITE, (30, 400, 120, 280), 2)
        left_status = "CLOSED" if self.left_door_closed else "OPEN"
        left_door_text = self.small_font.render(f"LEFT DOOR\n{left_status}", True, WHITE)
        self.screen.blit(left_door_text, (35, 555))
        
        # Right door visual
        pygame.draw.rect(self.screen, right_door_color, (SCREEN_WIDTH - 150, 400, 120, 280))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 150, 400, 120, 280), 2)
        right_status = "CLOSED" if self.right_door_closed else "OPEN"
        right_door_text = self.small_font.render(f"RIGHT DOOR\n{right_status}", True, WHITE)
        self.screen.blit(right_door_text, (SCREEN_WIDTH - 145, 555))
        
        # Left light panel
        pygame.draw.rect(self.screen, (30, 30, 30), (20, 365, 160, 80))
        pygame.draw.rect(self.screen, (0, 255, 0) if self.left_light_on else GRAY, (20, 365, 160, 80), 2)
        light_text = self.small_font.render("LEFT LIGHT", True, WHITE)
        self.screen.blit(light_text, (30, 375))
        light_status = "ON" if self.left_light_on else "OFF"
        light_status_text = self.small_font.render(f"[{light_status}] Q", True, (0, 255, 0) if self.left_light_on else GRAY)
        self.screen.blit(light_status_text, (30, 405))
        
        # Right light panel
        pygame.draw.rect(self.screen, (30, 30, 30), (SCREEN_WIDTH - 180, 365, 160, 80))
        pygame.draw.rect(self.screen, (0, 255, 0) if self.right_light_on else GRAY, (SCREEN_WIDTH - 180, 365, 160, 80), 2)
        light_text = self.small_font.render("RIGHT LIGHT", True, WHITE)
        self.screen.blit(light_text, (SCREEN_WIDTH - 170, 375))
        light_status = "ON" if self.right_light_on else "OFF"
        light_status_text = self.small_font.render(f"[{light_status}] E", True, (0, 255, 0) if self.right_light_on else GRAY)
        self.screen.blit(light_status_text, (SCREEN_WIDTH - 170, 405))
        
        # Camera button - center top
        camera_button_color = GREEN if self.camera_open else BLUE
        pygame.draw.rect(self.screen, camera_button_color, (SCREEN_WIDTH // 2 - 80, 20, 160, 50))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH // 2 - 80, 20, 160, 50), 2)
        camera_text = self.small_font.render("CAMERA SYSTEM", True, BLACK)
        camera_rect = camera_text.get_rect(center=(SCREEN_WIDTH // 2, 45))
        self.screen.blit(camera_text, camera_rect)
        
        # Show animatronics at doors with lights
        if self.left_light_on:
            at_left = [a.name for a in self.animatronics if a.location == Location.LEFT_DOOR]
            if at_left:
                warning = self.font.render(f"WARNING: {at_left[0]}", True, RED)
                self.screen.blit(warning, (SCREEN_WIDTH // 4 - 100, 80))
        
        if self.right_light_on:
            at_right = [a.name for a in self.animatronics if a.location == Location.RIGHT_DOOR]
            if at_right:
                warning = self.font.render(f"WARNING: {at_right[0]}", True, RED)
                self.screen.blit(warning, (3 * SCREEN_WIDTH // 4 - 100, 80))
        
        # Draw HUD
        self.draw_hud()
    
    def draw_camera(self):
        """Draw camera view - FNAF style monitor"""
        self.screen.fill(BLACK)
        
        # Draw monitor frame
        monitor_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 150)
        pygame.draw.rect(self.screen, (40, 40, 40), monitor_rect)
        pygame.draw.rect(self.screen, GRAY, monitor_rect, 3)
        
        # Draw monitor screen (CRT green)
        pygame.draw.rect(self.screen, MONITOR_COLOR, (70, 70, SCREEN_WIDTH - 140, SCREEN_HEIGHT - 190))
        
        # Camera static/scanlines effect
        for _ in range(80):
            x = random.randint(70, SCREEN_WIDTH - 70)
            y = random.randint(70, SCREEN_HEIGHT - 120)
            pygame.draw.circle(self.screen, (40, 120, 40), (x, y), 1)
        
        # Draw scanlines for CRT effect
        for y in range(70, SCREEN_HEIGHT - 120, 3):
            pygame.draw.line(self.screen, (0, 0, 0), (70, y), (SCREEN_WIDTH - 70, y), 1)
        
        # Show current location
        location_names = {
            Location.STAGE: "STAGE",
            Location.DINING: "DINING AREA",
            Location.HALLWAY: "HALLWAY",
            Location.LEFT_DOOR: "LEFT DOOR",
            Location.RIGHT_DOOR: "RIGHT DOOR"
        }
        
        cam_text = self.font.render(f"CAM: {location_names[self.current_camera]}", True, GREEN)
        self.screen.blit(cam_text, (90, 100))
        
        # Show animatronics at current location
        at_location = [a for a in self.animatronics if a.location == self.current_camera]
        if at_location:
            y = 200
            for anim in at_location:
                # Draw animatronic representation
                pygame.draw.circle(self.screen, RED, (SCREEN_WIDTH // 2, y), 50)
                pygame.draw.circle(self.screen, (255, 100, 100), (SCREEN_WIDTH // 2, y), 45)
                name_text = self.font.render(anim.name, True, WHITE)
                name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, y))
                self.screen.blit(name_text, name_rect)
                y += 120
        else:
            empty_text = self.small_font.render("[NO MOVEMENT DETECTED]", True, GREEN)
            empty_rect = empty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        
        # Draw camera selection buttons at bottom
        cam_y = SCREEN_HEIGHT - 90
        cam_buttons = [
            ("1-STAGE", Location.STAGE, 120),
            ("2-DINING", Location.DINING, 320),
            ("3-HALLWAY", Location.HALLWAY, 520),
            ("4-LEFT", Location.LEFT_DOOR, 720),
            ("5-RIGHT", Location.RIGHT_DOOR, 920)
        ]
        
        for label, loc, btn_x in cam_buttons:
            color = GREEN if loc == self.current_camera else GRAY
            text = self.small_font.render(label, True, color)
            rect = text.get_rect(center=(btn_x, cam_y))
            self.screen.blit(text, rect)
            if loc == self.current_camera:
                pygame.draw.rect(self.screen, GREEN, (btn_x - 65, cam_y - 20, 130, 30), 2)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw close instruction
        hint = self.small_font.render("Press SPACE to close camera", True, GREEN)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 35))
    
    def draw_hud(self):
        """Draw heads-up display - FNAF style"""
        # Power meter
        power_text = self.font.render(f"POWER: {int(self.power)}%", True, WHITE if self.power > 20 else RED)
        self.screen.blit(power_text, (20, 20))
        
        # Power bar
        bar_width = 200
        bar_height = 20
        bar_x = 20
        bar_y = 60
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Power bar fill
        power_percent = max(0, min(100, self.power)) / 100.0
        bar_fill_color = GREEN if self.power > 20 else RED
        pygame.draw.rect(self.screen, bar_fill_color, (bar_x, bar_y, bar_width * power_percent, bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Time
        hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
        time_text = self.font.render(f"TIME: {hours[min(self.game_hour, 6)]}", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 250, 20))
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(RED)
        
        if self.jumpscare_timer > 0:
            # Jumpscare animation
            text = self.font.render(self.jumpscare_animatronic.name.upper(), True, BLACK)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, rect)
            
            # Draw jumpscare visual
            pygame.draw.circle(self.screen, (255, 100, 100), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), 80)
            pygame.draw.circle(self.screen, RED, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), 75)
        else:
            text = self.font.render("GAME OVER", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, rect)
            
            reason = self.small_font.render(f"You were caught by {self.jumpscare_animatronic.name}", True, WHITE)
            reason_rect = reason.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(reason, reason_rect)
            
            restart = self.small_font.render("Press SPACE to return to menu", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(restart, restart_rect)
    
    def draw_win(self):
        """Draw win screen"""
        self.screen.fill(GREEN)
        
        text = self.font.render("6 AM - NIGHT COMPLETE!", True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, rect)
        
        sub = self.small_font.render("You survived the night!", True, BLACK)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(sub, sub_rect)
        
        restart = self.small_font.render("Press SPACE to return to menu", True, BLACK)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
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