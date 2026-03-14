"""
projectile.py — Missiles, Wind Wall segments
"""
from ..physics import vec_add, vec_scale, vec_dist, line_hitbox_hit, vec_normalize

class Projectile:
    UID = 0

    def __init__(self, owner_uid, team, pos, direction, speed,
                 half_width, range_max, dmg_fn, dmg_type="physical",
                 knockup=0.0, spell_name="", piercing=True, blockable=True): # <--- Thêm 2 cờ mới
        Projectile.UID += 1
        self.uid               = Projectile.UID
        self.owner_uid         = owner_uid
        self.team              = team
        self.pos               = pos
        self.start_pos         = pos
        self.direction         = direction
        self.speed             = speed
        self.half_width        = half_width   # capsule half-width
        self.range_max         = range_max
        self.distance_traveled = 0.0
        self.dmg_fn            = dmg_fn       # callable(target)
        self.dmg_type          = dmg_type
        self.knockup           = knockup      # seconds; 0 = no knockup
        self.spell_name        = spell_name
        self.piercing          = piercing     # Đạn xuyên thấu? (True = Xuyên hết, False = Trúng 1 mục tiêu là biến mất)
        self.blockable         = blockable    # Có bị Tường Gió chặn không?
        self.dead              = False
        self.hit_uids          = set()        # already-hit targets (prevent multi-hit)

    def update(self, dt: float):
        step = self.speed * dt
        self.pos = vec_add(self.pos, vec_scale(self.direction, step))
        self.distance_traveled += step
        if self.distance_traveled >= self.range_max:
            self.dead = True

    def check_hit(self, targets: list, wind_walls: list) -> list:
        """
        Returns list of targets that should receive damage this frame.
        Respects Wind Wall blocking.
        """
        if self.dead:
            return[]
        hits =[]
        seg_a = vec_add(self.start_pos,
                        vec_scale(self.direction, max(0, self.distance_traveled - self.speed * 0.033)))
        seg_b = self.pos

        # 1. KIỂM TRA TƯỜNG GIÓ (Chỉ check nếu đạn này bị cản được)
        if self.blockable:
            for ww in wind_walls:
                if ww.team == self.team:
                    continue
                if _segment_crosses_wall(seg_a, seg_b, ww):
                    self.dead = True
                    return[]

        # 2. KIỂM TRA TRÚNG MỤC TIÊU
        for tgt in targets:
            if tgt.uid in self.hit_uids:
                continue
            if not getattr(tgt, 'alive', True):
                continue
                
            if line_hitbox_hit(tgt.pos, seg_a, seg_b, self.half_width, tgt.gameplay_radius):
                hits.append(tgt)
                self.hit_uids.add(tgt.uid)
                
                # Nếu Đạn KHÔNG xuyên thấu -> Trúng 1 mục tiêu là tự hủy ngay lập tức
                if not self.piercing:
                    self.dead = True
                    break
                    
        return hits

    def to_dict(self) -> dict:
        return {
            "uid":       self.uid,
            "team":      self.team,
            "pos":       list(self.pos),
            "direction": list(self.direction),
            "spell":     self.spell_name,
            "traveled":  round(self.distance_traveled),
            "range":     round(self.range_max),
            "width":     self.half_width * 2,
        }


class WindWall:
    UID = 0

    def __init__(self, owner_uid, team, center, direction, half_width, duration=3.75):
        WindWall.UID += 1
        self.uid        = WindWall.UID
        self.owner_uid  = owner_uid
        self.team       = team
        self.center     = center
        self.direction  = direction
        self.half_width = half_width
        self.duration   = duration
        self.dead       = False

        perp_dx = -direction[1]
        perp_dy = direction[0]

        self.p1 = (center[0] + perp_dx * half_width, center[1] + perp_dy * half_width)
        self.p2 = (center[0] - perp_dx * half_width, center[1] - perp_dy * half_width)
    def update(self, dt: float):
        self.duration -= dt
        if self.duration <= 0:
            self.dead = True

    def to_dict(self) -> dict:
        return {
            "uid":    self.uid,
            "team":   self.team,
            "center": list(self.center),
            "p1":     list(self.p1), # Gửi P1, P2 xuống Client để vẽ đường thẳng chéo
            "p2":     list(self.p2),
            "width":  self.half_width * 2,
            "ttl":    round(self.duration, 2),
        }

def _segment_crosses_wall(p_start, p_end, wall: WindWall) -> bool:
    """Kiểm tra Đạn (p_start -> p_end) CẮT NGANG Tường Gió (wall.p1 -> wall.p2)"""
    from ..physics import segments_intersect
    return segments_intersect(p_start, p_end, wall.p1, wall.p2)
