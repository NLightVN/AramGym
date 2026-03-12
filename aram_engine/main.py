"""
main.py — WebSocket server entry point
Run: python -m aram_engine.main
"""
import asyncio
import json
import websockets
from .game import GameState, GameLoop

HOST = "localhost"
PORT = 8765


async def handler(websocket, gs: GameState, loop: GameLoop):
    """Handle a single client connection."""
    loop.clients.add(websocket)
    print(f"[+] Client connected — total: {len(loop.clients)}")

    # Assign champion UID to this client (first blue, next red)
    assigned_uid = _assign_champion(gs, loop)
    try:
        await websocket.send(json.dumps({
            "type": "init",
            "assigned_uid": assigned_uid,
            "map_size": 12800,
        }))

        async for raw in websocket:
            try:
                msg = json.loads(raw)
                uid = msg.get("uid", assigned_uid)
                action = msg.get("action", {})
                loop.enqueue_input(uid, action)
            except Exception as e:
                print(f"[!] Bad message: {e}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        loop.clients.discard(websocket)
        print(f"[-] Client disconnected — total: {len(loop.clients)}")


def _assign_champion(gs: GameState, loop: GameLoop) -> int:
    """Assign a champion UID sequentially — first client gets blue, second red."""
    used = set(getattr(loop, '_assigned_uids', set()))
    for uid, champ in gs.champions.items():
        if uid not in used:
            if not hasattr(loop, '_assigned_uids'):
                loop._assigned_uids = set()
            loop._assigned_uids.add(uid)
            return uid
    # Observer: return first champion
    return next(iter(gs.champions.keys()))


async def main():
    gs   = GameState()
    loop = GameLoop(gs)

    print(f"[ARAM Engine] Starting WebSocket server on ws://{HOST}:{PORT}")
    print("[ARAM Engine] Open client/raw/index.html or client/fancy/index.html in browser")

    async with websockets.serve(
        lambda ws: handler(ws, gs, loop),
        HOST, PORT,
        ping_interval=None,
    ):
        await loop.run()


if __name__ == "__main__":
    asyncio.run(main())
