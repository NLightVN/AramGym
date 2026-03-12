"""
damage.py — Physical / Magic / True damage, shields, kill gold/XP rewards
"""
from .constants import (
    CRIT_DAMAGE_MULT, AS_HARD_CAP,
    KILL_GOLD_BASE, FIRST_BLOOD_GOLD, ASSIST_POOL_PCT,
)


# ─────────────────────────────────────────────────
# Armor / MR effective calculation
# ─────────────────────────────────────────────────
def effective_armor(target) -> float:
    armor = target.armor
    armor -= getattr(target, 'flat_armor_reduction', 0.0)
    armor *= (1.0 - getattr(target, 'pct_armor_reduction', 0.0))
    armor -= getattr(target, 'flat_armor_pen', 0.0)
    armor *= (1.0 - getattr(target, 'pct_armor_pen', 0.0))
    return max(0.0, armor)


def effective_mr(target) -> float:
    mr = target.mr
    mr -= getattr(target, 'flat_mr_reduction', 0.0)
    mr *= (1.0 - getattr(target, 'pct_mr_reduction', 0.0))
    mr -= getattr(target, 'flat_mr_pen', 0.0)
    mr *= (1.0 - getattr(target, 'pct_mr_pen', 0.0))
    return max(0.0, mr)


# ─────────────────────────────────────────────────
# Damage application
# ─────────────────────────────────────────────────
def apply_physical(attacker, target, raw_dmg: float) -> float:
    eff = effective_armor(target)
    dealt = raw_dmg * 100.0 / (100.0 + eff)
    return _absorb(target, dealt, "physical")


def apply_magic(attacker, target, raw_dmg: float) -> float:
    eff = effective_mr(target)
    dealt = raw_dmg * 100.0 / (100.0 + eff)
    return _absorb(target, dealt, "magic")


def apply_true(target, raw_dmg: float) -> float:
    return _absorb(target, raw_dmg, "true")


def _absorb(target, dmg: float, dmg_type: str) -> float:
    """Drain shields first (FIFO), then HP. Returns actual damage dealt."""
    remaining = dmg
    to_remove = []
    for shield in target.shields:
        if shield["type"] in ("omnishield", dmg_type):
            absorbed = min(shield["hp"], remaining)
            shield["hp"] -= absorbed
            remaining -= absorbed
            if shield["hp"] <= 0:
                to_remove.append(shield)
        if remaining <= 0:
            break
    for s in to_remove:
        target.shields.remove(s)
    actual_hp_dmg = remaining
    target.hp = max(0.0, target.hp - actual_hp_dmg)
    return dmg   # total damage applied (shields + hp)


# ─────────────────────────────────────────────────
# Auto-attack DPS helper
# ─────────────────────────────────────────────────
def auto_attack_damage(attacker, target) -> float:
    """Compute a single auto-attack physical damage (no crit roll here)."""
    import random
    crit = random.random() < attacker.crit_chance
    multiplier = CRIT_DAMAGE_MULT if crit else 1.0
    raw = attacker.ad * multiplier
    # lifesteal
    dealt = apply_physical(attacker, target, raw)
    lifesteal = getattr(attacker, 'lifesteal', 0.0)
    attacker.hp = min(attacker.max_hp, attacker.hp + dealt * lifesteal)
    return dealt


# ─────────────────────────────────────────────────
# Kill reward system
# ─────────────────────────────────────────────────
def kill_gold(victim, is_first_blood: bool = False) -> int:
    """Gold for the killer (not including bounty yet)."""
    base = FIRST_BLOOD_GOLD if is_first_blood else KILL_GOLD_BASE
    # Bounty: positive if victim has kill streak
    bounty = min(700, max(0, (getattr(victim, 'kill_streak', 0) - 2) * 100))
    # Depreciation: if victim has death streak reduce value
    death_streak = getattr(victim, 'death_streak', 0)
    if death_streak >= 2:
        reduction = min(188, (death_streak - 1) * 47)
        base = max(112, base - reduction)
    return base + bounty


def assist_gold(victim, num_assists: int) -> int:
    """Gold per assistant."""
    if num_assists == 0:
        return 0
    pool = KILL_GOLD_BASE * ASSIST_POOL_PCT
    return int(pool / num_assists)


def kill_xp(victim_level: int) -> float:
    """XP granted to kill participant (approx formula)."""
    return 100.0 + victim_level * 20.0
