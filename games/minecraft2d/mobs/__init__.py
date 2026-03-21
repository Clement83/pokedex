"""
Package mobs – exports publics.
"""
from mobs.base import (
    Mob,
    MOB_SLIME, MOB_ZOMBIE, MOB_GOLEM,
    MOB_CHICKEN, MOB_FROG, MOB_SEAGULL,
)
from mobs.manager import MobManager

__all__ = [
    "MobManager", "Mob",
    "MOB_SLIME", "MOB_ZOMBIE", "MOB_GOLEM",
    "MOB_CHICKEN", "MOB_FROG", "MOB_SEAGULL",
]
