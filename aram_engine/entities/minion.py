"""
minion.py — MinionAI: behavior sweep, priority targeting, ARAM waypoints,
            wave spawning, gold/XP scaling
"""
from ..physics import vec_dist, vec_normalize, vec_sub, vec_add, vec_scale, update_position
from ..constants import (
    MINION_STATS, MINION_WAYPOINTS,
    MINION_SWEEP_TICK, MINION_IGNORE_SECS,
    MINION_ACQUIRE_RANGE, MINION_ACQUIRE_ALLY,
    MINION_DROP_RANGE,
    FIRST_WAVE_TIME, WAVE_INTERVAL, CANNON_EVERY_N, WAVE_COMPOSITION,
    SIMULATION_HZ,
)
from ..damage import apply_physical


class Minion:
    UID = 0

    def __init__(self, team: str, mtype: str, pos, game_time: float = 0):
        Minion.UID += 1
        self.uid          = Minion.UID
        self.team         = team
        self.mtype        = mtype   # melee | caster | cannon | super

        stats = MINION_STATS[mtype]
        mins_elapsed = game_time / 60.0

        # HP with time scaling
        growth_hp = stats.get("hp_growth_per_min", 0) * mins_elapsed
        self.max_hp       = stats["base_hp"] + growth_hp
        self.hp           = self.max_hp

        self.base_ad      = stats["base_ad"] + stats.get("ad_growth_per_min", 0) * mins_elapsed
        self.ad           = self.base_ad
        self.armor        = float(stats["armor"])
        self.mr           = float(stats["mr"])
        self.base_ms      = float(stats["base_ms"])
        self.flat_ms_bonus = 0.0
        self.pct_ms_bonuses = []
        self.mult_ms_bonuses = []
        self.slows        = []
        self.attack_range = float(stats["attack_range"])
        self.attack_speed = float(stats["attack_speed"])
        self.attack_timer = 0.0

        self.gameplay_radius    = stats["gameplay_radius"]
        self.pathfinding_radius = stats["pathfinding_radius"]

        self.pos          = pos
        self.facing       = (1.0, 0.0)
        self.move_target  = None
        self.ghosted      = False

        # Shields/pen stubs for damage API
        self.shields              = []
        self.flat_armor_reduction = 0.0
        self.pct_armor_reduction  = 0.0
        self.flat_armor_pen       = 0.0
        self.pct_armor_pen        = 0.0
        self.flat_mr_reduction    = 0.0
        self.pct_mr_reduction     = 0.0
        self.flat_mr_pen          = 0.0
        self.pct_mr_pen           = 0.0

        # CC stubs
        self.is_airborne  = False
        self.is_rooted    = False
        self.is_suppressed = False
        self.cc_timers    = {}

        # Gold/XP
        self.gold_value   = self._calc_gold(stats, game_time)
        self.xp_value     = stats.get("xp", 0)

        # AI state
        self.waypoint_idx = 0
        self.waypoints    = MINION_WAYPOINTS[team]
        self.target       = None
        self.ignored_uids = set()
        self.fail_timer   = 0.0
        self.sweep_timer  = 0.0

        self.alive        = True

    def _calc_gold(self, stats, game_time: float) -> int:
        if self.mtype == "super":
            return stats["gold"]
        if self.mtype == "cannon":
            wave_n = int((game_time - FIRST_WAVE_TIME) / WAVE_INTERVAL / CANNON_EVERY_N)
            return min(stats["gold"] + wave_n * 3, stats.get("gold_max", 999))
        intervals = int(game_time / stats.get("gold_growth_interval", 90))
        return int(stats["gold"] + intervals * stats.get("gold_growth_rate", 0))

    def update(self, dt: float, game_state):
        if not self.alive:
            return

        # CC tick-down
        for cc in list(self.cc_timers.keys()):
            self.cc_timers[cc] -= dt
            if self.cc_timers[cc] <= 0:
                del self.cc_timers[cc]
                setattr(self, f"is_{cc}", False)

        # Attack timer
        if self.attack_timer > 0:
            self.attack_timer -= dt

        # Behavior sweep at 0.25s intervals
        self.sweep_timer += dt
        if self.sweep_timer >= MINION_SWEEP_TICK:
            self.sweep_timer = 0.0
            self.behavior_sweep(game_state)

        # Move toward move_target
        update_position(self, dt)

    def behavior_sweep(self, gs):
        # 1. Follow CC
        if self.is_airborne or self.is_rooted or self.is_suppressed:
            self.move_target = None
            return

        # 2. Current target
        if self.target:
            if not getattr(self.target, 'alive', True) or self.target.uid in self.ignored_uids:
                self.target = None
            elif vec_dist(self.pos, self.target.pos) > MINION_DROP_RANGE:
                self.target = None
            else:
                if not self._in_attack_range(self.target):
                    self.fail_timer += MINION_SWEEP_TICK
                    if self.fail_timer >= MINION_IGNORE_SECS:
                        self.ignored_uids.add(self.target.uid)
                        self.target = None
                        self.fail_timer = 0.0
                    else:
                        self.move_toward(self.target.pos)
                else:
                    self.fail_timer = 0.0
                    self.move_target = None  # dừng lại khi trong tầm đánh
                    self._attack(self.target)
                return

        # 3. Find new target by priority
        if gs:
            new_target = self._find_target(gs)
            if new_target:
                self.target     = new_target
                self.fail_timer = 0.0
                if not self._in_attack_range(new_target):
                    self.move_toward(new_target.pos)
                else:
                    self.move_target = None  # dừng lại khi trong tầm đánh
                    self._attack(new_target)
                return

        # 4. Advance waypoints
        wp = self.waypoints[self.waypoint_idx]
        if vec_dist(self.pos, wp) < 50 and self.waypoint_idx + 1 < len(self.waypoints):
            self.waypoint_idx += 1
        self.move_toward(self.waypoints[self.waypoint_idx])

    def _in_attack_range(self, target) -> bool:
        return vec_dist(self.pos, target.pos) <= self.attack_range + target.gameplay_radius

    def _attack(self, target):
        if self.attack_timer <= 0:
            apply_physical(self, target, self.ad)
            self.attack_timer = 1.0 / self.attack_speed
            if target.hp <= 0:
                if hasattr(target, 'on_death'):
                    target.on_death(0)

    def move_toward(self, dest):
        self.move_target = dest

    def _find_target(self, gs) -> object:
        """7-level priority system từ Riot spec + Priority 8 (Công trình)."""
        enemies = gs.get_enemies(self.team)
        allies  = gs.get_allies(self.team)

        candidates = [e for e in enemies
                      if e.uid not in self.ignored_uids
                      and getattr(e, 'alive', True)
                      and vec_dist(self.pos, e.pos) <= MINION_ACQUIRE_RANGE]

        def _get_target_uid(e):
            if hasattr(e, 'attack_target_uid') and e.attack_target_uid is not None:
                return e.attack_target_uid
            if hasattr(e, 'attack_target') and getattr(e, 'attack_target', None) is not None:
                if hasattr(e.attack_target, 'uid'):
                    return e.attack_target.uid
                return e.attack_target
            return None

        def _is_attacking_ally_champ(e):
            tgt_uid = _get_target_uid(e)
            if tgt_uid is None: return False
            return any(a.uid == tgt_uid for a in allies if a.__class__.__name__ == "Champion")

        def _is_attacking_ally_minion(e):
            tgt_uid = _get_target_uid(e)
            if tgt_uid is None: return False
            return any(a.uid == tgt_uid for a in allies if a.__class__.__name__ == "Minion")

        is_hitting_turret = (self.target and self.target.__class__.__name__ == "Turret")

        if not is_hitting_turret:
            p1 = [e for e in candidates if e.__class__.__name__ == "Champion" and _is_attacking_ally_champ(e)]
            if p1: return min(p1, key=lambda e: vec_dist(self.pos, e.pos))

        p2 = [e for e in candidates if e.__class__.__name__ == "Minion" and _is_attacking_ally_champ(e)]
        if p2: return min(p2, key=lambda e: vec_dist(self.pos, e.pos))

        p3 = [e for e in candidates if e.__class__.__name__ == "Minion" and _is_attacking_ally_minion(e)]
        if p3: return min(p3, key=lambda e: vec_dist(self.pos, e.pos))

        p4 = [e for e in candidates if e.__class__.__name__ == "Turret" and _is_attacking_ally_minion(e)]
        if p4: return min(p4, key=lambda e: vec_dist(self.pos, e.pos))

        p5 = [e for e in candidates if e.__class__.__name__ == "Champion" and _is_attacking_ally_minion(e)]
        if p5: return min(p5, key=lambda e: vec_dist(self.pos, e.pos))

        p6 = [e for e in candidates if e.__class__.__name__ == "Minion"]
        if p6: return min(p6, key=lambda e: vec_dist(self.pos, e.pos))

        p7 = [e for e in candidates if e.__class__.__name__ == "Champion"]
        if p7: return min(p7, key=lambda e: vec_dist(self.pos, e.pos))

        p8 = [e for e in candidates if e.__class__.__name__ == "Turret"]
        if p8: return min(p8, key=lambda e: vec_dist(self.pos, e.pos))

        return None

    def on_call_for_help(self, attacker_uid: int):
        self.ignored_uids.discard(attacker_uid)

    def on_collision(self):
        self.ignored_uids.clear()
    def apply_cc(self, cc_type: str, duration: float):
        setattr(self, f"is_{cc_type}", True)
        self.cc_timers[cc_type] = duration
        self.move_target = None
    def on_death(self, game_time: float):
        self.alive = False

    def to_dict(self) -> dict:
        return {
            "uid":           self.uid,
            "team":          self.team,
            "mtype":         self.mtype,
            "pos":           list(self.pos),
            "hp":            round(self.hp, 1),
            "max_hp":        round(self.max_hp, 1),
            "alive":         self.alive,
            "gameplay_r":    self.gameplay_radius,
            "pathfinding_r": self.pathfinding_radius,
            "attack_range":  self.attack_range,
            "target_uid":    self.target.uid if self.target else None,
        }


# ─────────────────────────────────────────────────
# Wave Spawner
# ─────────────────────────────────────────────────
class WaveSpawner:
    def __init__(self):
        self.next_wave_time = 30.0
        self.wave_number    = 0

    def update(self, game_time: float, gs) -> list:
        new_minions = []
        if game_time >= self.next_wave_time:
            self.wave_number += 1

            if game_time < 14 * 60:
                self.next_wave_time += 30.0
            elif game_time < 30 * 60:
                self.next_wave_time += 25.0
            else:
                self.next_wave_time += 20.0

            is_cannon = False
            if game_time < 14 * 60:
                is_cannon = (self.wave_number % 3 == 0)
            elif game_time < 25 * 60:
                is_cannon = (self.wave_number % 2 == 0)
            else:
                is_cannon = True

            num_casters = 2 if game_time >= 30 * 60 else 3
            num_melees  = 2 if (game_time >= 14 * 60 and is_cannon) else 3

            for team in ("blue", "red"):
                spawn_pos = gs.barracks_pos(team)

                for i in range(num_melees):
                    offset = (i * 80 - 80, 0)
                    pos = (spawn_pos[0] + offset[0], spawn_pos[1] + offset[1])
                    new_minions.append(Minion(team, "melee", pos, game_time))

                for i in range(num_casters):
                    offset = (i * 80 - 80, 100)
                    pos = (spawn_pos[0] + offset[0], spawn_pos[1] + offset[1])
                    new_minions.append(Minion(team, "caster", pos, game_time))

                if is_cannon:
                    pos = (spawn_pos[0], spawn_pos[1] - 100)
                    new_minions.append(Minion(team, "cannon", pos, game_time))

        return new_minions