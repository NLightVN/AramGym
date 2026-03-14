"""
champion.py — Champion entity: stats, auto-attack, CC state, death/respawn
"""
from ..constants import (
    YASUO_STATS, CHAMPION_GAMEPLAY_RADIUS, CHAMPION_PATHFINDING_RADIUS,
    FLASH, ARAM_PASSIVE_XP_PER_SECOND, SIMULATION_HZ,
    yasuo_stat_at_level,
)
from ..physics import vec_dist, update_position


class Champion:
    UID = 0

    def __init__(self, team: str, champ_name: str = "yasuo",
                 level: int = 1, start_pos=None):
        Champion.UID += 1
        self.uid         = Champion.UID
        self.team        = team
        self.champ_name  = champ_name
        self.level       = level
        self.pos         = start_pos or (0.0, 0.0)
        self.facing      = (1.0, 0.0)
        self.move_target = None
        self.q_buffer_timer = 0.0

        # ── Radii ──────────────────────────────────
        self.gameplay_radius    = CHAMPION_GAMEPLAY_RADIUS
        self.pathfinding_radius = CHAMPION_PATHFINDING_RADIUS

        # ── Base stats at level ─────────────────────
        self._apply_level_stats()

        # ── Combat state ────────────────────────────
        self.shields        = []        # list of {"type": str, "hp": float}
        self.buffs          = {}        # name → remaining_duration
        self.slows          = []
        self.pct_ms_bonuses = []
        self.flat_ms_bonus  = 0.0
        self.mult_ms_bonuses = []

        # pen (set by items)
        self.flat_armor_pen   = 0.0
        self.pct_armor_pen    = 0.0
        self.flat_armor_reduction = 0.0
        self.pct_armor_reduction  = 0.0
        self.flat_mr_pen     = 0.0
        self.pct_mr_pen      = 0.0
        self.flat_mr_reduction    = 0.0
        self.pct_mr_reduction     = 0.0

        self.crit_chance    = 0.0
        self.lifesteal      = 0.0
        self.bonus_ad       = 0.0      # from items (not base)
        self.ap             = 0.0

        # ── CC flags ────────────────────────────────
        self.is_airborne    = False
        self.is_rooted      = False
        self.is_stunned     = False
        self.is_grounded    = False
        self.is_suppressed  = False
        self.is_silenced    = False
        self.is_feared      = False
        self.cc_timers      = {}       # cc_type → remaining

        # ── Attack state ────────────────────────────
        self.attack_timer    = 0.0     # countdown to next auto
        self.attack_target   = None    # uid of attack target
        self.ghosted         = False

        # ── Flash ───────────────────────────────────
        self.flash_cd        = 0.0
        self.flash_range     = FLASH["range"]

        # ── Ability CDs (yasuo) ─────────────────────
        self.q_cd = 0.0; self.q_level = 0
        self.w_cd = 0.0; self.w_level = 0
        self.e_cd = 0.0; self.e_level = 0
        self.r_cd = 0.0; self.r_level = 0
        self.q_stacks = 0
        self.q_stack_timer = 0.0
        self.e_stacks = 0
        self.e_stack_timer = 0.0

        # ── Economy ─────────────────────────────────
        self.gold           = 500      # ARAM start gold
        self.kill_streak    = 0
        self.death_streak   = 0
        self.kills          = 0
        self.deaths         = 0
        self.assists        = 0

        # ── XP ──────────────────────────────────────
        self.xp             = 0.0
        self.xp_to_next     = self._xp_to_next_level(level)

        # ── Respawn ─────────────────────────────────
        self.alive          = True
        self.respawn_timer  = 0.0

    def _apply_level_stats(self):
        s = YASUO_STATS
        lvl = self.level
        self.max_hp    = yasuo_stat_at_level(s["base_hp"],    s["hp_growth"], lvl)
        self.hp        = self.max_hp
        self.max_mana  = s["base_mp"]     # Flow (Max 100)
        self.mana      = 0.0              # Khởi đầu trận Flow = 0
        self.ad        = yasuo_stat_at_level(s["base_ad"],    s["ad_growth"], lvl)
        self.armor     = yasuo_stat_at_level(s["base_armor"], s["armor_growth"], lvl)
        self.mr        = yasuo_stat_at_level(s["base_mr"],    s["mr_growth"], lvl)
        self.base_ms   = s["base_ms"]
        self.attack_range = s["attack_range"]
        self.acquisition_range = s["acquisition_range"]
        
        # Công thức Attack Speed chuẩn LMHT
        self.base_as   = s["base_as"]
        # Bonus AS từ cấp độ
        from ..constants import _growth_factor
        self.bonus_as_pct = s["as_growth"] * _growth_factor(lvl)
        if lvl == 1:
            self.bonus_as_pct += 0.04  # Level 1 được tặng 4% AS mặc định
            
        self.attack_speed = min(self.base_as + s["as_ratio"] * self.bonus_as_pct, 2.5)
        
        # Regen
        self.hp_regen  = yasuo_stat_at_level(s["base_hp_regen"], s["hp_regen_growth"], lvl)
    def _xp_to_next_level(self, lvl: int) -> float:
        """Approximate XP required to go from lvl to lvl+1."""
        base = [0, 280, 660, 1140, 1720, 2400, 3180, 4060, 5040,
                6120, 7300, 8580, 9960, 11440, 13020, 14700, 16480, 18360]
        if lvl >= 18: return float("inf")
        return float(base[lvl])

    def update(self, dt: float):
        if self.q_buffer_timer > 0:
            self.q_buffer_timer -= dt
        if not self.alive:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self._respawn()
            return

        # ── HP regen ────────────────────────────────
        regen_per_sec = self.hp_regen / 5.0   # hp_regen stat is per 5 seconds
        self.hp = min(self.max_hp, self.hp + regen_per_sec * dt)

        # ── ARAM passive XP ─────────────────────────
        self.xp += ARAM_PASSIVE_XP_PER_SECOND * dt
        self._check_level_up()

        # ── Cooldowns ───────────────────────────────
        for attr in ("q_cd", "w_cd", "e_cd", "r_cd", "flash_cd"):
            val = getattr(self, attr)
            if val > 0:
                setattr(self, attr, max(0.0, val - dt))

        # Q stack timer
        if self.q_stacks > 0:
            self.q_stack_timer -= dt
            if self.q_stack_timer <= 0:
                self.q_stacks = 0

        # E stack decay
        if self.e_stacks > 0:
            self.e_stack_timer -= dt
            if self.e_stack_timer <= 0:
                self.e_stacks = 0

        # ── Auto-attack timer ────────────────────────
        if self.attack_timer > 0:
            self.attack_timer -= dt

        # ── CC tick-down ────────────────────────────
        for cc in list(self.cc_timers.keys()):
            self.cc_timers[cc] -= dt
            if self.cc_timers[cc] <= 0:
                del self.cc_timers[cc]
                setattr(self, f"is_{cc}", False)

        # ── Buff tick-down ───────────────────────────
        for buf in list(self.buffs.keys()):
            self.buffs[buf] -= dt
            if self.buffs[buf] <= 0:
                del self.buffs[buf]

        # ── MS temp lists (re-computed each tick from buffs) ─
        # Slows are cleared each tick and re-applied by CC system
        self.slows = []

        # ── Movement ────────────────────────────────
        update_position(self, dt)

    def _check_level_up(self):
        while self.level < 18 and self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            old_hp_pct = self.hp / self.max_hp
            self._apply_level_stats()
            self.hp = self.max_hp * old_hp_pct
            self.xp_to_next = self._xp_to_next_level(self.level)

    def apply_cc(self, cc_type: str, duration: float):
        """Apply a CC effect (airborne, rooted, stunned, etc.)."""
        # Airborne beats all
        existing = self.cc_timers.get(cc_type, 0.0)
        self.cc_timers[cc_type] = max(existing, duration)
        setattr(self, f"is_{cc_type}", True)
        if cc_type == "airborne":
            self.move_target = None  # can't move while airborne

    def on_death(self, game_time: float):
        self.alive      = False
        self.hp         = 0.0
        self.shields    = []
        self.death_streak += 1
        self.kill_streak  = 0
        # ARAM respawn timer (increases with level, shorter than SR)
        base_respawn = 6.0 + self.level * 2.5
        self.respawn_timer = base_respawn

    def _respawn(self):
        from ..constants import SPAWN_POINTS
        self.alive       = True
        self.pos         = SPAWN_POINTS[self.team]
        self.hp          = self.max_hp
        self.mana        = self.max_mana
        self.move_target = None
        self.shields     = []
        self.cc_timers   = {}
        for cc in ("airborne","rooted","stunned","grounded","suppressed","silenced","feared"):
            setattr(self, f"is_{cc}", False)

    def on_kill(self):
        self.kill_streak += 1
        self.death_streak  = 0
        self.kills        += 1

    def to_dict(self) -> dict:
        return {
            "uid":        self.uid,
            "team":       self.team,
            "pos":        list(self.pos),
            "facing":     list(self.facing),
            "hp":         round(self.hp, 1),
            "max_hp":     round(self.max_hp, 1),
            "level":      self.level,
            "alive":      self.alive,
            "respawn_t":  round(self.respawn_timer, 1),
            "gold":       self.gold,
            "kills":      self.kills,
            "deaths":     self.deaths,
            "assists":    self.assists,
            # Radii for renderer
            "gameplay_r":    self.gameplay_radius,
            "pathfinding_r": self.pathfinding_radius,
            "attack_range":  self.attack_range,
            "acquisition_r": self.acquisition_range,
            "flash_range":   self.flash_range,
            # Cooldowns
            "q_cd": round(self.q_cd, 2),
            "w_cd": round(self.w_cd, 2),
            "e_cd": round(self.e_cd, 2),
            "r_cd": round(self.r_cd, 2),
            "flash_cd": round(self.flash_cd, 1),
            "q_stacks": self.q_stacks,
            "e_stacks": self.e_stacks,
            # CC
            "is_airborne":   self.is_airborne,
            "is_rooted":     self.is_rooted,
            "is_stunned":    self.is_stunned,
        }
