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
DARK_RED = (100, 20, 20)
DARK_PURPLE = (60, 20, 80)
DARK_GREEN = (20, 80, 20)
VERY_DARK_GRAY = (20, 20, 25)
CHARCOAL = (40, 40, 45)
MUTED_RED = (180, 50, 50)
MUTED_GREEN = (100, 180, 100)
DIM_YELLOW = (180, 160, 80) 

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Five Nights at Blankas")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 20)
        
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
        
        # Separate toggle cooldowns for each control
        self.left_door_cooldown = 0
        self.right_door_cooldown = 0
        self.left_light_cooldown = 0
        self.right_light_cooldown = 0
        self.camera_cooldown = 0
    
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
        """Draw main menu with darker, scarier atmosphere"""
        self.screen.fill(VERY_DARK_GRAY)
        
        # Draw subtle grid background
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.line(self.screen, (30, 30, 35), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 80):
            pygame.draw.line(self.screen, (30, 30, 35), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Draw subtle border
        pygame.draw.rect(self.screen, DARK_PURPLE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 2)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        # Draw dark decorative lines
        pygame.draw.line(self.screen, DARK_PURPLE, (0, 150), (SCREEN_WIDTH, 150), 2)
        pygame.draw.line(self.screen, DARK_PURPLE, (0, SCREEN_HEIGHT - 150), (SCREEN_WIDTH, SCREEN_HEIGHT - 150), 2)
        
        title = self.large_font.render("FIVE NIGHTS AT BLANKAS", True, MUTED_RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font.render("Can you survive until 6 AM?", True, MUTED_GREEN)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Start button with darker styling
        start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 210, 300, 60)
        pygame.draw.rect(self.screen, DARK_RED, start_button_rect)
        pygame.draw.rect(self.screen, MUTED_RED, start_button_rect, 2)
        start_text = self.font.render("Press SPACE to Start", True, WHITE)
        start_rect = start_text.get_rect(center=start_button_rect.center)
        self.screen.blit(start_text, start_rect)
        
        # Draw controls with better formatting
        controls = [
            "━━━━━━━━━━━━━━━━━ CONTROLS ━━━━━━━━━━━━━━━━━",
            "A - TOGGLE LEFT DOOR     |     D - TOGGLE RIGHT DOOR",
            "Q - TOGGLE LEFT LIGHT     |     E - TOGGLE RIGHT LIGHT",
            "SPACE - OPEN/CLOSE CAMERA     |     ARROW KEYS - SWITCH CAMERAS",
            "",
            "━━━━━━━━━━━━━━━━━ OBJECTIVE ━━━━━━━━━━━━━━━━━",
            "Survive from 12 AM to 6 AM",
            "Manage your power supply carefully",
            "Use DOORS to block animatronics at the entrance",
            "Use LIGHTS to detect who's outside"
        ]
        
        y = 310
        for line in controls:
            if "CONTROLS" in line or "OBJECTIVE" in line:
                text = self.small_font.render(line, True, DARK_PURPLE)
            elif line == "":
                y += 5
                continue
            else:
                text = self.tiny_font.render(line, True, GRAY)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, rect)
            y += 22
    
    def draw_office(self):
        """Draw office view - FNAF style with dark, scary atmosphere"""
        # Very dark walls
        self.screen.fill(VERY_DARK_GRAY)
        
        # Draw office interior (desk area)
        pygame.draw.rect(self.screen, (30, 25, 35), (0, 400, SCREEN_WIDTH, 320))
        pygame.draw.rect(self.screen, DARK_PURPLE, (0, 400, SCREEN_WIDTH, 3))
        pygame.draw.rect(self.screen, (45, 40, 55), (100, 380, SCREEN_WIDTH - 200, 340), 2)
        
        # Draw left side panel with darker styling
        pygame.draw.rect(self.screen, CHARCOAL, (10, 360, 200, 360))
        pygame.draw.rect(self.screen, DARK_PURPLE, (10, 360, 200, 360), 2)
        
        # Draw right side panel
        pygame.draw.rect(self.screen, CHARCOAL, (SCREEN_WIDTH - 210, 360, 200, 360))
        pygame.draw.rect(self.screen, DARK_PURPLE, (SCREEN_WIDTH - 210, 360, 200, 360), 2)
        
        # Draw doors with darker, scary appearance
        left_door_color = (80, 20, 20) if self.left_door_closed else (50, 50, 55)
        right_door_color = (80, 20, 20) if self.right_door_closed else (50, 50, 55)
        
        # Left door visual
        pygame.draw.rect(self.screen, left_door_color, (30, 400, 120, 280))
        pygame.draw.rect(self.screen, MUTED_RED if self.left_door_closed else GRAY, (30, 400, 120, 280), 2)
        left_status = "SECURED" if self.left_door_closed else "OPEN"
        left_status_color = MUTED_GREEN if self.left_door_closed else MUTED_RED
        left_door_text = self.font.render(left_status, True, left_status_color)
        left_door_rect = left_door_text.get_rect(center=(90, 540))
        self.screen.blit(left_door_text, left_door_rect)
        left_label = self.tiny_font.render("[A]", True, DIM_YELLOW)
        self.screen.blit(left_label, (50, 560))
        
        # Right door visual
        pygame.draw.rect(self.screen, right_door_color, (SCREEN_WIDTH - 150, 400, 120, 280))
        pygame.draw.rect(self.screen, MUTED_RED if self.right_door_closed else GRAY, (SCREEN_WIDTH - 150, 400, 120, 280), 2)
        right_status = "SECURED" if self.right_door_closed else "OPEN"
        right_status_color = MUTED_GREEN if self.right_door_closed else MUTED_RED
        right_door_text = self.font.render(right_status, True, right_status_color)
        right_door_rect = right_door_text.get_rect(center=(SCREEN_WIDTH - 90, 540))
        self.screen.blit(right_door_text, right_door_rect)
        right_label = self.tiny_font.render("[D]", True, DIM_YELLOW)
        self.screen.blit(right_label, (SCREEN_WIDTH - 130, 560))
        
        # Left light panel with toggle switch appearance
        light_rect_left = pygame.Rect(20, 370, 180, 70)
        pygame.draw.rect(self.screen, (25, 25, 30), light_rect_left)
        pygame.draw.rect(self.screen, DARK_GREEN if self.left_light_on else DARK_GRAY, light_rect_left, 2)
        
        light_text = self.font.render("LEFT LIGHT", True, GRAY)
        self.screen.blit(light_text, (30, 375))
        
        # Toggle switch visual
        switch_y = 410
        switch_rect = pygame.Rect(120, switch_y, 60, 25)
        pygame.draw.rect(self.screen, (40, 40, 45), switch_rect)
        pygame.draw.rect(self.screen, DARK_GREEN if self.left_light_on else DARK_GRAY, switch_rect, 2)
        
        switch_status = "ON" if self.left_light_on else "OFF"
        switch_color = MUTED_GREEN if self.left_light_on else MUTED_RED
        switch_text = self.tiny_font.render(switch_status, True, switch_color)
        switch_rect_center = switch_text.get_rect(center=switch_rect.center)
        self.screen.blit(switch_text, switch_rect_center)
        
        key_label_left = self.tiny_font.render("[Q]", True, DIM_YELLOW)
        self.screen.blit(key_label_left, (30, 420))
        
        # Right light panel with toggle switch appearance
        light_rect_right = pygame.Rect(SCREEN_WIDTH - 200, 370, 180, 70)
        pygame.draw.rect(self.screen, (25, 25, 30), light_rect_right)
        pygame.draw.rect(self.screen, DARK_GREEN if self.right_light_on else DARK_GRAY, light_rect_right, 2)
        
        light_text_r = self.font.render("RIGHT LIGHT", True, GRAY)
        self.screen.blit(light_text_r, (SCREEN_WIDTH - 190, 375))
        
        # Toggle switch visual
        switch_rect_r = pygame.Rect(SCREEN_WIDTH - 90, switch_y, 60, 25)
        pygame.draw.rect(self.screen, (40, 40, 45), switch_rect_r)
        pygame.draw.rect(self.screen, DARK_GREEN if self.right_light_on else DARK_GRAY, switch_rect_r, 2)
        
        switch_status_r = "ON" if self.right_light_on else "OFF"
        switch_color_r = MUTED_GREEN if self.right_light_on else MUTED_RED
        switch_text_r = self.tiny_font.render(switch_status_r, True, switch_color_r)
        switch_rect_center_r = switch_text_r.get_rect(center=switch_rect_r.center)
        self.screen.blit(switch_text_r, switch_rect_center_r)
        
        key_label_right = self.tiny_font.render("[E]", True, DIM_YELLOW)
        self.screen.blit(key_label_right, (SCREEN_WIDTH - 190, 420))
        
        # Camera button - center top with darker styling
        camera_button_color = DARK_GREEN if self.camera_open else (50, 50, 70)
        camera_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 20, 200, 60)
        pygame.draw.rect(self.screen, camera_button_color, camera_rect)
        pygame.draw.rect(self.screen, DARK_PURPLE, camera_rect, 2)
        camera_text = self.font.render("CAMERA", True, GRAY)
        camera_rect_center = camera_text.get_rect(center=camera_rect.center)
        self.screen.blit(camera_text, camera_rect_center)
        
        # Show animatronics at doors with lights - dark alerts
        if self.left_light_on:
            at_left = [a.name for a in self.animatronics if a.location == Location.LEFT_DOOR]
            if at_left:
                warning_bg = pygame.Rect(50, 80, 200, 50)
                pygame.draw.rect(self.screen, (80, 20, 20), warning_bg)
                pygame.draw.rect(self.screen, MUTED_RED, warning_bg, 2)
                warning = self.font.render(f"⚠ {at_left[0]}", True, MUTED_RED)
                self.screen.blit(warning, (60, 90))
        
        if self.right_light_on:
            at_right = [a.name for a in self.animatronics if a.location == Location.RIGHT_DOOR]
            if at_right:
                warning_bg = pygame.Rect(SCREEN_WIDTH - 250, 80, 200, 50)
                pygame.draw.rect(self.screen, (80, 20, 20), warning_bg)
                pygame.draw.rect(self.screen, MUTED_RED, warning_bg, 2)
                warning = self.font.render(f"⚠ {at_right[0]}", True, MUTED_RED)
                self.screen.blit(warning, (SCREEN_WIDTH - 240, 90))
        
        # Draw HUD
        self.draw_hud()
    
    def draw_camera(self):
        """Draw camera view - FNAF style monitor with dark atmosphere"""
        self.screen.fill((10, 10, 12))
        
        # Draw monitor frame
        monitor_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 150)
        pygame.draw.rect(self.screen, (35, 30, 40), monitor_rect)
        pygame.draw.rect(self.screen, DARK_PURPLE, monitor_rect, 3)
        
        # Draw monitor bezel
        pygame.draw.rect(self.screen, (50, 45, 60), (40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 130), 8)
        
        # Draw monitor screen (CRT green)
        pygame.draw.rect(self.screen, MONITOR_COLOR, (70, 70, SCREEN_WIDTH - 140, SCREEN_HEIGHT - 190))
        
        # Camera static/scanlines effect
        for _ in range(80):
            x = random.randint(70, SCREEN_WIDTH - 70)
            y = random.randint(70, SCREEN_HEIGHT - 120)
            pygame.draw.circle(self.screen, (35, 90, 35), (x, y), 1)
        
        # Draw scanlines for CRT effect
        for y in range(70, SCREEN_HEIGHT - 120, 3):
            pygame.draw.line(self.screen, (10, 25, 10), (70, y), (SCREEN_WIDTH - 70, y), 1)
        
        # Show current location
        location_names = {
            Location.STAGE: "STAGE",
            Location.DINING: "DINING AREA",
            Location.HALLWAY: "HALLWAY",
            Location.LEFT_DOOR: "LEFT DOOR",
            Location.RIGHT_DOOR: "RIGHT DOOR"
        }
        
        cam_text = self.large_font.render(f"CAM: {location_names[self.current_camera]}", True, MUTED_GREEN)
        self.screen.blit(cam_text, (90, 90))
        
        # Show animatronics at current location
        at_location = [a for a in self.animatronics if a.location == self.current_camera]
        if at_location:
            y = 200
            for anim in at_location:
                # Draw animatronic representation
                pygame.draw.circle(self.screen, (150, 50, 50), (SCREEN_WIDTH // 2, y), 60)
                pygame.draw.circle(self.screen, (200, 80, 80), (SCREEN_WIDTH // 2, y), 55)
                pygame.draw.circle(self.screen, (180, 100, 100), (SCREEN_WIDTH // 2 - 20, y - 15), 8)
                pygame.draw.circle(self.screen, (180, 100, 100), (SCREEN_WIDTH // 2 + 20, y - 15), 8)
                
                name_text = self.font.render(anim.name.upper(), True, MUTED_GREEN)
                name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, y + 70))
                self.screen.blit(name_text, name_rect)
                y += 150
        else:
            empty_text = self.font.render("[NO MOVEMENT DETECTED]", True, MUTED_GREEN)
            empty_rect = empty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        
        # Draw camera selection buttons at bottom with dark styling
        cam_y = SCREEN_HEIGHT - 90
        cam_buttons = [
            ("1-STAGE", Location.STAGE, 120),
            ("2-DINING", Location.DINING, 320),
            ("3-HALLWAY", Location.HALLWAY, 520),
            ("4-LEFT", Location.LEFT_DOOR, 720),
            ("5-RIGHT", Location.RIGHT_DOOR, 920)
        ]
        
        for label, loc, btn_x in cam_buttons:
            color = MUTED_GREEN if loc == self.current_camera else GRAY
            bg_color = (30, 60, 30) if loc == self.current_camera else CHARCOAL
            
            # Draw button background
            btn_rect = pygame.Rect(btn_x - 70, cam_y - 25, 140, 50)
            pygame.draw.rect(self.screen, bg_color, btn_rect)
            pygame.draw.rect(self.screen, color, btn_rect, 2)
            
            text = self.font.render(label, True, color)
            rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, rect)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw close instruction
        hint = self.small_font.render("Press SPACE to close camera", True, MUTED_GREEN)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 35))
    
    def draw_hud(self):
        """Draw heads-up display with dark, subtle styling"""
        # Power meter background
        power_bg = pygame.Rect(15, 15, 250, 80)
        pygame.draw.rect(self.screen, CHARCOAL, power_bg)
        pygame.draw.rect(self.screen, DARK_GREEN, power_bg, 2)
        
        # Power text
        power_color = MUTED_GREEN if self.power > 20 else MUTED_RED
        power_text = self.font.render(f"POWER: {int(self.power)}%", True, power_color)
        self.screen.blit(power_text, (25, 20))
        
        # Power bar
        bar_width = 220
        bar_height = 25
        bar_x = 25
        bar_y = 55
        pygame.draw.rect(self.screen, (50, 50, 55), (bar_x, bar_y, bar_width, bar_height))
        
        # Power bar fill with color changes
        power_percent = max(0, min(100, self.power)) / 100.0
        if self.power > 50:
            bar_fill_color = DARK_GREEN
        elif self.power > 20:
            bar_fill_color = DIM_YELLOW
        else:
            bar_fill_color = MUTED_RED
        
        pygame.draw.rect(self.screen, bar_fill_color, (bar_x, bar_y, bar_width * power_percent, bar_height))
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Time display with subtle styling
        hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
        time_bg = pygame.Rect(SCREEN_WIDTH - 265, 15, 250, 80)
        pygame.draw.rect(self.screen, CHARCOAL, time_bg)
        pygame.draw.rect(self.screen, DARK_PURPLE, time_bg, 2)
        
        time_text = self.font.render(f"TIME: {hours[min(self.game_hour, 6)]}", True, DARK_PURPLE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 255, 20))
        
        # Progress bar for time
        progress_width = 220
        progress_height = 25
        progress_x = SCREEN_WIDTH - 255
        progress_y = 55
        pygame.draw.rect(self.screen, (50, 50, 55), (progress_x, progress_y, progress_width, progress_height))
        
        time_percent = min(self.game_hour / 6.0, 1.0)
        pygame.draw.rect(self.screen, DARK_PURPLE, (progress_x, progress_y, progress_width * time_percent, progress_height))
        pygame.draw.rect(self.screen, GRAY, (progress_x, progress_y, progress_width, progress_height), 1)
    
    def draw_game_over(self):
        """Draw game over screen with dark, scary atmosphere"""
        self.screen.fill((60, 15, 15))
        
        # Draw decorative border
        pygame.draw.rect(self.screen, MUTED_RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        if self.jumpscare_timer > 0:
            # Jumpscare animation with pulse effect
            pulse = abs(int(self.jumpscare_timer * 10) % 20 - 10) / 10.0
            jumpscare_text = self.large_font.render(f"{self.jumpscare_animatronic.name.upper()}", True, (255, int(100 * pulse), int(100 * pulse)))
            rect = jumpscare_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            self.screen.blit(jumpscare_text, rect)
            
            # Draw jumpscare visual with enhanced effect
            circle_size = int(80 + pulse * 20)
            pygame.draw.circle(self.screen, (120, 40, 40), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), circle_size)
            pygame.draw.circle(self.screen, (180, 60, 60), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), circle_size - 5)
        else:
            text = self.large_font.render("GAME OVER", True, MUTED_RED)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(text, rect)
            
            reason = self.font.render(f"You were caught by {self.jumpscare_animatronic.name}", True, DIM_YELLOW)
            reason_rect = reason.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(reason, reason_rect)
            
            restart = self.small_font.render("Press SPACE to return to menu", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(restart, restart_rect)
    
    def draw_win(self):
        """Draw win screen with dark, subtle styling"""
        self.screen.fill((20, 50, 20))
        
        # Draw decorative border
        pygame.draw.rect(self.screen, DARK_GREEN, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        text = self.large_font.render("6 AM - NIGHT COMPLETE", True, MUTED_GREEN)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(text, rect)
        
        sub = self.font.render("You survived the night!", True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(sub, sub_rect)
        
        restart = self.small_font.render("Press SPACE to return to menu", True, GRAY)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(restart, restart_rect)
    
    def handle_input(self):
        """Handle keyboard input with independent toggle support"""
        keys = pygame.key.get_pressed()
        
        # Update individual cooldowns
        if self.left_door_cooldown > 0:
            self.left_door_cooldown -= 1
        if self.right_door_cooldown > 0:
            self.right_door_cooldown -= 1
        if self.left_light_cooldown > 0:
            self.left_light_cooldown -= 1
        if self.right_light_cooldown > 0:
            self.right_light_cooldown -= 1
        if self.camera_cooldown > 0:
            self.camera_cooldown -= 1
        
        if self.state == GameState.PLAYING:
            # Left door - independent toggle
            if keys[pygame.K_a] and self.left_door_cooldown <= 0:
                self.left_door_closed = not self.left_door_closed
                self.left_door_cooldown = 10
            
            # Right door - independent toggle
            if keys[pygame.K_d] and self.right_door_cooldown <= 0:
                self.right_door_closed = not self.right_door_closed
                self.right_door_cooldown = 10
            
            # Left light - independent toggle
            if keys[pygame.K_q] and self.left_light_cooldown <= 0:
                self.left_light_on = not self.left_light_on
                self.left_light_cooldown = 10
            
            # Right light - independent toggle
            if keys[pygame.K_e] and self.right_light_cooldown <= 0:
                self.right_light_on = not self.right_light_on
                self.right_light_cooldown = 10
        
        elif self.state == GameState.CAMERA:
            # Camera switching with cooldown
            if keys[pygame.K_LEFT] and self.camera_cooldown <= 0:
                cam_list = list(Location)
                idx = cam_list.index(self.current_camera)
                self.current_camera = cam_list[(idx - 1) % len(cam_list)]
                self.camera_cooldown = 12
            
            elif keys[pygame.K_RIGHT] and self.camera_cooldown <= 0:
                cam_list = list(Location)
                idx = cam_list.index(self.current_camera)
                self.current_camera = cam_list[(idx + 1) % len(cam_list)]
                self.camera_cooldown = 12
    
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