


Tôi hiểu ý bạn rồi! Tức là Trụ (Turrets) và Nhà lính/Nhà chính là **mục tiêu mặc định trên đường đi (Waypoints)**, nhưng **Bảng ưu tiên 7 bước (Priority Queue) vẫn được xếp cao hơn**. 

Nếu Lính đang đánh Trụ mà có Lính địch hoặc Tướng địch lọt vào tầm quét và thỏa mãn điều kiện ưu tiên (ví dụ: Lính địch đánh lính phe ta), nó sẽ quay sang đánh mục tiêu ưu tiên đó. Nếu dọn sạch mục tiêu ưu tiên rồi, nó lại lầm lũi đi tiếp đến Trụ và gõ Trụ.

Tôi đã sửa lại phần **3.3 Thuật toán Di chuyển & Quét Mục tiêu** và **Mã giả Python** để mô phỏng chính xác tuyệt đối logic này của bạn. Dưới đây là bản cập nhật file `minion.md`:

--- START OF FILE minion.md ---

# MINION - GAMEPLAY DATA SCHEMA & LOGIC RULES
**Metadata:**
- **Entity Type:** Minion (Lính)
- **Role:** AI-controlled units sent periodically from the Nexus to attack the enemy base.
- **Latest Patch Update:** V26.01

---

## 1. SPAWNING MECHANICS (CƠ CHẾ XUẤT HIỆN LÍNH)
Các đợt lính (Minion waves) bắt đầu xuất hiện từ nhà chính (Nexus) của 2 đội và đi dọc theo các đường (Lanes). 

### 1.1 Spawn Timings (Thời gian sinh lính)
- **Đợt lính đầu tiên xuất hiện:** `0:30` giây.
- Khoảng cách giữa các lính trong cùng một đợt: `0.792` giây.
- **Từ 0:30 đến 14:00:** Mỗi đợt lính xuất hiện cách nhau `30` giây.
- **Từ 14:00 đến 30:00:** Mỗi đợt lính xuất hiện cách nhau `25` giây. *(Ví dụ: 13:30 -> 14:00 -> 14:25)*.
- **Từ 30:00 trở đi:** Mỗi đợt lính xuất hiện cách nhau `20` giây. *(Ví dụ: 29:25 -> 29:50 -> 30:10)*.

### 1.2 Wave Composition (Đội hình đợt lính)
Một đợt lính tiêu chuẩn bao gồm: `3 Lính cận chiến` + `3 Lính đánh xa`. Có thể có Lính xe (Siege) hoặc Lính siêu cấp (Super) tùy điều kiện.

- **Siege Minion (Lính Xe):** Đi ở giữa lính cận chiến và lính đánh xa.
  - Đợt Lính xe đầu tiên xuất hiện ở đợt thứ 3 (`01:30`).
  - Dưới 14 phút: Xuất hiện `1` xe mỗi `3` đợt lính.
  - Từ 14 phút - 25 phút: Xuất hiện `1` xe mỗi `2` đợt lính (mốc 12:00 / 13:30 / 14:25 / 15:15).
  - Từ 25 phút trở đi: Xuất hiện `1` xe ở **mọi** đợt lính.
  - *Ngoại lệ (V26.01):* Từ phút 14:00, nếu Lính xe xuất hiện trong đợt, số lượng Lính cận chiến giảm đi 1 (chỉ còn 2 Cận chiến).
- **Super Minion (Lính Siêu cấp):** 
  - Chỉ xuất hiện khi Nhà lính (Inhibitor) của đối phương bị phá hủy ở lane tương ứng.
  - Lính siêu cấp sẽ **thay thế hoàn toàn** sự xuất hiện của Lính xe trong đợt đó.
  - Nếu tất cả 3 Nhà lính bị phá: Sẽ có `2` Lính siêu cấp xuất hiện ở mỗi lane.
- **Caster Minion Modifier (Giảm lính xa - V26.01):** Từ phút 30:00 trở đi, mỗi đợt lính sẽ sinh ra **ít hơn 1** Lính đánh xa (chỉ còn 2 Caster minion).

---

## 2. BASE STATISTICS (CHỈ SỐ CƠ BẢN TỪNG LOẠI LÍNH)
*(Lưu ý: Lính sẽ được buff tăng sức mạnh (Health, AD) mỗi 90 giây. Dưới đây là chỉ số cấp 1 ở đầu trận).*

### 2.1 Melee Minion (Lính Cận Chiến)
- **Base HP:** 477
- **Base AD:** 12
- **Attack Speed:** 1.25
- **Attack Range:** 110
- **Base Gold:** 20g
- **Gameplay Radius (Hitbox trúng chiêu):** 48.0
- **Pathfinding Radius (Hitbox va chạm):** 35.7
- **On-hit Bonus:** Gây thêm Sát thương vật lý bằng `2%` Máu hiện tại của mục tiêu khi đánh Lính phe địch.

### 2.2 Caster Minion (Lính Đánh Xa)
- **Base HP:** 296
- **Base AD:** 24
- **Attack Speed:** 0.667
- **Attack Range:** 550
- **Base Gold:** 14g
- **Gameplay Radius:** 48.0
- **Pathfinding Radius:** 35.7

### 2.3 Siege/Cannon Minion (Lính Xe To)
- **Base HP:** 900
- **Base AD:** 40
- **Attack Speed:** 1.00
- **Attack Range:** 300
- **Base Gold:** Bắt đầu từ 50g.
- **Gameplay Radius:** 65.0
- **Pathfinding Radius:** 55.7
- **On-hit Bonus:** Gây thêm Sát thương vật lý bằng `6%` Máu hiện tại của mục tiêu khi đánh Lính phe địch.
- *Đặc biệt:* Lính xe chỉ chịu `70%` sát thương nhận vào từ Trụ.

### 2.4 Super Minion (Lính Siêu Cấp)
- **Base HP:** 1600
- **Base AD:** 230
- **Attack Speed:** 0.85
- **Attack Range:** 170
- **Armor / Magic Resist:** 30 / -30
- **Minions Commander Buff:** Cung cấp cho lính đồng minh xung quanh `+70 Armor`, `+70 MR` và `+70% Sát thương`.
- *Đặc biệt:* Giống lính xe, Lính siêu cấp chịu sát thương giảm từ Trụ.

---

## 3. COMBAT LOGIC & AI BEHAVIOR (THUẬT TOÁN HÀNH VI VÀ CHIẾN ĐẤU)

### 3.1 Damage Modifiers (Hệ số Sát thương)
- Đối với Tướng (Champions): Lính chỉ gây `55%` Sát thương.
- Đối với Công trình (Structures/Turrets): Lính chỉ gây `60%` Sát thương.

### 3.2 Movement Speed (Tốc độ Di chuyển)
- **Base MS:** `350`
- **MS Scaling:** Tăng thêm `25` tốc chạy mỗi 5 phút, bắt đầu từ phút thứ 11, tới phút 26 (Mốc tăng: 11 / 16 / 21 / 26). Tối đa đạt `450` MS.
- **Sidelane MS Buff (Khởi hành nhanh cho Top và Bot):**
  - Kích hoạt ở các đợt lính (trước phút 14) để lính 2 cánh gặp nhau cùng lúc với Mid. Đợt thứ 2 nhận `111` Bonus MS. Các đợt sau bị trừ `4.5` Bonus MS cho mỗi đợt.
  - Buff này tồn tại 25 giây và bị suy giảm theo 4 giai đoạn.

### 3.3 Thuật toán Di chuyển & Quét Mục tiêu (Aggro Logic)

Lính được điều khiển bởi AI hoạt động theo logic ưu tiên (Priority). Trụ (Turrets) là mục tiêu trên tuyến đường (Waypoints), nhưng Lính sẽ luôn ưu tiên giải quyết các mối đe dọa (Tướng địch/Lính địch) theo Bảng ưu tiên 7 bước trước khi đánh Trụ.

**A. Bảng Thứ tự Ưu tiên (Priority Queue):**
Lính sẽ liên tục quét mục tiêu trong bán kính `500` (Acquisition Range) hoặc `1000` (Call for Help) và chọn mục tiêu theo ưu tiên từ cao xuống thấp (1 -> 7):
1. Tướng địch đang tấn công Tướng đồng minh ("Call for Help").
2. Lính địch đang tấn công Tướng đồng minh.
3. Lính địch đang tấn công Lính đồng minh.
4. Trụ địch đang tấn công Lính đồng minh.
5. Tướng địch đang tấn công Lính đồng minh.
6. Lính địch gần nhất.
7. Tướng địch gần nhất.
*(Lưu ý từ Patch 13.10: Nếu Lính đang đánh Trụ, chúng sẽ bỏ qua Ưu tiên số 1 - Call for help).*

**B. Logic Xử lý Trụ & Waypoint:**
- Nếu lọt vào các điều kiện từ 1 đến 7 -> Bám theo và đánh mục tiêu ưu tiên đó.
- Nếu KHÔNG lọt vào priority nào (hoặc đã tiêu diệt xong mục tiêu) -> Di chuyển theo Waypoint tới Trụ/Nhà lính tiếp theo. Gặp Trụ thì đánh Trụ cho sập mới đi tiếp.

**C. Python Pseudocode cho Lính (Minion AI Logic):**
```python
class Minion:
    def __init__(self):
        self.target = None
        self.waypoints = [...] # Danh sách tọa độ đường đi về Nexus địch
        self.acquisition_range = 500.0
        
    def update_logic(self, visible_enemies, allied_champions, enemy_structures):
        # 1. Quét kẻ địch trong tầm (Tướng, Lính, Pet)
        enemies_in_range =[e for e in visible_enemies if distance(self, e) <= self.acquisition_range]
        
        # 2. Lọc mục tiêu theo Bảng Ưu tiên (Priority 1 -> 7)
        priority_target = self.find_highest_priority_target(enemies_in_range, allied_champions)
        
        # Xử lý ngoại lệ Patch 13.10: 
        # Đang đánh Trụ thì phớt lờ Tướng địch đánh Tướng đồng minh (Call for Help - Priority 1)
        if self.target and self.target.is_structure():
            if priority_target and priority_target.reason == "Call_For_Help":
                priority_target = None # Bỏ qua ưu tiên 1, giữ nguyên target là Trụ
                
        # 3. Quyết định hành động
        if priority_target:
            # Rơi vào các trường hợp priority -> Đánh tiếp mục tiêu priority
            self.target = priority_target
            return self.move_and_attack(self.target)
        else:
            # Không rơi vào priority nào -> Tìm Công trình (Trụ/Nhà lính/Nexus) trên đường đi
            structure_in_path = self.find_nearest_structure(enemy_structures)
            
            if structure_in_path and distance(self, structure_in_path) <= self.attack_range:
                # Trụ trong tầm -> Đánh trụ
                self.target = structure_in_path
                return self.attack(self.target)
            else:
                # Không có gì trong tầm -> Đi tới trụ/waypoint tiếp theo
                self.target = None
                return self.move_along_waypoints()

    def find_highest_priority_target(self, enemies, allied_champions):
        """Hàm lọc mục tiêu tuân thủ tuyệt đối 7 bước Priority của LMHT"""
        # Nếu có nhiều mục tiêu cùng mức độ ưu tiên, trả về mục tiêu GẦN NHẤT
        pass
```

### 3.4 Pushing Advantage Buff (Buff Đẩy Đường Áp Đảo)
Hoạt động sau phút thứ `3:30` trên Summoner's Rift. Đội có Level trung bình cao hơn sẽ kích hoạt Buff này cho Lính.
- **Level_Advantage (Tối đa = 3):** Level trung bình đội nhà - Level trung bình đội địch.
- **Turret_Advantage:** Số trụ phá được ở lane đó (Phe nhà) - Số trụ phá được (Phe địch). (Không được nhỏ hơn 0).
- `Bonus_Damage_To_Enemy_Minions = (5% + (5% * Turret_Advantage)) * Level_Advantage` (Tối đa = +60% DMG)
- `Damage_Reduction_From_Enemy_Minions = 1 + (Turret_Advantage * Level_Advantage)` (Tối đa = Giảm 10 Sát thương).

### 3.5 Death Grace (Cơ chế Bất tử Tạm thời của Lính)
Khi lính dưới `<0.35%` Max HP và bị nhận sát thương chí mạng **từ một lính khác** (không phải Tướng), HP của lính đó được giữ lại ở mức `1 HP`.
- Tồn tại trong thời gian Delay là `0.066s`.
- Nếu trong `0.066s` này Tướng đánh vào, Tướng sẽ được tính là Last-hit. Nếu không, lính sẽ chết ngay sau khi delay kết thúc.
- Cơ chế này không hoạt động nếu sát thương của đòn kết liễu từ lính kia lớn hơn `190`.

---

## 4. EXPERIENCE LOGIC (THUẬT TOÁN KINH NGHIỆM TỪ LÍNH)
Khi Lính chết, kinh nghiệm (XP) sẽ được chia đều cho tất cả Tướng phe địch đứng trong bán kính `1500` đơn vị (tính từ vị trí Lính chết).
*(Áp dụng công thức EXP Share mới cập nhật từ bản V26.01)*

- Nếu có **1 Tướng** đứng gần: Tướng đó nhận `100%` XP.
- Nếu có **2 Tướng** đứng gần: Mỗi Tướng nhận `65%` XP (Tổng 130%).
- Nếu có **3 Tướng** đứng gần: Mỗi Tướng nhận `43.3%` XP (Tổng ~130%).
- Nếu có **4 Tướng** đứng gần: Mỗi Tướng nhận `32.5%` XP (Tổng 130%).
- Nếu có **5 Tướng** đứng gần: Mỗi Tướng nhận `26%` XP (Tổng 130%).

*(Lưu ý: Game khuyến khích đi chung (Shared XP) bằng cách tạo ra thêm 30% XP tổng (từ 100% lên 130%) so với việc solo).*

--- END OF FILE minion.md ---