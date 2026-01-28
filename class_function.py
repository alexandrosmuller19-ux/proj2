"""
Helper module containing classes and utility functions for the FNAF-like game.
Keeps data structures and utility functions separate from main game logic.
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class GameState(Enum):
    """Enum for different game states"""
    MENU = 1
    PLAYING = 2
    CAMERA = 3
    GAME_OVER = 4
    WIN = 5


class Location(Enum):
    """Enum for game locations"""
    STAGE = 0
    DINING = 1
    HALLWAY = 2
    LEFT_DOOR = 3
    RIGHT_DOOR = 4


@dataclass
class Animatronic:
    """Dataclass representing an animatronic character"""
    name: str
    location: Location
    ai_level: int
    move_timer: float
    active: bool = True
    
    def update(self, dt: float, game_hour: int) -> bool:
        """Update animatronic, returns True if moved"""
        if not self.active:
            return False
            
        self.move_timer -= dt
        
        if self.move_timer <= 0:
            # Movement chance increases with AI level and game hour
            difficulty = (self.ai_level + game_hour) / 20.0
            if random.random() < difficulty:
                self.move_timer = random.uniform(3.0, 8.0)
                return True
            self.move_timer = random.uniform(2.0, 5.0)
        return False
    
    def move(self):
        """Move animatronic to next location"""
        path = {
            Location.STAGE: [Location.DINING],
            Location.DINING: [Location.HALLWAY],
            Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
            Location.LEFT_DOOR: [Location.LEFT_DOOR],
            Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
        }
        
        if self.location in path:
            possible = path[self.location]
            self.location = random.choice(possible)


# ============= UTILITY FUNCTIONS =============

def get_location_name(location: Location) -> str:
    """Get human-readable name for a location"""
    location_names = {
        Location.STAGE: "Show Stage",
        Location.DINING: "Dining Area",
        Location.HALLWAY: "Hallway",
        Location.LEFT_DOOR: "Left Door",
        Location.RIGHT_DOOR: "Right Door"
    }
    return location_names.get(location, "Unknown")


def create_animatronics() -> List[Animatronic]:
    """Factory function to create default animatronics for a new night"""
    return [
        Animatronic("Freddy", Location.STAGE, 2, 5.0),
        Animatronic("Bonnie", Location.STAGE, 3, 4.0),
        Animatronic("Chica", Location.STAGE, 3, 4.5),
    ]


def get_animatronics_at_location(animatronics: List[Animatronic], location: Location) -> List[Animatronic]:
    """Get list of animatronics at a specific location"""
    return [a for a in animatronics if a.location == location]


def get_animatronic_names_at_location(animatronics: List[Animatronic], location: Location) -> List[str]:
    """Get list of animatronic names at a specific location"""
    return [a.name for a in get_animatronics_at_location(animatronics, location)]


def get_movement_path() -> Dict[Location, List[Location]]:
    """Get the movement path graph for animatronics"""
    return {
        Location.STAGE: [Location.DINING],
        Location.DINING: [Location.HALLWAY],
        Location.HALLWAY: [Location.LEFT_DOOR, Location.RIGHT_DOOR],
        Location.LEFT_DOOR: [Location.LEFT_DOOR],
        Location.RIGHT_DOOR: [Location.RIGHT_DOOR]
    }


def format_game_time(game_hour: int) -> str:
    """Format game hour to readable time string"""
    hours = ["12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM"]
    return hours[min(game_hour, 6)]


def calculate_difficulty(ai_level: int, game_hour: int) -> float:
    """Calculate movement difficulty based on AI level and game progression"""
    return (ai_level + game_hour) / 20.0
