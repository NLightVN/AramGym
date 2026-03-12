# AramGym — Game Stats & Data

File này lưu trữ các thông số chi tiết về map, champion, minion, items, v.v. được sử dụng trong simulator **1v1 ARAM**.

## 1. ARAM Map Buildings (Map 12 — Howling Abyss)

> **Nguồn**: Extract từ `LeagueSandbox-Default-indev/Maps/Map12/Scene/*.sco.json`
> **Hệ tọa độ**: Dùng `CentralPoint.X` và `CentralPoint.Z` làm tọa độ 2D (X, Z).
> Order base (nhà xanh) ≈ góc `(0, 0)`, Chaos base (nhà đỏ) ≈ góc `(12800, 12800)`.

### Hệ frame tọa độ ARAM

```
Order Spawn:  (~937,  ~1061)
Chaos Spawn:  (~11860, ~11596)

Đơn vị: game units (1:1 với hệ tọa độ chung)
Chú ý: Trục Z ở đây tương ứng trục Y trong code 2D (top = Z lớn)
```

### Trụ Order (Team 1 — xanh)

| File | ID | Mô tả | X | Z |
|------|----|-------|---|---|
| `Turret_OrderTurretShrine` | order_shrine | Trụ tế đàn (Nexus turret) | 648.1 | 764.2 |
| `Turret_T1_C_05` | order_inhib | Trụ Inhibitor | 5448.4 | 6169.1 |
| `Turret_T1_C_07` | order_front_1 | Trụ lane 1 (gần Chaos) | 3809.1 | 3829.1 |
| `Turret_T1_C_08` | order_front_2 | Trụ lane 2 | 4943.5 | 4929.8 |
| `Turret_T1_C_09` | order_base_1 | Trụ base 1 (gần Order) | 2493.2 | 2101.2 |
| `Turret_T1_C_010` | order_base_2 | Trụ base 2 (gần Order) | 2036.7 | 2552.7 |

### Trụ Chaos (Team 2 — đỏ)

| File | ID | Mô tả | X | Z |
|------|----|-------|---|---|
| `Turret_ChaosTurretShrine` | chaos_shrine | Trụ tế đàn (Nexus turret) | 12168.7 | 11913.3 |
| `Turret_T2_C_05` | chaos_inhib | Trụ Inhibitor | 8548.8 | 8289.5 |
| `Turret_T2_L_01` | chaos_front_1 | Trụ lane 1 (gần Order) | 7879.1 | 7774.8 |
| `Turret_T2_L_02` | chaos_front_2 | Trụ lane 2 | 9017.6 | 8871.4 |
| `Turret_T2_L_03` | chaos_base_1 | Trụ base 1 (gần Chaos) | 10785.2 | 10117.6 |
| `Turret_T2_L_04` | chaos_base_2 | Trụ base 2 (gần Chaos) | 10325.2 | 10608.2 |

### Nhà Lính / Barracks

| File | Team | X | Z |
|------|------|---|---|
| `__P_Order_Spawn_Barracks__C01` | Order (xanh) | 3064.1 | 3212.7 |
| `__P_Chaos_Spawn_Barracks__C01` | Chaos (đỏ) | 10786.9 | 11110.9 |

### Spawn Points Champion

| File | Team | X | Z |
|------|------|---|---|
| `__Spawn_T1` | Order (xanh) | 937.0 | 1060.6 |
| `__Spawn_T2` | Chaos (đỏ) | 11860.1 | 11596.2 |

### Python constants

```python
# ── ARAM (Map 12 — Howling Abyss) Building Coordinates ──────────────────
# Tọa độ 2D: (x, z) từ CentralPoint trong SCO files
# Nguồn: LeagueSandbox-Default-indev/Maps/Map12/Scene/*.sco.json

ARAM_SPAWN_POINTS = {
    "order": (937.0, 1060.6),      # __Spawn_T1
    "chaos": (11860.1, 11596.2),   # __Spawn_T2
}

ARAM_BARRACKS = {
    "order": (3064.1, 3212.7),     # __P_Order_Spawn_Barracks__C01
    "chaos": (10786.9, 11110.9),   # __P_Chaos_Spawn_Barracks__C01
}

ARAM_TURRETS = {
    # ── Order (Team 1 — xanh) ──
    "order_shrine":  (648.1,   764.2),   # Turret_OrderTurretShrine (trụ tế đàn)
    "order_inhib":   (5448.4,  6169.1),  # Turret_T1_C_05 (trụ Inhibitor)
    "order_front_1": (3809.1,  3829.1),  # Turret_T1_C_07 (trụ lane gần Chaos)
    "order_front_2": (4943.5,  4929.8),  # Turret_T1_C_08
    "order_base_1":  (2493.2,  2101.2),  # Turret_T1_C_09 (trụ base gần Order)
    "order_base_2":  (2036.7,  2552.7),  # Turret_T1_C_010

    # ── Chaos (Team 2 — đỏ) ──
    "chaos_shrine":  (12168.7, 11913.3), # Turret_ChaosTurretShrine (trụ tế đàn)
    "chaos_inhib":   (8548.8,  8289.5),  # Turret_T2_C_05 (trụ Inhibitor)
    "chaos_front_1": (7879.1,  7774.8),  # Turret_T2_L_01 (trụ lane gần Order)
    "chaos_front_2": (9017.6,  8871.4),  # Turret_T2_L_02
    "chaos_base_1":  (10785.2, 10117.6), # Turret_T2_L_03 (trụ base gần Chaos)
    "chaos_base_2":  (10325.2, 10608.2), # Turret_T2_L_04
}

# Thứ tự destroy — Order must kill in this sequence:
# chaos_front_1/2 → chaos_inhib → chaos_base_1/2 → chaos_shrine → Nexus
# (Shrine turret bảo vệ Nexus, chỉ có 1 lane nên không có top/mid/bot)
```

### Minion Waypoints ARAM (1 lane duy nhất)

```python
# ARAM chỉ có 1 lane (mid bridge). Lính đi thẳng từ barracks đến barracks đối diện.
ARAM_MINION_WAYPOINTS = {
    "order": [
        (3064.1, 3212.7),   # __P_Order_Spawn_Barracks__C01 (spawn)
        (5448.4, 6169.1),   # order_inhib
        (8548.8, 8289.5),   # chaos_inhib
        (10786.9, 11110.9), # __P_Chaos_Spawn_Barracks__C01 (target)
    ],
    "chaos": [
        (10786.9, 11110.9), # __P_Chaos_Spawn_Barracks__C01 (spawn)
        (8548.8,  8289.5),  # chaos_inhib
        (5448.4,  6169.1),  # order_inhib
        (3064.1,  3212.7),  # __P_Order_Spawn_Barracks__C01 (target)
    ],
}
```

---

## 2. Unit & Building Stats (Hitbox & Range)

> **Nguồn**: Extract từ `LeagueSandbox-Default-indev/Stats/*/*.json`

Thông số của các đối tượng trong game quy định 2 loại Hitbox (vòng tròn va chạm) và Tầm đánh.

**Giải nghĩa các chỉ số hitbox quan trọng:**
1. **`GameplayCollisionRadius`**: Kích thước vòng tròn để **TÍNH TRÚNG ĐÒN (Damage & Skillshot)**. Ví dụ: Q của Ezreal hay đạn của trụ chạm vào vòng này thì tính là trúng mục tiêu.
2. **`PathfindingCollisionRadius`**: Kích thước vòng tròn để **TÍNH VA CHẠM DI CHUYỂN (Unit Collision)**. Ví dụ: Lính lách qua nhau hoặc tướng bị kẹt lính (Minion Block) khi hai vòng này đụng nhau. Vòng này luôn nhỏ hơn vòng Gameplay để unit dễ lách qua đám đông hơn.
3. **`AttackRange`**: Tầm đánh tự động (Auto Attack). Tính từ RÌA vòng `GameplayCollisionRadius` của kẻ tấn công đến RÌA vòng `GameplayCollisionRadius` của mục tiêu.

### 2.1. Champion: Yasuo

**a. Thông số Hitbox & Tầm nhìn:**
- **GameplayCollisionRadius**: `65.0` *(Bán kính trúng Skillshot / Tầm đánh/bị chọn mục tiêu)*
- **PathfindingCollisionRadius**: `32.0` *(Bán kính va chạm tĩnh/cản lính)*
- **AttackRange**: `175.0` *(Tầm đánh cận chiến)*
- **AcquisitionRange**: `400.0` *(Tầm nhìn auto-tìm mục tiêu)*

**b. Chỉ số Cơ bản & Tăng trưởng (Base & Growth Stats):**
*Ghi chú: Giá trị thực tế tại cấp N = `Base + Growth * (N - 1)`*

| Chỉ số (Stat) | Cơ bản (cấp 1) | Tăng mỗi cấp (Growth) |
| :--- | :--- | :--- |
| **HP (Máu)** | 517.76 | +82.0 |
| **HP Regen (Hồi máu/5s)** | 6.512 `(1.3024 * 5)` | +0.9 `(0.18 * 5)` |
| **MP (Nội năng/Nhịp độ)** | 60.0 (Gió) | 0 |
| **AD (ST Vật lý)** | 55.376 | +3.2 |
| **Armor (Giáp)** | 24.712 | +3.4 |
| **Spell Block (Kháng phép)** | 30.0 | +0.0 |
| **Attack Speed (Tốc đánh base)** | 0.670 *(Mặc định)* | +3.2% |
| **Move Speed (Tốc chạy)** | **340.0** (Cơ bản - Chưa có giày) | 0 |

### 2.2. Các Công Trình (Buildings & Turrets)

- **Hitbox của Trụ Thường / Trụ Tế Đàn**: `88.4` (Cả vòng kích thước lẫn khoảng cản bước đi).
- **Hitbox của Nhà Lính (Inhibitor)**: Khoảng `150.0` đến `200.0` *(Gấp đôi trụ).*
- **Hitbox của Nhà Chính (Nexus)**: Khoảng `250.0` đến `300.0` *(Cấu trúc to nhất game).*

**a. Chỉ số Chiến đấu của Công trình (ARAM):**
- **Trụ Thường (Outer/Inhibitor/Nexus Turret):**
    - **AttackRange**: `750.0`
    - **BaseDamage**: `152.0`
    - **BaseHP**: `1300.0` (Trụ đầu thường máu ở quanh mức 1300-2000 tùy buff)
    - **Armor/SpellBlock**: `60` / `100`

- **Trụ Tế Đàn (Obelisk / Laser Shrine ở Bệ đá):**
    - **AttackRange**: `1250.0` *(Tầm bắn cực xa quét tới rìa bệ đá)*
    - **BaseDamage**: `999.0` (Sát thương chuẩn cực lớn dồn vào mục tiêu liên tục, không thể dùng giáp hay khiên để chặn đỡ lâu được).
    - **BaseHP**: `9999.0` (Vô địch/Bất tử, không thể bị định vị).

- **Nhà Lính (Inhibitor) & Nhà Chính (Nexus):**
    - *Đặc điểm:* Cấu trúc tĩnh đứng im, **không có sát thương**, **không có tầm đánh**. Chỉ là vật cản lớn.
    - **Nhà lính (Inhibitor)**: BaseHP `4000`. **Hồi máu** `15 HP/s`. Có `20 Armor`, `0 Spell Block`. Tự động hồi sinh sau khi sập `5 phút` (khi hồi sinh thì minion siêu cấp đối phương ngừng spawn).
    - **Nhà chính (Nexus)**: BaseHP `5500`. **KHÔNG TỰ ĐỘNG HỒI MÁU**. Mọi sát thương nhận vào là vĩnh viễn.

**💰 Cơ chế Hồi máu của Trụ (Health Regeneration & Thresholds):**
Trụ trong LMHT hồi phục theo **Ngưỡng máu (Thresholds)**. Máu chỉ có thể hồi phục lên mức tối đa của "Bậc" (Tier) mà nó đang đứng:
- **Trụ ngoài & Trụ trong (Outer/Inner Turret):** **KHÔNG** hồi máu, không hồi sinh. Bị phá là mất vĩnh viễn.
- **Trụ Nhà lính (Inhibitor Turret):** Hồi phục `3 HP/s`. Ngưỡng hồi máu:
    - **Dưới 33.3%**: Chỉ hồi tối đa đến 33.3%.
    - **Từ 33.3% – 66.7%**: Chỉ hồi tối đa đến 66.7%.
    - **Trên 66.7%**: Hồi tối đa đến 100%.
    - **Hồi sinh:** Có hồi sinh sau **5 phút** kể từ khi bị phá.
- **Trụ Nhà chính (Nexus Turret):** Hồi máu `6 HP/s`. Ngưỡng hồi máu:
    - **Dưới 40%**: Hồi đến 40%.
    - **Từ 40% – 70%**: Hồi đến 70%.
    - **Trên 70%**: Hồi đến 100%.
    - **Hồi sinh:** Có hồi sinh sau `3 phút` kể từ khi bị phá, nhưng chỉ hồi sinh với **40% Máu tối đa** (Update 2026).
- **Trụ Tế đàn:** Luôn ở trạng thái `9999/9999` (Vô địch).

**🛡️ Passive Đặc biệt (Turret Vanguard - Khiên Trụ):**
- Trụ sở hữu một lớp Shield (Khiên) `30 HP` gọi là **Turret Vanguard**.
- Lớp khiên này sẽ **tự hồi đầy sau 30 giây** không bị tấn công.
- **Tác dụng lên đồng minh:** Khi Tướng đứng gần trụ đang còn phần khiên Turret Vanguard, tướng đó sẽ được nhận một lượng hồi máu từ khiên trụ là `30 HP/giây` (Hồi tối đa `300 HP` mỗi lượt chờ). Đây là cơ chế "bơm máu" từ trụ về cho Tướng phòng thủ.

**b. Cơ chế Phần thưởng (Vàng & Kinh nghiệm) Phá Trụ:**
Sẽ luôn có 2 khoản tiền thưởng song song khi Trụ sập đổ:
1. **Global Gold / Global XP (Thưởng toàn bản đồ):** Khi Trụ sập, **toàn bộ 5 thành viên** trên bản đồ (dù đang ở đâu) đều nhận được một lượng Vàng (VD: 150g) và Kinh nghiệm gốc.
2. **Local Gold (Thưởng chia sẻ cục bộ):** Một khoản tiền cộng thêm rơi ra tại chân Trụ để chia đều cho những người đang đứng gần đó đánh phụ phá Trụ.

**💰 Vàng khi phá Nhà Lính (Inhibitor):**
Khác với Trụ, Nhà Lính **KHÔNG** cung cấp vàng toàn bản đồ (Global Gold) hay vàng cục bộ (Local Gold).
- **Vàng cho người kết liễu (Last-hit):** Chỉ người trực tiếp phá hủy Nhà lính mới nhận được **`50 Vàng`**.
- **Nếu Lính phá hủy:** Không ai trong team nhận được vàng.
- **Giá trị thực tế:** Phá Nhà lính quan trọng ở việc triệu hồi **Lính Siêu Cấp (Super Minon)** mạnh hơn để đẩy đường, chứ không phải nguồn thu nhập vàng chính như phá Trụ.

>*Vậy Trụ bị Lính đập và Tướng đập khác nhau chỗ nào?*
> - **Nếu Tướng (Yasuo) Last-hit trụ**: Nhận được **Global Gold** + ăn trọn phần **Local Gold** (khoản tiền cộng thêm).
> - **Nếu Lính Last-hit trụ dập**: Cả team VẪN ĐƯỢC NHẬN **Global Gold** và **Global XP** y như bình thường. Tuy nhiên, phần tiền **Local Gold sinh ra ở chân trụ sẽ bị hủy bỏ (chia cho không khí)** -> Team bạn bị thất thoát một lượng vàng cục bộ. Do đó kinh nghiệm không thay đổi nhưng Vàng tối đa sẽ ít đi khoảng ~100-200g so với việc người chơi trực tiếp kết liễu trụ.

### 2.3. Lính (Minion)

> Vòng Gameplay to hơn để dễ đấm trúng, vòng Pathfinding (Obstacle) rất nhỏ để dễ lách qua nhau.
> **Move Speed**: Tốc độ di chuyển chuẩn của mọi loại lính ban đầu là **`325.0`**. (Thấp hơn Yasuo một chút).

- **GameplayCollisionRadius**: `48.0` (Cận chiến/Đánh xa) — `65.0` (Xe Cannon)
- **PathfindingCollisionRadius**: `35.7437` (Tất cả loại lính - cả lính xe cũng dùng 55.7437 hoặc 35.7 theo thông số Caster/Melee, Xe Cannon là `55.74`)

**a. Chỉ số chiến đấu Lính Cơ bản (Giai đoạn đầu trận):**
*Ghi chú: Lính sẽ được buff tăng sức mạnh (Máu, AD) theo thời gian. Mức tăng máu/dame phụ thuộc vào cơ chế logic map ở Server.*

*   **Melee (Lính Gần - Blue_Minion_Basic):**
    *   **BaseHP:** `455` | **BaseDamage:** `12.0` | **Armor:** `0` | **AttackRange:** `110.0`
*   **Caster (Lính Xa - Blue_Minion_Wizard):**
    *   **BaseHP:** `290` | **BaseDamage:** `23.0` | **Armor:** `0` | **AttackRange:** `550.0`
*   **Cannon (Lính Xe - Blue_Minion_MechCannon):**
    *   **BaseHP:** `700` | **BaseDamage:** `40.0` | **Armor:** `15` | **AttackRange:** `300.0`
*   **Super Minion (Lính Siêu Cấp - SRU_OrderMinionSuper):**
    *   *Xuất hiện khi:* Một Nhà Lính của đối phương bị phá hủy. 
    *   **Cơ chế thay thế:** Lính Siêu Cấp sẽ **THAY THẾ HOÀN TOÀN** mốc xuất hiện của Lính Xe (Cannon).
    *   **HP Scaling:** Base `1500.0` (Tăng `+150 HP` mỗi **180 giây**/3 phút). Scaling dừng ở phút thứ 90.
    *   **AD Scaling:** Base `215.0` (Tăng `+5 AD` mỗi **90 giây**/1.5 phút). Scaling dừng ở phút thứ 90.
    *   **Quy tắc sức mạnh:** Chỉ số tính theo **thời gian trận đấu (Game Time)**. Nếu nhà lính sập ở phút 20, lính siêu cấp sinh ra sẽ có ngay stats của phút 20.
    *   **Logic hồi phục Nhà lính:** Lính Siêu Cấp sẽ **ngừng xuất hiện 2 đợt lính trước khi** Nhà Lính hồi sinh (để cân bằng bản đồ).
    *   **Armor/SpellBlock:** `30` / `-30`.
    *   **AttackRange:** `170.0`.

**b. Cơ chế Phần thưởng (Vàng và Kinh nghiệm trong ARAM):**
- **Vàng tăng theo thời gian**: Tất cả các loại lính (bao gồm cả Siêu Cấp) đều tăng bounty vàng theo thời gian trận đấu.
- **XP sinh ra TỪ LÍNH LÀ CỐ ĐỊNH** (Riot đã xóa tính năng scale XP lính từ patch 3.14).

**💰 Vàng (Gold) nhận được khi Last hit:**
| Loại lính | Vàng cơ bản | Tốc độ tăng trưởng |
| :--- | :--- | :--- |
| **Melee (Cận chiến)** | 20 Vàng | Tăng `+0.125` vàng mỗi 90 giây |
| **Caster (Đánh xa)** | 17 Vàng | Tăng `+0.125` vàng mỗi 90 giây |
| **Cannon (Xe to)** | 60 Vàng | Tăng `+3` vàng mỗi lần xuất hiện (Max: `90` vàng). Tức tăng sau 10 lần spawn (từ 3:35 tới 16:05). |
| **Super (Siêu cấp)** | **40 Vàng** | **CỐ ĐỊNH** (Không tăng theo thời gian). |

> *Lưu ý:* Lính Siêu Cấp trong ARAM cho ít vàng hơn Xe Cannon để tránh việc team đang bị ép sân ăn quá nhiều vàng từ lính siêu cấp, giúp cân bằng lại trận đấu.

**⭐ Kinh nghiệm (XP) từ lính:**
- **Melee:** `60 XP`
- **Caster:** `29 XP`
- **Cannon:** `90 XP`
- **Super:** **`95 XP`** (Cao nhất nhưng không lệch quá nhiều so với Xe Cannon).

**🔄 Cơ chế nhận và chia sẻ XP (Solo vs Shared):**
- **ARAM Passive XP:** Tướng sẽ tự động nhận thêm XP theo thời gian (dù đứng yên hay đã chết).
- **Phạm vi nhận XP lính:** `1500` units quanh lính (bất kể có last hit hay không, khi lính chết thì những champion trên cùng team đứng lân cận sẽ được áp dụng).
- **Quy tắc phân chia XP:**
  - Nếu lính bị tiêu diệt và chỉ có **1 người** đứng trong tầm 1500 (Solo): Người đó chỉ được nhận **`95%`** tổng lượng XP phía trên cơ bản.
  - Nếu lính bị tiêu diệt và có **Nhiều (2+)** người trên cùng team trong tầm 1500 (Shared): Tổng XP phần thưởng sẽ được tăng lên **`124%`**, sau đó đem chia đều cho tất cả mọi người có mặt. *(Lưu ý: Kể cả khi không ai last hit, lính tự chết do lính/trụ/thời gian thì vẫn chia theo công thức này cho những người đồng minh lân cận).*

### 2.4. Kỹ năng Champion (Yasuo)

Dưới đây là các thông số quan trọng (Tầm xa, Độ rộng, Sát thương, Thời gian khống chế) trích xuất từ file JSON (`LeagueSandbox-Default-indev/Spells/Yasuo*/*.json`) kết hợp với thông số chuẩn LMHT do các tooltip text bị thiếu trong resource raw:

*   **Q - Bão Kiếm (Steel Tempest / YasuoQW)**
    *   **Cast Range (Tầm đâm):** `475.0`
    *   **Missile Speed:** `1500.0`
    *   **Width (Độ rộng hitbox đâm):** `55.0`
    *   **Cooldown:** `6.0 / 5.5 / 5.0 / 4.5 / 4.0` giây *(Có thể giảm theo Tốc độ Đánh, thấp nhất 1.33s)*
    *   *Sát thương cơ bản (Level 1-5):* `20 / 40 / 60 / 80 / 100` (+1.0 AD)
*   **Q3 - Lốc Kiếm (Tornado / YasuoQ3W)**
    *   **Cast Range (Display):** `1000.0` *(server-side travel tối đa `3250`, nhưng hiển thị indicator `1000`)*
    *   **Width (Độ rộng lốc):** `90.0` *(từ `YasuoQ3W.json`: `LineWidth: 90`)*
    *   **MissileSpeed:** `1500` units/giây *(từ `YasuoQ3W.json`)*
    *   **Knockup Duration (Thời gian hất tung): `0.75s` CỐ ĐỊNH** *(không đổi theo cấp, nằm trong buff Lua — cross-confirmed)*
    *   **Stack timer** (thời gian giữ Q stack, từ `Effect4`): `5.0 / 4.75 / 4.5 / 4.25 / 4.0` giây theo cấp Q
*   **W - Tường Gió (Wind Wall / YasuoWMovingWall)**
    *   **Cooldown:** `26.0 / 24.0 / 22.0 / 20.0 / 18.0` giây
    *   **Cast Range (Khoảng cách đặt tường tính từ tâm Yasuo):** `400.0`
    *   **Wall Width (Độ rộng tường chặn đạn theo Cấp độ W):** `300 / 350 / 400 / 450 / 500`
*   **E - Quét Kiếm (Sweeping Blade / YasuoDashWrapper)**
    *   **Cooldown:** `0.5 / 0.4 / 0.3 / 0.2 / 0.1` giây (Giữa mỗi lần lướt)
    *   **Cast Range (Khoảng cách lướt):** `475.0` ← **CỐ ĐỊNH, không đổi theo cấp độ hay stats**
    *   *Sát thương cơ bản (Level 1-5):* `70 / 90 / 110 / 130 / 150` (+0.6 AP)
    *   *Ghi chú:* Thời gian hồi chiêu lên **cùng 1 mục tiêu (Target Cooldown)**: `10.0 / 9.0 / 8.0 / 7.0 / 6.0` giây.
    *   **Cơ chế Dash (quan trọng cho simulator):**
        *   **Khoảng cách dash: CỐ ĐỊNH `475` units** — không phụ thuộc vào vị trí ban đầu, con trỏ chuột hay khoảng cách đến mục tiêu.
        *   **Hướng dash:** từ tâm Yasuo xuyên qua tâm địch, điểm đến = `target_pos + normalize(target_pos - yasuo_pos) * 475`.
        *   **Tốc độ dash animation** scale theo Bonus MS (MS cao → hoàn thành nhanh hơn), nhưng **khoảng cách thực tế vẫn là 475**.
        *   **Không xuyên tường:** Nếu điểm đến nằm trong terrain, Yasuo dừng tại mép walkable gần nhất (terrain vẫn chặn, chỉ unit-collision bị bỏ qua khi dash).
        *   **Không phụ thuộc con trỏ chuột** cho khoảng cách — hướng xác định bởi vector Yasuo→Target.
    *   **⚡ Cơ chế Stack Damage (Dash liên tiếp):**
        *   Mỗi lần E vào **mục tiêu KHÁC NHAU** liên tiếp → tăng stack, tối đa **4 stacks**.
        *   Mỗi stack cộng thêm **+25% base damage** của E.
        *   **Bảng sát thương theo stack (Level 1 / Level 5):**

            | Stack | Bonus | Damage (Lv1) | Damage (Lv5) |
            |:---:|:---:|:---:|:---:|
            | 0 | +0% | 70 | 150 |
            | 1 | +25% | 87.5 | 187.5 |
            | 2 | +50% | 105 | 225 |
            | 3 | +75% | 122.5 | 262.5 |
            | 4 (max) | +100% | **140** | **300** |

        *   **Decay:** Stack bị reset nếu không dùng E trong một khoảng thời gian (~4–5 giây).
        *   **Cùng 1 mục tiêu:** KHÔNG tăng stack (target cooldown `6–10s`).
        *   **Công thức implement:**
            ```python
            E_STACK_BONUS_PER_STACK = 0.25
            E_MAX_STACKS = 4

            def e_damage(yasuo, stacks: int) -> float:
                base = YASUO_E_BASE_DMG[yasuo.e_level]
                multiplier = 1.0 + E_STACK_BONUS_PER_STACK * min(stacks, E_MAX_STACKS)
                return base * multiplier + 0.6 * yasuo.ap
            ```
*   **EQ Combo - Bão Vòng Kiếm (YasuoEQCombo)**
    *   **Area of Effect (Bán kính vòng xoay):** `375.0` (Hitbox trúng đạn). *File JSON ghi `OT_AreaRadius`: `425.0` là bao quát hình ảnh hiển thị.*
    *   **Cơ chế:** Kích hoạt Q trong lúc đang lướt E sẽ đổi sang dạng xoay vòng tròn sát thương ra xung quanh tâm tướng (dùng hitbox của E+Q combo thay vì đâm thẳng).
*   **R - Trăn Trối (Last Breath / YasuoRKnockUpComboW)**
    *   **Cooldown:** `80.0 / 55.0 / 30.0` giây
    *   **Cast Range (Khoảng cách chọn mục tiêu):** `1200.0`
    *   **Knockup Extension (Giữ nạn nhân trên không):** `+1.0s`
    *   *Sát thương cơ bản (Level 1-3):* `200 / 300 / 400` (+1.5 Bonus AD)
    *   **AOE radius (địch xung quanh cũng bị kéo lên):** `BounceRadius = 450` (từ `YasuoRKnockUpCombo.json`)
    *   **⚠️ Vị trí Yasuo xuất hiện sau địch — KHÔNG có offset cố định:**
        *   Được xử lý bởi C++/Lua engine, **không encode trong spell JSON**.
        *   **Trường hợp thường:** Yasuo xuất hiện **phía sau lưng địch** theo vector `Yasuo → Target`. Khoảng offset thực tế ước tính **~100 units** phía sau tâm địch (tức gần sát lưng, trong tầm Q ngay lập tức).
        *   **Trường hợp gần trụ địch:** Yasuo **ưu tiên đứng ngoài tầm trụ** (750 units từ trụ). Nếu phía sau địch nằm trong range trụ → Yasuo có thể xuất hiện ở **mặt trước hoặc bên cạnh** địch, miễn là ngoài tầm trụ. Nếu không thể thoát khỏi tầm trụ → mặc định đứng phía sau.
        *   **Nhiều địch bị airborne:** Yasuo blink đến địch **gần con trỏ chuột nhất**, rồi tất cả địch trong `BounceRadius = 450` cũng bị kéo.
        *   **Json field liên quan** (từ `YasuoRKnockUpComboW.json`):
            *   `CastConeDistance: 100` — khoảng cách cone offset (tham chiếu hướng)
            *   `LocationTargettingLength: 400/500/600/700/800` (per level W) — chiều dài targeting display, không phải offset spawn
            *   `LocationTargettingWidth: 175` — chiều rộng vùng targeting
        *   **Công thức recommend cho simulator:**
            ```python
            def yasuo_r_spawn_pos(yasuo_pos, target_pos, turrets) -> Vec2:
                direction = normalize(target_pos - yasuo_pos)
                # Đứng phía sau địch ~100 units
                candidate = target_pos + direction * 100
                # Kiểm tra có trong tầm trụ địch không
                for turret in turrets:
                    if turret.team != yasuo.team and distance(candidate, turret.pos) < 750:
                        # Thử đứng ở hướng ngược lại (phía trước địch)
                        alt = target_pos - direction * 100
                        if distance(alt, turret.pos) >= 750:
                            return alt
                        # Không thoát được → vẫn đứng phía sau
                return candidate
            ```

### 2.5. Bổ Trợ Tướng — Flash (Tốc Biến)

Dịch chuyển tức thời đến 1 điểm gần con trỏ chuột, có thể xuyên qua địa hình mỏng. Cả 2 tướng trong 1v1 ARAM đều mang Flash (meta mặc định).

**Thông số cốt lõi:**

| Thông số | Giá trị |
| :--- | :--- |
| **Loại** | Blink (dịch chuyển tức thời) |
| **Khoảng cách dịch chuyển tối đa** | **425 units** |
| **Thời gian hồi (Cooldown)** | **300 giây (5 phút)** |
| **Thời gian cast** | Tức thì (instant — không tốn thời gian animation) |
| **Điểm đến** | Hướng con trỏ chuột — nếu ngoài 425u thì Flash đến điểm xa nhất trong hướng đó |
| **Mục tiêu** | Bản thân (Self-cast) |

**Cơ chế quan trọng cho Simulator:**
- **Instant blink:** Không phải dash — tướng biến mất và xuất hiện ngay tại điểm đến trong **cùng 1 frame** (không animation di chuyển, không theo quán tính).
- **Xuyên tường:** Cho phép blink qua địa hình nếu tâm điểm đến ở phía bên kia tường đủ mỏng. Nếu điểm đến nằm trong terrain → snap về vị trí **walkable gần nhất về phía con trỏ** (≠ vị trí gốc).
- **CC chặn Flash:**
  - **BỊ CHẶN:** Root (Cố định), Ground (Giam giữ mặt đất), Suppression, Airborne (đang bay trên không).
  - **KHÔNG BỊ CHẶN:** Stun, Slow, Silence, Fear (tướng vẫn Flash được khi bị Stun/Silence).
- **Hướng mặt sau Flash:** Tướng quay mặt về hướng blink — với Yasuo, **Q stack không bị mất** khi Flash.
- **Không thể Flash vào tường dày:** Nếu thử Flash vào terrain dày, vị trí snap về gần ngay điểm đặt chân hiện tại → hiệu ứng "fail-flash" (Flash mà không đi xa).

**Công thức implement (Python simulator):**

```python
FLASH_RANGE    = 425.0
FLASH_COOLDOWN = 300.0   # giây

def cast_flash(unit, cursor_world_pos, navgrid):
    """
    Instant blink tối đa FLASH_RANGE units về phía cursor.
    Trả về True nếu Flash thành công, False nếu bị CC chặn.
    """
    # Kiểm tra CC chặn
    if unit.is_rooted or unit.is_grounded or unit.is_suppressed or unit.is_airborne:
        return False

    direction = normalize(cursor_world_pos - unit.pos)
    dist      = min(distance(cursor_world_pos, unit.pos), FLASH_RANGE)
    candidate = unit.pos + direction * dist

    # Snap về walkable nếu đích nằm trong tường
    if not navgrid.is_walkable(candidate):
        candidate = navgrid.nearest_walkable_toward(candidate, cursor_world_pos)

    unit.pos      = candidate          # Teleport tức thì, cùng frame
    unit.facing   = direction          # Cập nhật hướng mặt
    unit.flash_cd = FLASH_COOLDOWN
    return True
```

**Ghi chú ARAM / Display:**
- Hiển thị vòng tròn range **425 units** khi người chơi giữ phím `D` (giống game thật hiển thị range indicator).
- Flash của Yasuo kết hợp với E (lướt vào → Flash thoát ra khỏi trụ) là combo thường thấy — Simulator cần đảm bảo Flash hoạt động độc lập với `target_cooldown` của E (không reset stack E khi Flash).

---

### 2.6. Cơ chế Phần thưởng khi Hạ gục Tướng (Kills & Assists)

Khi một Tướng bị hạ gục (Kill) trong ARAM, Server sẽ xử lý phần thưởng Vàng (Gold) và Kinh nghiệm (XP) cho phe hạ gục thông qua 3 hệ thống: Base Kill, Hỗ trợ (Assist) và Tiền thưởng chuỗi (Bounty / Death Streak).
*(Ghi chú: Thông số dưới đây là chuẩn logic cơ bản phổ biến của ARAM/LMHT).*

**a. Vàng (Gold) Nhận Được:**
1.  **First Blood (Chiến công đầu):** `400 Vàng` cho người Last-hit (Giết mạng đầu tiên của trận đấu).
2.  **Base Kill (Mạng cơ bản):** `300 Vàng` cho người Last-hit.
3.  **Hỗ Trợ (Assist Pool):** Tổng lượng Vàng dành cho người Hỗ trợ bằng **50% lượng Vàng của mạng đó** (Tức `150 Vàng` gốc). Số vàng Hỗ trợ này được SẼ CHIA ĐỀU cho tất cả những Tướng đồng minh có tham gia đóng góp sát thương/khống chế/buff trong vòng `10 giây` trước khi nạn nhân chết.
    *   *Ví dụ:* Yasuo solo kill -> Thu 300 Vàng. Yasuo kill có 2 người buff/đánh phụ -> Yasuo nhận 300 Vàng, 2 người kia mỗi người nhận `150 / 2 = 75 Vàng`.
4.  **Bounty & Death Streak (Tiền thưởng chuỗi & Mạng Feed):**
    *   **Chuỗi hạ gục (Killing Spree - 3 mạng trở lên):** Người hạ gục liên tục không chết sẽ "tích tụ" tiền thưởng thêm vào đầu (Shutdown Gold). Người nào kết liễu Tướng đang có Bounty sẽ nhận được > 300 Vàng (Tối đa `1000 Vàng` bao gồm cả 300 gốc).
    *   **Chuỗi chết (Death Streak - Bị giết liên tục không có điểm hạ gục):** Tướng "Feed" liên tục giá trị mạng sẽ bị giảm giá (Depreciation) theo cấp số. Mạng gốc 300 Vàng có thể giảm xuống `274` -> `220` -> ... chạm đáy là khoảng **`112 Vàng`** để tránh team kia đè bẹp bằng cách farm người. *(Cắt đứt chuỗi chết bằng 1 mạng Kill sẽ đưa giá trị bản thân về 300 lại).*

**b. Kinh Nghiệm (XP) Nhận Được:**
- Người tiêu diệt hoặc Hỗ Trợ sẽ nhận chung một lượng **XP tính dựa trên Cấp Độ (Level) của Tướng bị hạ gục**.
- XP tăng lên rất nhiều nếu team bạn đang bị đối phương Level cao hơn nhiều (Under-leveled Catch-up XP).
- Nếu Solo kill 1 Tướng đồng cấp: Nhận lượng XP khá lớn ở mốc ~50% - 75% lượng cần thiết để lên 1 level đầu. Nếu có Assist, XP sẽ bị CHIA RA cho tất cả người dính Assist tương tự như chia Vàng Assist, nhưng người Last-hit luôn nhận số phần trăm trội hơn.

---

## 3. Items (Trang bị cho Yasuo)

Danh sách 20 trang bị (Dựa theo ID gốc v4.x + chỉ số mô phỏng chuẩn của các item mới/hiện đại không có trong DB cũ):

### 3.1. Starter & Consumables (Tạm thời, có thể bán)
1. **Doran's Blade** (`ID: 1055`): +70 HP, +7 AD, +3% Lifesteal
2. **Health Potion** (`ID: 2003`): Hồi 150 HP trong 15s
3. **Refillable Potion**: Hồi 125 HP trong 12s (2 Charges, sạc lại ở Bệ đá)

### 3.2. Boots (Giày di chuyển)
4. **Boots of Speed** (`ID: 1001`): +25 Tốc chạy (Movement Speed)
5. **Berserker's Greaves** (`ID: 3006`): +45 Tốc chạy, +25% Tốc đánh (AS)
6. **Ninja Tabi** (`ID: 3047`): +45 Tốc chạy, +25 Giáp (Armor)
7. **Mercury's Treads** (`ID: 3111`): +45 Tốc chạy, +25 Kháng phép (MR), +35% Kháng hiệu ứng (Tenacity)

### 3.3. Components (Trang bị thành phần)
8. **Long Sword** (`ID: 1036`): +10 AD
9. **Pickaxe** (`ID: 1037`): +25 AD
10. **Cloak of Agility** (`ID: 1018`): +15% Tỉ lệ chí mạng (Crit Chance)
11. **Vampiric Scepter** (`ID: 1053`): +10 AD, +10% Lifesteal
12. **Null-Magic Mantle** (`ID: 1033`): +25 Kháng phép (MR)
13. **Cloth Armor** (`ID: 1029`): +15 Giáp (Armor)
14. **Zeal** (`ID: 3086`): +15% Tốc đánh (AS), +15% Crit Chance, +5% Tốc chạy (MS)

### 3.4. Core Items (Trang bị Hoàn chỉnh - Yasuo Core)
15. **Immortal Shieldbow** *(Mô phỏng)*: +50 AD, +20% Crit Chance, +12% Lifesteal. *Nội tại:* Tạo khiên (Lifeline) khi HP < 30%.
16. **Infinity Edge** (`ID: 3031`): +80 AD, +25% Crit. *Nội tại:* Tăng sát thương chí mạng.
17. **Navori Quickblades** *(Mô phỏng)*: +60 AD, +20% Crit, +15 Điểm hồi kỹ năng. *Nội tại:* Crit giảm Hồi chiêu (CDR) hoặc tăng sát thương kỹ năng dựa trên Crit.
18. **Phantom Dancer** (`ID: 3046`): +50% AS, +30% Crit, +5% MS. *Nội tại:* Tấn công tăng thêm %AS và có hiệu ứng Xuyên Lính (Ghosted).
19. **Statikk Shiv** (`ID: 3087`): +40% AS, +20% Crit, +5% MS. *Nội tại:* Tích điện (Energized), giật sét xoay quanh lính.

### 3.5. Situational (Đọc đối thủ - Tuỳ chọn)
20. **Death's Dance** *(Mô phỏng)*: +55 AD, +45 Armor, +15 Hồi chiêu. *Nội tại:* Trì hoãn một phần sát thương vật lý/phép nhận vào thành sát thương chảy máu.
21. **Wit's End** (`ID: 3091`): +40 AD, +40 AS, +40 MR. *Nội tại:* Đòn đánh gay sát thương phép thuật thêm và hồi máu khi HP < 50%.
22. **Lord Dominik's Regards** *(Mô phỏng)*: +35 AD, +20% Crit, +30% Armor Penetration (Xuyên giáp). *Nội tại:* Sát thương tăng thêm trên mục tiêu có HP max cao hơn.
23. **Guardian Angel** (`ID: 3026`): +45 AD, +40 Armor. *Nội tại:* Hồi sinh lại với 50% Base HP và 30% Max Mana sau khi chịu sát thương hạ gục (CD siêu lâu).
24. **Ravenous Hydra** (`ID: 3074`): +70 AD, +10% Lifesteal. *Nội tại:* Đánh lan (Cleave). Tỉ lệ hút máu áp dụng lên AOE.
