"""
physics.py — Kinematic movement, MS soft cap, unit collision, Flash blink
"""
import math
from typing import List, Tuple

Vec2 = Tuple[float, float]


# ─────────────────────────────────────────────────
# Vec2 helpers
# ─────────────────────────────────────────────────
def vec_add(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] + b[0], a[1] + b[1])

def vec_sub(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])

def vec_scale(a: Vec2, s: float) -> Vec2:
    return (a[0] * s, a[1] * s)

def vec_length(a: Vec2) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1])

def vec_normalize(a: Vec2) -> Vec2:
    l = vec_length(a)
    if l < 1e-9:
        return (0.0, 0.0)
    return (a[0] / l, a[1] / l)

def vec_dist(a: Vec2, b: Vec2) -> float:
    return vec_length(vec_sub(a, b))

def vec_dot(a: Vec2, b: Vec2) -> float:
    return a[0] * b[0] + a[1] * b[1]


# ─────────────────────────────────────────────────
# Movement Speed soft cap
# ─────────────────────────────────────────────────
def calculate_ms(unit) -> float:
    """Apply bonus, slow, then soft cap."""
    raw = unit.base_ms + unit.flat_ms_bonus
    raw *= (1.0 + sum(unit.pct_ms_bonuses))
    if unit.slows:
        raw *= (1.0 - max(unit.slows))
    # multiplicative bonuses
    for m in unit.mult_ms_bonuses:
        raw *= m
    # soft cap
    if raw < 220:
        return 220.0
    elif raw <= 414:
        return raw
    elif raw <= 490:
        return 415.0 + (raw - 415.0) * 0.8
    else:
        return 415.0 + 60.0 + (raw - 490.0) * 0.5


def update_position(unit, dt: float):
    """Kinematic movement — no acceleration. Snap to target if overshoot."""
    if unit.move_target is None:
        return
    if unit.is_rooted or unit.is_suppressed:
        return   # can't move
    ms = calculate_ms(unit)
    direction = vec_normalize(vec_sub(unit.move_target, unit.pos))
    step = ms * dt
    dist = vec_dist(unit.pos, unit.move_target)
    if step >= dist:
        unit.pos = unit.move_target
        unit.move_target = None
    else:
        unit.pos = vec_add(unit.pos, vec_scale(direction, step))
    unit.facing = direction


# ─────────────────────────────────────────────────
# Unit-to-unit collision (push-apart)
# ─────────────────────────────────────────────────
def resolve_collisions(units: list):
    """
    Push overlapping units apart based on PathfindingCollisionRadius.
    Only applied between units that are NOT ghosted.
    """
    n = len(units)
    for i in range(n):
        a = units[i]
        if getattr(a, 'ghosted', False):
            continue
        for j in range(i + 1, n):
            b = units[j]
            if getattr(b, 'ghosted', False):
                continue
            min_dist = a.pathfinding_radius + b.pathfinding_radius
            diff = vec_sub(a.pos, b.pos)
            dist = vec_length(diff)
            if dist < min_dist and dist > 1e-6:
                overlap = min_dist - dist
                push = vec_scale(vec_normalize(diff), overlap * 0.5)
                a.pos = vec_add(a.pos, push)
                b.pos = vec_sub(b.pos, push)


# ─────────────────────────────────────────────────
# Flash blink
# ─────────────────────────────────────────────────
FLASH_RANGE    = 425.0
FLASH_COOLDOWN = 300.0

def cast_flash(unit, cursor_world: Vec2, walkable_fn=None) -> bool:
    """
    Instant blink toward cursor_world, max FLASH_RANGE units.
    Returns True if flash succeeded.
    Blocked by: airborne, rooted, grounded, suppressed.
    """
    blocked = {"airborne", "rooted", "grounded", "suppressed"}
    for cc in blocked:
        if getattr(unit, f"is_{cc}", False):
            return False

    direction = vec_normalize(vec_sub(cursor_world, unit.pos))
    dist_to_cursor = vec_dist(cursor_world, unit.pos)
    blink_dist = min(dist_to_cursor, FLASH_RANGE)
    candidate = vec_add(unit.pos, vec_scale(direction, blink_dist))

    # Wall snap: if walkable_fn provided, ensure we land on walkable cell
    if walkable_fn and not walkable_fn(candidate):
        # Binary search back along direction to find last walkable
        lo, hi = 0.0, blink_dist
        for _ in range(16):
            mid = (lo + hi) / 2
            test = vec_add(unit.pos, vec_scale(direction, mid))
            if walkable_fn(test):
                lo = mid
            else:
                hi = mid
        candidate = vec_add(unit.pos, vec_scale(direction, lo))

    unit.pos = candidate
    unit.facing = direction
    unit.flash_cd = FLASH_COOLDOWN
    return True


# ─────────────────────────────────────────────────
# Projectile movement
# ─────────────────────────────────────────────────
def update_projectile(proj, dt: float):
    """Move a straight-line projectile."""
    step = proj.speed * dt
    proj.pos = vec_add(proj.pos, vec_scale(proj.direction, step))
    proj.distance_traveled += step


# ─────────────────────────────────────────────────
# Geometry helpers for abilities
# ─────────────────────────────────────────────────
def point_segment_dist(p: Vec2, a: Vec2, b: Vec2) -> float:
    """Shortest distance from point p to segment a-b."""
    ab = vec_sub(b, a)
    ap = vec_sub(p, a)
    t = vec_dot(ap, ab) / max(vec_dot(ab, ab), 1e-9)
    t = max(0.0, min(1.0, t))
    closest = vec_add(a, vec_scale(ab, t))
    return vec_dist(p, closest)


def line_hitbox_hit(p: Vec2, seg_a: Vec2, seg_b: Vec2, half_width: float, target_radius: float) -> bool:
    """Check if a capsule (line + width) hits a circle target."""
    return point_segment_dist(p, seg_a, seg_b) <= half_width + target_radius
