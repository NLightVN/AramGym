# AramGym — Game Stats & Data

File này lưu trữ các thông số chi tiết về map, champion, minion, items, v.v. được sử dụng trong simulator **1v1 ARAM**. Đã được cập nhật và đồng bộ hoàn toàn với `yasuo.md`, `minion.md`, `turret.md` (Patch V26.01).

---

## 1. ARAM Map Buildings (Map 12 — Howling Abyss)

> **Nguồn**: Extract từ `LeagueSandbox-Default-indev/Maps/Map12/Scene/*.sco.json`
> **Hệ tọa độ**: Dùng `CentralPoint.X` và `CentralPoint.Z` làm tọa độ 2D (X, Z).
> Order base (nhà xanh) ≈ góc `(0, 0)`, Chaos base (nhà đỏ) ≈ góc `(12800, 12800)`.

### Hệ frame tọa độ ARAM

```text
Order Spawn:  (~937,  ~1061)
Chaos Spawn:  (~11860, ~11596)

Đơn vị: game units (1:1 với hệ tọa độ chung)
Chú ý: Trục Z ở đây tương ứng trục Y trong code 2D (top = Z lớn)
```

### Python constants (Tọa độ Công trình)

```python
# ── ARAM (Map 12 — Howling Abyss) Building Coordinates ──────────────────
ARAM_SPAWN_POINTS = {
    "order": (937.0, 1060.6),
    "chaos": (11860.1, 11596.2),
}

ARAM_BARRACKS = {
    "order": (3064.1, 3212.7),
    "chaos": (10786.9, 11110.9),
}

ARAM_TURRETS = {
    # ── Order (Team 1 — xanh) ──
    "order_shrine":  (648.1,   764.2),
    "order_inhib":   (5448.4,  6169.1),
    "order_front_1": (3809.1,  3829.1),
    "order_front_2": (4943.5,  4929.8),
    "order_base_1":  (2493.2,  2101.2),
    "order_base_2":  (2036.7,  2552.7),

    # ── Chaos (Team 2 — đỏ) ──
    "chaos_shrine":  (12168.7, 11913.3),
    "chaos_inhib":   (8548.8,  8289.5),
    "chaos_front_1": (7879.1,  7774.8),
    "chaos_front_2": (9017.6,  8871.4),
    "chaos_base_1":  (10785.2, 10117.6),
    "chaos_base_2":  (10325.2, 10608.2),
}

# Minion Waypoints ARAM (1 lane duy nhất)
ARAM_MINION_WAYPOINTS = {
    "order": [
        (3064.1, 3212.7),    # Spawn
        (5448.4, 6169.1),    # order_inhib
        (8548.8, 8289.5),    # chaos_inhib
        (10786.9, 11110.9),  # Target
    ],
    "chaos": [
        (10786.9, 11110.9),  # Spawn
        (8548.8,  8289.5),   # chaos_inhib
        (5448.4,  6169.1),   # order_inhib
        (3064.1,  3212.7),   # Target
    ],
}
```

---

## 2. Unit Stats (Hitbox, Growth & Abilities)

**Quy tắc tăng trưởng chỉ số (Growth Multiplier):**
Mọi chỉ số tăng theo cấp độ (Level) từ 1 đến 18 áp dụng công thức phi tuyến tính:
`Stat_Level_N = Base_Stat + Growth_Stat * Multiplier`
Với **`Multiplier = (N - 1) * (0.7025 + 0.0175 * (N - 1))`**

---

### 2.1. Champion: Yasuo

**a. Thông số Hitbox & Không gian:**
- **GameplayCollisionRadius**: `65.0`
- **SelectionRadius**: `120.0`
- **PathfindingCollisionRadius**: `32.0`
- **AttackRange**: `175.0`
- **AcquisitionRange**: `400.0`

**b. Chỉ số Cơ bản & Tăng trưởng:**

| Chỉ số (Stat) | Cơ bản (cấp 1) | Tăng trưởng (Growth) |
| :--- | :--- | :--- |
| **HP (Máu)** | 590.0 | +110.0 |
| **HP Regen (Hồi máu/5s)** | 6.5 | +0.9 |
| **Resource (Flow - Nhịp)** | 100.0 | 0 |
| **AD (ST Vật lý)** | 60.0 | +2.5 |
| **Armor (Giáp)** | 32.0 | +4.6 |
| **Spell Block (Kháng phép)** | 32.0 | +2.05 |
| **Attack Speed Base** | 0.697 *(Ratio: 0.67)* | +3.5% |
| **Attack Windup (Vận đòn)** | 22% | 0 |
| **Move Speed (Tốc chạy)** | 345.0 | 0 |

*(Ghi chú: Yasuo bắt đầu trận đấu ở Cấp 1 với **+4% Bonus Attack Speed** mặc định.)*

---

### 2.2. Kỹ năng Champion (Yasuo Abilities)

**Nội tại — Đạo Của Lãng Khách (Way of the Wanderer)**
- **Intent (Chí mạng):**
  - `Total_Crit_Chance = Bonus_Crit_Chance * 2`
  - `Bonus_AD_from_Excess_Crit = (Total_Crit_Chance - 100%) * 0.5` (chỉ khi Total > 100%)
  - `Crit_Damage_Multiplier = 180%` (mặc định, thay vì 200% của tướng thường)
  - Nếu có **Infinity Edge**: `Crit_Damage_Multiplier = 207%`
- **Resolve (Khiên):**
  - Tích 1 Flow mỗi `59 / 52.5 / 46` units di chuyển (giảm ở cấp 1, 7, 13).
  - Khi đủ 100 Flow, chịu sát thương từ Tướng/Quái tạo khiên tồn tại `1.0 giây`.
- **Giá trị Khiên theo Cấp (1→18):**
  `[125, 145.12, 166.21, 188.29, 211.34, 235.37, 260.38, 286.36, 313.32, 341.26, 370.18, 400.08, 430.96, 462.81, 495.64, 529.45, 564.24, 600]`

**Q — Bão Kiếm (Steel Tempest)**
- **Cast Range:** `450` (Đâm) / `1150` (Lốc)
- **Width:** `80` (Đâm) / `180` (Lốc). Hitbox Combo E+Q: bán kính `215`
- **Missile Speed (Lốc):** `1200`
- **Sát thương:** `[20, 45, 70, 95, 120] + 1.05 * Total_AD` (Vật lý)
- **Thời gian hất tung (Lốc):** `0.9s`. Stack tồn tại `6s`.
- **Cast Time:** `0.35s - (0.035 * (Bonus_AS / 24%))`. Minimum `0.175s` tại 120% Bonus AS.
- **Cooldown:** `4.0s * (1 - (0.01 * (Bonus_AS / 1.67%)))`. Minimum `1.33s` tại 111.11% Bonus AS.

**W — Tường Gió (Wind Wall)**
- **Cooldown (SR):** `[25, 23, 21, 19, 17]` giây
- **Cooldown (ARAM — nerf):** `[27, 25, 23, 21, 19]` giây
- **Cast Range:** Trượt tới trước `350/450`, trong `0.6s` đầu, trôi thêm `50` units.
- **Wall Width:** `[320, 390, 460, 530, 600]`
- **Thời gian tồn tại:** `4.0s`. Cast time: `0.013s`.

**E — Quét Kiếm (Sweeping Blade)**
- **Cooldown giữa các lần lướt:** `[0.5, 0.4, 0.3, 0.2, 0.1]` giây
- **Target Immunity:** `[10, 9, 8, 7, 6]` giây
- **Cast Range:** `475.0` (Tối đa `625` nếu qua tường)
- **Speed:** `750 + (0.6 * Yasuo_MS)`
- **Sát thương:** `[70, 85, 100, 115, 130] + 0.2 * Bonus_AD + 0.6 * Total_AP` (Phép)
- **Stack Damage:**
  - Tối đa **4 stacks**. Mỗi stack lưu `5` giây.
  - % sát thương tăng thêm mỗi stack theo cấp (1→18):
    `[15%, 15.59%, 16.18%, 16.76%, 17.35%, 17.94%, 18.53%, 19.12%, 19.71%, 20.29%, 20.88%, 21.47%, 22.06%, 22.65%, 23.24%, 23.82%, 24.41%, 25%]`
  - Max buff tại 4 stack: **gấp đôi Base Damage**
- **Python implement (E damage):**
  ```python
  STACK_BONUS_BY_LEVEL = [
      0.15, 0.1559, 0.1618, 0.1676, 0.1735, 0.1794,
      0.1853, 0.1912, 0.1971, 0.2029, 0.2088, 0.2147,
      0.2206, 0.2265, 0.2324, 0.2382, 0.2441, 0.25
  ]
  E_MAX_STACKS = 4

  def e_damage(yasuo, stacks: int, e_rank: int) -> float:
      base_dmg = [0, 70, 85, 100, 115, 130][e_rank]
      bonus_pct = STACK_BONUS_BY_LEVEL[yasuo.level - 1]
      multiplier = 1.0 + bonus_pct * min(stacks, E_MAX_STACKS)
      return base_dmg * multiplier + (0.2 * yasuo.bonus_ad) + (0.6 * yasuo.ap)
  ```
- **Ghosted (Xuyên vật thể):** `2.0` giây sau lướt.
- **Queue E+Q:** Nếu bấm Q trong `0.5s` lúc đang lướt → tạo bão vòng tròn. Khóa đánh thường `0.5s` sau khi đáp.

**R — Trăn Trối (Last Breath)**
- **Điều kiện:** Kẻ địch phải đang bị Hất tung (Airborne).
- **Cast Range:** `1400.0`
- **AOE Radius:** `400.0`
- **Cooldown:** `[70, 50, 30]` giây
- **Sát thương:** `[200, 350, 500] + 1.5 * Bonus_AD` (Vật lý)
- **Hiệu ứng:** Giữ mục tiêu trên không thêm `1.0s`. Xoay góc nhìn địch mỗi `0.25s`.
- **Buff:** Bỏ qua 60% Bonus Armor của địch cho đòn chí mạng, kéo dài `15s`.
- **Reset:** Phục hồi ngay 100 Flow. Xóa toàn bộ stack Q.
- **Lockout State:**
  - Không thể dùng: Di chuyển, Đánh thường, Skill, Items, Flash, Teleport.
  - Có thể dùng: Barrier, Cleanse, Exhaust, Ghost, Heal, Ignite.
- **Python Logic (Spawn Pos):**
  ```python
  def yasuo_r_spawn_pos(yasuo_pos, target_pos, turrets) -> Vec2:
      direction = normalize(target_pos - yasuo_pos)
      candidate = target_pos + direction * 100
      for turret in turrets:
          if turret.team != yasuo.team and distance(candidate, turret.pos) < 750:
              alt = target_pos - direction * 100
              if distance(alt, turret.pos) >= 750:
                  return alt
      return candidate
  ```

---

### 2.3. Bổ Trợ — Flash (Tốc Biến)

| Thông số | Giá trị |
| :--- | :--- |
| **Loại** | Blink (dịch chuyển tức thời) |
| **Khoảng cách dịch chuyển** | 425 units |
| **Cooldown** | 300 giây (5 phút) |
| **Bị chặn bởi** | Root, Grounded, Suppression, Airborne |

---

## 3. Lính (Minions)

> Nguồn nhất quán: `minion.md` (Patch V26.01)

### 3.1 Spawn Mechanics

- **Đợt lính đầu tiên:** `0:30` giây.
- **Khoảng cách giữa các lính trong đợt:** `0.792` giây.
- **0:30 → 14:00:** Mỗi đợt cách nhau `30` giây.
- **14:00 → 30:00:** Mỗi đợt cách nhau `25` giây.
- **30:00 trở đi:** Mỗi đợt cách nhau `20` giây.

**Thành phần đợt lính tiêu chuẩn:** 3 Cận chiến + 3 Đánh xa.

**Lính Xe (Siege):**
- Đợt xe đầu tiên: đợt thứ 3 (`01:30`).
- Dưới 14 phút: `1` xe mỗi `3` đợt.
- 14–25 phút: `1` xe mỗi `2` đợt. Khi có xe: số lính cận chiến giảm còn 2.
- Từ 25 phút: `1` xe ở mọi đợt.

**Lính Siêu Cấp (Super):** Xuất hiện khi Nhà lính địch bị phá, thay thế hoàn toàn lính xe trong đợt đó. Nếu cả 3 nhà lính bị phá: `2` lính siêu cấp/đợt.

**Giảm lính xa từ 30:00:** Chỉ còn `2` Caster mỗi đợt (giảm 1).

---

### 3.2 Chỉ số Lính (Base Stats — đầu trận)

| Loại lính | Base HP | Base AD | Attack Speed | Tầm đánh | Gold | XP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Melee (Cận chiến)** | 477 | 12 | 1.25 | 110 | 20g | 60 XP |
| **Caster (Đánh xa)** | 296 | 24 | 0.667 | 550 | 14g | 29 XP |
| **Cannon (Xe to)** | 900 | 40 | 1.00 | 300 | 50g (bắt đầu) | 90 XP |
| **Super (Siêu cấp)** | 1600 | 230 | 0.85 | 170 | 40g | 95 XP |

**Hitbox lính:**
- Melee & Caster: Gameplay Radius `48.0`, Pathfinding Radius `35.7`
- Cannon: Gameplay Radius `65.0`, Pathfinding Radius `55.7`

**On-hit Bonus:**
- Cận chiến: +`2%` máu hiện tại của mục tiêu khi đánh lính địch.
- Xe to: +`6%` máu hiện tại của mục tiêu khi đánh lính địch.

**Super Minion — Buff Commander:** Cung cấp cho lính đồng minh xung quanh `+70 Armor`, `+70 MR` và `+70% Sát thương`.

**Giảm sát thương từ Trụ:** Lính xe và lính siêu cấp chỉ chịu `70%` sát thương từ Trụ.

---

### 3.3 Tốc độ Di chuyển Lính

- **Base MS:** `350`
- **Tăng theo thời gian:** +`25` mỗi 5 phút bắt đầu từ phút 11 (mốc: 11 / 16 / 21 / 26). Tối đa `450`.

---

### 3.4 Hệ số Sát thương Lính

- Vs Tướng (Champions): chỉ gây `55%` sát thương.
- Vs Công trình (Structures): chỉ gây `60%` sát thương.

---

### 3.5 Thuật toán AI Lính (Aggro Logic)

**Bảng Ưu tiên (Priority Queue) — quét bán kính `500`):**
1. Tướng địch đang tấn công Tướng đồng minh ("Call for Help").
2. Lính địch đang tấn công Tướng đồng minh.
3. Lính địch đang tấn công Lính đồng minh.
4. Trụ địch đang tấn công Lính đồng minh.
5. Tướng địch đang tấn công Lính đồng minh.
6. Lính địch gần nhất.
7. Tướng địch gần nhất.

*(Patch 13.10: Nếu lính đang đánh Trụ, bỏ qua Ưu tiên số 1.)*

Nếu không rơi vào priority nào → di chuyển theo Waypoint đến Trụ/Nhà lính tiếp theo và đánh.

---

### 3.6 Kinh nghiệm (XP Share — V26.01)

| Số Tướng trong bán kính 1500 | XP mỗi Tướng | Tổng XP trích xuất |
| :--- | :--- | :--- |
| 1 | 100% | 100% |
| 2 | 65% | 130% |
| 3 | ~43.3% | ~130% |
| 4 | 32.5% | 130% |
| 5 | 26% | 130% |

---

### 3.7 Death Grace (Bất tử Tạm thời)

Khi lính dưới `<0.35%` Max HP và bị chí mạng từ một lính khác (không phải Tướng):
- HP được giữ lại ở `1 HP` trong delay `0.066s`.
- Trong delay này: Tướng đánh vào sẽ được tính Last-hit.
- Không hoạt động nếu sát thương kết liễu > `190`.

---

## 4. Công Trình (Buildings)

> Nguồn nhất quán: `turret.md` (Patch 13.5+)

### 4.1 Trụ (Turrets)

**Hằng số:**
```python
TURRET_ATTACK_RANGE  = 750.0
TURRET_ATTACK_SPEED  = 0.833   # phát/giây
SHRINE_ATTACK_RANGE  = 1250.0
SHRINE_DAMAGE        = 999.0   # True Damage
```

**Sát thương Trụ theo Thời gian (AD scaling):**

| Loại trụ | 0 phút | 8 phút | Tối đa (phút) | AD tối đa |
| :--- | :--- | :--- | :--- | :--- |
| Outer | 185 | 233 | 12 phút | 293 |
| Inhibitor | 195 | 243 | 15 phút | ~375 |
| Nexus | 175 | 223 | 15 phút | ~375 |
| Shrine | 999 (True) | — | — | — |

```python
def get_turret_ad(tier: TurretTier, game_time_minutes: float) -> float:
    if tier == TurretTier.SHRINE:
        return 999.0
    t1 = min(game_time_minutes, 8.0)
    t2 = max(0.0, game_time_minutes - 8.0)
    if tier == TurretTier.OUTER:
        t2 = min(t2, 4.0)
        return 185.0 + (6.0 * t1) + (15.0 * t2)
    elif tier == TurretTier.INHIBITOR:
        t2 = min(t2, 7.0)
        return 195.0 + (6.0 * t1) + ((132.0 / 7.0) * t2)
    elif tier == TurretTier.NEXUS:
        t2 = min(t2, 7.0)
        return 175.0 + (6.0 * t1) + ((152.0 / 7.0) * t2)
```

**Giáp & Kháng phép Trụ (đối xứng, luôn bằng nhau):**

| Điều kiện | Giáp = Kháng phép |
| :--- | :--- |
| Shrine | 9999 (miễn phá hủy) |
| Outer sau phút 12 | 40 |
| Mọi loại, 0–8 phút | 75 → 96 (tăng tuyến tính) |
| Mọi loại, sau 8 phút | 96 (cố định) |

```python
def get_turret_resistances(tier, game_time_minutes):
    if tier == TurretTier.SHRINE:
        return (9999.0, 9999.0)
    if tier == TurretTier.OUTER and game_time_minutes >= 12.0:
        return (40.0, 40.0)
    t = min(game_time_minutes, 8.0)
    res = 75.0 + (21.0 / 8.0) * t
    return (res, res)
```

**Lưu ý quan trọng:** Trụ **miễn nhiễm với Xuyên Giáp %**. Chỉ bị ảnh hưởng bởi **Lethality (Xuyên Giáp Thẳng)**.

---

### 4.2 Nhà Lính (Inhibitor) & Nhà Chính (Nexus)

| Công trình | HP | Hồi máu | Hồi sinh |
| :--- | :--- | :--- | :--- |
| **Nhà lính (Inhibitor)** | 4000 | 3 HP/s (theo bậc) | 5 phút sau khi bị phá |
| **Nhà chính (Nexus)** | 5500 | 6 HP/s (theo bậc) | Không hồi sinh |

**Cơ chế Hồi máu theo Bậc (Threshold):** Trụ không hồi vượt quá ngưỡng HP hiện tại.

```python
def update_turret_health_regen(turret, delta_time_sec):
    if turret.tier == TurretTier.OUTER:
        return  # Trụ ngoài không hồi máu
    regen_rate = 3.0 if turret.tier == TurretTier.INHIBITOR else 6.0
    heal_amount = regen_rate * delta_time_sec
    health_pct = turret.current_hp / turret.max_hp
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
    target_hp_cap = turret.max_hp * max_heal_pct
    if turret.current_hp < target_hp_cap:
        turret.current_hp = min(turret.current_hp + heal_amount, target_hp_cap)
```

---

### 4.3 Thuật toán Aggro Trụ

**Bước 1 — Call for Help:** Nếu Tướng địch vừa gây sát thương lên Tướng đồng minh trong tầm → chuyển Aggro ngay lập tức sang Tướng địch đó.

**Bước 2 — Tìm mục tiêu mới (nếu chưa có):**
Thứ tự ưu tiên (chọn mục tiêu gần nhất trong cùng nhóm):
1. Lính Xe / Siêu cấp
2. Lính Cận chiến
3. Lính Đánh xa
4. Tướng địch

**Mục tiêu bị xóa khi:** chết, ra ngoài tầm `750`, hoặc Untargetable (Zhonyas, v.v.).

---

### 4.4 Tính Sát thương Tướng lên Trụ

```python
def calculate_damage_to_turret(attacker, turret, raw_physical_damage, game_time_minutes):
    armor, _ = get_turret_resistances(turret.tier, game_time_minutes)
    effective_armor = max(0, armor - attacker.lethality)  # Chỉ Lethality có tác dụng, không phải % Armor Pen
    damage_multiplier = 100.0 / (100.0 + effective_armor)
    actual_damage = raw_physical_damage * damage_multiplier
    if turret.tier == TurretTier.INHIBITOR and turret.has_fortification_buff:
        actual_damage *= 0.70  # Pháo Đài: giảm 30% khi Trụ ngoài vừa bị phá
    return actual_damage
```

---

## 5. Items (Trang bị mô phỏng cho Simulator)

| # | Tên | Giá | Stats chính | Nội tại |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Doran's Blade** | 450g | +100 HP, +10 AD | +3% Lifesteal |
| 2 | **Health Potion** | 50g | — | Hồi 120 HP trong 15s |
| 3 | **Long Sword** | 350g | +10 AD | — |
| 4 | **Berserker's Greaves** | 1100g | +45 MS, +30% AS | — |
| 5 | **Cloak of Agility** | 600g | +15% Crit | — |
| 6 | **Zeal** | 1100g | +15% AS, +15% Crit, +5% MS | — |
| 7 | **Infinity Edge** | 3500g | +75 AD, +25% Crit | +30% Crit Damage. Yasuo đạt `207%` crit multiplier |
| 8 | **Immortal Shieldbow** | 3000g | +50 AD, +20% Crit, +12% Lifesteal | Lifeline: tạo khiên 320–530 khi HP < 30% |
| 9 | **Phantom Dancer** | 2800g | +60% AS, +20% Crit, +10% MS | Đi xuyên vật thể |
| 10 | **Death's Dance** | 3200g | +60 AD, +40 Armor, +15 Haste | Chuyển 30% sát thương vật lý thành chảy máu theo thời gian |
| 11 | **Mortal Reminder** | 3000g | +40 AD, +25% Crit, +30% Armor Pen | Gây 40% Grievous Wounds khi sát thương vật lý |
