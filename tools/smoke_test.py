"""Headless smoke test: drives the real game loop with simulated input.

Run from the project root:  python tools/smoke_test.py
Screenshots are written to tools/screenshots/ (git-ignored). Saves go to a temp folder.
"""
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame  # noqa: E402

SHOTS = os.path.join(ROOT, "tools", "screenshots")
os.makedirs(SHOTS, exist_ok=True)


class FakeInput:
    def __init__(self):
        self.keys = set()
        self.mouse = (0, 0)
        self.buttons = [False, False, False]


fake = FakeInput()


class _Keys:
    def __getitem__(self, k):
        return k in fake.keys


pygame.key.get_pressed = lambda: _Keys()
pygame.mouse.get_pos = lambda: fake.mouse
pygame.mouse.get_pressed = lambda num_buttons=3: tuple(fake.buttons)

from settings import *  # noqa: E402
from tiles import T, W, AIR, TILES  # noqa: E402
import save  # noqa: E402
from game import Game  # noqa: E402
import actions  # noqa: E402
from npc import check_house, NPC_TYPES  # noqa: E402
from physics import rect_solid  # noqa: E402
from creatures import Creature as Creature_cls  # noqa: E402

TMP_SAVES = tempfile.mkdtemp(prefix="pyterraria_saves_")
save.SAVE_DIR = TMP_SAVES
TS = TILE_SIZE
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


def step(g, n=1, draw=False):
    for _ in range(n):
        g.update()
        if draw:
            g.draw()


def aim_at_tile(g, tx, ty):
    fake.mouse = (int(tx * TS + TS / 2 - g.camera.x), int(ty * TS + TS / 2 - g.camera.y))


def shot(g, name):
    g.draw()
    pygame.image.save(g.screen, os.path.join(SHOTS, name))


def select(g, item, count=50):
    for i, s in enumerate(g.player.inventory.slots[:10]):
        if s and s[0] == item:
            g.inv_ui.selected = i
            return
    g.player.inventory.slots[9] = [item, count]
    g.inv_ui.selected = 9


def place_player(g, tx, ty_feet):
    p = g.player
    p.x = tx * TS + (TS - p.W) / 2
    p.y = ty_feet * TS - p.H
    p.vx = p.vy = 0
    p.fall_peak = p.y
    g.camera.update(*p.center())


def ground_under(g, tx):
    y = g.world.surface_at(tx) - 40
    while not g.world.is_solid(tx, y):
        y += 1
    return y


def build_house(g, x0):
    """A valid 12x9 wooden room: walls, door, torch, bed. Returns the bed anchor."""
    world = g.world
    floor = ground_under(g, x0 + 6)
    for x in range(x0 - 1, x0 + 13):
        for y in range(floor - 12, floor):
            world.set_tile(x, y, AIR)
        for y in range(floor, floor + 3):
            world.set_tile(x, y, T["wood"])
    for x in range(x0, x0 + 12):
        world.set_tile(x, floor - 9, T["wood"])
        for y in range(floor - 9, floor + 1):
            world.set_wall(x, y, W["wood_wall"])
    for y in range(floor - 9, floor):
        world.set_tile(x0, y, T["wood"])
        world.set_tile(x0 + 11, y, T["wood"])
    for y in range(floor - 3, floor):
        world.set_tile(x0, y, AIR)
    world.place_object(T["door"], x0, floor - 3)
    world.set_tile(x0 + 6, floor - 6, T["torch"])
    world.place_object(T["bed"], x0 + 3, floor - 2)
    return (x0 + 3, floor - 2), floor


def main():
    g = Game()
    t0 = time.time()
    g.setup(seed=4242, slot=0, name="测试世界")
    check("world setup fast", time.time() - t0 < 3.0, f"{time.time() - t0:.2f}s")
    g.creatures.cooldown = 10 ** 9
    p = g.player
    w = g.world
    step(g, 60, draw=True)
    check("player lands on spawn surface", p.on_ground, f"y={p.y:.0f}")
    check("player is ~1.5 tiles wide", abs(p.W / TS - 1.5) < 0.01, f"{p.W}px / {TS}px tiles")
    shot(g, "01_spawn_day.png")

    # ---- 2. jump height ----
    base_y = p.y
    fake.keys = {pygame.K_SPACE}
    top = p.y
    for _ in range(60):
        step(g)
        top = min(top, p.y)
    fake.keys = set()
    step(g, 60)
    rise = (base_y - top) / TS
    check("held jump is about 5-6 tiles", 4.5 <= rise <= 6.5, f"{rise:.1f} tiles = {base_y - top:.0f}px")

    hp0 = p.hp
    step(g, 300)
    check("standing still keeps HP", p.hp == hp0, f"{hp0}->{p.hp}")

    # ---- mining process + pickup ----
    select(g, "copper_pickaxe")
    tx = int(p.center()[0]) // TS + 2
    ty = ground_under(g, tx)
    before = w.get_tile(tx, ty)
    fake.buttons[0] = True
    frames = 0
    while w.get_tile(tx, ty) == before and frames < 300:
        aim_at_tile(g, tx, ty)
        step(g)
        frames += 1
    fake.buttons[0] = False
    step(g, 90)
    check("mining takes several hits", 10 < frames < 300, f"{frames} frames for {TILES[before].name}")
    check("drop picked up", p.inventory.count(TILES[before].drop) >= 1)

    # ---- dig straight down: no HP drain ----
    hp0 = p.hp
    start_y = p.y
    fake.buttons[0] = True
    for _ in range(40 * 40):
        below = int(p.y + p.H) // TS
        cols = range(int(p.x) // TS, int(p.x + p.W - 1) // TS + 1)
        target = next((c for c in cols if w.is_solid(c, below)), None)
        if target is None:
            step(g)
        else:
            aim_at_tile(g, target, below)
            step(g)
        if (p.y - start_y) / TS >= 30:
            break
    fake.buttons[0] = False
    step(g, 120)
    dug = (p.y - start_y) / TS
    check("dug down 30 tiles", dug >= 25, f"{dug:.1f} tiles")
    check("no HP drain after digging", p.hp >= hp0 - 2, f"{hp0}->{p.hp}")
    shot(g, "02_dig_down.png")

    # ---- fall damage beyond 25 tiles ----
    sx = w.spawn_tx + 40
    floor = ground_under(g, sx)
    for x in range(sx - 1, sx + 3):
        for y in range(floor - 60, floor):
            w.set_tile(x, y, AIR)
    place_player(g, sx, floor - 45)
    p.on_ground = False
    hp0 = p.hp
    step(g, 200)
    check("falling 45 tiles hurts", p.hp < hp0, f"{hp0}->{p.hp}")
    p.equip["acc0"] = "slime_boots"
    p.recompute_stats()
    p.hp = p.max_hp
    place_player(g, sx, floor - 45)
    p.on_ground = False
    step(g, 200)
    check("slime boots prevent fall damage", p.hp == p.max_hp)
    p.equip["acc0"] = None
    p.recompute_stats()

    # ---- 1. oxygen ----
    pit_x = w.spawn_tx - 60
    floor = ground_under(g, pit_x)
    for x in range(pit_x - 1, pit_x + 4):
        for y in range(floor - 10, floor + 1):
            w.set_tile(x, y, T["stone"])
    for x in range(pit_x, pit_x + 3):
        for y in range(floor - 8, floor):
            w.set_tile(x, y, AIR)
            w.place_liquid(x, y, T["water"])
    place_player(g, pit_x, floor)
    p.hp = p.max_hp
    p.breath = p.breath_max
    step(g, 30)
    check("head under water detected", p.head_under)
    step(g, BREATH_MAX + 60)
    check("breath runs out underwater", p.breath == 0)
    hp_drown = p.hp
    step(g, 120)
    check("drowning deals damage", p.hp < hp_drown, f"{hp_drown}->{p.hp}")
    shot(g, "03_underwater.png")
    p.hp = p.max_hp
    p.equip["acc0"] = "diving_mask"
    p.recompute_stats()
    check("diving mask triples breath", p.breath_max == BREATH_MAX * 3)
    p.equip["acc0"] = None
    p.recompute_stats()

    # ---- 1. lava burns over time ----
    lx = w.spawn_tx - 80
    floor = ground_under(g, lx)
    for x in range(lx - 1, lx + 3):
        for y in range(floor - 6, floor):
            w.set_tile(x, y, AIR)
    w.place_liquid(lx, floor - 1, T["lava"])
    w.place_liquid(lx + 1, floor - 1, T["lava"])
    place_player(g, lx, floor)
    p.hp = p.max_hp
    p.invuln = 0
    step(g, 5)
    check("lava sets the player on fire", p.burning > 0)
    place_player(g, lx + 6, ground_under(g, lx + 6))
    hp_burn = p.hp
    step(g, 120)
    check("burning keeps hurting after leaving lava", p.hp < hp_burn, f"{hp_burn}->{p.hp}")
    p.equip["acc0"] = "obsidian_charm"
    p.recompute_stats()
    p.hp = p.max_hp
    place_player(g, lx, floor)
    step(g, 60)
    check("obsidian charm gives lava immunity", p.hp == p.max_hp and p.burning == 0)
    p.equip["acc0"] = None
    p.recompute_stats()
    shot(g, "04_lava.png")

    # ---- 3. liquid flow ----
    fx = w.spawn_tx + 120
    floor = ground_under(g, fx)
    for x in range(fx - 6, fx + 7):
        for y in range(floor - 8, floor):
            w.set_tile(x, y, AIR)
    w.place_liquid(fx, floor - 6, T["water"])
    for _ in range(80):
        w.update_liquids(500)
    cells = [(x, y) for x in range(fx - 6, fx + 7) for y in range(floor - 8, floor) if w.get_tile(x, y) == T["water"]]
    check("water falls and spreads", len(cells) >= 3 and all(y >= floor - 2 for _, y in cells),
          f"{len(cells)} cells")
    w.place_liquid(fx + 5, floor - 1, T["lava"])
    for _ in range(80):
        w.update_liquids(500)
    obs = sum(1 for x in range(fx - 6, fx + 7) for y in range(floor - 8, floor + 1)
              if w.get_tile(x, y) == T["obsidian"])
    check("water meeting lava makes obsidian", obs >= 1, f"{obs} obsidian")

    # ---- 4. equipment ----
    place_player(g, w.spawn_tx, ground_under(g, w.spawn_tx))
    for slot, name in (("head", "iron_helmet"), ("body", "iron_chainmail"), ("legs", "iron_greaves")):
        p.equip[slot] = name
    p.equip["acc0"] = "hermes_boots"
    p.equip["acc1"] = "cloud_bottle"
    p.recompute_stats()
    check("armor adds defense", p.defense == 7, f"defense {p.defense}")
    p.invuln = 0
    dealt = p.hurt(20)
    check("defense reduces damage", dealt == 20 - 7 // 2, f"took {dealt}")
    check("accessory raises speed", p.stats["speed"] > 0.3)
    check("cannot equip the same accessory twice", not p.can_equip("acc2", "hermes_boots"))
    p.hp = p.max_hp
    step(g, 30)
    base_y = p.y
    fake.keys = {pygame.K_SPACE}
    step(g, 20)
    fake.keys = set()
    step(g, 2)
    fake.keys = {pygame.K_SPACE}
    top = p.y
    for _ in range(50):
        step(g)
        top = min(top, p.y)
    fake.keys = set()
    step(g, 90)
    check("cloud bottle double jump goes higher", (base_y - top) / TS > 7, f"{(base_y - top) / TS:.1f} tiles")
    g.inv_ui.open = True
    fake.mouse = (480, 120)
    shot(g, "05_equipment.png")
    g.inv_ui.close(g)

    # ---- 8. walls: hammer and place ----
    wx_ = w.spawn_tx + 8
    wy_ = ground_under(g, wx_) + 3
    for y in range(wy_ - 2, wy_ + 1):
        w.set_tile(wx_, y, AIR)
    w.set_wall(wx_, wy_, W["dirt_wall"])
    place_player(g, wx_ - 2, ground_under(g, wx_ - 2))
    select(g, "wooden_hammer")
    fake.buttons[0] = True
    for _ in range(200):
        aim_at_tile(g, wx_, wy_)
        step(g)
        if not w.get_wall(wx_, wy_):
            break
    fake.buttons[0] = False
    check("hammer removes background wall", w.get_wall(wx_, wy_) == 0)
    step(g, 20)
    select(g, "wood_wall")
    fake.buttons[0] = True
    aim_at_tile(g, wx_, wy_)
    step(g, 3)
    fake.buttons[0] = False
    check("wall item places a wall", w.get_wall(wx_, wy_) == W["wood_wall"])

    # ---- 5. NPC housing, arrival and trade ----
    bed1, floor1 = build_house(g, w.spawn_tx + 20)
    ok, reason = check_house(w, bed1)
    check("built house passes housing check", ok, reason)
    w.set_tile(bed1[0] + 3, floor1 - 6, AIR)
    ok2, reason2 = check_house(w, bed1)
    check("house without light is rejected", not ok2 and "光源" in reason2, reason2)
    w.set_tile(bed1[0] + 3, floor1 - 6, T["torch"])
    g.npcs.check_arrivals()
    guide = g.npcs.by_kind("guide")
    check("guide moves into the house", guide is not None and guide.home == bed1)
    bed2, _ = build_house(g, w.spawn_tx + 36)
    p.inventory.add("coin", 300)
    g.npcs.check_arrivals()
    merchant = g.npcs.by_kind("merchant")
    check("merchant arrives with 50+ coins and a free house", merchant is not None and merchant.home == bed2)
    coins = p.inventory.count("coin")
    g.buy("healing_potion", 30)
    check("buying costs coins", p.inventory.count("coin") == coins - 30)
    g.sell("gold_bar", 2)
    check("selling gives coins", p.inventory.count("coin") > coins - 30)
    place_player(g, bed1[0] + 2, floor1)
    for _ in range(60):
        step(g)
    from panels import DialogPanel
    g.panel = DialogPanel(g, merchant)
    shot(g, "06_npc_dialog.png")
    g.panel = None
    g.inv_ui.open_shop(merchant)
    shot(g, "07_shop.png")
    g.inv_ui.close(g)

    # ---- beds: spawn point and sleeping ----
    g.ticks = int(23 / 24 * DAY_LENGTH)
    g.creatures.creatures = []
    g.use_bed(bed1)
    check("bed sets spawn point", p.spawn_point == bed1)
    for _ in range(100):
        step(g)
    check("sleeping skips to morning", 6 <= g.hour() < 7, f"{g.hour():.1f}h")

    # ---- shipping bin sells at dawn ----
    bin_x = bed2[0] + 6
    by = ground_under(g, bin_x)
    w.place_object(T["shipping_bin"], bin_x, by - 2)
    bin_anchor = (bin_x, by - 2)
    w.containers[bin_anchor][0] = ["gold_bar", 5]
    coins = p.inventory.count("coin")
    g.on_dawn()
    check("shipping bin sold items at dawn", p.inventory.count("coin") > coins and not w.containers[bin_anchor][0])

    # ---- 8. furnace: input + fuel, smelts over time; bars are not craftable directly ----
    from items import RECIPES, SMELTING
    check("metal bars have no crafting recipe", not any(r.result.endswith("_bar") for r in RECIPES))
    sm_x = bed2[0] + 12
    sy = ground_under(g, sm_x)
    for x in range(sm_x, sm_x + 3):
        for y in range(sy - 3, sy):
            w.set_tile(x, y, AIR)
        w.set_tile(x, sy, T["stone"])
    w.place_object(T["furnace"], sm_x, sy - 2)
    furnace = w.containers[(sm_x, sy - 2)]
    furnace[0] = ["iron_ore", 9]
    for _ in range(SMELTING["iron_ore"][2] * 2):
        g._update_furnaces()
    check("furnace does nothing without fuel", furnace[2] is None)
    furnace[1] = ["wood", 1]
    for _ in range(SMELTING["iron_ore"][2] * 3 + 5):
        g._update_furnaces()
    check("one wood smelts exactly one batch", furnace[2] == ["iron_bar", 1], str(furnace[2]))
    furnace[1] = ["coal", 1]
    for _ in range(SMELTING["iron_ore"][2] * 3 + 5):
        g._update_furnaces()
    check("coal smelts the remaining ore", furnace[2] == ["iron_bar", 3] and furnace[0] is None, str(furnace))
    place_player(g, sm_x - 2, sy)
    g.inv_ui.open_container((sm_x, sy - 2), furnace, "熔炉")
    fake.mouse = (300, 300)
    shot(g, "16_furnace.png")
    g.inv_ui.close(g)

    # ---- teleport via pylons ----
    w.place_object(T["pylon"], bed1[0] - 6, floor1 - 3)
    far = w.spawn_tx - 300
    ff = ground_under(g, far)
    for x in range(far, far + 2):
        for y in range(ff - 3, ff):
            w.set_tile(x, y, AIR)
    w.place_object(T["pylon"], far, ff - 3)
    g.open_teleport()
    check("teleport panel lists pylons", len(g.panel.buttons) >= 2)
    shot(g, "08_teleport.png")
    g.teleport_to((far, ff - 3))
    g.panel = None
    check("teleported to far pylon", abs(p.center()[0] / TS - far) < 6)

    # ---- 9. structures and chests ----
    kinds = {s.kind for s in w.gen.structures}
    check("all structure types planned", kinds >= {"surface_cabin", "underground_cabin", "mineshaft", "pyramid",
                                                     "igloo", "jungle_ruins", "shipwreck", "sky_island", "hell_tower",
                                                     "miner_camp", "watchtower", "temple"},
          ", ".join(sorted(kinds)))
    pyr = next(s for s in w.gen.structures if s.kind == "pyramid" and s.npc)
    ax, ay, slots = pyr.chests[0]
    check("structure chest holds loot", any(slots), ", ".join(s[0] for s in slots if s))
    kind, nx, ny = pyr.npc
    place_player(g, nx + 2, ny + 1)
    step(g, 30)
    traveler = g.npcs.by_kind("traveler")
    check("bound traveler waits in the pyramid", traveler is not None and traveler.bound)
    shot(g, "09_pyramid.png")
    g.npcs.rescue(traveler)
    check("rescued traveler is free", not traveler.bound and w.flags.get("traveler_rescued"))
    g.inv_ui.open_container((ax, ay), w.containers[(ax, ay)], "箱子")
    g.inv_ui._loot_all(g)
    check("looting a structure chest", not any(w.containers[(ax, ay)]))
    g.inv_ui.close(g)
    isl = next(s for s in w.gen.structures if s.kind == "sky_island")
    place_player(g, isl.chests[0][0] - 2, isl.chests[0][1] + 2)
    step(g, 10)
    shot(g, "10_sky_island.png")
    tower = next(s for s in w.gen.structures if s.kind == "hell_tower")
    place_player(g, tower.chests[0][0], tower.chests[0][1] + 2)
    step(g, 10)
    shot(g, "11_hell_tower.png")

    # ---- 10. structure counts, ruins, lore and locked chests ----
    from collections import Counter
    from structures import COUNTS
    counts = Counter(s.kind for s in w.gen.structures)
    check("pyramids are rare (at most 2)", counts["pyramid"] <= 2, str(counts["pyramid"]))
    check("mineshafts are common (20+)", counts["mineshaft"] >= 20, str(counts["mineshaft"]))
    check("counts stay within each type's range",
          all(counts[k] <= hi for k, (lo, hi) in COUNTS.items()), str(dict(counts)))
    camp = next(s for s in w.gen.structures if s.kind == "miner_camp")
    webs = sum(1 for t in camp.tiles.values() if t == T["cobweb"])
    check("abandoned camps look ruined (cobwebs, broken walls)", webs > 0 and len(camp.walls) < 9 * 10, f"{webs} webs")
    from story import TOTAL_NOTES
    check("every lore note is placed once", sorted(w.notes.values()) == list(range(1, TOTAL_NOTES + 1)))
    note_pos = next(pos for pos, nid in w.notes.items() if nid == 1)
    place_player(g, note_pos[0] - 1, note_pos[1] + 1)
    step(g, 20)
    shot(g, "17_miner_camp.png")
    actions.interact(g, *note_pos)
    check("reading a lore tablet adds it to the journal", 1 in p.journal and g.panel is not None)
    shot(g, "18_lore_note.png")
    g.panel = None
    for pos, nid in w.notes.items():
        g.read_note(*pos)
        g.panel = None
    check("collecting all notes rewards the expedition badge", p.inventory.count("expedition_badge") == 1)
    from panels import JournalPanel
    g.panel = JournalPanel(g)
    shot(g, "19_journal.png")
    g.panel = None

    temple_st = next(s for s in w.gen.structures if s.kind == "temple")
    gold = temple_st.locked[0]
    check("temple gold chests are locked", gold in w.locked)
    place_player(g, gold[0] - 2, gold[1] + 2)
    step(g, 20)
    shot(g, "20_temple.png")
    p.inventory.remove("lockpick", p.inventory.count("lockpick"))
    actions.interact(g, *gold)
    check("locked chest needs a lockpick", g.panel is None and gold in w.locked)
    p.inventory.add("lockpick", 3)
    actions.interact(g, *gold)
    from panels import LockpickPanel
    lp = g.panel
    check("lockpick mini-game opens", isinstance(lp, LockpickPanel))
    shot(g, "21_lockpick.png")
    space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    lp.pos = (lp.zone[0] + lp.zone[1] + 30) % lp.bar.w if lp.zone[0] + lp.zone[1] + 30 < lp.bar.w else 0
    lp.handle_event(space)
    check("a missed pin snaps a lockpick", p.inventory.count("lockpick") == 2 and lp.pin == 0)
    for _ in range(3):
        lp.pos = lp.zone[0] + lp.zone[1] / 2
        if lp.handle_event(space):
            g.panel = None
    check("three good pins unlock the chest", gold not in w.locked and g.inv_ui.container is not None)
    g.inv_ui.close(g)

    # ---- treasure map ----
    select(g, "treasure_map", 1)
    fake.buttons[0] = True
    step(g, 2)
    fake.buttons[0] = False
    tr = w.flags.get("treasure")
    check("treasure map buries a chest and marks it", tr is not None and w.objects.get(tuple(tr)) == T["chest"])
    shot(g, "22_treasure_hud.png")
    g.open_chest(tuple(tr), "箱子")
    check("opening the buried chest completes the hunt", "treasure" not in w.flags)
    g.inv_ui.close(g)

    # ---- requests (quests) ----
    guide = g.npcs.by_kind("guide")
    g.quests.offers["guide"] = {"giver": "guide", "type": "kill", "target": "zombie", "count": 2, "progress": 0,
                                "coins": 50, "extras": [("card_pack", 1)]}
    from panels import DialogPanel
    g.panel = DialogPanel(g, guide)
    check("NPC dialog offers a request", any(a == "quest" for _, a in g.panel.buttons))
    g.dialog_action(g.panel, "quest")
    g.dialog_action(g.panel, "accept")
    check("request accepted", g.quests.from_giver("guide") is not None)
    for _ in range(2):
        z = Creature_cls("zombie", p.x + 40, p.y, w)
        z.alive = False
        g.on_creature_hit(z, 1)
    coins = p.inventory.count("coin")
    g.dialog_action(g.panel, "turn_in")
    check("kill request completes and pays out", g.quests.from_giver("guide") is None
          and p.inventory.count("coin") == coins + 50 and p.inventory.count("card_pack") >= 1)
    g.panel = None

    # ---- 6. housing query tool (no item needed) ----
    fake.keys = set()
    place_player(g, bed1[0] + 2, floor1)
    step(g, 5)
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)
    pygame.event.post(ev)
    g.events()
    check("J toggles the housing tool", g.house_mode)
    g.query_room(((bed1[0] + 5) * TS - g.camera.x, (floor1 - 4) * TS - g.camera.y))
    check("tool reports a valid house", g.room_report and g.room_report.r["ok"])
    shot(g, "23_housing_tool_ok.png")
    g.query_room(((w.spawn_tx - 20) * TS - g.camera.x, (ground_under(g, w.spawn_tx - 20) - 3) * TS - g.camera.y))
    check("tool explains why open ground is not a house", not g.room_report.r["ok"]
          and "不封闭" in g.room_report.r["reasons"][0], g.room_report.r["reasons"][0])
    g.toggle_house_mode()

    # ---- 7. natural walls are patchy ----
    tx0 = w.spawn_tx + 400
    cells = [(x, y) for x in range(tx0, tx0 + 120) for y in range(w.surface_at(x) + 3, w.surface_at(x) + 25)]
    walled = sum(1 for x, y in cells if w.get_wall(x, y)) / len(cells)
    check("natural walls cover only part of the shallow underground", 0.3 < walled < 0.95, f"{walled:.0%}")

    # ---- 9. ore textures stand out from stone ----
    def avg(surf):
        px = [surf.get_at((x, y)) for x in range(16) for y in range(16)]
        return [sum(c[i] for c in px) / len(px) for i in range(3)]
    stone = avg(g.assets.tile_tex[T["stone"]][0])
    iron = g.assets.tile_tex[T["iron_ore"]][0]
    bright = sum(1 for x in range(16) for y in range(16)
                 if sum(abs(iron.get_at((x, y))[i] - stone[i]) for i in range(3)) > 120)
    check("iron ore has large distinct nuggets", bright >= 24, f"{bright} distinct pixels")

    # ---- 2 / 4 / 5. creatures: factions, spawn odds, flyers avoid water ----
    from creatures import CREATURE_TYPES, passive_table
    factions = Counter(t.get("faction", "hostile") for t in CREATURE_TYPES.values())
    check("world has friendly and neutral creatures", factions["friendly"] >= 3 and factions["neutral"] >= 3,
          str(dict(factions)))
    place_player(g, w.spawn_tx - 30, ground_under(g, w.spawn_tx - 30))
    g.creatures.creatures = []
    bunny = Creature_cls("bunny", p.x, p.y + p.H - 14, w)
    g.creatures.creatures.append(bunny)
    hp0 = p.hp
    p.invuln = 0
    step(g, 10)
    check("friendly critters never hurt the player", p.hp >= hp0)
    boar = Creature_cls("boar", p.x + 60, p.y + p.H - 20, w)
    g.creatures.creatures = [boar]
    check("neutral boar starts peaceful", not boar.hostile)
    boar.hit(5, p.center()[0], 2, attacker=p)
    check("hitting a neutral animal provokes it", boar.hostile)
    wolves = [Creature_cls("snow_wolf", p.x + 80 + i * 40, p.y + p.H - 20, w) for i in range(3)]
    g.creatures.creatures = wolves
    g.on_creature_hit(wolves[0], wolves[0].hit(5, p.center()[0], 2, attacker=p))
    check("wolves defend their pack", all(wf.provoked for wf in wolves))
    g.creatures.creatures = []
    g.creatures.slime_rain = False      # a random slime rain may have started at an earlier dawn
    ctx_day = g.creatures.spawn_context(p, False, [])
    ctx_night = g.creatures.spawn_context(p, True, [])
    ctx_town = g.creatures.spawn_context(p, False, g.npcs.npcs + [g.npcs.by_kind("guide")] * 2)
    check("spawn odds differ by time of day", ctx_night[1] > ctx_day[1], f"{ctx_day[1]:.2f} vs {ctx_night[1]:.2f}")
    p_y = p.y
    p.y = (CAVERN_LINE + 60) * TS
    ctx_cave = g.creatures.spawn_context(p, False, [])
    p.y = p_y
    check("spawn odds differ by layer", abs(ctx_cave[1] - ctx_day[1]) > 0.05, f"cavern {ctx_cave[1]:.2f}")
    check("towns reduce spawn odds", ctx_town[1] < ctx_day[1] * 0.5)
    g.creatures.roll_timer = 1
    g.creatures.creatures = []
    spawned = 0
    for _ in range(FPS * 60):
        before = g.creatures.count(True)
        g.creatures._spawn_roll(p, False, [])
        spawned += max(0, g.creatures.count(True) - before)
    check("daytime surface spawns are slow (a few per minute)", spawned <= 10, f"{spawned} in 60 s")
    check("passive animals appear on the surface", g.creatures.count(False) > 0,
          ", ".join(sorted({c.kind for c in g.creatures.creatures if c.faction != 'hostile'})))
    shot(g, "24_animals.png")
    g.creatures.creatures = []
    # a bat chasing a target under water must stay out of it
    wx0 = w.spawn_tx - 140
    wf = ground_under(g, wx0)
    for x in range(wx0 - 1, wx0 + 9):
        for y in range(wf - 14, wf + 6):
            w.set_tile(x, y, T["stone"] if x in (wx0 - 1, wx0 + 8) or y == wf + 5 else AIR)
    for x in range(wx0, wx0 + 8):
        for y in range(wf - 1, wf + 5):
            w.place_liquid(x, y, T["water"])
    bat = Creature_cls("cave_bat", (wx0 + 3) * TS, (wf - 10) * TS, w)
    for _ in range(300):
        bat.update(p, [p])
        p.x, p.y = (wx0 + 3) * TS, (wf + 2) * TS
    check("bats never fly into water", not any(w.get_tile(x, y) == T["water"] for x in range(
        int(bat.x) // TS, int(bat.x + bat.w - 1) // TS + 1) for y in range(int(bat.y) // TS, int(bat.y + bat.h - 1) // TS + 1)))

    # ---- 3. NPCs fight hostile creatures and can be hurt ----
    place_player(g, bed1[0] + 2, floor1)
    guide = g.npcs.by_kind("guide")
    guide.x, guide.y = (bed1[0] + 1) * TS, (floor1 - 3) * TS
    zombie = Creature_cls("zombie", guide.x + 70, guide.y, w)    # inside the same room
    g.creatures.creatures = [zombie]
    hp_z = zombie.hp
    for _ in range(240):
        p.invuln = 30
        step(g)
    check("NPC attacks hostile creatures on its own", zombie.hp < hp_z or not zombie.alive, f"zombie hp {zombie.hp}")
    dps_npc = {k: v["attack"][1] * FPS / v["attack"][2] for k, v in NPC_TYPES.items() if v["attack"][0] != "heal"}
    from items import ITEMS as IT
    dps_player = IT["copper_sword"].damage * FPS / IT["copper_sword"].use_time
    check("NPC damage per second stays below the player's", max(dps_npc.values()) < dps_player,
          f"max NPC {max(dps_npc.values()):.1f} vs player {dps_player:.1f}")
    guide.invuln = 0
    hp_g = guide.hp
    g.creatures.creatures = [Creature_cls("zombie", guide.x, guide.y, w)]
    step(g, 3)
    check("hostile creatures hurt NPCs", guide.hp < hp_g, f"{hp_g}->{guide.hp}")
    shot(g, "25_npc_fight.png")
    guide.hp = 1
    guide.invuln = 0
    guide.hurt(50)
    g.creatures.creatures = []
    step(g, 2)
    check("NPC can die", g.npcs.by_kind("guide") is None)
    g.npcs.check_arrivals()
    check("dead NPC does not return the same day", g.npcs.by_kind("guide") is None)
    g.day_count += 1
    g.npcs.check_arrivals()
    check("dead NPC returns the next day", g.npcs.by_kind("guide") is not None)

    # ---- 1. card game with NPCs ----
    from cards import CardGame, NPC_DECKS, STARTER, CardPanel
    results = Counter()
    import random as _r
    for i in range(200):
        m = CardGame(STARTER, NPC_DECKS["merchant"])
        for _ in range(200):
            if m.winner:
                break
            if m.turn == "p":
                hand = m.sides["p"].hand
                if hand and _r.random() < 0.8:
                    m.play("p", _r.randrange(len(hand)))
                else:
                    m.pass_round("p")
            else:
                m.ai_move()
        results[m.winner] += 1
    check("200 simulated card matches all finish", sum(results.values()) == 200 and None not in results,
          str(dict(results)))
    check("card games unlock with 3 housed NPCs", g.cards_unlocked() == (len(g.npcs.housed()) >= 3),
          f"{len(g.npcs.housed())} housed")
    g.world.flags.pop("cards_given", None)
    p.cards = []
    while not g.cards_unlocked():
        b, _ = build_house(g, w.spawn_tx + 84 + 16 * len(g.npcs.housed()))
        g.npcs.check_arrivals()
        if len(g.npcs.housed()) < 3 and not g.npcs.by_kind("nurse"):
            p.max_hp = 140
    g.ticks += FPS * 5 - g.ticks % (FPS * 5) - 1    # update() advances time by one frame first
    g.update()
    check("starter deck is given when cards unlock", len(p.cards) == len(STARTER))
    merchant = g.npcs.by_kind("merchant")
    g.panel = DialogPanel(g, merchant)
    check("dialog shows the card option", any(a == "cards" for _, a in g.panel.buttons))
    g.dialog_action(g.panel, "cards")
    cp = g.panel
    check("card table opens", isinstance(cp, CardPanel))
    coins = p.inventory.count("coin")
    bet_btn = next(b for b, amount in cp.bet_buttons if amount == 20)
    cp.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=bet_btn.rect.center))
    shot(g, "26_cards.png")
    for _ in range(600):
        if cp.state == "over":
            break
        if cp.match.turn == "p":
            rects = cp._hand_rects()
            if rects:
                cp.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rects[0].center))
            else:
                cp.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=cp.pass_btn.rect.center))
        else:
            g.update()
    expected = {"p": coins + 20, "o": coins - 20, "draw": coins}[cp.match.winner]
    check("card match settles the bet", cp.state == "over" and p.inventory.count("coin") == expected,
          f"winner {cp.match.winner}")
    shot(g, "27_cards_result.png")
    g.panel = None
    select(g, "card_pack", 1)
    n_cards = len(p.cards)
    fake.buttons[0] = True
    step(g, 2)
    fake.buttons[0] = False
    check("card packs add three cards", len(p.cards) == n_cards + 3)

    # ---- 7. bosses ----
    place_player(g, w.spawn_tx - 30, ground_under(g, w.spawn_tx - 30))
    p.hp = p.max_hp
    g.ticks = int(21 / 24 * DAY_LENGTH)
    select(g, "eye_summon", 1)
    fake.buttons[0] = True
    step(g, 2)
    fake.buttons[0] = False
    step(g, 120)
    boss = g.bosses.active()
    check("summoning item spawns the eye boss at night", boss is not None and boss.kind == "eye")
    for _ in range(90):
        p.invuln = 30
        step(g)
    shot(g, "12_boss_eye.png")
    while boss.alive:
        g.on_creature_hit(boss, boss.hit(200, p.center()[0], 0))
    step(g, 5)
    check("eye boss defeat sets flag", w.flags.get("eye_defeated"))
    check("eye boss drops a treasure bag", any(d.name == "eye_bag" for d in g.drops) or p.inventory.count("eye_bag"))
    bag = next((d for d in g.drops if d.name == "eye_bag"), None)
    check("boss drops are never buried in terrain",
          bag is None or not rect_solid(w, bag.x, bag.y, bag.W, bag.H))
    step(g, 120)
    select(g, "eye_bag", 1)
    fake.buttons[0] = True
    step(g, 2)
    fake.buttons[0] = False
    check("treasure bag contains the shield", p.inventory.count("eye_shield") == 1)
    # the rescued traveler takes the first free house, the blacksmith the next one
    build_house(g, w.spawn_tx + 52)
    build_house(g, w.spawn_tx + 68)
    g.npcs.check_arrivals()
    check("rescued traveler moves into a house", g.npcs.by_kind("traveler").home is not None)
    check("blacksmith arrives after a boss", g.npcs.by_kind("blacksmith") is not None)

    from creatures import Creature
    g.ticks = int(10 / 24 * DAY_LENGTH)
    g.creatures.slime_rain = True
    g.slime_kills = 0
    for _ in range(40):
        c = Creature("green_slime", p.x + 40, p.y, w)
        c.alive = False
        g.on_creature_hit(c, 1)
    step(g, 200)
    ks = g.bosses.active()
    check("40 slime-rain kills summon King Slime", ks is not None and ks.kind == "king_slime")
    for _ in range(60):
        p.invuln = 30
        step(g)
    check("king slime is not stuck inside terrain", not rect_solid(w, ks.x, ks.y, ks.w, ks.h, creature=True))
    shot(g, "13_boss_king_slime.png")
    while ks.alive:
        g.on_creature_hit(ks, ks.hit(200, p.center()[0], 0))
    check("king slime defeat sets flag", w.flags.get("king_slime_defeated"))

    # ---- death drops coins ----
    coins = p.inventory.count("coin")
    p.invuln = 0
    p.hurt(10 ** 6)
    step(g)
    check("death halves carried coins", g.state == "dead" and p.inventory.count("coin") == coins - coins // 2)
    shot(g, "14_death.png")
    g._death_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=g.death_buttons[0].rect.center))
    check("respawn at bed", g.state == "playing" and abs(p.center()[0] / TS - (bed1[0] + 1.5)) < 3)

    # ---- performance ----
    place_player(g, w.spawn_tx, ground_under(g, w.spawn_tx))
    g.ticks = int(12 / 24 * DAY_LENGTH)
    g.creatures.creatures = []
    step(g, 30, draw=True)
    t0 = time.time()
    for _ in range(120):
        g.update()
        g.draw()
    ms = (time.time() - t0) / 120 * 1000
    check("surface frame time under 16.7ms", ms < 16.7, f"{ms:.1f} ms/frame")
    place_player(g, w.spawn_tx + 200, CAVERN_LINE + 40)
    step(g, 30, draw=True)
    t0 = time.time()
    for _ in range(120):
        g.update()
        g.draw()
    ms = (time.time() - t0) / 120 * 1000
    check("cavern frame time under 16.7ms", ms < 16.7, f"{ms:.1f} ms/frame")

    # ---- 6. save / load round trip ----
    place_player(g, w.spawn_tx, ground_under(g, w.spawn_tx))
    mark = (w.spawn_tx + 3, ground_under(g, w.spawn_tx + 3))
    w.set_tile(*mark, T["gold_ore"])
    p.inventory.slots[25] = ["mana_crystal", 3]
    g.save(quiet=True)
    meta = save.list_slots()[0]
    check("save slot written", meta and meta["name"] == "测试世界")
    inv_before = [list(s) if s else None for s in p.inventory.slots]
    equip_before = dict(p.equip)
    npcs_before = sorted(n.kind for n in g.npcs.npcs)
    g2 = Game()
    g2.load(0)
    check("load restores inventory", [list(s) if s else None for s in g2.player.inventory.slots] == inv_before)
    check("load restores equipment", g2.player.equip == equip_before)
    check("load restores modified tiles", g2.world.get_tile(*mark) == T["gold_ore"])
    check("load restores objects", g2.world.objects.get(bed1) == T["bed"])
    check("load restores NPCs", sorted(n.kind for n in g2.npcs.npcs) == npcs_before, ", ".join(npcs_before))
    check("load restores boss flags", g2.world.flags.get("eye_defeated"))
    check("load restores card collection and journal",
          sorted(g2.player.cards) == sorted(p.cards) and g2.player.journal == p.journal)
    check("load restores unlocked chests and furnace state",
          gold not in g2.world.locked and g2.world.furnaces.get((sm_x, sy - 2)) == w.furnaces.get((sm_x, sy - 2)))

    # world selection screen: screenshot the slot list, then press "返回"
    import menus
    cx = SCREEN_WIDTH // 2
    real_flip = pygame.display.flip

    def flip_and_go_back():
        pygame.image.save(g.screen, os.path.join(SHOTS, "15_world_select.png"))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, SCREEN_HEIGHT - 50)))

    pygame.display.flip = flip_and_go_back
    check("world select returns on back", menus.world_select(g) is None)
    pygame.display.flip = real_flip
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx + 220, 110 + 140 + 60)))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx - 70, 430)))
    choice = menus.world_select(g)
    check("world select creates a new world in an empty slot", choice and choice[:3] == ("new", 1, "世界 2"),
          str(choice))
    save.delete_slot(0)
    check("delete slot", save.list_slots()[0] is None)

    g.draw_start_screen()
    pygame.image.save(g.screen, os.path.join(SHOTS, "00_start_screen.png"))
    shutil.rmtree(TMP_SAVES, ignore_errors=True)
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
