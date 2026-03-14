


Dưới đây là nội dung file `turret.md`. Tôi đã thiết kế nó như một bản đặc tả thuật toán (Algorithm Specification) kèm mã giả Python (Pseudocode) chi tiết. 

Trong file này, tôi đã hệ thống hóa lại **Cơ chế thay đổi chỉ số theo thời gian (Scaling Stats)**, **Thuật toán tìm kiếm mục tiêu (Aggro/Targeting Logic)**, và **Cơ chế hồi máu (Health Regeneration)** để AI hoặc Engine của bạn có thể áp dụng 100% chuẩn xác vào môi trường giả lập (Simulator).

--- START OF FILE turret.md ---

# ARAM Turret - Algorithms & Logic Simulation

File này chứa thuật toán mô phỏng toàn bộ logic hoạt động của Trụ (Turret) trong chế độ ARAM (Howling Abyss) dành cho Simulator. Các thông số được cập nhật chuẩn xác theo Patch 13.5+.

## 1. Định nghĩa Hằng số và Phân loại (Constants & Enums)

```python
from enum import Enum
import math

class TurretTier(Enum):
    OUTER = 1      # Trụ ngoài
    INHIBITOR = 2  # Trụ nhà lính
    NEXUS = 3      # Trụ bảo vệ nhà chính
    SHRINE = 4     # Trụ bệ đá (Tế đàn)

# Hằng số cơ bản
TURRET_ATTACK_RANGE = 750.0
TURRET_ATTACK_SPEED = 0.833  # Bắn khoảng 0.833 phát mỗi giây
SHRINE_ATTACK_RANGE = 1250.0
SHRINE_DAMAGE = 999.0        # Sát thương chuẩn (True Damage)
```

---

## 2. Thuật toán Tăng tiến Chỉ số theo Thời gian (Scaling Logic)

Trong ARAM, Sát thương (AD), Giáp (Armor) và Kháng phép (MR) của trụ không cố định mà tăng tiến theo thời gian trận đấu (`game_time_minutes`).

### 2.1. Hàm tính Sát thương (Attack Damage)
```python
def get_turret_ad(tier: TurretTier, game_time_minutes: float) -> float:
    """Tính toán AD của trụ dựa trên thời gian trận đấu (phút)."""
    
    if tier == TurretTier.SHRINE:
        return SHRINE_DAMAGE
        
    # Thời gian chặn ở các mốc tối đa
    t1 = min(game_time_minutes, 8.0)
    t2 = max(0.0, game_time_minutes - 8.0)
    
    if tier == TurretTier.OUTER:
        # Từ 0-8 phút: 185 -> 233 (+6 AD/phút)
        # Từ 8-12 phút: 233 -> 293 (+15 AD/phút)
        t2 = min(t2, 4.0) # Khóa ở phút 12 (12 - 8 = 4)
        return 185.0 + (6.0 * t1) + (15.0 * t2)
        
    elif tier == TurretTier.INHIBITOR:
        # Từ 0-8 phút: 195 -> 243 (+6 AD/phút)
        # Từ 8-15 phút: 243 -> 375 (~18.85 AD/phút)
        t2 = min(t2, 7.0) # Khóa ở phút 15 (15 - 8 = 7)
        return 195.0 + (6.0 * t1) + ((132.0 / 7.0) * t2)
        
    elif tier == TurretTier.NEXUS:
        # Từ 0-8 phút: 175 -> 223 (+6 AD/phút)
        # Từ 8-15 phút: 223 -> 375 (~21.71 AD/phút)
        t2 = min(t2, 7.0) # Khóa ở phút 15
        return 175.0 + (6.0 * t1) + ((152.0 / 7.0) * t2)
```

### 2.2. Hàm tính Khả năng Phòng ngự (Armor & MR)
```python
def get_turret_resistances(tier: TurretTier, game_time_minutes: float) -> float:
    """Trả về giá trị (Armor, MR). Giáp và Kháng phép của trụ luôn bằng nhau."""
    
    if tier == TurretTier.SHRINE:
        return (9999.0, 9999.0) # Không thể phá hủy

    if tier == TurretTier.OUTER and game_time_minutes >= 12.0:
        # Sau phút 12, Trụ ngoài bị sập đổ cấu trúc, Giáp/MR tụt thê thảm
        return (40.0, 40.0)

    # Từ 0-8 phút: 75 -> 96 (+2.625/phút). Sau phút thứ 8 thì giữ nguyên 96.
    t = min(game_time_minutes, 8.0)
    res = 75.0 + (21.0 / 8.0) * t
    return (res, res)
```

---

## 3. Thuật toán Chọn Mục tiêu (Turret Aggro Logic)

Đây là thuật toán quan trọng nhất để AI học cách "Dive trụ" hoặc "Hủy Aggro".

```python
class Turret:
    def __init__(self, team, tier, pos):
        self.team = team
        self.tier = tier
        self.pos = pos
        self.current_target = None
        self.attack_timer = 0.0

    def update_aggro(self, enemies_in_range, allied_champions):
        """
        Cập nhật mục tiêu mỗi tick (frame) của Simulator.
        enemies_in_range: Danh sách kẻ địch (Champion, Minion, Pet) đứng trong tầm 750 (tính theo hitbox edge).
        """
        # BƯỚC 1: Xóa mục tiêu nếu mục tiêu đã chết, ra khỏi tầm, hoặc không thể chọn làm mục tiêu (Untargetable/Zhonyas)
        if self.current_target:
            if (self.current_target.is_dead or 
                self.current_target.is_untargetable or 
                distance_edge_to_edge(self, self.current_target) > TURRET_ATTACK_RANGE):
                self.current_target = None

        # BƯỚC 2: Kiểm tra "Tiếng gọi trợ giúp" (Call for Help)
        # Nếu một Tướng địch (Enemy Champion) gây sát thương lên Tướng đồng minh (Allied Champion) trong tầm trụ,
        # Trụ sẽ LẬP TỨC chuyển mục tiêu (Aggro) sang Tướng địch đó.
        for enemy in enemies_in_range:
            if enemy.is_champion and enemy.just_damaged_champion(allied_champions):
                self.current_target = enemy
                return # Khóa mục tiêu này, kết thúc logic

        # BƯỚC 3: Nếu chưa có mục tiêu, tiến hành dò tìm theo thứ tự Ưu tiên (Priority List)
        if not self.current_target:
            self.current_target = self.find_new_target(enemies_in_range)

    def find_new_target(self, enemies_in_range):
        """Thuật toán quét mục tiêu theo mức độ ưu tiên chuẩn LMHT."""
        if not enemies_in_range:
            return None

        # Phân loại địch
        enemy_pets =[e for e in enemies_in_range if e.is_pet]          # Hư không bọ, Gấu Tibbers...
        enemy_cannons =[e for e in enemies_in_range if e.is_cannon]    # Xe to / Siêu cấp
        enemy_melees = [e for e in enemies_in_range if e.is_melee]      # Lính đánh gần
        enemy_casters = [e for e in enemies_in_range if e.is_caster]    # Lính đánh xa
        enemy_champs = [e for e in enemies_in_range if e.is_champion]   # Tướng địch

        # Thứ tự ưu tiên (Priority List):
        # 1. Pet / Phân bóng đang tấn công Tướng đồng minh (Bỏ qua trong 1v1 đơn giản)
        # 2. Lính Xe / Siêu cấp
        # 3. Lính Đánh gần
        # 4. Lính Đánh xa
        # 5. Tướng địch
        
        target_lists =[enemy_cannons, enemy_melees, enemy_casters, enemy_champs]
        
        for group in target_lists:
            if group:
                # Nếu có nhiều mục tiêu cùng loại, chọn mục tiêu GẦN NHẤT
                return min(group, key=lambda e: distance_edge_to_edge(self, e))
                
        return None
```

---

## 4. Thuật toán Hồi máu & Hồi sinh Trụ (Health Regen Thresholds)

Trụ Nhà lính và Nhà chính trong ARAM có cơ chế hồi máu theo "Bậc" (Tier). Trụ không thể tự hồi máu vượt quá Bậc mà nó vừa bị đánh tụt xuống.

```python
def update_turret_health_regen(turret, delta_time_sec):
    """Gọi hàm này mỗi frame để xử lý hồi máu của trụ."""
    
    # Trụ ngoài không hồi máu
    if turret.tier == TurretTier.OUTER:
        return
        
    # Xác định tốc độ hồi máu
    regen_rate = 3.0 if turret.tier == TurretTier.INHIBITOR else 6.0
    heal_amount = regen_rate * delta_time_sec
    
    health_pct = turret.current_hp / turret.max_hp
    
    # Xác định giới hạn hồi (Threshold Cap)
    max_heal_pct = 1.0
    
    if turret.tier == TurretTier.INHIBITOR:
        if health_pct <= 0.333:
            max_heal_pct = 0.333
        elif health_pct <= 0.667:
            max_heal_pct = 0.667
    
    elif turret.tier == TurretTier.NEXUS:
        if health_pct <= 0.40:
            max_heal_pct = 0.40
        elif health_pct <= 0.70:
            max_heal_pct = 0.70
            
    # Áp dụng hồi máu
    target_hp_cap = turret.max_hp * max_heal_pct
    if turret.current_hp < target_hp_cap:
        turret.current_hp = min(turret.current_hp + heal_amount, target_hp_cap)
```

## 5. Cơ Chế Giảm Sát Thương (Damage Mitigation)

Khi một Tướng (như Yasuo) tấn công trụ, lượng sát thương sẽ bị can thiệp bởi Giáp của trụ và Cơ chế **Mảnh vỡ / Pháo đài**.

```python
def calculate_damage_to_turret(attacker, turret, raw_physical_damage, game_time_minutes):
    """Hàm tính sát thương cuối cùng trụ phải nhận."""
    
    # 1. Lấy Giáp của trụ theo thời gian
    armor, _ = get_turret_resistances(turret.tier, game_time_minutes)
    
    # Trụ miễn nhiễm với Xuyên Giáp theo % của tướng, chỉ chịu Xuyên Giáp Thẳng (Lethality)
    # (Lưu ý: Tùy phiên bản LMHT, Xuyên giáp % có thể không tác dụng lên công trình)
    effective_armor = max(0, armor - attacker.lethality)
    
    # 2. Tính hệ số giảm sát thương từ Giáp
    damage_multiplier = 100.0 / (100.0 + effective_armor)
    actual_damage = raw_physical_damage * damage_multiplier
    
    # 3. Pháo Đài (Fortification) - Chỉ dùng nếu có rules cụ thể trong ARAM
    # "Khi Trụ Ngoài bị phá hủy, Trụ Nhà Lính nhận được 30% Giảm sát thương nhận vào trong 60s"
    if turret.tier == TurretTier.INHIBITOR and turret.has_fortification_buff:
        actual_damage *= 0.70 # Giảm 30%
        
    return actual_damage
```

--- END OF FILE turret.md ---