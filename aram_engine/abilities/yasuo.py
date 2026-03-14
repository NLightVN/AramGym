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
    Hoạt động như một đòn đánh thường định hướng: có Cast Time khóa di chuyển.
    """
    lvl_i = _level_idx(yasuo.q_level)
    
    # Tính Bonus AS % (Dựa theo AS Ratio của Yasuo là 0.670)
    bonus_as_pct = (yasuo.attack_speed - yasuo.base_as) / 0.670
    
    # 1. Tính Cooldown (Scale nghịch với Tốc đánh)
    cd = 4.0 * (1.0 - min(0.67, 0.01 * (bonus_as_pct / 0.0167)))
    cd = max(1.33, cd)
    
    # 2. Tính Cast Time (Thời gian vung kiếm khóa di chuyển)
    cast_time = 0.35 - (0.035 * (bonus_as_pct / 0.24))
    cast_time = max(0.175, cast_time)

    if yasuo.q_cd > 0 or yasuo.is_silenced or not yasuo.alive:
        return False

    direction = vec_normalize(vec_sub(cursor_world, yasuo.pos))

    # Mô phỏng Cast Time của Đòn đánh: Dừng di chuyển ngay lập tức và khóa đòn đánh
    yasuo.attack_timer = cast_time

    if yasuo.q_stacks >= 2:
        # ── Q3 Tornado ──────────────────────────
        _fire_tornado(yasuo, direction, gs)
        yasuo.q_stacks = 0
        yasuo.q_stack_timer = 0.0
    else:
        # ── Normal Q stab ────────────────────────
        _fire_q_missile(yasuo, direction, gs)
        # LƯU Ý: Không cộng Stack ở đây nữa. Stack chỉ được cộng khi ĐÂM TRÚNG (bên trong dmg_fn)

    yasuo.q_cd = cd
    yasuo.q_buffer_timer = 0.5
    return True


def _fire_q_missile(yasuo, direction, gs):
    """
    Xử lý Q Thường bằng Toán học Hình học (Instant Capsule Hitbox).
    Hoàn toàn KHÔNG dùng đạn thật để tránh lỗi Xuyên Tường Gió và Lỗi Render.
    """
    from ..physics import line_hitbox_hit
    from ..damage import apply_physical
    
    lvl_i = _level_idx(yasuo.q_level)
    base_dmg = YASUO_Q["base_dmg"][lvl_i]
    ad_bonus = yasuo.ad * YASUO_Q["ad_ratio"]
    
    # 1. Vẽ Hitbox: Tính điểm đầu (seg_a) và điểm cuối (seg_b) của nét chém 450 units
    seg_a = yasuo.pos
    seg_b = vec_add(yasuo.pos, vec_scale(direction, YASUO_Q["cast_range"]))
    half_width = YASUO_Q["width"] / 2
    
    hit_tracker = [False]
    
    # 2. Duyệt qua TẤT CẢ kẻ địch và check chạm hitbox MỘT LẦN DUY NHẤT (Instant)
    for target in gs.get_enemies(yasuo.team):
        if not getattr(target, 'alive', True):
            continue
            
        # Hàm line_hitbox_hit (đã có trong physics.py) tính toán khoảng cách từ tâm hình tròn 
        # của đối phương đến đường thẳng nhát chém. Nếu < bán kính -> Trúng đích!
        if line_hitbox_hit(target.pos, seg_a, seg_b, half_width, target.gameplay_radius):
            
            # Gây sát thương trực tiếp ngay lập tức
            apply_physical(yasuo, target, base_dmg + ad_bonus)
            
            # Kiểm tra Kết liễu & Vàng ngay tại chỗ
            if target.hp <= 0:
                if hasattr(target, 'on_death'):
                    target.on_death(gs.game_time)
                # Import hàm kill_feed cục bộ để tránh lỗi vòng lặp import (Circular Import)
                from ..game import _handle_kill
                _handle_kill(gs, yasuo.uid, target)
            
            # Cộng đúng 1 Stack Gió nếu chém trúng (dù có chém trúng 10 mục tiêu)
            if not hit_tracker[0]:
                hit_tracker[0] = True
                yasuo.q_stacks = min(2, yasuo.q_stacks + 1)
                yasuo.q_stack_timer = YASUO_Q["stack_timer"][lvl_i]
                
    # 3. XỬ LÝ RENDER (HIỂN THỊ HÌNH ẢNH TRÊN BẢN ĐỒ)
    # Ta tạo một "VFX ảo" không có sát thương, đứng im tại chỗ và sống đúng 0.15 giây 
    # Điều này đảm bảo Client HTML nhận được thông điệp và vẽ nét chém lên màn hình.
    def dummy_dmg(t): pass
    
    visual_vfx = Projectile(
        owner_uid=yasuo.uid, team=yasuo.team, pos=seg_b, direction=direction,
        speed=0.0, half_width=half_width, range_max=YASUO_Q["cast_range"],
        dmg_fn=dummy_dmg, spell_name="Q",
        piercing=True, blockable=False   # <--- Đảm bảo nó xuyên qua lính và Tường gió mà không bị biến mất!
    )
    # Gán distance_traveled = 450 để Client hiểu và vẽ một nét chém dài đủ 450 units
    visual_vfx.distance_traveled = YASUO_Q["cast_range"]
    
    # Ghi đè hàm update để "ảo ảnh" tự biến mất sau 0.15s (Render kịp khoảng 4-5 frame)
    visual_vfx.life_timer = 0.15
    def vfx_update(dt):
        visual_vfx.life_timer -= dt
        if visual_vfx.life_timer <= 0:
            visual_vfx.dead = True
            
    visual_vfx.update = vfx_update
    gs.projectiles.append(visual_vfx)


def _fire_tornado(yasuo, direction, gs):
    base_dmg = YASUO_Q["base_dmg"][_level_idx(yasuo.q_level)]
    ad_bonus = yasuo.ad * YASUO_Q["ad_ratio"]

    def dmg_fn(target):
        apply_physical(yasuo, target, base_dmg + ad_bonus)
        if hasattr(target, 'apply_cc'):
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
        direction=direction, # <--- ĐÃ TRUYỀN HƯỚNG VÀO ĐÂY
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
    STACK_BONUS_BY_LEVEL =[
        0.15, 0.1559, 0.1618, 0.1676, 0.1735, 0.1794,
        0.1853, 0.1912, 0.1971, 0.2029, 0.2088, 0.2147,
        0.2206, 0.2265, 0.2324, 0.2382, 0.2441, 0.25
    ]
    
    # Damage = Base * (1 + Stack_Bonus * Stacks) + 0.2 BonusAD + 0.6 AP
    base_dmg = YASUO_E["base_dmg"][lvl_i]
    lvl_idx_for_stack = max(0, min(yasuo.level - 1, 17))
    bonus_pct = STACK_BONUS_BY_LEVEL[lvl_idx_for_stack]
    
    stack_mult = 1.0 + bonus_pct * min(yasuo.e_stacks, YASUO_E["max_stacks"])
    dmg = base_dmg * stack_mult + 0.2 * yasuo.bonus_ad + 0.6 * yasuo.ap
    # Check if Q is ready/mid-cast → EQ Combo (AoE spin)
    eq_combo = yasuo.q_buffer_timer > 0  # nếu player đã nhấn Q trong 0.5s trước khi E

    if eq_combo:
        # AoE spin quanh vị trí mới
        from ..physics import line_hitbox_hit
        aoe_radius = YASUO_EQ_COMBO["aoe_radius"]
        base_dmg = YASUO_Q["base_dmg"][lvl_i]
        ad_bonus = yasuo.ad * YASUO_Q["ad_ratio"]
        for t in gs.get_enemies(yasuo.team):
            if not getattr(t, 'alive', True): continue
            if vec_dist(yasuo.pos, t.pos) <= aoe_radius:
                apply_physical(yasuo, t, base_dmg + ad_bonus)
                if not hit_tracker[0]:
                    hit_tracker[0] = True
                    yasuo.q_stacks = min(2, yasuo.q_stacks + 1)
        yasuo.q_cd = 0  # reset Q CD sau EQ
        yasuo.q_buffer_timer = 0   

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
        if not getattr(unit, 'is_airborne', False):
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
