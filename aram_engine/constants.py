"""
constants.py — Toàn bộ thông số game từ gamestats.md & lol-simulator-spec.md
"""
import math

# ─────────────────────────────────────────────────
# MAP — ARAM (Howling Abyss, Map 12)
# ─────────────────────────────────────────────────
MAP_SIZE = 12800  # units (approximate)

SPAWN_POINTS = {
    "blue": (937.0,   1060.6),
    "red":  (11860.1, 11596.2),
}

BARRACKS = {
    "blue": (3064.1,  3212.7),
    "red":  (10786.9, 11110.9),
}

# Waypoints: blue marches từ barracks → red barracks
MINION_WAYPOINTS = {
    "blue": [
        (3064.1,  3212.7),
        (5448.4,  6169.1),
        (8548.8,  8289.5),
        (10786.9, 11110.9),
    ],
    "red": [
        (10786.9, 11110.9),
        (8548.8,  8289.5),
        (5448.4,  6169.1),
        (3064.1,  3212.7),
    ],
}

TURRET_DATA = {
    # ── Blue (Order) ──────────────────────────────────────────
    "blue_shrine":  {"pos": (648.1,   764.2),   "team": "blue", "type": "shrine",
                     "hp": 9999, "armor": 9999, "mr": 9999,
                     "attack_range": 1250, "base_dmg": 999, "invuln": True},
    "blue_outer":   {"pos": (5448.4,  6169.1),  "team": "blue", "type": "outer",
                     "hp": 5000, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 185, "invuln": False},
    "blue_inner":   {"pos": (4943.5,  4929.8),  "team": "blue", "type": "outer",
                     "hp": 5000, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 185, "invuln": False},
    "blue_base_1":  {"pos": (2493.2,  2101.2),  "team": "blue", "type": "nexus",
                     "hp": 5500, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 175, "invuln": False},
    "blue_base_2":  {"pos": (2036.7,  2552.7),  "team": "blue", "type": "nexus",
                     "hp": 5500, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 175, "invuln": False},

    # ── Red (Chaos) ───────────────────────────────────────────
    "red_shrine":   {"pos": (12168.7, 11913.3), "team": "red",  "type": "shrine",
                     "hp": 9999, "armor": 9999, "mr": 9999,
                     "attack_range": 1250, "base_dmg": 999, "invuln": True},
    "red_outer":    {"pos": (7879.1,  7774.8),  "team": "red",  "type": "outer",
                     "hp": 5000, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 185, "invuln": False},
    "red_inner":    {"pos": (8548.8,  8289.5),  "team": "red",  "type": "outer",
                     "hp": 5000, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 185, "invuln": False},
    "red_base_1":   {"pos": (10785.2, 10117.6), "team": "red",  "type": "nexus",
                     "hp": 5500, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 175, "invuln": False},
    "red_base_2":   {"pos": (10325.2, 10608.2), "team": "red",  "type": "nexus",
                     "hp": 5500, "armor": 75, "mr": 75,
                     "attack_range": 750,  "base_dmg": 175, "invuln": False},
}

INHIBITOR_DATA = {
    "blue_inhib": {"pos": (3809.1, 3829.1), "team": "blue",
                   "hp": 4000, "max_hp": 4000, "armor": 20, "mr": 0, "radius": 150},
    "red_inhib":  {"pos": (9017.6, 8871.4), "team": "red",
                   "hp": 4000, "max_hp": 4000, "armor": 20, "mr": 0, "radius": 150},
}

NEXUS_DATA = {
    "blue_nexus": {"pos": (937.0,   1060.6), "team": "blue",
                   "hp": 5500, "max_hp": 5500, "armor": 0, "mr": 0, "radius": 250},
    "red_nexus":  {"pos": (11860.1, 11596.2), "team": "red",
                   "hp": 5500, "max_hp": 5500, "armor": 0, "mr": 0, "radius": 250},
}

# ─────────────────────────────────────────────────
# TURRET MECHANICS
# ─────────────────────────────────────────────────
TURRET_GAMEPLAY_RADIUS    = 88.4
TURRET_VANGUARD_SHIELD    = 30.0   # HP shield
TURRET_VANGUARD_REGEN_CD  = 30.0   # seconds to regen shield
TURRET_ALLY_HEAL_RATE     = 30.0   # HP/s to nearby ally champion
TURRET_ATTACK_SPEED       = 1.0    # attacks per second (approx)

# ─────────────────────────────────────────────────
# GAMPLAY / PATHFINDING RADII
# ─────────────────────────────────────────────────
CHAMPION_GAMEPLAY_RADIUS    = 65.0
CHAMPION_PATHFINDING_RADIUS = 32.0

MINION_GAMEPLAY_RADIUS_NORMAL = 48.0
MINION_GAMEPLAY_RADIUS_CANNON = 65.0
MINION_PATHFINDING_RADIUS     = 35.74

# ─────────────────────────────────────────────────
# CHAMPION — YASUO BASE STATS (Level 1)
# ─────────────────────────────────────────────────
YASUO_STATS = {
    "base_hp":       590.0, "hp_growth":       110.0,
    "base_hp_regen":   6.5, "hp_regen_growth":   0.9,
    "base_mp":       100.0, "mp_growth":         0.0, # Flow
    "base_ad":        60.0, "ad_growth":         2.5,
    "base_armor":     32.0, "armor_growth":      4.6,
    "base_mr":        32.0, "mr_growth":        2.05,
    "base_ms":       345.0,
    "base_as":       0.697, "as_ratio":         0.670, "as_growth": 0.035, # 3.5%
    "attack_range":  175.0,
    "acquisition_range": 400.0,
    "gameplay_radius":     CHAMPION_GAMEPLAY_RADIUS,
    "pathfinding_radius":  CHAMPION_PATHFINDING_RADIUS,
}

# Stat growth formula multiplier per level (approximation from LoL Wiki)
# stat(lvl) = base + growth * (lvl-1) * (0.7025 + 0.0175*(lvl-1))
def _growth_factor(level: int) -> float:
    if level <= 1:
        return 0.0
    n = level - 1
    return n * (0.7025 + 0.0175 * n)

def yasuo_stat_at_level(stat_base: float, stat_growth: float, level: int) -> float:
    return stat_base + stat_growth * _growth_factor(level)

# ─────────────────────────────────────────────────
# ABILITIES — YASUO
# ─────────────────────────────────────────────────
YASUO_Q = {
    "cast_range": 475.0,
    "missile_speed": 1500.0,
    "width": 55.0,
    "cooldown": [6.0, 5.5, 5.0, 4.5, 4.0],       # per level 1-5
    "base_dmg": [20, 40, 60, 80, 100],
    "ad_ratio": 1.0,
    "stack_timer": [5.0, 4.75, 4.5, 4.25, 4.0],  # seconds to hold Q stack
}

YASUO_Q3 = {
    "display_range": 1000.0,
    "server_range":  3250.0,
    "width": 90.0,
    "missile_speed": 1500.0,
    "knockup_duration": 0.75,   # seconds, fixed
}

YASUO_W = {
    "cast_range": 400.0,
    "wall_widths": [300, 350, 400, 450, 500],  # per level 1-5
    "cooldown": [26.0, 24.0, 22.0, 20.0, 18.0],
    "duration": 3.75,
}

YASUO_E = {
    "dash_range": 475.0,          # fixed, NOT dependent on cursor
    "cooldown_between": [0.5, 0.4, 0.3, 0.2, 0.1],  # per level
    "target_cooldown": [10.0, 9.0, 8.0, 7.0, 6.0],  # per level, same target
    "base_dmg": [70, 90, 110, 130, 150],
    "ap_ratio": 0.6,
    "stack_bonus": 0.25,   # +25% base dmg per stack
    "max_stacks": 4,
    "stack_decay": 4.5,    # seconds before stacks reset
}

YASUO_EQ_COMBO = {
    "aoe_radius": 375.0,   # spin AoE when Q cast during E
}

YASUO_R = {
    "cast_range": 1200.0,
    "cooldown": [80.0, 55.0, 30.0],   # per level 1-3
    "base_dmg": [200, 300, 400],
    "bonus_ad_ratio": 1.5,
    "knockup_extension": 1.0,   # seconds added to target's airborne
    "bounce_radius": 450.0,     # pulls all airborne enemies in range
    "spawn_offset": 100.0,      # units behind target
    "turret_avoid_range": 750.0,
}

# ─────────────────────────────────────────────────
# SUMMONER SPELLS
# ─────────────────────────────────────────────────
FLASH = {
    "range": 425.0,
    "cooldown": 300.0,
    "key": "D",
    # CC states that BLOCK flash
    "blocked_by": {"airborne", "rooted", "grounded", "suppressed"},
}

# ─────────────────────────────────────────────────
# MINION STATS
# ─────────────────────────────────────────────────
MINION_STATS = {
    "melee": {
        "base_hp": 477, "hp_growth_per_min": 22,
        "base_ad": 12,  "ad_growth_per_min": 1.5,
        "base_ms": 350, "armor": 0, "mr": 0,
        "attack_range": 110, "attack_speed": 1.25,
        "gameplay_radius": MINION_GAMEPLAY_RADIUS_NORMAL,
        "pathfinding_radius": MINION_PATHFINDING_RADIUS,
        "gold": 20, "gold_growth_rate": 0.125, "gold_growth_interval": 90,
        "xp": 60,
    },
    "caster": {
        "base_hp": 296, "hp_growth_per_min": 15,
        "base_ad": 24,  "ad_growth_per_min": 1.5,
        "base_ms": 350, "armor": 0, "mr": 0,
        "attack_range": 550, "attack_speed": 0.667,
        "gameplay_radius": MINION_GAMEPLAY_RADIUS_NORMAL,
        "pathfinding_radius": MINION_PATHFINDING_RADIUS,
        "gold": 14, "gold_growth_rate": 0.125, "gold_growth_interval": 90,
        "xp": 29,
    },
    "cannon": {
        "base_hp": 900, "hp_growth_per_min": 35,
        "base_ad": 40,  "ad_growth_per_min": 3,
        "base_ms": 350, "armor": 30, "mr": 0,
        "attack_range": 300, "attack_speed": 1.00,
        "gameplay_radius": MINION_GAMEPLAY_RADIUS_CANNON,
        "pathfinding_radius": MINION_PATHFINDING_RADIUS,
        "gold": 50, "gold_max": 90, "gold_per_wave": 3,
        "xp": 90,
    },
    "super": {
        "base_hp": 1600, "hp_growth_per_180s": 150, "hp_scale_stop_min": 90,
        "base_ad": 230,  "ad_growth_per_90s": 5,    "ad_scale_stop_min": 90,
        "base_ms": 350, "armor": 30, "mr": -30,
        "attack_range": 170, "attack_speed": 0.85,
        "gameplay_radius": MINION_GAMEPLAY_RADIUS_CANNON,
        "pathfinding_radius": MINION_PATHFINDING_RADIUS,
        "gold": 40,
        "xp": 95,
    },
}

# ─────────────────────────────────────────────────
# MINION WAVE TIMING
# ─────────────────────────────────────────────────
FIRST_WAVE_TIME    = 65.0   # seconds
WAVE_INTERVAL      = 30.0   # seconds
CANNON_EVERY_N     = 3      # every 3rd wave has a cannon
WAVE_COMPOSITION   = {"melee": 3, "caster": 3}   # standard wave

# ─────────────────────────────────────────────────
# MINION AI
# ─────────────────────────────────────────────────
MINION_SWEEP_TICK    = 0.25   # seconds
MINION_IGNORE_SECS   = 4.0
MINION_ACQUIRE_RANGE = 500
MINION_ACQUIRE_ALLY  = 1000
MINION_DROP_RANGE    = 500    # drop aggro if > this

# ─────────────────────────────────────────────────
# PHYSICS / MOVEMENT
# ─────────────────────────────────────────────────
SIMULATION_HZ = 30
TICK_DT       = 1.0 / SIMULATION_HZ   # 0.03333s

# Vision ranges
VISION_CHAMPION = 1100
VISION_MINION   = 900
VISION_TURRET   = 900

# ─────────────────────────────────────────────────
# DAMAGE / KILL REWARDS
# ─────────────────────────────────────────────────
KILL_GOLD_BASE      = 300
FIRST_BLOOD_GOLD    = 400
ASSIST_POOL_PCT     = 0.5    # 50% of kill gold → assist pool
CRIT_DAMAGE_MULT    = 1.75
AS_HARD_CAP         = 2.5
XP_RANGE_FROM_KILL  = 1500   # champion kill XP radius

# ARAM passive XP (approximate per second)
ARAM_PASSIVE_XP_PER_SECOND = 3.5

# ─────────────────────────────────────────────────
# COLORS for raw client
# ─────────────────────────────────────────────────
TEAM_COLOR = {"blue": "#4a9eff", "red": "#ff4a4a"}
