# Hjälpmodul innehållande klasser och hjälpfunktioner för FNAF-liknande spel.
# Håller datastrukturer och hjälpfunktioner åtskilda från huvudspellogiken.

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class GameState(Enum):
    # Enum för olika speltillstånd
    MENU = 1
    PLAYING = 2
    CAMERA = 3
    GAME_OVER = 4
    WIN = 5


class Location(Enum):
    # Enum för spelobjekt
    STAGE = 0
    DINING = 1
    HALLWAY = 2
    LEFT_DOOR = 3
    RIGHT_DOOR = 4


@dataclass
class Animatronic:
    # Dataclass som representerar en animatronisk karaktär med personlighetsstyrd AI
    name: str
    location: Location
    ai_level: int
    move_timer: float
    active: bool = True
    
    # AI-personlighetsdrag (0.0-1.0)
    aggression: float = 0.5  # Hur sannolikt det är att attackera
    persistence: float = 0.5  # Hur länge man ska stanna vid dörrar
    strategy: str = "random"  # "aggressive", "cautious", "strategic", "random"
    
    # Tillståndsövervakning
    preferred_side: str = "random"  # "left", "right", or "random"
    stalled_moves: int = 0  # Konsekutiva flyttningar till samma plats indikerar uthållighet
    last_blocked_time: float = 0.0  # Spåra när den senast blockerades vid dörr
    
    def update(self, dt: float, game_hour: int) -> bool:
        # Uppdatera animatronik, returnerar True om animatroniken förflyttades
        if not self.active:
            return False
        
        self.move_timer -= dt
        self.last_blocked_time -= dt
        
        if self.move_timer <= 0:
            # Svårighetsgraden ökar exponentiellt i senare timmar
            hour_multiplier = 1.0 + (game_hour ** 1.5) * 0.15
            base_difficulty = (self.ai_level + game_hour) / 20.0
            difficulty = base_difficulty * hour_multiplier * self.aggression
            
            if random.random() < min(difficulty, 0.95):  # Begränsa till 95% för att undvika säkerhet
                self.move_timer = random.uniform(2.0, 5.0)  # Flytta snabbare när natten fortskrider
                return True
            
            self.move_timer = random.uniform(3.0, 7.0)
        return False
    
    def move(self, door_blocked: bool = False, dt: float = 0, doors_pressure: tuple = None):
        # Flytta animatronik till nästa plats med strategiskt beslutsfattande
        path = {
            Location.STAGE: [Location.DINING],
            Location.DINING: [Location.HALLWAY],
            Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
            Location.LEFT_DOOR: [Location.LEFT_DOOR],
            Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
        }
        
        # Vid dörr med strategiskt beteende
        if self.location in [Location.LEFT_DOOR, Location.RIGHT_DOOR]:
            if door_blocked:
                self.last_blocked_time = 2.0
                # Dra dig tillbaka baserat på uthållighet och strategi
                if self.strategy == "cautious":
                    retreat_chance = 0.5
                elif self.strategy == "aggressive":
                    retreat_chance = 0.1
                elif self.strategy == "strategic":
                    retreat_chance = 0.2
                else:  # slumpmässig
                    retreat_chance = 0.3
                
                if random.random() < retreat_chance:
                    self.location = Location.HALLWAY
                    self.stalled_moves = 0
                else:
                    self.stalled_moves += 1
                return
            else:
                self.stalled_moves = 0
        
        if self.location in path:
            possible = path[self.location]
            
            # Strategiskt dörurval
            if self.location == Location.HALLWAY and possible == [Location.LEFT_DOOR, Location.RIGHT_DOOR]:
                if self.strategy == "aggressive":
                    # Aggressiv: välj dörren som inte har använts nyligen
                    if doors_pressure:
                        left_pressure, right_pressure = doors_pressure
                        if left_pressure < right_pressure:
                            self.location = Location.LEFT_DOOR
                        else:
                            self.location = Location.RIGHT_DOOR
                    else:
                        self.location = random.choice(possible)
                elif self.strategy == "strategic":
                    # Strategisk: fokusera på en dörr men byt ibland
                    if self.preferred_side == "random":
                        self.preferred_side = random.choice(["left", "right"])
                    if random.random() < 0.1:  # 10% chans att byta strategi
                        self.preferred_side = "left" if self.preferred_side == "right" else "right"
                    self.location = Location.LEFT_DOOR if self.preferred_side == "left" else Location.RIGHT_DOOR
                else:
                    self.location = random.choice(possible)
            else:
                self.location = random.choice(possible)


# HJÄLPFUNKTIONER

def get_location_name(location: Location) -> str:
    # Få ett läsligt namn för en plats
    location_names = {
        Location.STAGE: "Show Stage",
        Location.DINING: "Dining Area",
        Location.HALLWAY: "Hallway",
        Location.LEFT_DOOR: "Left Door",
        Location.RIGHT_DOOR: "Right Door"
    }
    return location_names.get(location, "Unknown")


def create_animatronics() -> List[Animatronic]:
    # Fabriksfunktion för att skapa standard animatroniker med unika personligheter
    return [
        Animatronic(
            "Tablos", Location.STAGE, 2, 5.0,
            aggression=0.6, persistence=0.8, strategy="strategic",
            preferred_side="random"
        ),
        Animatronic(
            "Vegeta", Location.STAGE, 3, 4.0,
            aggression=0.9, persistence=0.6, strategy="aggressive",
            preferred_side="random"
        ),
        Animatronic(
            "Goku", Location.STAGE, 3, 4.5,
            aggression=0.4, persistence=0.5, strategy="cautious",
            preferred_side="random"
        ),
    ]


def get_animatronics_at_location(animatronics: List[Animatronic], location: Location) -> List[Animatronic]:
    # Få en lista över animatroniker på en specifik plats
    return [a for a in animatronics if a.location == location]


def get_animatronic_names_at_location(animatronics: List[Animatronic], location: Location) -> List[str]:
    # Få en lista över animatroniska namn på en specifik plats
    return [a.name for a in get_animatronics_at_location(animatronics, location)]


def get_movement_path() -> Dict[Location, List[Location]]:
    # Få rörelsvägsgrafen för animatroniker
    return {
        Location.STAGE: [Location.DINING],
        Location.DINING: [Location.HALLWAY],
        Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
        Location.LEFT_DOOR: [Location.LEFT_DOOR],
        Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
    }


def format_game_time(game_hour: int) -> str:
    # Formatera speltimme till läsbar tidssträng
    hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
    return hours[min(game_hour, 6)]


def calculate_difficulty(ai_level: int, game_hour: int) -> float:
    # Beräkna rörelsesvårigheten baserat på AI-nivå och spelutveckling
    return (ai_level + game_hour) / 20.0
