"""
turret.py — Turret entity with Vanguard shield, HP threshold regen, Aggro AI, 
Call for Help mechanic, and Time-scaling Stats (AD/Armor)
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
        
        # Sửa lại HP chuẩn xác nếu constants.py truyền nhầm
        if self.turret_type == "inhibitor":
            self.max_hp = 4000.0
        elif self.turret_type == "nexus":
            self.max_hp = 5500.0
        elif self.turret_type == "shrine":
            self.max_hp = 9999.0
        else:
            self.max_hp = 5000.0  # Outer Turret HP chuẩn
            
        self.hp             = self.max_hp
        self.attack_range   = float(data["attack_range"])
        self.invuln         = data.get("invuln", False)
        self.alive          = True
        self.dead           = False

        self.gameplay_radius    = TURRET_GAMEPLAY_RADIUS
        self.pathfinding_radius = 0.0   # turrets don't block pathing

        # Stats biến thiên (sẽ được update theo thời gian)
        self.base_dmg       = float(data["base_dmg"])
        self.armor          = float(data["armor"])
        self.mr             = float(data["mr"])

        # Shields / pen stubs (cho damage API)
        self.shields              =[]
        self.flat_armor_reduction = 0.0
        self.pct_armor_reduction  = 0.0
        self.flat_armor_pen       = 0.0
        self.pct_armor_pen        = 0.0
        self.flat_mr_reduction    = 0.0
        self.pct_mr_reduction     = 0.0
        self.flat_mr_pen          = 0.0
        self.pct_mr_pen           = 0.0

        # Vanguard shield (chỉ áp dụng cho non-shrine)
        self.vanguard_hp        = TURRET_VANGUARD_SHIELD if not self.invuln else 0.0
        self.vanguard_max       = TURRET_VANGUARD_SHIELD
        self.vanguard_regen_cd  = 0.0
        self.last_hit_timer     = 0.0

        # Attack state
        self.attack_timer       = 0.0
        self.attack_target_uid  = None

        # HP threshold regen
        self._regen_rate  = self._get_regen_rate()

    def _get_regen_rate(self) -> float:
        if self.turret_type == "inhibitor": return 3.0
        if self.turret_type == "nexus": return 6.0
        return 0.0

    def _regen_threshold(self) -> float:
        pct = self.hp / self.max_hp
        if self.turret_type == "inhibitor":
            if pct <= 0.333: return self.max_hp * 0.333
            if pct <= 0.667: return self.max_hp * 0.667
            return self.max_hp
        if self.turret_type == "nexus":
            if pct <= 0.40: return self.max_hp * 0.40
            if pct <= 0.70: return self.max_hp * 0.70
            return self.max_hp
        return self.max_hp

    def _update_scaling_stats(self, game_time: float):
        """Tính toán Sát thương và Giáp/Kháng phép theo thời gian trận đấu."""
        if self.turret_type == "shrine":
            self.base_dmg = 999.0
            self.armor = 9999.0
            self.mr = 9999.0
            return

        minutes = game_time / 60.0
        t1 = min(minutes, 8.0)
        t2 = max(0.0, minutes - 8.0)

        # AD Scaling
        if self.turret_type == "outer":
            t2_ad = min(t2, 4.0)
            self.base_dmg = 185.0 + (6.0 * t1) + (15.0 * t2_ad)
        elif self.turret_type == "inhibitor":
            t2_ad = min(t2, 7.0)
            self.base_dmg = 195.0 + (6.0 * t1) + ((132.0 / 7.0) * t2_ad)
        elif self.turret_type == "nexus":
            t2_ad = min(t2, 7.0)
            self.base_dmg = 175.0 + (6.0 * t1) + ((152.0 / 7.0) * t2_ad)

        # Armor/MR Scaling
        if self.turret_type == "outer" and minutes >= 12.0:
            self.armor = 40.0
            self.mr = 40.0
        else:
            res = 75.0 + (21.0 / 8.0) * t1
            self.armor = res
            self.mr = res

    def _check_call_for_help(self, enemies, allies) -> object:
        """
        Nếu Tướng địch đánh Tướng phe ta trong tầm Trụ -> Trụ chuyển Aggro sang Tướng địch đó.
        Sử dụng attack_target làm heuristic cho việc tấn công.
        """
        for enemy in enemies:
            if enemy.__class__.__name__ == "Champion" and getattr(enemy, 'alive', True):
                if vec_dist(enemy.pos, self.pos) <= self.attack_range + enemy.gameplay_radius:
                    # Lấy UID mục tiêu mà Tướng địch đang tấn công
                    tgt_uid = getattr(enemy, 'attack_target', None)
                    if tgt_uid is not None:
                        # Kiểm tra xem mục tiêu đó có phải Tướng phe ta không
                        if any(a.uid == tgt_uid for a in allies if a.__class__.__name__ == "Champion"):
                            return enemy
        return None

    def _pick_target(self, enemies):
        """
        Turret aggro chuẩn LMHT: Xe/Siêu cấp > Cận chiến > Đánh xa > Tướng
        Chọn mục tiêu gần nhất trong nhóm ưu tiên.
        """
        in_range =[e for e in enemies
                    if getattr(e, 'alive', True)
                    and vec_dist(e.pos, self.pos) <= self.attack_range + e.gameplay_radius]
        if not in_range:
            return None

        # Phân loại nhóm lính và tướng
        cannons =[e for e in in_range if e.__class__.__name__ == "Minion" and e.mtype in ("cannon", "super")]
        melees  =[e for e in in_range if e.__class__.__name__ == "Minion" and e.mtype == "melee"]
        casters =[e for e in in_range if e.__class__.__name__ == "Minion" and e.mtype == "caster"]
        champs  = [e for e in in_range if e.__class__.__name__ == "Champion"]

        # Xét theo thứ tự ưu tiên
        for group in [cannons, melees, casters, champs]:
            if group:
                return min(group, key=lambda e: vec_dist(e.pos, self.pos))
        
        # Fallback (phòng hờ)
        return min(in_range, key=lambda e: vec_dist(e.pos, self.pos))

    def _get_unit_by_uid(self, uid, enemies):
        for e in enemies:
            if e.uid == uid:
                return e
        return None

    def update(self, dt: float, ally_champions: list, enemy_units: list, game_time: float):
        if not self.alive:
            return

        # 1. Update Scaling Stats
        self._update_scaling_stats(game_time)

        # 2. Vanguard shield regen
        self.last_hit_timer += dt
        if self.last_hit_timer >= TURRET_VANGUARD_REGEN_CD:
            self.vanguard_hp = self.vanguard_max

        # 3. HP threshold regen
        if self._regen_rate > 0:
            cap = self._regen_threshold()
            if self.hp < cap:
                self.hp = min(cap, self.hp + self._regen_rate * dt)

        # 4. Heal nearby ally champion via Vanguard
        if self.vanguard_hp > 0:
            for champ in ally_champions:
                if not getattr(champ, 'alive', True):
                    continue
                if vec_dist(champ.pos, self.pos) <= self.attack_range:
                    champ.hp = min(champ.max_hp, champ.hp + TURRET_ALLY_HEAL_RATE * dt)

        # 5. AGGRO LOGIC
        # 5.1 Xóa mục tiêu hiện tại nếu chết hoặc ra khỏi tầm
        if self.attack_target_uid:
            target_obj = self._get_unit_by_uid(self.attack_target_uid, enemy_units)
            if not target_obj or not getattr(target_obj, 'alive', True) or vec_dist(target_obj.pos, self.pos) > self.attack_range + target_obj.gameplay_radius:
                self.attack_target_uid = None

        # 5.2 Call for Help (Ưu tiên TỐI CAO - Bỏ mục tiêu cũ để bảo vệ Tướng phe ta)
        cfh_target = self._check_call_for_help(enemy_units, ally_champions)
        if cfh_target:
            self.attack_target_uid = cfh_target.uid

        # 5.3 Chọn mục tiêu mới nếu chưa có
        if not self.attack_target_uid and enemy_units:
            new_target = self._pick_target(enemy_units)
            if new_target:
                self.attack_target_uid = new_target.uid

        # 6. FIRE (Tấn công)
        self.attack_timer -= dt
        if self.attack_timer <= 0 and self.attack_target_uid:
            target_obj = self._get_unit_by_uid(self.attack_target_uid, enemy_units)
            if target_obj:
                self._fire(target_obj)
                self.attack_timer = 1.0 / TURRET_ATTACK_SPEED

    def _fire(self, target):
        """Apply instant turret damage (giản lược: không có thời gian đạn bay)."""
        if not getattr(target, 'alive', True):
            return
        # Dùng sát thương đã scale tính toán ở trên
        apply_physical(self, target, self.base_dmg)
        
        if target.hp <= 0:
            # Gửi 0 thay vì game_time cho hàm on_death (tương thích chữ ký cũ)
            target.on_death(0)

    def take_damage(self, dmg: float, dmg_type: str = "physical"):
        """Absorb qua khiên Vanguard trước, sau đó trừ HP."""
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
            # Gửi kèm ad/armor để debug trên client nếu cần
            "ad":          round(self.base_dmg, 1),
            "armor":       round(self.armor, 1),
        }