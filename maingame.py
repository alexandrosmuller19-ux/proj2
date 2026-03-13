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
MONITOR_COLOR = (30, 80, 30)  # CRT-monitor
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
        
        # Ladda animatroniska bilder
        self.animatronic_images = {}
        try:
            self.animatronic_images['Tablos'] = pygame.image.load('freddy.png')
            self.animatronic_images['Vegeta'] = pygame.image.load('bonnie.png')
            self.animatronic_images['Goku'] = pygame.image.load('chica.png')
            # Skala bilder till lämplig storlek för kameravyn
            for name in self.animatronic_images:
                self.animatronic_images[name] = pygame.transform.scale(self.animatronic_images[name], (150, 150))
        except pygame.error as e:
            print(f"Warning: Could not load animatronic images: {e}")
        
        self.state = GameState.MENU
        self.mouse_pos = (0, 0)
        
        # Svårighetsinställningar
        self.difficulty = 1.0  # 0.7 (Lätt), 1.0 (Normal), 1.3 (Svårt), 1.6 (Omöjlig)
        self.difficulty_names = ["EASY", "NORMAL", "HARD", "IMPOSSIBLE"]
        self.difficulty_multipliers = [0.7, 1.0, 1.3, 1.6]
        self.selected_difficulty = 1  # Standard till Normal (index 1)
        
        self.reset_game()
    
    def reset_game(self):
        # Återställ speltillståndet för ny natt
        # Tillämpa svårighetsmultiplikator
        self.difficulty = self.difficulty_multipliers[self.selected_difficulty]
        
        self.power = 100.0
        self.time_elapsed = 0
        self.game_hour = 0  # 0-6 (12 på natten till 6 på morgonen)
        
        self.left_door_closed = False
        self.right_door_closed = False
        self.left_light_on = False
        self.right_light_on = False
        self.camera_open = False
        self.current_camera = Location.STAGE
        
        # Skapa animatroniker med varierande AI-nivåer
        self.animatronics = create_animatronics()
        
        self.jumpscare_timer = 0
        self.jumpscare_animatronic = None
        
        # Separata växlingsvägningstider för varje kontroll
        self.left_door_cooldown = 0
        self.right_door_cooldown = 0
        self.left_light_cooldown = 0
        self.right_light_cooldown = 0
        self.camera_cooldown = 0
        
        # Dörrtrycksspårning för AI-strategi
        self.left_door_pressure = 0.0
        self.right_door_pressure = 0.0
    
    def update_power(self, dt: float):
        # Uppdatera strömförbrukningen med skalasvårighetsgrad
        drain_rate = 0.08  # Basavlopp (något reducerat)
        
        # Öka strömavloppets intensitet när natten fortskrider
        hour_multiplier = 1.0 + (self.game_hour * 0.12)
        
        if self.left_door_closed:
            drain_rate += 0.5 * hour_multiplier
        if self.right_door_closed:
            drain_rate += 0.5 * hour_multiplier
        if self.left_light_on:
            drain_rate += 0.15 * hour_multiplier
        if self.right_light_on:
            drain_rate += 0.15 * hour_multiplier
        if self.camera_open:
            drain_rate += 0.12 * hour_multiplier
        
        # Tillämpa svårighetsmultiplikator på strömavlopp
        drain_rate *= self.difficulty
        
        self.power -= drain_rate * dt
        self.power = max(0, self.power)
    
    def update_time(self, dt: float):
        # Uppdatera speltid
        self.time_elapsed += dt
        self.game_hour = int((self.time_elapsed / NIGHT_LENGTH) * 6)
        
        if self.game_hour >= 6:
            self.state = GameState.WIN
    
    def update_animatronics(self, dt: float):
        # Beräkna dörrtryck (hur många animatroniker är vid varje dörr)
        left_at_door = len([a for a in self.animatronics if a.location == Location.LEFT_DOOR])
        right_at_door = len([a for a in self.animatronics if a.location == Location.RIGHT_DOOR])
        self.left_door_pressure = left_at_door
        self.right_door_pressure = right_at_door
        
        # Uppdatera alla animatroniker
        for anim in self.animatronics:
            if anim.update(dt, self.game_hour):
                # Kontrollera om animatroniken är vid en dörr
                if anim.location == Location.LEFT_DOOR:
                    # Skicka dörrtillstånd och tryckinformation för strategiska beslut
                    anim.move(door_blocked=self.left_door_closed, dt=dt, 
                             doors_pressure=(self.left_door_pressure, self.right_door_pressure))
                    # Attackera endast om dörren är öppen 
                    if not self.left_door_closed:
                        # Personlighetsbchans för attack med svårighetsmultiplikator
                        base_attack = 0.75 + (anim.ai_level * 0.08) + (self.game_hour * 0.08)
                        attack_chance = base_attack * anim.aggression * self.difficulty
                        if random.random() < min(attack_chance, 0.98):  # Begränsa till 98%
                            self.trigger_jumpscare(anim)
                elif anim.location == Location.RIGHT_DOOR:
                    anim.move(door_blocked=self.right_door_closed, dt=dt,
                             doors_pressure=(self.left_door_pressure, self.right_door_pressure))
                    # Attackera endast om dörren är öppen
                    if not self.right_door_closed:
                        # Personlighetsbchans för attack med svårighetsmultiplikator
                        base_attack = 0.75 + (anim.ai_level * 0.08) + (self.game_hour * 0.08)
                        attack_chance = base_attack * anim.aggression * self.difficulty
                        if random.random() < min(attack_chance, 0.98):  # Begränsa till 98%
                            self.trigger_jumpscare(anim)
                else:
                    anim.move(door_blocked=False, dt=dt)
    
    def trigger_jumpscare(self, animatronic: Animatronic):
        # Utlös game over med jumpscare
        self.jumpscare_animatronic = animatronic
        self.jumpscare_timer = 2.0
        self.state = GameState.GAME_OVER
    
    def check_power_out(self):
        # Kontrollera om strömmen är slut
        if self.power <= 0:
            self.trigger_jumpscare(self.animatronics[0])  # Freddy får dig
    
    def draw_menu(self):
        # Rita huvudmeny med mörkare, skrämmande atmosfär
        self.screen.fill(VERY_DARK_GRAY)
        
        # Rita subtil rutnätsbakgrund
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.line(self.screen, (30, 30, 35), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 80):
            pygame.draw.line(self.screen, (30, 30, 35), (0, y), (SCREEN_WIDTH, y), 1)
        
        # Rita subtil gräns
        pygame.draw.rect(self.screen, DARK_PURPLE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 2)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        # Rita mörka dekorativa linjer
        pygame.draw.line(self.screen, DARK_PURPLE, (0, 150), (SCREEN_WIDTH, 150), 2)
        pygame.draw.line(self.screen, DARK_PURPLE, (0, SCREEN_HEIGHT - 150), (SCREEN_WIDTH, SCREEN_HEIGHT - 150), 2)
        
        title = self.large_font.render("FIVE NIGHTS AT BLANKAS", True, MUTED_RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font.render("Can you survive until 6 AM?", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Startknapp med mörkare styling
        start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 210, 300, 60)
        pygame.draw.rect(self.screen, DARK_RED, start_button_rect)
        pygame.draw.rect(self.screen, MUTED_RED, start_button_rect, 2)
        start_text = self.font.render("Press SPACE to Start", True, WHITE)
        start_rect = start_text.get_rect(center=start_button_rect.center)
        self.screen.blit(start_text, start_rect)
        
        # Rita kontroller med bättre formatering
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
        
        # Rita svårighetsväljare
        difficulty_label = self.font.render("DIFFICULTY:", True, WHITE)
        label_rect = difficulty_label.get_rect(center=(SCREEN_WIDTH // 2, 530))
        self.screen.blit(difficulty_label, label_rect)
        
        # Rita svårighetsknappar - centrerade och korrekt avstånd
        button_width = 85
        button_height = 50
        button_spacing = 105
        # Centrera 4 knappar: (4 * 85) + (3 * 20) = 400px totalt, centrerat på 1280px
        total_buttons_width = (len(self.difficulty_names) * button_width) + ((len(self.difficulty_names) - 1) * 20)
        start_x = (SCREEN_WIDTH - total_buttons_width) // 2
        button_y = 580
        
        for i, name in enumerate(self.difficulty_names):
            btn_x = start_x + (i * button_spacing)
            btn_rect = pygame.Rect(btn_x, button_y, button_width, button_height)
            
            # Markera vald svårighet
            if i == self.selected_difficulty:
                pygame.draw.rect(self.screen, DARK_GREEN, btn_rect)
                pygame.draw.rect(self.screen, WHITE, btn_rect, 3)
                text_color = WHITE
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, btn_rect)
                pygame.draw.rect(self.screen, GRAY, btn_rect, 2)
                text_color = GRAY
            
            # Rita svårighetsnamn
            diff_text = self.small_font.render(name, True, text_color)
            text_rect = diff_text.get_rect(center=btn_rect.center)
            self.screen.blit(diff_text, text_rect)
        
        # Rita svårighetsinformation
        multiplier_text = self.tiny_font.render(f"Multiplier: {self.difficulty_multipliers[self.selected_difficulty]:.1f}x", True, DIM_YELLOW)
        multiplier_rect = multiplier_text.get_rect(center=(SCREEN_WIDTH // 2, 645))
        self.screen.blit(multiplier_text, multiplier_rect)
        
        # Rita pilanjvisningar
        arrow_hint = self.tiny_font.render("Use ARROW KEYS or click to change difficulty", True, GRAY)
        arrow_rect = arrow_hint.get_rect(center=(SCREEN_WIDTH // 2, 665))
        self.screen.blit(arrow_hint, arrow_rect)
    
    def draw_office(self):
        # Rita kontorsutsikt - FNAF-stil med mörk, skrämmande atmosfär
        # Mycket mörka väggar
        self.screen.fill(VERY_DARK_GRAY)
        
        # Rita kontorsinteriör (skrivbordarea)
        pygame.draw.rect(self.screen, (30, 25, 35), (0, 400, SCREEN_WIDTH, 320))
        pygame.draw.rect(self.screen, DARK_PURPLE, (0, 400, SCREEN_WIDTH, 3))
        pygame.draw.rect(self.screen, (45, 40, 55), (100, 380, SCREEN_WIDTH - 200, 340), 2)
        
        # Rita vänster sidopanel med mörkare styling
        pygame.draw.rect(self.screen, CHARCOAL, (10, 360, 200, 360))
        pygame.draw.rect(self.screen, DARK_PURPLE, (10, 360, 200, 360), 2)
        
        # Rita höger sidopanel
        pygame.draw.rect(self.screen, CHARCOAL, (SCREEN_WIDTH - 210, 360, 200, 360))
        pygame.draw.rect(self.screen, DARK_PURPLE, (SCREEN_WIDTH - 210, 360, 200, 360), 2)
        
        # Rita dörrar med mörkare, skrämmande utseende
        left_door_color = (80, 20, 20) if self.left_door_closed else (50, 50, 55)
        right_door_color = (80, 20, 20) if self.right_door_closed else (50, 50, 55)
        
        # Visuell representation av vänster dörr
        pygame.draw.rect(self.screen, left_door_color, (30, 400, 120, 280))
        pygame.draw.rect(self.screen, MUTED_RED if self.left_door_closed else GRAY, (30, 400, 120, 280), 2)
        left_status = "SECURED" if self.left_door_closed else "OPEN"
        left_status_color = WHITE if self.left_door_closed else MUTED_RED
        left_door_text = self.font.render(left_status, True, left_status_color)
        left_door_rect = left_door_text.get_rect(center=(90, 540))
        self.screen.blit(left_door_text, left_door_rect)
        left_label = self.tiny_font.render("[A]", True, DIM_YELLOW)
        self.screen.blit(left_label, (50, 560))
        
        # Visuell representation av höger dörr
        pygame.draw.rect(self.screen, right_door_color, (SCREEN_WIDTH - 150, 400, 120, 280))
        pygame.draw.rect(self.screen, MUTED_RED if self.right_door_closed else GRAY, (SCREEN_WIDTH - 150, 400, 120, 280), 2)
        right_status = "SECURED" if self.right_door_closed else "OPEN"
        right_status_color = WHITE if self.right_door_closed else MUTED_RED
        right_door_text = self.font.render(right_status, True, right_status_color)
        right_door_rect = right_door_text.get_rect(center=(SCREEN_WIDTH - 90, 540))
        self.screen.blit(right_door_text, right_door_rect)
        right_label = self.tiny_font.render("[D]", True, DIM_YELLOW)
        self.screen.blit(right_label, (SCREEN_WIDTH - 130, 560))
        
        # Vänster ljuspanel med växlingsomkopplare-utseende
        light_rect_left = pygame.Rect(20, 370, 180, 70)
        pygame.draw.rect(self.screen, (25, 25, 30), light_rect_left)
        pygame.draw.rect(self.screen, DARK_GREEN if self.left_light_on else DARK_GRAY, light_rect_left, 2)
        
        light_text = self.font.render("LEFT LIGHT", True, GRAY)
        self.screen.blit(light_text, (30, 375))
        
        # Toggle switch visual - positioned properly within panel
        switch_rect = pygame.Rect(110, 395, 70, 30)
        pygame.draw.rect(self.screen, (40, 40, 45), switch_rect)
        pygame.draw.rect(self.screen, DARK_GREEN if self.left_light_on else DARK_GRAY, switch_rect, 2)
        
        switch_status = "ON" if self.left_light_on else "OFF"
        switch_color = WHITE if self.left_light_on else MUTED_RED
        switch_text = self.tiny_font.render(switch_status, True, switch_color)
        switch_rect_center = switch_text.get_rect(center=switch_rect.center)
        self.screen.blit(switch_text, switch_rect_center)
        
        key_label_left = self.tiny_font.render("[Q]", True, DIM_YELLOW)
        self.screen.blit(key_label_left, (30, 420))
        
        # Höger ljuspanel med växlingsomkopplare-utseende
        light_rect_right = pygame.Rect(SCREEN_WIDTH - 200, 370, 180, 70)
        pygame.draw.rect(self.screen, (25, 25, 30), light_rect_right)
        pygame.draw.rect(self.screen, DARK_GREEN if self.right_light_on else DARK_GRAY, light_rect_right, 2)
        
        light_text_r = self.font.render("RIGHT LIGHT", True, GRAY)
        self.screen.blit(light_text_r, (SCREEN_WIDTH - 190, 375))
        
        # Visuell omkopplare - positioned properly within panel
        switch_rect_r = pygame.Rect(SCREEN_WIDTH - 100, 395, 70, 30)
        pygame.draw.rect(self.screen, (40, 40, 45), switch_rect_r)
        pygame.draw.rect(self.screen, DARK_GREEN if self.right_light_on else DARK_GRAY, switch_rect_r, 2)
        
        switch_status_r = "ON" if self.right_light_on else "OFF"
        switch_color_r = WHITE if self.right_light_on else MUTED_RED
        switch_text_r = self.tiny_font.render(switch_status_r, True, switch_color_r)
        switch_rect_center_r = switch_text_r.get_rect(center=switch_rect_r.center)
        self.screen.blit(switch_text_r, switch_rect_center_r)
        
        key_label_right = self.tiny_font.render("[E]", True, DIM_YELLOW)
        self.screen.blit(key_label_right, (SCREEN_WIDTH - 190, 420))
        
        # Kameraknapp - mitten överst med mörkare styling
        camera_button_color = DARK_GREEN if self.camera_open else (50, 50, 70)
        camera_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 20, 200, 60)
        pygame.draw.rect(self.screen, camera_button_color, camera_rect)
        pygame.draw.rect(self.screen, DARK_PURPLE, camera_rect, 2)
        camera_text = self.font.render("CAMERA", True, GRAY)
        camera_rect_center = camera_text.get_rect(center=camera_rect.center)
        self.screen.blit(camera_text, camera_rect_center)
        
        # Visa animatroniker vid dörrar med ljus - förbättrade varningar med tryckindikatorer
        if self.left_light_on:
            at_left = [a for a in self.animatronics if a.location == Location.LEFT_DOOR]
            if at_left:
                anim = at_left[0]
                # Glitch-effekt för varningsruta
                glitch_offset = random.randint(-2, 2) if random.random() < 0.1 else 0
                warning_bg = pygame.Rect(50 + glitch_offset, 80, 200, 120)
                pygame.draw.rect(self.screen, (80, 20, 20), warning_bg)
                pygame.draw.rect(self.screen, MUTED_RED, warning_bg, 2)
                # Pulsande gräns för större brådska
                pulse = abs(int(pygame.time.get_ticks() * 0.003) % 20 - 10) / 10.0
                pygame.draw.rect(self.screen, (int(255 * pulse), 0, 0), warning_bg, 1)
                # Visa animatronisk bild om tillgänglig
                if anim.name in self.animatronic_images:
                    img = pygame.transform.scale(self.animatronic_images[anim.name], (80, 80))
                    self.screen.blit(img, (60 + glitch_offset, 90))
                warning = self.font.render(anim.name, True, MUTED_RED)
                self.screen.blit(warning, (60 + glitch_offset, 180))
                # Visa AI-personlighet
                strategy_text = self.tiny_font.render(f"[{anim.strategy.upper()}]", True, DIM_YELLOW)
                self.screen.blit(strategy_text, (70 + glitch_offset, 195))
                # Dörrtrycksindikator
                pressure_text = self.tiny_font.render(f"Pressure: {int(self.left_door_pressure)}", True, MUTED_RED)
                self.screen.blit(pressure_text, (60 + glitch_offset, 210))
        
        if self.right_light_on:
            at_right = [a for a in self.animatronics if a.location == Location.RIGHT_DOOR]
            if at_right:
                anim = at_right[0]
                # Glitch-effekt för varningsruta
                glitch_offset = random.randint(-2, 2) if random.random() < 0.1 else 0
                warning_bg = pygame.Rect(SCREEN_WIDTH - 250 + glitch_offset, 80, 200, 120)
                pygame.draw.rect(self.screen, (80, 20, 20), warning_bg)
                pygame.draw.rect(self.screen, MUTED_RED, warning_bg, 2)
                # Pulsande gräns för större brådska
                pulse = abs(int(pygame.time.get_ticks() * 0.003) % 20 - 10) / 10.0
                pygame.draw.rect(self.screen, (int(255 * pulse), 0, 0), warning_bg, 1)
                # Visa animatronisk bild om tillgänglig
                if anim.name in self.animatronic_images:
                    img = pygame.transform.scale(self.animatronic_images[anim.name], (80, 80))
                    self.screen.blit(img, (SCREEN_WIDTH - 240 + glitch_offset, 90))
                warning = self.font.render(anim.name, True, MUTED_RED)
                self.screen.blit(warning, (SCREEN_WIDTH - 240 + glitch_offset, 180))
                # Visa AI-personlighet
                strategy_text = self.tiny_font.render(f"[{anim.strategy.upper()}]", True, DIM_YELLOW)
                self.screen.blit(strategy_text, (SCREEN_WIDTH - 230 + glitch_offset, 195))
                # Dörrtrycksindikator
                pressure_text = self.tiny_font.render(f"Pressure: {int(self.right_door_pressure)}", True, MUTED_RED)
                self.screen.blit(pressure_text, (SCREEN_WIDTH - 240 + glitch_offset, 210))
        
        # Rita HUD
        self.draw_hud()
    
    def draw_camera(self):
        # Rita kameravyn - FNAF-stil övervakningsmonitor med mörk atmosfär, fullständig vy utan HUD
        self.screen.fill((10, 10, 12))
        
        # Rita monitorbilad
        monitor_rect = pygame.Rect(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60)
        pygame.draw.rect(self.screen, (35, 30, 40), monitor_rect)
        pygame.draw.rect(self.screen, DARK_PURPLE, monitor_rect, 3)
        
        # Rita monitorfattning
        pygame.draw.rect(self.screen, (50, 45, 60), (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 8)
        
        # Rita monitorskärm (CRT grön)
        pygame.draw.rect(self.screen, MONITOR_COLOR, (50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100))
        
        # Kamerastöj/scanlines-effekt
        for _ in range(80):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(50, SCREEN_HEIGHT - 50)
            pygame.draw.circle(self.screen, (35, 90, 35), (x, y), 1)
        
        # Rita scanlines för CRT-effekt
        for y in range(50, SCREEN_HEIGHT - 50, 3):
            pygame.draw.line(self.screen, (10, 25, 10), (50, y), (SCREEN_WIDTH - 50, y), 1)
        
        # Visa aktuell plats
        location_names = {
            Location.STAGE: "STAGE",
            Location.DINING: "DINING AREA",
            Location.HALLWAY: "HALLWAY",
            Location.LEFT_DOOR: "LEFT DOOR",
            Location.RIGHT_DOOR: "RIGHT DOOR"
        }
        
        cam_text = self.large_font.render(f"CAM: {location_names[self.current_camera]}", True, WHITE)
        self.screen.blit(cam_text, (70, 70))
        
        # Visa animatroniker på aktuell plats
        at_location = [a for a in self.animatronics if a.location == self.current_camera]
        if at_location:
            y = 250
            for anim in at_location:
                # Rita animatronisk bild om tillgänglig, annars använd platshållare
                if anim.name in self.animatronic_images:
                    img = self.animatronic_images[anim.name]
                    img_rect = img.get_rect(center=(SCREEN_WIDTH // 2, y))
                    self.screen.blit(img, img_rect)
                else:
                    # Reserv: rita cirklar om bilden inte hittas
                    pygame.draw.circle(self.screen, (150, 50, 50), (SCREEN_WIDTH // 2, y), 60)
                    pygame.draw.circle(self.screen, (200, 80, 80), (SCREEN_WIDTH // 2, y), 55)
                    pygame.draw.circle(self.screen, (180, 100, 100), (SCREEN_WIDTH // 2 - 20, y - 15), 8)
                    pygame.draw.circle(self.screen, (180, 100, 100), (SCREEN_WIDTH // 2 + 20, y - 15), 8)
                
                y += 150
        else:
            empty_text = self.font.render("[NO MOVEMENT DETECTED]", True, WHITE)
            empty_rect = empty_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        
        # Rita kameraval-knappar längst ner med mörk styling
        cam_y = SCREEN_HEIGHT - 70
        cam_buttons = [
            ("1-STAGE", Location.STAGE, 120),
            ("2-DINING", Location.DINING, 320),
            ("3-HALLWAY", Location.HALLWAY, 520),
            ("4-LEFT", Location.LEFT_DOOR, 720),
            ("5-RIGHT", Location.RIGHT_DOOR, 920)
        ]
        
        for label, loc, btn_x in cam_buttons:
            color = WHITE if loc == self.current_camera else GRAY
            bg_color = (30, 60, 30) if loc == self.current_camera else CHARCOAL
            
            # Rita knappbakgrund
            btn_rect = pygame.Rect(btn_x - 70, cam_y - 25, 140, 50)
            pygame.draw.rect(self.screen, bg_color, btn_rect)
            pygame.draw.rect(self.screen, color, btn_rect, 2)
            
            text = self.font.render(label, True, color)
            rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, rect)
        
        # Rita stänginstruktion
        hint = self.small_font.render("Press SPACE to close camera", True, WHITE)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 30))
    
    def draw_hud(self):
        # Rita heads-up display med mörk, subtil styling
        # Strömmeterbakgrund
        power_bg = pygame.Rect(15, 15, 250, 100)
        pygame.draw.rect(self.screen, CHARCOAL, power_bg)
        pygame.draw.rect(self.screen, DARK_GREEN, power_bg, 2)
        
        # Strömtext med kritisk varning
        power_color = WHITE if self.power > 30 else (MUTED_RED if self.power > 15 else RED)
        power_text = self.font.render(f"POWER: {int(self.power)}%", True, power_color)
        self.screen.blit(power_text, (25, 20))
        
        # Strömmätare
        bar_width = 220
        bar_height = 25
        bar_x = 25
        bar_y = 55
        pygame.draw.rect(self.screen, (50, 50, 55), (bar_x, bar_y, bar_width, bar_height))
        
        # Strömmätarfyllning med färgändringar
        power_percent = max(0, min(100, self.power)) / 100.0
        if self.power > 50:
            bar_fill_color = DARK_GREEN
        elif self.power > 30:
            bar_fill_color = DIM_YELLOW
        elif self.power > 15:
            bar_fill_color = MUTED_RED
        else:
            bar_fill_color = RED
        
        pygame.draw.rect(self.screen, bar_fill_color, (bar_x, bar_y, bar_width * power_percent, bar_height))
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Svårighetsindikator
        hour_multiplier = 1.0 + (self.game_hour ** 1.5) * 0.15
        difficulty_text = self.tiny_font.render(f"DIFFICULTY: {int(hour_multiplier * 100)}%", True, DIM_YELLOW)
        self.screen.blit(difficulty_text, (25, 85))
        
        # Tidsdisplay med subtil styling
        hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
        time_bg = pygame.Rect(SCREEN_WIDTH - 265, 15, 250, 100)
        pygame.draw.rect(self.screen, CHARCOAL, time_bg)
        pygame.draw.rect(self.screen, DARK_PURPLE, time_bg, 2)
        
        time_text = self.font.render(f"TIME: {hours[min(self.game_hour, 6)]}", True, WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 255, 20))
        
        # Förloppsindikator för tid
        progress_width = 220
        progress_height = 25
        progress_x = SCREEN_WIDTH - 255
        progress_y = 55
        pygame.draw.rect(self.screen, (50, 50, 55), (progress_x, progress_y, progress_width, progress_height))
        
        time_percent = min(self.game_hour / 6.0, 1.0)
        pygame.draw.rect(self.screen, DARK_PURPLE, (progress_x, progress_y, progress_width * time_percent, progress_height))
        pygame.draw.rect(self.screen, GRAY, (progress_x, progress_y, progress_width, progress_height), 1)
        
        # AI-statusindikator  
        active_animatronics = sum(1 for a in self.animatronics if a.active)
        ai_status = f"THREAT LEVEL: {active_animatronics}/3"
        ai_text = self.tiny_font.render(ai_status, True, MUTED_RED if active_animatronics >= 2 else DIM_YELLOW)
        self.screen.blit(ai_text, (SCREEN_WIDTH - 255, 85))
    
    def draw_game_over(self):
        # Rita game over-skärm med mörk, skrämmande atmosfär
        self.screen.fill((60, 15, 15))
        
        # Rita dekorativ gräns
        pygame.draw.rect(self.screen, MUTED_RED, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        if self.jumpscare_timer > 0:
            # Jumpscare-animation med pulseffekt och karakterbild
            pulse = abs(int(self.jumpscare_timer * 10) % 20 - 10) / 10.0
            jumpscare_text = self.large_font.render(f"{self.jumpscare_animatronic.name.upper()}", True, (255, int(100 * pulse), int(100 * pulse)))
            rect = jumpscare_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180))
            self.screen.blit(jumpscare_text, rect)
            
            # Rita animatronisk bild om tillgänglig, skalad stor för jumpscare-effekt
            if self.jumpscare_animatronic.name in self.animatronic_images:
                img = pygame.transform.scale(self.animatronic_images[self.jumpscare_animatronic.name], (300, 300))
                img_rect = img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                self.screen.blit(img, img_rect)
            else:
                # Rita jumpscare-visuell med förbättrad effekt om ingen bild finns
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
        # Rita vinnerskärm med mörk, subtil styling
        self.screen.fill((20, 50, 20))
        
        # Rita dekorativ gräns
        pygame.draw.rect(self.screen, DARK_GREEN, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
        pygame.draw.rect(self.screen, CHARCOAL, (20, 20, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 40), 1)
        
        text = self.large_font.render("6 AM - NIGHT COMPLETE", True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(text, rect)
        
        sub = self.font.render("You survived the night!", True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(sub, sub_rect)
        
        restart = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(restart, restart_rect)
    
    def handle_input(self):
        # Hantera tangentbordsinmatning med oberoende växlingsupport
        keys = pygame.key.get_pressed()
        
        # Hantera svårighetsval på meny med nedkylning
        if self.state == GameState.MENU:
            if keys[pygame.K_LEFT] and self.camera_cooldown <= 0:
                self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulty_names)
                self.camera_cooldown = 12
            elif keys[pygame.K_RIGHT] and self.camera_cooldown <= 0:
                self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulty_names)
                self.camera_cooldown = 12
        
        # Uppdatera individuella nedkylningar
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
            # Vänster dörr - oberoende växling
            if keys[pygame.K_a] and self.left_door_cooldown <= 0:
                self.left_door_closed = not self.left_door_closed
                self.left_door_cooldown = 10
            
            # Höger dörr - oberoende växling
            if keys[pygame.K_d] and self.right_door_cooldown <= 0:
                self.right_door_closed = not self.right_door_closed
                self.right_door_cooldown = 10
            
            # Vänster ljus - oberoende växling
            if keys[pygame.K_q] and self.left_light_cooldown <= 0:
                self.left_light_on = not self.left_light_on
                self.left_light_cooldown = 10
            
            # Höger ljus - oberoende växling
            if keys[pygame.K_e] and self.right_light_cooldown <= 0:
                self.right_light_on = not self.right_light_on
                self.right_light_cooldown = 10
        
        elif self.state == GameState.CAMERA:
            # Kamerabyte med nedkylning
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
        # Hantera musklickshändelser
        x, y = pos
        
        if self.state == GameState.MENU:
            # Klicka på startknappens område
            start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 210, 300, 60)
            if start_rect.collidepoint(x, y):
                self.reset_game()
                self.state = GameState.PLAYING
            
            # Klicka på svårighetsknappar - måste matcha draw_menu-beräkningar
            button_width = 85
            button_height = 50
            button_spacing = 105
            total_buttons_width = (len(self.difficulty_names) * button_width) + ((len(self.difficulty_names) - 1) * 20)
            start_x = (SCREEN_WIDTH - total_buttons_width) // 2
            button_y = 580
            
            for i in range(len(self.difficulty_names)):
                btn_x = start_x + (i * button_spacing)
                diff_rect = pygame.Rect(btn_x, button_y, button_width, button_height)
                if diff_rect.collidepoint(x, y):
                    self.selected_difficulty = i
        
        elif self.state == GameState.PLAYING:
            # Definiera alla rektanglar
            left_light_rect = pygame.Rect(20, 370, 180, 70)
            right_light_rect = pygame.Rect(SCREEN_WIDTH - 200, 370, 180, 70)
            left_door_rect = pygame.Rect(30, 400, 120, 280)
            right_door_rect = pygame.Rect(SCREEN_WIDTH - 150, 400, 120, 280)
            camera_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 20, 200, 60)
            
            # Kontrollera ljus först (högre prioritet för att undvika överlappningsproblem med dörrar)
            if left_light_rect.collidepoint(x, y):
                self.left_light_on = not self.left_light_on
            elif right_light_rect.collidepoint(x, y):
                self.right_light_on = not self.right_light_on
            # Kontrollera dörrar endast om ljus inte klickades
            elif left_door_rect.collidepoint(x, y):
                self.left_door_closed = not self.left_door_closed
            elif right_door_rect.collidepoint(x, y):
                self.right_door_closed = not self.right_door_closed
            # Kontrollera kameraknapp
            elif camera_button_rect.collidepoint(x, y):
                self.camera_open = True
                self.state = GameState.CAMERA
        
        elif self.state == GameState.CAMERA:
            # Klicka på kameraval-knappar med rätt positioner
            cam_y = SCREEN_HEIGHT - 90
            cam_buttons = [
                (Location.STAGE, 120),
                (Location.DINING, 320),
                (Location.HALLWAY, 520),
                (Location.LEFT_DOOR, 720),
                (Location.RIGHT_DOOR, 920)
            ]
            
            for loc, btn_x in cam_buttons:
                btn_rect = pygame.Rect(btn_x - 70, cam_y - 25, 140, 50)
                if btn_rect.collidepoint(x, y):
                    self.current_camera = loc
            
            # Klicka för att stänga kamera - stäng ledtråd längst ner
            close_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 35, 360, 25)
            if close_rect.collidepoint(x, y):
                self.camera_open = False
                self.state = GameState.PLAYING
        
        elif self.state in [GameState.GAME_OVER, GameState.WIN]:
            # Klicka för att återgå till meny
            menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 40, 400, 50)
            if menu_rect.collidepoint(x, y):
                self.state = GameState.MENU
    
    def run(self):
        # Huvudspelloop
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.mouse_pos = pygame.mouse.get_pos()
            
            # Händelsehantering
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Vänster musknapp
                        self.handle_mouse_click(event.pos)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    
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
            
            # Uppdatering
            self.handle_input()
            
            if self.state == GameState.PLAYING or self.state == GameState.CAMERA:
                self.update_time(dt)
                self.update_power(dt)
                self.update_animatronics(dt)
                self.check_power_out()
            
            if self.state == GameState.GAME_OVER and self.jumpscare_timer > 0:
                self.jumpscare_timer -= dt
            
            # Rita
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