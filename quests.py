"""NPC requests: each housed NPC offers one request per day (gather / hunt / explore).
Up to three can be active; finished requests are handed in to the NPC who gave them."""
import random

from items import ITEMS
from creatures import CREATURE_TYPES

MAX_ACTIVE = 3
POOLS = {
    "guide": [("gather", "wood", 30), ("gather", "mushroom", 5), ("gather", "torch", 20),
              ("kill", "green_slime", 6), ("kill", "zombie", 5), ("note", None, 1)],
    "merchant": [("gather", "gel", 15), ("gather", "lens", 3), ("gather", "cactus", 10),
                 ("kill", "demon_eye", 3), ("card_win", None, 1), ("treasure", None, 1)],
    "nurse": [("gather", "mushroom", 8), ("gather", "healing_potion", 2), ("gather", "cooked_meat", 3),
              ("kill", "cave_bat", 5)],
    "blacksmith": [("gather", "iron_bar", 10), ("gather", "gold_bar", 5), ("gather", "coal", 20),
                   ("gather", "obsidian", 5), ("kill", "skeleton", 5), ("unlock", None, 1)],
    "traveler": [("gather", "cloud", 15), ("gather", "mana_crystal", 1), ("unlock", None, 1),
                 ("treasure", None, 1), ("note", None, 2)],
}
EXTRA_REWARDS = [("card_pack", 1, 0.5), ("treasure_map", 1, 0.25), ("lockpick", 3, 0.4)]


def quest_text(q):
    t, target, n = q["type"], q["target"], q["count"]
    if t == "gather":
        return f"收集 {ITEMS[target].display} ×{n}"
    if t == "kill":
        return f"讨伐 {CREATURE_TYPES[target]['name']} ×{n}"
    return {"note": f"找到剧情日志 ×{n}", "card_win": "在牌局中赢一次", "treasure": "挖出一处埋藏的宝藏",
            "unlock": "撬开一个藏宝金箱"}[t]


class QuestBook:
    def __init__(self):
        self.active = []
        self.offers = {}        # npc kind -> quest or None (already taken today)
        self.completed = 0

    def new_day(self):
        self.offers = {}

    def offer(self, npc_kind):
        if npc_kind not in POOLS:
            return None
        if npc_kind not in self.offers:
            if any(q["giver"] == npc_kind for q in self.active):
                return None
            t, target, n = random.choice(POOLS[npc_kind])
            if t == "gather":
                coins = 20 + n * max(1, ITEMS[target].value) * 2
            elif t == "kill":
                coins = 20 + n * 12
            else:
                coins = 90
            extras = [(name, cnt) for name, cnt, chance in EXTRA_REWARDS if random.random() < chance]
            self.offers[npc_kind] = {"giver": npc_kind, "type": t, "target": target, "count": n,
                                     "progress": 0, "coins": coins, "extras": extras}
        return self.offers[npc_kind]

    def accept(self, npc_kind):
        q = self.offers.get(npc_kind)
        if q and len(self.active) < MAX_ACTIVE:
            self.active.append(q)
            self.offers[npc_kind] = None
            return True
        return False

    def event(self, kind, target=None, amount=1):
        for q in self.active:
            if q["type"] == kind and (q["type"] != "kill" or q["target"] == target):
                q["progress"] = min(q["count"], q["progress"] + amount)

    def progress(self, q, player):
        if q["type"] == "gather":
            return min(q["count"], player.inventory.count(q["target"]))
        return q["progress"]

    def ready(self, q, player):
        return self.progress(q, player) >= q["count"]

    def from_giver(self, npc_kind):
        return next((q for q in self.active if q["giver"] == npc_kind), None)

    def turn_in(self, npc_kind, player):
        """Complete the request from this NPC; returns the rewards [(item, count)] or None."""
        q = self.from_giver(npc_kind)
        if not q or not self.ready(q, player):
            return None
        if q["type"] == "gather":
            player.inventory.remove(q["target"], q["count"])
        self.active.remove(q)
        self.completed += 1
        return [("coin", q["coins"])] + list(q["extras"])
