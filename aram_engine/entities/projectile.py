"""
projectile.py — Missiles, Wind Wall segments
"""
from ..physics import vec_add, vec_scale, vec_dist, line_hitbox_hit, vec_normalize


class Projectile:
    UID = 0

    def __init__(self, owner_uid, team, pos, direction, speed,
                 half_width, range_max, dmg_fn, dmg_type="physical",
                 knockup=0.0, spell_name=""):
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
            return []
        hits = []
        seg_a = vec_add(self.start_pos,
                        vec_scale(self.direction, max(0, self.distance_traveled - self.speed * 0.033)))
        seg_b = self.pos

        # Wind Wall blocks: if projectile crosses a Wind Wall segment → destroy
        for ww in wind_walls:
            if ww.team == self.team:
                continue
            if _segment_crosses_wall(seg_a, seg_b, ww):
                self.dead = True
                return []

        for tgt in targets:
            if tgt.uid in self.hit_uids:
                continue
            if not getattr(tgt, 'alive', True):
                continue
            if line_hitbox_hit(tgt.pos, seg_a, seg_b,
                               self.half_width, tgt.gameplay_radius):
                hits.append(tgt)
                self.hit_uids.add(tgt.uid)
                # Most single-target missiles die on first hit
                if self.spell_name == "Q":
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

    def __init__(self, owner_uid, team, center, half_width, duration=3.75):
        WindWall.UID += 1
        self.uid        = WindWall.UID
        self.owner_uid  = owner_uid
        self.team       = team
        self.center     = center
        self.half_width = half_width
        self.duration   = duration
        self.dead       = False

    def update(self, dt: float):
        self.duration -= dt
        if self.duration <= 0:
            self.dead = True

    def to_dict(self) -> dict:
        return {
            "uid":    self.uid,
            "team":   self.team,
            "center": list(self.center),
            "width":  self.half_width * 2,
            "ttl":    round(self.duration, 2),
        }


def _segment_crosses_wall(p1, p2, wall: WindWall) -> bool:
    """Rough check: does segment p1→p2 pass within wall's width of center?"""
    from ..physics import point_segment_dist
    dist = point_segment_dist(wall.center, p1, p2)
    return dist <= wall.half_width
