"""Headless smoke test: drives the real game loop with simulated input.

Run from the project root:  python tools/smoke_test.py
Screenshots are written to tools/screenshots/ (git-ignored).
"""
import os
import sys
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
from tiles import T, AIR, TILES  # noqa: E402
from game import Game  # noqa: E402
import actions  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


def step(g, n=1, draw=False):
    for _ in range(n):
        g.update()
        if draw:
            g.draw()


def aim_at_tile(g, tx, ty):
    fake.mouse = (int(tx * TILE_SIZE + 16 - g.camera.x), int(ty * TILE_SIZE + 16 - g.camera.y))


def shot(g, name):
    g.draw()
    pygame.image.save(g.screen, os.path.join(SHOTS, name))


def select(g, item):
    for i, s in enumerate(g.player.inventory.slots[:10]):
        if s and s[0] == item:
            g.inv_ui.selected = i
            return True
    g.player.inventory.slots[9] = [item, 50]
    g.inv_ui.selected = 9
    return True


def main():
    g = Game()
    t0 = time.time()
    g.setup(seed=4242)
    check("world setup fast", time.time() - t0 < 3.0, f"{time.time() - t0:.2f}s")
    g.creatures.cooldown = 10 ** 9   # no spawns during mechanics tests
    p = g.player
    step(g, 60, draw=True)
    check("player lands on spawn surface", p.on_ground, f"y={p.y:.0f}")
    check("spawn biome is forest surface", g.world.get_biome(*p.center()) == "forest",
          g.world.get_biome(*p.center()))
    shot(g, "01_spawn_day.png")

    # ---- item 5: standing still must never hurt ----
    hp0 = p.hp
    step(g, 300)
    check("standing still keeps HP", p.hp == hp0, f"{hp0}->{p.hp}")

    # ---- item 1: mining takes several hits and drops an item that gets picked up ----
    select(g, "copper_pickaxe")
    ptx = int(p.center()[0]) // TILE_SIZE
    below = int(p.y + p.H) // TILE_SIZE
    target = (ptx, below)
    tile_before = g.world.get_tile(*target)
    fake.buttons[0] = True
    frames = 0
    while g.world.get_tile(*target) == tile_before and frames < 300:
        aim_at_tile(g, *target)
        step(g)
        frames += 1
        if frames == 12:
            shot(g, "02_mining_progress.png")
    fake.buttons[0] = False
    check("mining is a multi-hit process", 15 < frames < 300, f"{frames} frames for {TILES[tile_before].name}")
    check("broken tile spawned a drop or was picked up", len(g.drops) > 0 or
          p.inventory.count(TILES[tile_before].drop or "dirt") > 0)
    step(g, 90)
    got = p.inventory.count(TILES[tile_before].drop)
    check("drop flies to player and is picked up", got >= 1, f"{TILES[tile_before].drop} x{got}")

    # ---- item 5: dig straight down 25 tiles; HP must not drain ----
    hp0 = p.hp
    start_y = p.y
    fake.buttons[0] = True
    for _ in range(25 * 60):
        ptx = int(p.center()[0]) // TILE_SIZE
        below = int(p.y + p.H) // TILE_SIZE
        # dig the tile under whichever column the player straddles
        col = ptx if g.world.is_solid(ptx, below) else int(p.x + p.W - 1) // TILE_SIZE
        if not g.world.is_solid(col, below):
            col = int(p.x) // TILE_SIZE
        aim_at_tile(g, col, below)
        step(g)
        if (p.y - start_y) / TILE_SIZE >= 25:
            break
    fake.buttons[0] = False
    step(g, 120)
    dug = (p.y - start_y) / TILE_SIZE
    check("dug down", dug >= 20, f"{dug:.1f} tiles")
    check("no HP drain after digging deep", p.hp >= hp0 - 1, f"{hp0}->{p.hp}")
    shot(g, "03_underground_dig.png")

    # ---- real fall damage still exists ----
    p.x, p.y = p.x, p.y - 40 * TILE_SIZE
    # clear a shaft above so the player can fall
    tx = int(p.center()[0]) // TILE_SIZE
    for ty in range(int(p.y) // TILE_SIZE - 1, int(p.y + 40 * TILE_SIZE) // TILE_SIZE + 1):
        for x in (tx - 1, tx, tx + 1):
            if g.world.is_solid(x, ty) and ty < int(start_y + dug * TILE_SIZE + p.H) // TILE_SIZE:
                g.world.set_tile(x, ty, AIR)
    p.fall_peak = p.y
    p.on_ground = False
    hp0 = p.hp
    step(g, 240)
    check("long fall still hurts", p.hp < hp0, f"{hp0}->{p.hp}")
    p.hp = p.max_hp

    # ---- trees: chop with axe gives wood ----
    g.player.respawn()
    step(g, 30)
    tree_x = None
    sx = g.world.spawn_tx
    for dx in range(5, 300):
        for x in (sx + dx, sx - dx):
            if (x in g.world.gen.trees and g.world.gen.trees[x][1] == T["tree"]
                    and g.world.get_tile(x, g.world.surface[x] - 1) == T["tree"]):
                tree_x = x
                break
        if tree_x:
            break
    p.x = tree_x * TILE_SIZE - 40
    p.y = (g.world.surface[tree_x] - 3) * TILE_SIZE
    step(g, 60)
    select(g, "copper_axe")
    wood0 = p.inventory.count("wood")
    base_y = g.world.surface[tree_x] - 1
    fake.buttons[0] = True
    for _ in range(300):
        aim_at_tile(g, tree_x, base_y)
        step(g)
        if g.world.get_tile(tree_x, base_y) == AIR:
            break
    fake.buttons[0] = False
    step(g, 120)
    check("chopping a tree yields wood", p.inventory.count("wood") > wood0,
          f"wood {wood0}->{p.inventory.count('wood')}")

    # ---- crafting + placing ----
    p.inventory.add("wood", 40)
    p.inventory.add("gel", 5)
    from items import RECIPES
    from inventory import can_craft
    bench = next(r for r in RECIPES if r.result == "workbench")
    check("workbench craftable from wood", can_craft(p.inventory, bench))
    g.inv_ui._craft(bench, g)
    check("crafted workbench", p.inventory.count("workbench") == 1)
    select(g, "workbench")
    base_tx = int(p.center()[0]) // TILE_SIZE
    base_ty = int(p.y + p.H) // TILE_SIZE - 1
    spots = [(base_tx + dx, y) for dx in (2, -2, 3, -3, 4, -4) for y in range(base_ty - 4, base_ty + 4)
             if g.world.get_tile(base_tx + dx, y) == AIR and g.world.is_solid(base_tx + dx, y + 1)
             and actions.in_reach(p, base_tx + dx, y)]
    ptx, pty = spots[0]
    fake.buttons[0] = True
    aim_at_tile(g, ptx, pty)
    step(g, 3)
    fake.buttons[0] = False
    check("placed workbench", g.world.get_tile(ptx, pty) == T["workbench"], f"at {ptx},{pty}")
    step(g, 16)
    check("workbench detected as nearby station", "workbench" in g.inv_ui.stations)
    g.inv_ui.open = True
    fake.mouse = (200, 300)
    shot(g, "04_inventory_crafting.png")
    g.inv_ui.close(g)

    # ---- item 6: spawns depend on environment ----
    from creatures import spawn_table
    check("forest day spawns slimes", {k for k, _ in spawn_table("surface", "forest", False)} <=
          {"green_slime", "blue_slime"})
    check("snow night spawns frozen zombies", "frozen_zombie" in dict(spawn_table("surface", "snow", True)))
    check("hell spawns hell creatures", set(dict(spawn_table("hell", "forest", False))) ==
          {"lava_slime", "hellbat"})
    g.creatures.cooldown = 1
    for _ in range(600):
        step(g)
        g.creatures.cooldown = min(g.creatures.cooldown, 5)
    kinds = sorted({c.kind for c in g.creatures.creatures})
    check("creatures spawn around player", len(kinds) > 0, ", ".join(kinds))

    # ---- combat: sword kills a slime and it drops gel ----
    from creatures import Creature
    g.creatures.creatures = []
    cx, cy = p.center()
    slime = Creature("green_slime", cx + 30, p.y + p.H - 22, g.world)
    g.creatures.creatures.append(slime)
    select(g, "copper_sword")
    fake.buttons[0] = True
    for _ in range(200):
        fake.mouse = (int(slime.center()[0] - g.camera.x), int(slime.center()[1] - g.camera.y))
        p.invuln = 10
        step(g)
        if not slime.alive:
            break
    fake.buttons[0] = False
    check("sword kills slime", not slime.alive)
    step(g, 90)
    check("slime dropped gel that was collected", p.inventory.count("gel") > 5)

    # ---- night + lighting ----
    g.ticks = int(22 / 24 * DAY_LENGTH)
    check("22:00 is night", g.is_night())
    shot(g, "05_night.png")

    # ---- item 4: death and respawn ----
    p.invuln = 0
    p.hurt(10 ** 6)
    step(g)
    check("player dies at 0 HP", g.state == "dead" and not p.alive)
    shot(g, "06_death_screen.png")
    g._death_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=g.death_buttons[0].rect.center))
    check("respawn restores player", g.state == "playing" and p.alive and p.hp == p.max_hp)

    # ---- performance ----
    g.ticks = int(12 / 24 * DAY_LENGTH)
    t0 = time.time()
    for _ in range(120):
        g.update()
        g.draw()
    ms = (time.time() - t0) / 120 * 1000
    check("frame time under 16ms (update+draw)", ms < 16.7, f"{ms:.1f} ms/frame")

    # ---- deep layers render (no ungenerated gaps) ----
    p.y = (CAVERN_LINE + 40) * TILE_SIZE
    g.camera.update(*p.center())
    holes = 0
    for ty in range(CAVERN_LINE + 20, CAVERN_LINE + 60):
        for tx in range(int(p.x) // TILE_SIZE - 20, int(p.x) // TILE_SIZE + 20):
            g.world.get_tile(tx, ty)
    check("cavern chunks generated on demand", all(
        (cx, cy) in g.world.chunks for cx in range(int(p.x) // TILE_SIZE // CHUNK_SIZE - 1,
                                                   int(p.x) // TILE_SIZE // CHUNK_SIZE + 1)
        for cy in range((CAVERN_LINE + 20) // CHUNK_SIZE, (CAVERN_LINE + 60) // CHUNK_SIZE)), f"holes={holes}")
    shot(g, "07_cavern.png")
    p.y = (HELL_LINE + 40) * TILE_SIZE
    g.camera.update(*p.center())
    shot(g, "08_hell.png")

    # ---- biome scenes: spawned creatures must belong to the local spawn table ----
    g.ticks = int(10 / 24 * DAY_LENGTH)
    for biome in ("desert", "snow", "jungle"):
        xs = [x for x in range(WORLD_W) if g.world.gen.column_biome[x] == biome]
        x = xs[len(xs) // 2]
        p.respawn()
        p.x = x * TILE_SIZE
        p.y = (g.world.surface[x] - 3) * TILE_SIZE
        g.creatures.clear()
        for _ in range(500):
            g.creatures.cooldown = min(g.creatures.cooldown, 5)
            p.invuln = 10
            step(g)
        allowed = {k for k, _ in spawn_table("surface", biome, False)} | \
                  {k for k, _ in spawn_table("underground", biome, False)}
        kinds = {c.kind for c in g.creatures.creatures}
        check(f"{biome} creatures match environment", kinds and kinds <= allowed, ", ".join(sorted(kinds)))
        shot(g, f"09_{biome}.png")

    # ---- start screen ----
    g.draw_start_screen()
    pygame.image.save(g.screen, os.path.join(SHOTS, "00_start_screen.png"))
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:", ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
