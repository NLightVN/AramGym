# AramGym — Headless 1v1 ARAM Simulator Specification

> Môi trường giả lập **1v1 ARAM** headless để train RL agent.
> Scope: **1 champion vs 1 champion** trên Howling Abyss — không có jungle, không có 5v5.
> Item pool giới hạn **~20 items** được chọn lọc. Chạy nhanh, không phụ thuộc client Riot.

---

## Mục lục

1. [Map & Terrain](#1-map--terrain)
2. [Movement Speed](#2-movement-speed)
3. [Champion Stats](#3-champion-stats)
4. [Damage System](#4-damage-system)
5. [Item System (1v1 scope — ~20 items)](#5-item-system-1v1-scope--20-items)
6. [Minion AI](#6-minion-ai)
7. [Vision System](#7-vision-system)
8. [Unit Collision & Pathing](#8-unit-collision--pathing)
9. [Game Loop & Tick Rate](#9-game-loop--tick-rate)
10. [Data Sources](#10-data-sources)
11. [Trạng thái: Có sẵn vs Phải tự build](#11-trang-thai-co-san-vs-phai-tu-build)
12. [Thứ tự build khuyến nghị](#12-thu-tu-build-khuyen-nghi)
13. [ARAM Map — Tọa Độ Buildings](#13-aram-map--toa-do-buildings-map-12--howling-abyss)

---

## 1. Map & Terrain

### NavGrid — file đã được extract từ game

- File gốc: `.AIMESH_NGRID` (nằm trong game client)
- Grid size: **295 x 296 cells**
- Mỗi cell = **50 x 50 game units**
- Tổng map: ~14,750 x 14,800 units

### Cell flags

| Flag | Ý nghĩa |
|------|---------|
| `WALL` | Không đi qua được |
| `WALKABLE` | Đi được bình thường |
| `JUNGLE` | Đi được, vision layer riêng |
| `BRUSH` | Đi được, vision bị chặn |
| `TEAM_WALL` | Tường theo team (turret range...) |

### Công cụ extract

- Repo: `FrankTheBoxMonster/LoL-NGRID-converter`
- Output: bitmap 2D, mỗi pixel = 1 cell
- Dùng trực tiếp làm boolean grid trong Python:

```python
# navgrid[x][y] = True (walkable) / False (wall)
from PIL import Image
import numpy as np

def load_navgrid(path: str) -> np.ndarray:
    img = Image.open(path).convert("L")
    arr = np.array(img)
    return arr > 128  # True = walkable
```

### Coordinate system

```
(0, 0)           = góc dưới trái (Blue base)
(14750, 14800)   = góc trên phải (Red base)
Đơn vị: game units
1 cell = 50 units
```

---

## 2. Movement Speed

### Physics model — QUAN TRỌNG

- **Không có acceleration** — bắt đầu di chuyển là đạt ngay tốc độ đầy đủ
- **Không có momentum** — dừng lại là dừng ngay
- **Không có inertia, không có easing**
- 1 điểm MS = **1 game unit / giây**
- Model: **kinematic thuần** — chỉ cần vector math

### Công thức tính MS

```
MS_final = (BaseMS + FlatBonus)
         x (1 + Sum(%bonuses))
         x (1 - HighestSlow)
         x Product(MultiplicativeBonus)
```

Sau đó apply **soft cap**:

| Raw MS | Kết quả |
|--------|---------|
| < 220 | floor = 220 |
| 220 – 414 | Giữ nguyên |
| 415 – 490 | 415 + (raw - 415) x 0.8 |
| > 490 | 415 + 75x0.8 + (raw - 490) x 0.5 |

### Implement

```python
def calculate_ms(unit) -> float:
    raw = (unit.base_ms + unit.flat_ms_bonus)
    raw *= (1 + sum(unit.pct_ms_bonuses))
    raw *= (1 - unit.highest_slow)
    for m in unit.multiplicative_bonuses:
        raw *= m
    # Soft cap
    if raw < 220:   return 220.0
    elif raw < 415: return raw
    elif raw < 490: return 415 + (raw - 415) * 0.8
    else:           return 415 + 60 + (raw - 490) * 0.5

def update_position(unit, dt: float):
    if not unit.move_target:
        return
    ms = calculate_ms(unit)
    direction = normalize(unit.move_target - unit.pos)
    delta = direction * ms * dt
    dist = distance(unit.pos, unit.move_target)
    if length(delta) >= dist:
        unit.pos = unit.move_target   # snap đến đích, không overshoot
        unit.move_target = None
    else:
        unit.pos += delta             # thẳng, không easing
```

### Pathfinding

- Thuật toán: **A*** trên NavGrid
- Recalculate mỗi khi nhận lệnh di chuyển mới
- Unit khác là obstacle (trừ khi ghosted)
- Output: list waypoints, đi lần lượt

---

## 3. Champion Stats

### Công thức stat theo level

```
Stat(level) = base + growth x (level - 1) x (0.7025 + 0.0175 x (level - 1))
```

Hệ số nhân growth theo level:

| Level | Hệ số |
|-------|-------|
| 1 | 0% |
| 2 | 72% |
| 6 | 85% |
| 9 | 97% |
| 10 | 100% |
| 13 | 114% |
| 18 | 128% |

### Các stats cần implement

| Stat | Ghi chú |
|------|---------|
| `base_hp` + `hp_growth` | HP tối đa |
| `base_mana` + `mana_growth` | Mana / Energy / không có |
| `base_ad` + `ad_growth` | Attack Damage |
| `base_armor` + `armor_growth` | Giáp |
| `base_mr` + `mr_growth` | Magic Resist |
| `base_ms` | Movement Speed — KHÔNG có growth |
| `base_hp_regen` + `regen_growth` | HP hồi / 5 giây |
| `attack_range` | Range auto attack |
| `base_as` + `as_ratio` | Tốc đánh |

### Riot Data Dragon — lấy stats tự động

```python
import requests

def get_champion_stats(name: str, version="14.1.1") -> dict:
    url = (f"https://ddragon.leagueoflegends.com/cdn/"
           f"{version}/data/en_US/champion/{name}.json")
    data = requests.get(url).json()
    return data["data"][name]["stats"]

def get_latest_version() -> str:
    versions = requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json"
    ).json()
    return versions[0]
```

---

## 4. Damage System

### Physical Damage

```
effective_armor = armor
    - flat_armor_reduction          # step 1
    x (1 - pct_armor_reduction)    # step 2
    - flat_armor_pen                # step 3
    x (1 - pct_armor_pen)          # step 4
    (min = 0)

dmg_dealt = raw_dmg x 100 / (100 + effective_armor)
```

### Magic Damage

```
effective_mr = mr (tương tự armor, với MR pen)
dmg_dealt    = raw_dmg x 100 / (100 + effective_mr)
```

### True Damage

```
dmg_dealt = raw_dmg  (không bị giảm bởi bất kỳ thứ gì)
```

### DPS Formula (Auto Attack)

```
DPS = (AD x crit_dmg x crit_chance + AD x (1 - crit_chance))
    x (100 / (100 + effective_armor))
    x attack_speed
```

- `crit_dmg` mặc định = **1.75** (175%)
- AS hard cap = **2.5**

### Shields

- Hấp thụ damage trước HP
- Physical shield: chỉ block physical damage
- Omnishield: block tất cả loại damage
- Multiple shields: consume theo FIFO (thêm trước xài trước)

```python
def apply_damage(unit, dmg: float, dmg_type: str):
    # Shields đầu tiên
    remaining = dmg
    for shield in unit.shields:
        if shield.type == "omnishield" or shield.type == dmg_type:
            absorbed = min(shield.hp, remaining)
            shield.hp -= absorbed
            remaining -= absorbed
            if shield.hp <= 0:
                unit.shields.remove(shield)
        if remaining <= 0:
            return
    # Sau đó HP
    unit.hp = max(0, unit.hp - remaining)
```

---

## 5. Minion AI

### Nguồn: Riot Reinboom — Dev Corner post chính thức

### Behavior Sweep — tick mỗi 0.25 giây

Chạy checklist theo thứ tự, thực hiện hành động **đầu tiên hợp lệ** rồi dừng:

```
1. Follow CC hiện tại (Taunt, Fear, Flee)
2. Tiếp tục attack/chase target hiện tại (nếu còn valid)
3. Nếu fail attack target >= 4 giây -> IGNORE target đó tạm thời
4. Tìm target mới theo "path ease" (không phải gần nhất)
5. Nếu gần waypoint ke tiep -> advance waypoint
6. DEFAULT: đi về waypoint kế tiếp
```

### Target Priority

```
Priority 1: Enemy CHAMP  đang attack ALLY CHAMP
Priority 2: Enemy MINION đang attack ALLY CHAMP
Priority 3: Enemy MINION đang attack ALLY MINION
Priority 4: Enemy TURRET đang attack ALLY MINION
Priority 5: Enemy CHAMP  đang attack ALLY MINION
Priority 6: Closest enemy MINION
Priority 7: Closest enemy CHAMP
```

**Path ease**: khi nhiều target cùng priority, ưu tiên target **dễ path tới nhất** (ít obstacle), không phải target gần nhất.

### Aggro Trigger (Call for Help)

| Hành động | Trigger aggro? |
|-----------|---------------|
| Auto attack vào lính địch | Có |
| Targeted spell vào lính địch | Có |
| Skillshot (Yasuo Q, Ezreal Q...) | Không |
| Bước vào vùng lính | Không |

### Acquisition Range

```python
ACQUIRE_RANGE_NORMAL = 500   # bình thường
ACQUIRE_RANGE_ALLY   = 1000  # khi ally đang bị tấn công
```

### Drop Aggro — 2 điều kiện

```python
def should_drop_aggro(minion, target) -> bool:
    return (
        not minion.has_vision(target)        # mất vision (vào brush)
        or distance(minion.pos, target.pos) > 500
    )
```

### Ignored State — cơ chế quan trọng

Fail attack target trong 4 giây lien tiep -> ignore target do.

Ignored state bi XOA khi:
1. Call for Help (target tan cong lai ai do)
2. Collision voi unit khac
3. Target chet
4. CC tac dong len minion

**Ví dụ thực tế**: Bạn dẫn lính vào jungle -> lính đuổi -> fail reach 4 giây -> ignore bạn -> về lane. Bạn quay lại range -> lính KHÔNG re-aggro vì vẫn trong ignored state. Chỉ reset nếu bạn auto attack lại (Call for Help).

### Full State Machine

```
[WALKING LANE WAYPOINTS]
        |
        | enemy vào range + điều kiện met
        v
[CHASING / ATTACKING] <--------------------------+
        |                                        |
        | mất vision / > 500 units               | Call for Help
        v                                        | (auto/targeted spell)
[DROP AGGRO -> về waypoint]                      |
        |                                        |
        | fail attack 4 giây                     |
        v                                        |
[IGNORE TARGET] ---------------------------------+
        |
        | collision / target chết / CC
        v
[REEVALUATE -> chọn target mới theo priority]
```

### Implement đầy đủ

```python
class Minion:
    SWEEP_TICK    = 0.25
    IGNORE_SECS   = 4.0
    ACQUIRE_RANGE = 500
    ACQUIRE_ALLY  = 1000

    def __init__(self, team, lane):
        self.team         = team
        self.lane         = lane
        self.waypoint_idx = 0
        self.target       = None
        self.ignored      = set()   # set of unit ids
        self.fail_timer   = 0.0
        self.sweep_timer  = 0.0

    def update(self, dt, game_state):
        self.sweep_timer += dt
        if self.sweep_timer >= self.SWEEP_TICK:
            self.sweep_timer = 0.0
            self.behavior_sweep(game_state)
        self.move_step(dt)

    def behavior_sweep(self, gs):
        # 1. CC
        if self.has_cc():
            return self.follow_cc()
        # 2. Current target
        if self.target:
            if not self.is_valid_target(self.target):
                self.target = None
            elif self.target.id in self.ignored:
                self.target = None
            else:
                if not self.in_attack_range(self.target):
                    self.fail_timer += self.SWEEP_TICK
                    if self.fail_timer >= self.IGNORE_SECS:
                        self.ignored.add(self.target.id)
                        self.target = None
                        self.fail_timer = 0.0
                else:
                    self.fail_timer = 0.0
                    return self.attack(self.target)
        # 3. Find new target
        new = self.find_target_by_priority(gs)
        if new:
            self.target = new
            self.fail_timer = 0.0
            return self.attack_or_chase(new)
        # 4. Waypoint
        wp = self.waypoints[self.waypoint_idx]
        if distance(self.pos, wp) < 50 and self.waypoint_idx + 1 < len(self.waypoints):
            self.waypoint_idx += 1
        self.move_toward(self.waypoints[self.waypoint_idx])

    def on_call_for_help(self, attacker_id):
        self.ignored.discard(attacker_id)
        self.behavior_sweep(None)

    def on_collision(self):
        self.behavior_sweep(None)

    def on_target_died(self):
        self.target = None
        self.behavior_sweep(None)
```

### Minion Stats

```python
MINION_STATS = {
    "melee": {
        "base_hp": 478, "hp_growth_per_min": 22,
        "base_ad": 21,  "ad_growth_per_min": 1.5,
        "base_ms": 325, "armor": 0, "mr": 0,
        "attack_range": 110, "attack_speed": 0.625,
    },
    "caster": {
        "base_hp": 280, "hp_growth_per_min": 15,
        "base_ad": 24,  "ad_growth_per_min": 1.5,
        "base_ms": 325, "armor": 0, "mr": 0,
        "attack_range": 550, "attack_speed": 0.625,
    },
    "cannon": {
        "base_hp": 1100, "hp_growth_per_min": 35,
        "base_ad": 40,   "ad_growth_per_min": 3,
        "base_ms": 325,  "armor": 30, "mr": 0,
        "attack_range": 700, "attack_speed": 0.625,
    }
}

# MS bonus theo thời gian (phút)
MS_BONUS_BY_MINUTE = {20: 25, 25: 50, 30: 75, 35: 100}

# Timing
WAVE_INTERVAL_SECS  = 30   # spawn mỗi 30 giây
CANNON_EVERY_N_WAVE = 3    # cannon mỗi 3 waves (90 giây)
FIRST_WAVE_AT       = 65   # giây đầu tiên
```

### Minion Waypoints (Summoner's Rift — approximate)

```python
WAYPOINTS = {
    "blue_top": [
        (400, 1200), (600, 3000), (800, 7000),
        (1200, 10000), (1500, 13500)
    ],
    "blue_mid": [
        (1200, 1200), (3500, 3500), (7000, 7000),
        (10500, 10500), (13500, 13500)
    ],
    "blue_bot": [
        (1200, 400), (3000, 600), (7000, 800),
        (10000, 1200), (13500, 1500)
    ],
    # Red team: reverse order của blue
}
```

---

## 6. Jungle Monster AI

### Khác biệt chính so với Minion

| | Minion | Jungle Monster |
|--|--------|---------------|
| Leash range | Không có | Có (~1200 units) |
| Waypoint | Đi theo lane | Đứng tại camp |
| Soft reset | Không | Có (6 giây, 6% HP/giây) |
| Respawn | Không | Có (timer tùy camp) |

### Thông số

```python
JUNGLE_CONSTANTS = {
    "default_leash_range": 1200,
    "patience_max":        5,      # ticks trước khi soft reset
    "soft_reset_secs":     6,
    "hp_regen_pct":        0.06,   # 6% HP/giây khi soft resetting
}

CAMP_LEASH = {
    "baron":   None,   # không có leash
    "dragon":  800,
    "herald":  1200,
    "wolves":  1000,
    "raptors": 1000,
    "gromp":   900,
    "blue":    1100,
    "red":     1100,
    "krugs":   900,
}
```

### Soft Reset State Machine

```
[IDLE tại camp]
        |
        | champion vào range và tấn công
        v
[CHASING / ATTACKING]
        |
        | target vượt leash_range
        v
[PATIENCE DRAINING]
        |
        | patience = 0
        v
[SOFT RESETTING]
  -> về camp position
  -> hồi 6% HP/giây
  -> ignore mọi attacker ngoài leash range
        |
        | bị tấn công lại TRONG leash range
        v
[CANCEL SOFT RESET -> CHASING lại]
```

### Implement

```python
class JungleMonster:
    def __init__(self, monster_type, camp_pos):
        self.camp_pos    = camp_pos.copy()
        self.pos         = camp_pos.copy()
        self.target      = None
        self.patience    = JUNGLE_CONSTANTS["patience_max"]
        self.soft_reset  = False
        self.leash_range = CAMP_LEASH.get(monster_type, 1200)

    def update(self, dt):
        if self.soft_reset:
            self._update_soft_reset(dt)
            return
        if self.target:
            dist_from_camp = distance(self.pos, self.camp_pos)
            if self.leash_range and dist_from_camp > self.leash_range:
                self.patience -= 1
                if self.patience <= 0:
                    self._begin_soft_reset()
            else:
                self.patience = JUNGLE_CONSTANTS["patience_max"]
                self.attack_or_chase(self.target)

    def _begin_soft_reset(self):
        self.soft_reset = True
        self.target = None

    def _update_soft_reset(self, dt):
        regen = self.max_hp * JUNGLE_CONSTANTS["hp_regen_pct"] * dt
        self.hp = min(self.max_hp, self.hp + regen)
        self.move_toward(self.camp_pos)
        if distance(self.pos, self.camp_pos) < 10:
            self.soft_reset = False
            self.patience = JUNGLE_CONSTANTS["patience_max"]

    def on_attacked(self, attacker):
        if self.soft_reset:
            if not self.leash_range or distance(self.pos, self.camp_pos) <= self.leash_range:
                self.soft_reset = False
                self.target = attacker
        else:
            self.target = attacker
```

---

## 7. Vision System

### Fog of War cơ bản

- Mỗi unit có `vision_range`
- Chỉ thấy enemy unit nằm trong range của **bất kỳ ally unit nào**
- **Brush rule**: unit trong brush không thể bị nhìn thấy từ ngoài brush, trừ khi observer cũng trong cùng brush cluster

### Vision Range defaults

```python
VISION_RANGES = {
    "champion":     1100,
    "minion":        900,
    "turret":        900,
    "ward":         1100,   # Stealth Ward
    "control_ward":  900,
    "zombie_ward":   900,
}
```

### Implement

```python
def is_visible(observer_team, target_unit, gs) -> bool:
    for unit in gs.get_units(observer_team):
        d = distance(unit.pos, target_unit.pos)
        if d > unit.vision_range:
            continue
        # Brush check
        target_in_brush = in_brush(target_unit.pos, gs.navgrid)
        if not target_in_brush:
            return True
        observer_in_brush = in_brush(unit.pos, gs.navgrid)
        if observer_in_brush:
            if same_brush_cluster(unit.pos, target_unit.pos, gs):
                return True
    return False

def in_brush(pos, navgrid) -> bool:
    cx, cy = int(pos.x // 50), int(pos.y // 50)
    return navgrid[cx][cy].flag == "BRUSH"
```

---

## 8. Unit Collision & Pathing

### Pathing Radius

```python
PATHING_RADII = {
    "champion": 65,
    "minion":   25,
    "monster":  50,
    "turret":   0,   # không có collision
}
```

- Tâm 2 unit không được gần hơn `r1 + r2`
- **Ghosted** unit: bỏ qua unit-to-unit collision (vẫn bị wall collision)

### Minion Block

- Champion đứng vào đường đi của lính -> lính bị chặn hoặc đi vòng
- **Riot giữ mechanic này** vì wave manipulation là skill test quan trọng
- Không nên bỏ đi trong simulator — AI cần học mechanic này

### Collision Avoidance (Minion)

```python
def separation_force(minion, neighbors) -> Vec2:
    force = Vec2(0, 0)
    for n in neighbors:
        diff = minion.pos - n.pos
        dist = length(diff)
        min_dist = minion.pathing_radius + n.pathing_radius
        if dist < min_dist * 2:
            force += normalize(diff) * (min_dist / max(dist, 0.1))
    return force * 50.0
```

---

## 9. Game Loop & Tick Rate

### Tick rate

| Hệ thống | Tick rate |
|----------|----------|
| Game server (LOL thật) | 30 Hz (33ms) |
| Minion behavior sweep | 4 Hz (250ms) |
| Vision update | 4 Hz |
| Stat recalculation | On-change |

### Simulator — chạy nhanh nhất có thể

```python
SIMULATION_HZ = 30
TICK_DT       = 1.0 / SIMULATION_HZ  # 0.0333s

class GameLoop:
    def __init__(self, config):
        self.tick    = 0
        self.time    = 0.0
        self.running = True
        self.units   = {"blue": [], "red": []}

    def run_headless(self, max_seconds=None):
        """Chạy không có sleep() -> nhanh nhất có thể"""
        max_ticks = int(max_seconds * SIMULATION_HZ) if max_seconds else None
        while self.running:
            self._update(TICK_DT)
            self.tick += 1
            self.time += TICK_DT
            if max_ticks and self.tick >= max_ticks:
                break

    def _update(self, dt):
        self._spawn_waves()
        self._update_buffs(dt)
        self._update_movement(dt)
        self._process_attacks(dt)
        self._update_projectiles(dt)
        self._check_deaths()
        self._update_vision()
        self._check_win_condition()
```

### Thứ tự xử lý mỗi tick (quan trọng)

```
1.  Nhận input (actions từ champions / AI)
2.  Spawn units (waves, jungle respawn)
3.  Update CC / buff durations
4.  Update movement (tất cả unit di chuyển)
5.  Process attacks & damage
6.  Update projectiles (skillshots bay)
7.  Check deaths & cleanup
8.  Update vision / fog of war
9.  Emit observations (game state snapshot)
```

---

## 10. Data Sources

| Dữ liệu | Nguồn | Cách lấy |
|---------|-------|---------|
| Champion stats (base + growth) | Riot Data Dragon | HTTP GET JSON |
| NavGrid terrain 295x296 | `FrankTheBoxMonster/LoL-NGRID-converter` | Extract từ game |
| Minion AI rules | Riot Reinboom Dev Corner (official) | Đã document |
| Minion waypoints | Community maps | GitHub / Wiki |
| Damage formulas | LoL Wiki | Đã document |
| MS formula + soft cap | LoL Wiki | Đã document |
| Ability data (CD, cost, range) | Data Dragon + LoL Wiki | JSON + manual |
| Item stats | Data Dragon | HTTP GET JSON |
| Jungle camp stats | LoL Wiki | Manual |

### Riot Data Dragon endpoints

```
# Latest patch version
GET https://ddragon.leagueoflegends.com/api/versions.json

# Tất cả champion
GET https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json

# Chi tiết 1 champion (stats đầy đủ)
GET https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{Name}.json

# Tất cả items
GET https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json
```

---

## 11. Trạng thái: Có sẵn vs Phải tự build

### Đã có — không cần nghiên cứu thêm

| Phần | Nguồn |
|------|-------|
| Champion base stats + growth tất cả champion | Riot Data Dragon |
| Công thức stat per level | LoL Wiki |
| Công thức damage / armor reduction / MR | LoL Wiki |
| Công thức MS + soft cap đầy đủ | LoL Wiki |
| Physics model (kinematic, không acceleration) | LoL Wiki |
| NavGrid terrain 295x296 | NGRID converter |
| Minion AI rules (Riot official document) | Riot Reinboom post |
| Minion stats + growth per minute | LoL Wiki |
| Minion waypoints Summoner's Rift | Community |
| Jungle leash range + soft reset logic | LoL Wiki |
| Unit pathing radius | LoL Wiki |
| Vision range defaults | LoL Wiki |
| Item stats | Data Dragon |

### Phải tự build

| Phần | Độ khó | Ghi chú |
|------|--------|---------|
| Python headless engine core | 3/5 | Game loop, entity system, Vec2 |
| A* pathfinding trên NavGrid | 2/5 | Thư viện `pathfinding` có sẵn |
| Skillshot hitbox (line/cone/circle) | 4/5 | Geometry từng loại khác nhau |
| Brush cluster detection | 3/5 | Flood fill trên NavGrid |
| Fog of War headless | 3/5 | Có thể dùng simplified |
| Ability scripting per champion | 4/5 | Mỗi champ có unique logic |
| Turret AI + aggro | 2/5 | Đơn giản hơn minion nhiều |
| Parallel env runner | 2/5 | Python multiprocessing / asyncio |
| State serializer / replay | 2/5 | JSON dump per tick |

### Có skeleton, cần hoàn thiện

| Phần | Nguồn | Tình trạng |
|------|-------|-----------|
| Gymnasium interface | `lolgym` / `pylol` | Incomplete |
| C# game server | `LeagueSandbox` | Đầy đủ nhưng không headless |
| Champion ability scripts | `LeagueSandbox` (Lua) | Port sang Python cần effort |

---

## 12. Thứ tự build khuyến nghị

```
Phase 1 — Core Engine
  [ ] Vec2 math utilities (add, sub, normalize, length, distance)
  [ ] NavGrid loader (bitmap -> 2D numpy array)
  [ ] Entity base class (id, pos, hp, team, stats)
  [ ] Champion class + stat calculator (level, items)
  [ ] Movement system (calculate_ms, update_position, A*)
  [ ] Game loop (tick, time, headless run)

Phase 2 — Combat cơ bản
  [ ] Auto attack system (windup timer, projectile, hit)
  [ ] Damage calculator (physical / magic / true + shields)
  [ ] Death & respawn logic
  [ ] Turret class (aggro: champ > minion, attack turret first)

Phase 3 — Minion System
  [ ] Minion class + behavior sweep AI (full state machine)
  [ ] Minion wave spawner (timing, cannon rotation)
  [ ] Minion waypoints (top / mid / bot, cả 2 team)
  [ ] Minion stats + scaling per minute

Phase 4 — Jungle
  [ ] Jungle monster class + soft reset state machine
  [ ] Camp spawn positions + respawn timers
  [ ] Leash range per camp

Phase 5 — Map Systems
  [ ] Vision / fog of war
  [ ] Brush cluster detection (flood fill)
  [ ] Inhibitor logic (super minion spawn)
  [ ] Nexus + win condition

Phase 6 — Champion Abilities
  [ ] Skillshot geometry (line, cone, circle, targeted)
  [ ] CC system (stun, slow, knockup, silence)
  [ ] Buff / debuff system (duration, stacks)
  [ ] Yasuo abilities (Q line/tornado, W wall, E dash, R)
  [ ] Thêm champion khác dần dần

Phase 7 — Polish
  [ ] State serializer (JSON snapshot per tick)
  [ ] Replay system
  [ ] Parallel env runner (multiprocessing)
  [ ] Unit tests cho từng hệ thống
```

---

## 13. ARAM Map — Tọa Độ Buildings (Map 12 — Howling Abyss)

> **Chi tiết thông số Game, Tọa độ Buildings, Spawn Points, Minion Waypoints của ARAM (Map 12)**
> 👉 Xem file **[`gamestats.md`](./gamestats.md)**

