"""
turret.py — Turret entity with Vanguard shield, HP threshold regen, aggro AI
"""
from ..physics import vec_dist
from ..damage import apply_physical
from ..constants import (
    TURRET_GAMEPLAY_RADIUS, TURRET_VANGUARD_SHIELD,
    TURRET_VANGUARD_REGEN_CD, TURRET_ALLY_HEAL_RATE,
    TURRET_ATTACK_SPEED,
)


class Turret:
    UID = 0

    def __init__(self, tid: str, data: dict):
        Turret.UID += 1
        self.uid            = Turret.UID
        self.tid            = tid
        self.team           = data["team"]
        self.turret_type    = data["type"]   # "shrine"|"inhibitor"|"outer"|"nexus"
        self.pos            = data["pos"]
        self.max_hp         = float(data["hp"])
        self.hp             = self.max_hp
        self.armor          = float(data["armor"])
        self.mr             = float(data["mr"])
        self.attack_range   = float(data["attack_range"])
        self.base_dmg       = float(data["base_dmg"])
        self.invuln         = data.get("invuln", False)
        self.alive          = True
        self.dead           = False

        self.gameplay_radius    = TURRET_GAMEPLAY_RADIUS
        self.pathfinding_radius = 0.0   # turrets don't block pathing

        # shields / pen stubs (for damage API compatibility)
        self.shields              = []
        self.flat_armor_reduction = 0.0
        self.pct_armor_reduction  = 0.0
        self.flat_armor_pen       = 0.0
        self.pct_armor_pen        = 0.0
        self.flat_mr_reduction    = 0.0
        self.pct_mr_reduction     = 0.0
        self.flat_mr_pen          = 0.0
        self.pct_mr_pen           = 0.0

        # Vanguard shield (only non-shrine turrets)
        self.vanguard_hp        = TURRET_VANGUARD_SHIELD if not self.invuln else 0.0
        self.vanguard_max       = TURRET_VANGUARD_SHIELD
        self.vanguard_regen_cd  = 0.0    # countdown; 0 = full, >0 = was recently hit
        self.last_hit_timer     = 0.0    # time since last took damage

        # Attack state
        self.attack_timer       = 0.0
        self.attack_target_uid  = None

        # HP threshold regen (inhibitor/nexus turrets)
        self._regen_rate  = self._get_regen_rate()
        self._regen_max   = self.max_hp

    def _get_regen_rate(self) -> float:
        if self.turret_type == "inhibitor":
            return 3.0      # HP/s
        if self.turret_type == "nexus":
            return 6.0
        return 0.0

    def _regen_threshold(self) -> float:
        """Max HP this turret can regen to at its current threshold tier."""
        pct = self.hp / self.max_hp
        if self.turret_type == "inhibitor":
            if pct < 0.333:   return self.max_hp * 0.333
            if pct < 0.667:   return self.max_hp * 0.667
            return self.max_hp
        if self.turret_type == "nexus":
            if pct < 0.40:    return self.max_hp * 0.40
            if pct < 0.70:    return self.max_hp * 0.70
            return self.max_hp
        return self.max_hp

    def update(self, dt: float, ally_champions: list, enemy_units: list):
        if not self.alive:
            return

        # ── Vanguard shield regen ──────────────────
        self.last_hit_timer += dt
        if self.last_hit_timer >= TURRET_VANGUARD_REGEN_CD:
            self.vanguard_hp = self.vanguard_max

        # ── HP threshold regen ─────────────────────
        if self._regen_rate > 0:
            cap = self._regen_threshold()
            if self.hp < cap:
                self.hp = min(cap, self.hp + self._regen_rate * dt)

        # ── Heal nearby ally champion via Vanguard ─
        if self.vanguard_hp > 0:
            for champ in ally_champions:
                if not champ.alive:
                    continue
                if vec_dist(champ.pos, self.pos) <= self.attack_range:
                    champ.hp = min(champ.max_hp, champ.hp + TURRET_ALLY_HEAL_RATE * dt)

        # ── Attack AI ──────────────────────────────
        self.attack_timer -= dt
        if self.attack_timer <= 0 and enemy_units:
            target = self._pick_target(enemy_units)
            if target:
                self._fire(target)
                self.attack_timer = 1.0 / TURRET_ATTACK_SPEED

    def _pick_target(self, enemies):
        """Turret aggro: champion attacking turret > champion in range > nearest minion."""
        in_range = [e for e in enemies
                    if getattr(e, 'alive', True)
                    and vec_dist(e.pos, self.pos) <=
                        self.attack_range + e.gameplay_radius]
        if not in_range:
            return None
        # Priority: champion over minion
        champs = [e for e in in_range if e.__class__.__name__ == "Champion"]
        if champs:
            return min(champs, key=lambda e: vec_dist(e.pos, self.pos))
        return min(in_range, key=lambda e: vec_dist(e.pos, self.pos))

    def _fire(self, target):
        """Apply instant turret damage (simplified — no projectile travel)."""
        if not getattr(target, 'alive', True):
            return
        apply_physical(self, target, self.base_dmg)
        self.attack_target_uid = target.uid
        if target.hp <= 0:
            target.on_death(0)

    def take_damage(self, dmg: float, dmg_type: str = "physical"):
        """Absorb through Vanguard shield first, then HP."""
        if self.invuln:
            return
        self.last_hit_timer = 0.0   # reset Vanguard regen CD
        remaining = dmg
        if self.vanguard_hp > 0:
            absorbed = min(self.vanguard_hp, remaining)
            self.vanguard_hp -= absorbed
            remaining -= absorbed
        self.hp -= remaining
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead  = True

    def to_dict(self) -> dict:
        return {
            "uid":         self.uid,
            "tid":         self.tid,
            "team":        self.team,
            "type":        self.turret_type,
            "pos":         list(self.pos),
            "hp":          round(self.hp, 1),
            "max_hp":      self.max_hp,
            "alive":       self.alive,
            "invuln":      self.invuln,
            "attack_range":  self.attack_range,
            "gameplay_r":    self.gameplay_radius,
            "vanguard_hp":   round(self.vanguard_hp, 1),
            "vanguard_max":  self.vanguard_max,
            "target_uid":    self.attack_target_uid,
        }
