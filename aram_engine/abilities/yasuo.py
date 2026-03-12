"""
yasuo.py — Yasuo Q/Q3/W/E/EQ/R + Flash ability implementations
"""
import math
from ..physics import (
    vec_add, vec_sub, vec_scale, vec_normalize, vec_dist, vec_length,
    cast_flash,
)
from ..damage import apply_physical, apply_true
from ..constants import (
    YASUO_Q, YASUO_Q3, YASUO_W, YASUO_E, YASUO_EQ_COMBO, YASUO_R, FLASH,
)
from ..entities.projectile import Projectile, WindWall


# ─────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────
def _level_idx(lvl: int) -> int:
    return max(0, min(lvl - 1, 4))


# ─────────────────────────────────────────────────
# Q — Steel Tempest / Q3 Tornado
# ─────────────────────────────────────────────────
def cast_q(yasuo, cursor_world: tuple, gs) -> bool:
    """
    Q casts either a straight stab missile or a Tornado (Q3).
    Returns True if cast succeeded.
    """
    lvl_i = _level_idx(yasuo.q_level)
    cd = YASUO_Q["cooldown"][lvl_i]
    # CD scales with attack speed
    cd = max(1.33, cd / (yasuo.attack_speed / yasuo.base_as))

    if yasuo.q_cd > 0 or yasuo.is_silenced or not yasuo.alive:
        return False

    direction = vec_normalize(vec_sub(cursor_world, yasuo.pos))

    if yasuo.q_stacks >= 2:
        # ── Q3 Tornado ──────────────────────────
        _fire_tornado(yasuo, direction, gs)
        yasuo.q_stacks = 0
        yasuo.q_stack_timer = 0.0
    else:
        # ── Normal Q stab ────────────────────────
        _fire_q_missile(yasuo, direction, gs)
        yasuo.q_stacks += 1
        yasuo.q_stack_timer = YASUO_Q["stack_timer"][lvl_i]

    yasuo.q_cd = cd
    return True


def _fire_q_missile(yasuo, direction, gs):
    lvl_i = _level_idx(yasuo.q_level)
    base_dmg = YASUO_Q["base_dmg"][lvl_i]
    ad_bonus = yasuo.ad * YASUO_Q["ad_ratio"]

    def dmg_fn(target):
        apply_physical(yasuo, target, base_dmg + ad_bonus)

    proj = Projectile(
        owner_uid=yasuo.uid,
        team=yasuo.team,
        pos=yasuo.pos,
        direction=direction,
        speed=YASUO_Q["missile_speed"],
        half_width=YASUO_Q["width"] / 2,
        range_max=YASUO_Q["cast_range"],
        dmg_fn=dmg_fn,
        dmg_type="physical",
        spell_name="Q",
    )
    gs.projectiles.append(proj)


def _fire_tornado(yasuo, direction, gs):
    base_dmg = YASUO_Q["base_dmg"][_level_idx(yasuo.q_level)]
    ad_bonus = yasuo.ad * YASUO_Q["ad_ratio"]

    def dmg_fn(target):
        apply_physical(yasuo, target, base_dmg + ad_bonus)
        target.apply_cc("airborne", YASUO_Q3["knockup_duration"])
        # Call for help on affected minions' ally minions
        for unit in gs.get_allies(target.team):
            if hasattr(unit, 'on_call_for_help'):
                unit.on_call_for_help(yasuo.uid)

    proj = Projectile(
        owner_uid=yasuo.uid,
        team=yasuo.team,
        pos=yasuo.pos,
        direction=direction,
        speed=YASUO_Q3["missile_speed"],
        half_width=YASUO_Q3["width"] / 2,
        range_max=YASUO_Q3["server_range"],
        dmg_fn=dmg_fn,
        dmg_type="physical",
        knockup=YASUO_Q3["knockup_duration"],
        spell_name="Q3",
    )
    gs.projectiles.append(proj)


# ─────────────────────────────────────────────────
# W — Wind Wall
# ─────────────────────────────────────────────────
def cast_w(yasuo, cursor_world: tuple, gs) -> bool:
    lvl_i = _level_idx(yasuo.w_level)
    if yasuo.w_cd > 0 or yasuo.is_silenced or not yasuo.alive:
        return False

    direction = vec_normalize(vec_sub(cursor_world, yasuo.pos))
    wall_center = vec_add(yasuo.pos, vec_scale(direction, YASUO_W["cast_range"]))
    half_w = YASUO_W["wall_widths"][lvl_i] / 2

    ww = WindWall(
        owner_uid=yasuo.uid,
        team=yasuo.team,
        center=wall_center,
        half_width=half_w,
        duration=YASUO_W["duration"],
    )
    gs.wind_walls.append(ww)
    yasuo.w_cd = YASUO_W["cooldown"][lvl_i]
    return True


# ─────────────────────────────────────────────────
# E — Sweeping Blade (dash through target)
# ─────────────────────────────────────────────────
def cast_e(yasuo, target, gs) -> bool:
    lvl_i = _level_idx(yasuo.e_level)

    if yasuo.e_cd > 0 or yasuo.is_silenced or not yasuo.alive:
        return False
    if not getattr(target, 'alive', True):
        return False

    # Target cooldown check (same target)
    tc_key = f"e_target_{target.uid}"
    if yasuo.buffs.get(tc_key, 0) > 0:
        return False

    # Dash direction: Yasuo → target, land beyond target
    direction = vec_normalize(vec_sub(target.pos, yasuo.pos))
    dash_dest = vec_add(target.pos, vec_scale(direction, YASUO_E["dash_range"]))

    # Damage
    base_dmg = YASUO_E["base_dmg"][lvl_i]
    stack_mult = 1.0 + YASUO_E["stack_bonus"] * min(yasuo.e_stacks, YASUO_E["max_stacks"])
    dmg = base_dmg * stack_mult + YASUO_E["ap_ratio"] * yasuo.ap

    # Check if Q is ready/mid-cast → EQ Combo (AoE spin)
    eq_combo = False   # simplified: no mid-dash Q in this version

    apply_physical(yasuo, target, dmg)

    # Move Yasuo instantly to dash dest (E animation is near-instant at ~475 u)
    yasuo.pos = dash_dest
    yasuo.facing = direction
    yasuo.move_target = None
    yasuo.ghosted = True   # ignore unit collision during E

    # Stack update (different target → increase stacks)
    yasuo.e_stacks = min(yasuo.e_stacks + 1, YASUO_E["max_stacks"])
    yasuo.e_stack_timer = YASUO_E["stack_decay"]

    # CDs
    yasuo.e_cd = YASUO_E["cooldown_between"][lvl_i]
    yasuo.buffs[tc_key] = YASUO_E["target_cooldown"][lvl_i]

    # Un-ghost next physics tick  (ghosted cleared after collision resolve)
    gs.schedule_unghost(yasuo.uid, delay=0.1)

    # Target on damage
    if target.hp <= 0 and hasattr(target, 'on_death'):
        target.on_death(gs.game_time)

    return True


# ─────────────────────────────────────────────────
# R — Last Breath
# ─────────────────────────────────────────────────
def cast_r(yasuo, target, gs) -> bool:
    lvl_i = _level_idx(yasuo.r_level)
    if yasuo.r_cd > 0 or yasuo.is_silenced or not yasuo.alive:
        return False
    if not getattr(target, 'alive', True):
        return False
    if not target.is_airborne:
        return False   # requires airborne target
    if vec_dist(yasuo.pos, target.pos) > YASUO_R["cast_range"]:
        return False

    # Blink Yasuo behind target (or in front if near enemy turret)
    spawn = _r_spawn_pos(yasuo, target, gs)
    yasuo.pos        = spawn
    yasuo.move_target = None

    # Damage & extend airborne on primary target
    base_dmg = YASUO_R["base_dmg"][lvl_i]
    bonus_ad_dmg = yasuo.bonus_ad * YASUO_R["bonus_ad_ratio"]
    apply_true(target, base_dmg + bonus_ad_dmg)
    target.apply_cc("airborne", YASUO_R["knockup_extension"])

    # AoE: pull other airborne enemies within bounce radius
    for unit in gs.get_enemies(yasuo.team):
        if unit.uid == target.uid:
            continue
        if not getattr(unit, 'alive', True):
            continue
        if not unit.is_airborne:
            continue
        if vec_dist(target.pos, unit.pos) <= YASUO_R["bounce_radius"]:
            apply_true(unit, base_dmg + bonus_ad_dmg)
            unit.apply_cc("airborne", YASUO_R["knockup_extension"])

    yasuo.r_cd = YASUO_R["cooldown"][lvl_i]
    return True


def _r_spawn_pos(yasuo, target, gs) -> tuple:
    direction = vec_normalize(vec_sub(target.pos, yasuo.pos))
    candidate = vec_add(target.pos, vec_scale(direction, YASUO_R["spawn_offset"]))

    # If inside enemy turret range try opposite side
    enemy_turrets = [t for t in gs.turrets.values()
                     if t.team != yasuo.team and t.alive]
    for turret in enemy_turrets:
        if vec_dist(candidate, turret.pos) < YASUO_R["turret_avoid_range"]:
            alt = vec_sub(target.pos, vec_scale(direction, YASUO_R["spawn_offset"]))
            if vec_dist(alt, turret.pos) >= YASUO_R["turret_avoid_range"]:
                return alt
    return candidate


# ─────────────────────────────────────────────────
# D — Flash
# ─────────────────────────────────────────────────
def cast_flash_yasuo(yasuo, cursor_world: tuple, gs) -> bool:
    if yasuo.flash_cd > 0:
        return False
    blocked = FLASH["blocked_by"]
    for cc in blocked:
        if getattr(yasuo, f"is_{cc}", False):
            return False
    return cast_flash(yasuo, cursor_world)
