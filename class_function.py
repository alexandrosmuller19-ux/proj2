# Helper module containing classes and utility functions for the FNAF-like game.
# Keeps data structures and utility functions separate from main game logic.

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class GameState(Enum):
    # Enum for different game states
    MENU = 1
    PLAYING = 2
    CAMERA = 3
    GAME_OVER = 4
    WIN = 5


class Location(Enum):
    # Enum for game locations
    STAGE = 0
    DINING = 1
    HALLWAY = 2
    LEFT_DOOR = 3
    RIGHT_DOOR = 4


@dataclass
class Animatronic:
    # Dataclass representing an animatronic character with personality-driven AI
    name: str
    location: Location
    ai_level: int
    move_timer: float
    active: bool = True
    
    # AI personality traits (0.0-1.0)
    aggression: float = 0.5  # How likely to attack
    persistence: float = 0.5  # How long to stay at doors
    strategy: str = "random"  # "aggressive", "cautious", "strategic", "random"
    
    # State tracking
    preferred_side: str = "random"  # "left", "right", or "random"
    stalled_moves: int = 0  # Consecutive moves to same location indicates persistence
    last_blocked_time: float = 0.0  # Track when last blocked at door
    
    def update(self, dt: float, game_hour: int) -> bool:
        # Update animatronic, returns True if moved
        if not self.active:
            return False
        
        self.move_timer -= dt
        self.last_blocked_time -= dt
        
        if self.move_timer <= 0:
            # Difficulty increases exponentially in later hours
            hour_multiplier = 1.0 + (game_hour ** 1.5) * 0.15
            base_difficulty = (self.ai_level + game_hour) / 20.0
            difficulty = base_difficulty * hour_multiplier * self.aggression
            
            if random.random() < min(difficulty, 0.95):  # Cap at 95% to avoid certainty
                self.move_timer = random.uniform(2.0, 5.0)  # Move faster as night progresses
                return True
            
            self.move_timer = random.uniform(3.0, 7.0)
        return False
    
    def move(self, door_blocked: bool = False, dt: float = 0, doors_pressure: tuple = None):
        # Move animatronic to next location with strategic decision making
        path = {
            Location.STAGE: [Location.DINING],
            Location.DINING: [Location.HALLWAY],
            Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
            Location.LEFT_DOOR: [Location.LEFT_DOOR],
            Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
        }
        
        # At door with strategic behavior
        if self.location in [Location.LEFT_DOOR, Location.RIGHT_DOOR]:
            if door_blocked:
                self.last_blocked_time = 2.0
                # Retreat based on persistence and strategy
                if self.strategy == "cautious":
                    retreat_chance = 0.5
                elif self.strategy == "aggressive":
                    retreat_chance = 0.1
                elif self.strategy == "strategic":
                    retreat_chance = 0.2
                else:  # random
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
            
            # Strategic door selection
            if self.location == Location.HALLWAY and possible == [Location.LEFT_DOOR, Location.RIGHT_DOOR]:
                if self.strategy == "aggressive":
                    # Aggressive: pick the door that hasn't been used recently
                    if doors_pressure:
                        left_pressure, right_pressure = doors_pressure
                        if left_pressure < right_pressure:
                            self.location = Location.LEFT_DOOR
                        else:
                            self.location = Location.RIGHT_DOOR
                    else:
                        self.location = random.choice(possible)
                elif self.strategy == "strategic":
                    # Strategic: focus one door but switch occasionally
                    if self.preferred_side == "random":
                        self.preferred_side = random.choice(["left", "right"])
                    if random.random() < 0.1:  # 10% chance to switch strategy
                        self.preferred_side = "left" if self.preferred_side == "right" else "right"
                    self.location = Location.LEFT_DOOR if self.preferred_side == "left" else Location.RIGHT_DOOR
                else:
                    self.location = random.choice(possible)
            else:
                self.location = random.choice(possible)


# UTILITY FUNCTIONS

def get_location_name(location: Location) -> str:
    # Get human-readable name for a location
    location_names = {
        Location.STAGE: "Show Stage",
        Location.DINING: "Dining Area",
        Location.HALLWAY: "Hallway",
        Location.LEFT_DOOR: "Left Door",
        Location.RIGHT_DOOR: "Right Door"
    }
    return location_names.get(location, "Unknown")


def create_animatronics() -> List[Animatronic]:
    # Factory function to create default animatronics with unique personalities
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
    # Get list of animatronics at a specific location
    return [a for a in animatronics if a.location == location]


def get_animatronic_names_at_location(animatronics: List[Animatronic], location: Location) -> List[str]:
    # Get list of animatronic names at a specific location
    return [a.name for a in get_animatronics_at_location(animatronics, location)]


def get_movement_path() -> Dict[Location, List[Location]]:
    # Get the movement path graph for animatronics
    return {
        Location.STAGE: [Location.DINING],
        Location.DINING: [Location.HALLWAY],
        Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
        Location.LEFT_DOOR: [Location.LEFT_DOOR],
        Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
    }


def format_game_time(game_hour: int) -> str:
    # Format game hour to readable time string
    hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
    return hours[min(game_hour, 6)]


def calculate_difficulty(ai_level: int, game_hour: int) -> float:
    # Calculate movement difficulty based on AI level and game progression
    return (ai_level + game_hour) / 20.0
