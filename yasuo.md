# YASUO - COMPLETE CHAMPION DATA & LOGIC RULES
**Metadata:**
- **Champion Name:** Yasuo
- **Title:** The Unforgiven
- **Resource:** Flow (Nhịp - Max 100)
- **Role/Class:** Skirmisher (Legacy: Fighter, Assassin)
- **Attack Type:** Melee (Cận chiến)
- **Adaptive Type:** Physical
- **Store Price:** 675 BE / 585 RP
- **Release Date:** 2013-12-13
- **Difficulty:** 3/3
- **Latest Patch Update:** V26.01

---

## 1. OFFICIAL STAT GROWTH FORMULA (CÔNG THỨC TÍNH CHỈ SỐ MỌI CẤP ĐỘ)
Để tính toán bất kỳ chỉ số nào của Yasuo tại cấp độ `L` (từ 1 đến 18), áp dụng công thức sau:
**Stat_at_Level_L = Base_Stat + Growth_Stat * Growth_Multiplier**
- **Growth_Multiplier** = `(L - 1) * (0.7025 + 0.0175 * (L - 1))`

## 2. EXACT BASE STATISTICS & GROWTH (CHỈ SỐ CƠ BẢN VÀ TĂNG TRƯỞNG)
- **Health (Máu):** Base = 590 | Growth = 110
- **Health Regen (Hồi máu/5s - HP5):** Base = 6.5 | Growth = 0.9
- **Armor (Giáp):** Base = 32 | Growth = 4.6
- **Magic Resist (Kháng phép):** Base = 32 | Growth = 2.05
- **Attack Damage (AD):** Base = 60 | Growth = 2.5
- **Movement Speed (MS):** 345 | Growth = 0
- **Attack Range (Tầm đánh):** 175 | Growth = 0
- **Attack Speed (Tốc độ đánh - AS):**
  - Base AS = 0.697
  - AS Ratio = 0.67 (Hệ số dùng để nhân với Bonus AS)
  - AS Growth = 3.5%
  - Level 1 Bonus AS = +4% (Mặc định được cộng thêm 4% ở level 1)
- **Attack Windup (Thời gian vận đòn đánh):** 22%

### 2.1 Hitbox & Unit Radius Data
- **Gameplay radius (Bán kính trúng chiêu):** 65
- **Selection radius (Bán kính click chuột):** 120
- **Pathing radius (Bán kính va chạm vật lý):** 32
- **Selection height (Chiều cao mục tiêu):** 180
- **Acquisition radius (Tầm tự động tấn công):** 400

---

## 3. ABILITY MECHANICS & LOGIC RULES

### 3.1 INNATE (PASSIVE): WAY OF THE WANDERER
**A. Intent (Crit Rules):**
- `Total_Crit_Chance = Bonus_Crit_Chance * 2`
- `Bonus_AD_from_Excess_Crit = (Total_Crit_Chance - 100%) * 0.5` (Chỉ kích hoạt nếu Total > 100%).
- `Crit_Damage_Multiplier = 180%` (Bị trừ 10% so với 200% của tướng thường).
  - *Item Rule:* Nếu có Infinity Edge (Vô Cực Kiếm), `Crit_Damage_Multiplier = 180% + 27% = 207%`.

**B. Resolve (Flow & Shield Rules):**
- **Flow Generation:** Nhận 1 Flow sau mỗi khoảng cách `D` di chuyển.
  - Cấp 1-6: `D = 59`
  - Cấp 7-12: `D = 52.5`
  - Cấp 13-18: `D = 46`
- **Shield Trigger:** Khi Flow = 100, chịu sát thương từ Tướng/Quái rừng sẽ tạo khiên trong `1.0` giây, tiêu hao 100 Flow.
- **Shield Value by Level (1 to 20 Array):** `[125, 145.12, 166.21, 188.29, 211.34, 235.37, 260.38, 286.36, 313.32, 341.26, 370.18, 400.08, 430.96, 462.81, 495.64, 529.45, 564.24, 600, 636.74, 674.46]`. (Công thức nội bộ: `125 + ((600 - 125)/17 * (Level - 1) * (0.7025 + 0.0175 * (Level - 1)))`).

### 3.2 Q: STEEL TEMPEST
*Q scale nghịch với Bonus_AS (Tốc độ đánh cộng thêm). Càng nhiều AS, Cooldown và Cast time càng giảm.*

**A. Cast Time (Thời gian vung kiếm):**
- `Q_Cast_Time = 0.35 - (0.035 * (Bonus_AS / 24%))`
- Giảm tối đa `50%` tại mốc `120% Bonus_AS`. Minimum Cast Time = `0.175s`.

**B. Cooldown (Thời gian hồi chiêu):**
- `Q_Cooldown = 4.0 * (1 - (0.01 * (Bonus_AS / 1.67%)))`
- Giảm tối đa `67%` tại mốc `111.11% Bonus_AS`. Minimum Cooldown = `1.33s`.
- *Exception:* Bị dính hiệu ứng Disarm (Cấm đánh) khi đang cast -> Cooldown reset về `0.1s`.

**C. Damage & Mechanics:**
- Base Physical Damage: `[20, 45, 70, 95, 120] + (1.05 * Total_AD)`.
- Crit Damage: `Base Physical Damage + (1.89 * Total_AD)`. (Hệ số `1.89` tăng thêm `0.2835` nếu có Infinity Edge).
- Tầm Q1/Q2: `450` | Rộng: `80`.
- Tầm Q3 (Lốc): `1150` | Rộng: `180` | Tốc độ bay: `1200` | Thời gian lốc tồn tại (Stack): `6s` | Thời gian Hất tung: `0.9s`.
- Bán kính quét vòng tròn (E+Q): `215`. Thời gian khóa đánh thường (Lockout) sau E+Q: `0.5s`.
- On-hit / Spell vamp: Kích hoạt On-hit ở mục tiêu đầu tiên. Hút máu phép chỉ đạt `33.33%` hiệu quả từ mục tiêu thứ 2.

### 3.3 W: WIND WALL
- **Cooldown:** `[25, 23, 21, 19, 17]` giây.
- **Cast Time:** `0.013s`.
- **Duration:** `4.0s`.
- **Width:** `[320, 390, 460, 530, 600]`.
- **Mechanics:** Trượt tới trước từ khoảng cách `0 -> 350/450` trong `0.6s` đầu, sau đó trôi thêm `50` khoảng cách. Cấp tầm nhìn bán kính `300`. Bắt đầu chặn đạn ngay lập tức ở frame đầu tiên (`on-cast`).

### 3.4 E: SWEEPING BLADE
- **Target Immunity (Hồi chiêu trên cùng mục tiêu):** `[10, 9, 8, 7, 6]` giây.
- **Cooldown (Giữa 2 lần lướt):** `[0.5, 0.4, 0.3, 0.2, 0.1]` giây.
- **Range:** `475` (Max `625` nếu lướt xuyên địa hình).
- **Speed:** `750 + (0.60 * Yasuo_MS)`.
- **Damage:** `[70, 85, 100, 115, 130] + (0.20 * Bonus_AD) + (0.60 * Total_AP)` Magic Damage.
- **Damage Stacking Rules:**
  - Tối đa `4` Stacks. Mỗi stack lưu `5` giây.
  - Tỉ lệ % sát thương tăng thêm mỗi stack tính theo **Level (1-18)**: `[15%, 15.59%, 16.18%, 16.76%, 17.35%, 17.94%, 18.53%, 19.12%, 19.71%, 20.29%, 20.88%, 21.47%, 22.06%, 22.65%, 23.24%, 23.82%, 24.41%, 25%]`.
  - Max buff tại 4 stack: `100%` (Gấp đôi Base Damage).
- **Mechanics:** 
  - Xuyên vật thể (Ghosted) `2` giây sau lướt.
  - Kéo dài thanh Flow thêm `7.5` điểm nếu lướt khoảng cách tối đa.
  - Bị ngắt (Knocked down) bởi các hiệu ứng Trói (Immobilizing) hoặc Biến hóa (Polymorph).
  - Có thể buffer Q trong thời gian chờ (Queue Threshold) `0.5s` để tạo xoay E+Q.

### 3.5 R: LAST BREATH
- **Cast Range:** `1400` | **AOE Damage Radius:** `400`.
- **Cooldown:** `[70, 50, 30]` giây.
- **Damage:** `[200, 350, 500] + (1.50 * Bonus_AD)` Physical Damage.
- **Mechanics:**
  - Kéo dài thời gian hất tung của mục tiêu thêm `1.0` giây.
  - Instantly cấp Max Flow (100). Reset mọi stack Q (Gathering Storm).
  - Mục tiêu bị chém sẽ bị ép xoay góc nhìn mỗi `0.25s`.
- **Self-Buff:** Bỏ qua `60%` Giáp Cộng Thêm (Bonus Armor) của mục tiêu đối với Đòn đánh Chí mạng. Duy trì `15s`.
- **Lockout State (Trạng thái bị khóa của Yasuo khi dùng R):**
  - Disabled (Không thể dùng): Đánh thường, Di chuyển, Mọi chiêu thức, Mọi Item.
  - Phép bổ trợ Disabled: Flash, Teleport, Recall, Hexflash.
  - Phép bổ trợ Usable (Có thể dùng): Barrier, Clarity, Cleanse, Exhaust, Ghost, Heal, Ignite, Smite.

---

## 4. MAP-SPECIFIC BALANCING (ĐIỀU CHỈNH THEO BẢN ĐỒ)
- **ARAM:** Sát thương/Nhận vào (0%). Tốc đánh tổng cộng `+2.5%`. Chiêu W cooldown nerf thành `[27, 25, 23, 21, 19]`.
- **Arena:** Nội tại cộng thêm `0 -> 340` Máu cơ bản (theo cấp). E Target Immunity giảm `50%`.
- **URF:** Sát thương nhận vào `-10%`.

---

## 5. SPECIFIC INTERACTIONS (TƯƠNG TÁC ĐẶC BIỆT)
- **Infinity Edge:** Giá 3500 Vàng. Tăng +75 AD, 25% Crit Chance, 30% Crit Damage. Yasuo dùng IE sẽ có `Crit_Damage_Multiplier = 207%`.
- **Navori Quickblades / Hail of Blades:** Q tính là đòn đánh, sẽ tiêu hao stack của Mưa Kiếm và kích hoạt hiệu ứng Navori.
- **Spell Shield (Khiên phép):** R của Yasuo vẫn chém được mục tiêu có Khiên Phép nếu mục tiêu đang bị hất tung. (Khiên phép bị tiêu hủy nhưng sát thương/hất tung vẫn áp dụng). Q xuyên qua Khiên Phép để tích Stack Gió nhưng bị cản sát thương.

---

