"""Save slots: JSON files under saves/. Only chunks that differ from generation are stored
(zlib + base64); tile / wall name tables let old saves survive registry reordering."""
import base64
import json
import os
import time
import zlib

from settings import SAVE_DIR, SAVE_SLOTS, VERSION
from tiles import TILES, T, WALLS, W

FORMAT = 1


def slot_path(slot):
    return os.path.join(SAVE_DIR, f"slot{slot + 1}.json")


def _pack(data):
    return base64.b64encode(zlib.compress(bytes(data), 6)).decode("ascii")


def _unpack(text, table=None):
    raw = bytearray(zlib.decompress(base64.b64decode(text)))
    if table:
        raw = bytearray(table[b] for b in raw)
    return raw


def list_slots():
    """Metadata for each slot (None when empty or unreadable)."""
    out = []
    for slot in range(SAVE_SLOTS):
        try:
            with open(slot_path(slot), encoding="utf-8") as f:
                out.append(json.load(f)["meta"])
        except (OSError, ValueError, KeyError):
            out.append(None)
    return out


def delete_slot(slot):
    try:
        os.remove(slot_path(slot))
    except OSError:
        pass


def save_game(game):
    world = game.world
    p = game.player
    os.makedirs(SAVE_DIR, exist_ok=True)
    chunks = {}
    for key in world.modified:
        if key in world.chunks:
            chunks[f"{key[0]},{key[1]}"] = [_pack(world.chunks[key]), _pack(world.walls[key]),
                                            _pack(world.liquid[key])]
    for key, (tiles, walls, liq) in world.saved_chunks.items():
        chunks[f"{key[0]},{key[1]}"] = [_pack(tiles), _pack(walls), _pack(liq)]
    explored = sorted(set(world.chunks) | world.explored)
    game.playtime += time.time() - game.session_start
    game.session_start = time.time()
    data = {
        "meta": {"name": game.world_name, "seed": world.seed, "version": VERSION,
                 "created": game.created, "saved": time.strftime("%Y-%m-%d %H:%M"),
                 "playtime": int(game.playtime), "day": game.day_count,
                 "bosses": [k for k in ("eye", "king_slime") if world.flags.get(f"{k}_defeated")]},
        "format": FORMAT,
        "tile_names": [t.name for t in TILES],
        "wall_names": [w.name for w in WALLS],
        "world": {
            "chunks": chunks,
            "explored": [list(k) for k in explored],
            "objects": [[ax, ay, TILES[tid].name] for (ax, ay), tid in world.objects.items()],
            "containers": [[ax, ay, slots] for (ax, ay), slots in world.containers.items()],
            "flags": world.flags,
            "pending_npcs": [list(n) for n in world.pending_npcs],
            "locked": [list(a) for a in world.locked],
            "furnaces": [[ax, ay, state] for (ax, ay), state in world.furnaces.items()],
        },
        "player": {
            "x": p.x, "y": p.y, "hp": p.hp, "max_hp": p.max_hp, "mana": p.mana,
            "base_max_mana": p.base_max_mana, "inventory": p.inventory.slots, "equip": p.equip,
            "spawn_point": list(p.spawn_point) if p.spawn_point else None,
            "cards": p.cards, "journal": sorted(p.journal),
        },
        "quests": {"active": game.quests.active, "offers": game.quests.offers,
                   "completed": game.quests.completed},
        "npcs": [{"kind": n.kind, "x": n.x, "y": n.y, "home": list(n.home) if n.home else None,
                  "bound": n.bound, "hp": n.hp} for n in game.npcs.npcs],
        "game": {"ticks": game.ticks, "day_count": game.day_count, "slime_rain": game.creatures.slime_rain,
                 "slime_kills": game.slime_kills},
    }
    tmp = slot_path(game.slot) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, slot_path(game.slot))


def load_data(slot):
    with open(slot_path(slot), encoding="utf-8") as f:
        return json.load(f)


def apply_world(world, data):
    """Restore saved world state onto a freshly generated World with the same seed."""
    tile_table = [T.get(name, 0) for name in data["tile_names"]]
    wall_table = [W.get(name, 0) for name in data["wall_names"]]
    w = data["world"]
    for key, (tiles, walls, liq) in w["chunks"].items():
        cx, cy = map(int, key.split(","))
        world.saved_chunks[(cx, cy)] = (_unpack(tiles, tile_table), _unpack(walls, wall_table), _unpack(liq))
    world.explored = {tuple(k) for k in w["explored"]}
    world.objects.clear()
    world.obj_cells.clear()
    world.containers.clear()
    for ax, ay, slots in w["containers"]:
        world.containers[(ax, ay)] = [s if s else None for s in slots]
    for ax, ay, name in w["objects"]:
        if name in T:
            world._register_object(T[name], ax, ay)
    world.flags = w["flags"]
    world.pending_npcs = [tuple(n) for n in w["pending_npcs"]]
    if "locked" in w:
        world.locked = {tuple(a) for a in w["locked"]}
    for ax, ay, state in w.get("furnaces", []):
        world.furnaces[(ax, ay)] = state
