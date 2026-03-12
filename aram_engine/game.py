"""
game.py — GameState, GameLoop (30 Hz), input processing
"""
import asyncio
import json
from .constants import (
    TURRET_DATA, INHIBITOR_DATA, NEXUS_DATA,
    SPAWN_POINTS, BARRACKS, SIMULATION_HZ, TICK_DT,
)
from .entities.champion import Champion
from .entities.minion import Minion, WaveSpawner
from .entities.turret import Turret
from .entities.projectile import Projectile, WindWall
from .physics import resolve_collisions
from .damage import kill_gold, assist_gold, kill_xp
from .abilities import yasuo as yasuo_abilities


class GameState:
    """Holds all entities and provides query helpers."""

    def __init__(self):
        # Champions (one per team for 1v1)
        self.champions = {}          # uid → Champion
        self.minions   = []          # list of Minion
        self.turrets   = {}          # tid → Turret
        self.inhibitors = {}         # iid → dict (simplified)
        self.projectiles = []        # list of Projectile
        self.wind_walls  = []        # list of WindWall

        self.game_time   = 0.0
        self.first_blood = True      # flag for next kill

        # Kill feed log
        self.kill_feed   = []        # list of {"t": float, "killer": str, "victim": str}

        # Deferred actions
        self._unghost_queue = []     # [(uid, delay)]
        self._dead_units    = []     # units that died this tick (process after loop)

        self._init_entities()

    def _init_entities(self):
        # Turrets
        for tid, data in TURRET_DATA.items():
            self.turrets[tid] = Turret(tid, data)

        # Champions (1v1 ARAM)
        blue_champ = Champion("blue", "yasuo", level=1,
                              start_pos=SPAWN_POINTS["blue"])
        red_champ  = Champion("red",  "yasuo", level=1,
                              start_pos=SPAWN_POINTS["red"])
        # Give each champ level 1 abilities
        for c in (blue_champ, red_champ):
            c.q_level = 1; c.w_level = 1
            c.e_level = 1; c.r_level = 1

        self.champions[blue_champ.uid] = blue_champ
        self.champions[red_champ.uid]  = red_champ

        self.wave_spawner = WaveSpawner()

    # ── Query helpers ────────────────────────────────────────────
    def get_enemies(self, team: str) -> list:
        other = "red" if team == "blue" else "blue"
        result = []
        for c in self.champions.values():
            if c.team == other and c.alive: result.append(c)
        for m in self.minions:
            if m.team == other and m.alive:  result.append(m)
        for t in self.turrets.values():
            if t.team == other and t.alive:  result.append(t)
        return result

    def get_allies(self, team: str) -> list:
        result = []
        for c in self.champions.values():
            if c.team == team and c.alive: result.append(c)
        for m in self.minions:
            if m.team == team and m.alive:  result.append(m)
        return result

    def get_all_units(self) -> list:
        units = []
        units += [c for c in self.champions.values() if c.alive]
        units += [m for m in self.minions if m.alive]
        return units

    def barracks_pos(self, team: str) -> tuple:
        return BARRACKS[team]

    def schedule_unghost(self, uid: int, delay: float):
        self._unghost_queue.append([uid, delay])

    # ── Serialisation ────────────────────────────────────────────
    def snapshot(self) -> dict:
        champ_list = [c.to_dict() for c in self.champions.values()]
        minion_list = [m.to_dict() for m in self.minions if m.alive]
        turret_list = [t.to_dict() for t in self.turrets.values()]
        proj_list   = [p.to_dict() for p in self.projectiles]
        ww_list     = [w.to_dict() for w in self.wind_walls]

        return {
            "t":           round(self.game_time, 2),
            "champions":   champ_list,
            "minions":     minion_list,
            "turrets":     turret_list,
            "projectiles": proj_list,
            "wind_walls":  ww_list,
            "kill_feed":   self.kill_feed[-5:],   # last 5 kills
        }


class GameLoop:
    """30 Hz headless loop that broadcasts state via WebSocket."""

    def __init__(self, gs: GameState):
        self.gs        = gs
        self.running   = False
        self.clients   = set()      # connected WebSocket clients
        self._input_queue = []      # (uid, action_dict)

    # ── Input from clients ───────────────────────────────────────
    def enqueue_input(self, champ_uid: int, action: dict):
        self._input_queue.append((champ_uid, action))

    def _process_inputs(self):
        for uid, action in self._input_queue:
            champ = self.gs.champions.get(uid)
            if not champ or not champ.alive:
                continue
            atype = action.get("type")
            world = action.get("world", [0, 0])
            world = (world[0], world[1])

            if atype == "move":
                champ.move_target = world

            elif atype == "Q":
                yasuo_abilities.cast_q(champ, world, self.gs)

            elif atype == "W":
                yasuo_abilities.cast_w(champ, world, self.gs)

            elif atype == "E":
                # Find closest enemy alive in E range
                target = _closest_enemy_in_range(champ, self.gs, 700)
                if target:
                    yasuo_abilities.cast_e(champ, target, self.gs)

            elif atype == "R":
                # Find closest airborne enemy
                target = _closest_airborne_enemy(champ, self.gs)
                if target:
                    yasuo_abilities.cast_r(champ, target, self.gs)

            elif atype == "D":
                yasuo_abilities.cast_flash_yasuo(champ, world, self.gs)

        self._input_queue.clear()

    # ── Main update ──────────────────────────────────────────────
    def _update(self):
        gs = self.gs
        dt = TICK_DT

        # 1. Process player inputs
        self._process_inputs()

        # 2. Spawn minion waves
        new_minions = gs.wave_spawner.update(gs.game_time, gs)
        gs.minions.extend(new_minions)

        # 3. Update champions
        for champ in gs.champions.values():
            champ.update(dt)

        # 4. Update minions (AI + movement)
        for m in gs.minions:
            m.update(dt, gs)

        # 5. Update turrets (aggro + attack)
        for tid, turret in gs.turrets.items():
            team   = turret.team
            allys  = [c for c in gs.champions.values() if c.team == team and c.alive]
            allys += [m for m in gs.minions       if m.team == team and m.alive]
            enemys = gs.get_enemies(team)
            turret.update(dt, allys, enemys)

        # 6. Update projectiles
        for proj in gs.projectiles:
            proj.update(dt)
            enemies = [u for u in gs.get_all_units() if u.team != proj.team]
            hits = proj.check_hit(enemies, gs.wind_walls)
            for h in hits:
                proj.dmg_fn(h)
                if h.hp <= 0 and hasattr(h, 'on_death'):
                    h.on_death(gs.game_time)
                    _handle_kill(gs, proj.owner_uid, h)
                if proj.knockup > 0:
                    h.apply_cc("airborne", proj.knockup)

        # 7. Update wind walls
        for ww in gs.wind_walls:
            ww.update(dt)

        # 8. Collision resolution
        all_units = gs.get_all_units()
        resolve_collisions(all_units)

        # 9. Unghost queue
        still_pending = []
        for entry in gs._unghost_queue:
            entry[1] -= dt
            if entry[1] <= 0:
                c = gs.champions.get(entry[0])
                if c: c.ghosted = False
            else:
                still_pending.append(entry)
        gs._unghost_queue = still_pending

        # 10. Cleanup dead entities
        gs.projectiles = [p for p in gs.projectiles if not p.dead]
        gs.wind_walls  = [w for w in gs.wind_walls  if not w.dead]
        gs.minions     = [m for m in gs.minions      if m.alive]

        # 11. Advance time
        gs.game_time += dt

    # ── Async runner ─────────────────────────────────────────────
    async def run(self):
        self.running = True
        interval = TICK_DT
        while self.running:
            t_start = asyncio.get_event_loop().time()
            self._update()
            # Broadcast snapshot to all clients
            if self.clients:
                snap = json.dumps(self.gs.snapshot())
                await asyncio.gather(
                    *[_safe_send(ws, snap) for ws in self.clients],
                    return_exceptions=True
                )
            # Sleep remainder of tick
            elapsed = asyncio.get_event_loop().time() - t_start
            await asyncio.sleep(max(0.0, interval - elapsed))


# ── Helpers ─────────────────────────────────────────────────────
def _closest_enemy_in_range(champ, gs, max_range: float):
    from .physics import vec_dist
    best, best_d = None, max_range
    for e in gs.get_enemies(champ.team):
        d = vec_dist(champ.pos, e.pos)
        if d < best_d:
            best_d = d; best = e
    return best


def _closest_airborne_enemy(champ, gs):
    from .physics import vec_dist
    best, best_d = None, float("inf")
    for e in gs.get_enemies(champ.team):
        if not e.is_airborne: continue
        if vec_dist(champ.pos, e.pos) > 1200: continue
        d = vec_dist(champ.pos, e.pos)
        if d < best_d:
            best_d = d; best = e
    return best


def _handle_kill(gs: GameState, killer_uid: int, victim):
    first_blood = gs.first_blood
    gs.first_blood = False

    killer = gs.champions.get(killer_uid)
    gold   = kill_gold(victim, first_blood)
    if killer:
        killer.gold += gold
        killer.on_kill()
        killer.kills += 1
        gs.kill_feed.append({
            "t":      round(gs.game_time, 1),
            "killer": f"{killer.team.upper()}",
            "victim": getattr(victim, 'team', '?').upper()
        })
    if hasattr(victim, 'deaths'):
        victim.deaths += 1


async def _safe_send(ws, msg: str):
    try:
        await ws.send(msg)
    except Exception:
        pass
