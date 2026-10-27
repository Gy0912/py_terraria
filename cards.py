"""NPC card game (a small Gwent-like duel): best of three rounds, ten cards for the whole match.

Each turn a side plays one card or passes for the round; when both have passed the higher
board total wins the round. Cards are collected from packs, NPC victories and boss bags.
"""
import random

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from ui import draw_text, panel, Button

# name -> (power, kind, rarity); kind: unit / horn / frost / spy
CARDS = {
    "农夫": (1, "unit", "common"),
    "矿工": (2, "unit", "common"),
    "猎人": (3, "unit", "common"),
    "卫兵": (4, "unit", "common"),
    "铁匠": (5, "unit", "common"),
    "骑士": (6, "unit", "rare"),
    "法师": (7, "unit", "rare"),
    "巨魔": (8, "unit", "rare"),
    "史莱姆之王": (9, "unit", "boss"),
    "血瞳巨眼": (10, "unit", "boss"),
    "号角": (0, "horn", "rare"),
    "冰霜": (0, "frost", "rare"),
    "间谍": (4, "spy", "rare"),
}
CARD_HELP = {
    "horn": "号角：我方场上所有单位 +2",
    "frost": "冰霜：对方场上最强的单位变为 1",
    "spy": "间谍：把 4 点战力放到对方场上，自己抽 2 张牌",
}
STARTER = ["农夫"] * 3 + ["矿工"] * 3 + ["猎人"] * 3 + ["卫兵"] * 2 + ["铁匠"] * 2 + ["号角", "冰霜"]
PACK_POOL = [("农夫", 10), ("矿工", 10), ("猎人", 9), ("卫兵", 8), ("铁匠", 6), ("骑士", 3), ("法师", 2),
             ("巨魔", 1), ("号角", 3), ("冰霜", 3), ("间谍", 3)]
NPC_DECKS = {
    "guide": ["农夫"] * 4 + ["矿工"] * 4 + ["猎人"] * 4 + ["卫兵"] * 2 + ["号角"],
    "merchant": ["矿工"] * 3 + ["猎人"] * 3 + ["卫兵"] * 3 + ["铁匠"] * 2 + ["间谍"] * 3 + ["冰霜"],
    "blacksmith": ["猎人"] * 3 + ["卫兵"] * 3 + ["铁匠"] * 4 + ["骑士"] * 2 + ["巨魔"] + ["号角"] * 2,
    "traveler": ["矿工"] * 2 + ["卫兵"] * 3 + ["铁匠"] * 2 + ["法师"] * 2 + ["冰霜"] * 2 + ["间谍"] * 2 + ["号角"] * 2,
}
NPC_REWARD = {"guide": "骑士", "merchant": "间谍", "blacksmith": "巨魔", "traveler": "法师"}
HAND_SIZE = 10


def open_pack(rng=random):
    names = [n for n, _ in PACK_POOL]
    weights = [w for _, w in PACK_POOL]
    return rng.choices(names, weights, k=3)


class Side:
    def __init__(self, deck):
        self.deck = list(deck)
        random.shuffle(self.deck)
        self.hand = [self.deck.pop() for _ in range(min(HAND_SIZE, len(self.deck)))]
        self.board = []      # [name, power]
        self.lives = 2
        self.passed = False

    def total(self):
        return sum(p for _, p in self.board)

    def draw(self, n=1):
        for _ in range(n):
            if self.deck:
                self.hand.append(self.deck.pop())


class CardGame:
    def __init__(self, player_deck, npc_deck):
        self.sides = {"p": Side(player_deck), "o": Side(npc_deck)}
        self.round = 1
        self.turn = "p"
        self.starter = "p"
        self.log = ["第 1 局开始，你先出牌"]
        self.winner = None   # "p", "o" or "draw" when the match ends

    def other(self, who):
        return "o" if who == "p" else "p"

    def play(self, who, index):
        me, opp = self.sides[who], self.sides[self.other(who)]
        name = me.hand.pop(index)
        power, kind, _ = CARDS[name]
        actor = "你" if who == "p" else "对手"
        if kind == "unit":
            me.board.append([name, power])
        elif kind == "spy":
            opp.board.append([name, power])
            me.draw(2)
        elif kind == "horn":
            for unit in me.board:
                unit[1] += 2
        elif kind == "frost" and opp.board:
            max(opp.board, key=lambda u: u[1])[1] = 1
        self.log.append(f"{actor}打出了「{name}」")
        self._advance(who)

    def pass_round(self, who):
        self.sides[who].passed = True
        self.log.append(("你" if who == "p" else "对手") + "放弃了本局")
        self._advance(who)

    def _advance(self, who):
        p, o = self.sides["p"], self.sides["o"]
        for side in (p, o):
            if not side.hand:
                side.passed = True
        if p.passed and o.passed:
            self._end_round()
            return
        nxt = self.other(who)
        self.turn = nxt if not self.sides[nxt].passed else who

    def _end_round(self):
        p, o = self.sides["p"], self.sides["o"]
        tp, to = p.total(), o.total()
        if tp > to:
            o.lives -= 1
            self.log.append(f"第 {self.round} 局你赢了（{tp} : {to}）")
        elif to > tp:
            p.lives -= 1
            self.log.append(f"第 {self.round} 局对手赢了（{tp} : {to}）")
        else:
            p.lives -= 1
            o.lives -= 1
            self.log.append(f"第 {self.round} 局平局（{tp} : {to}）")
        if p.lives <= 0 or o.lives <= 0:
            self.winner = "draw" if p.lives == o.lives else ("p" if o.lives <= 0 else "o")
            return
        self.round += 1
        self.starter = self.other(self.starter)
        self.turn = self.starter
        for side in (p, o):
            side.board = []
            side.draw(1)
            side.passed = not side.hand
        self.log.append(f"第 {self.round} 局开始")
        if p.passed and o.passed:
            self._end_round()
        elif self.sides[self.turn].passed:
            self.turn = self.other(self.turn)

    # -------------------- AI --------------------

    def ai_move(self):
        me, opp = self.sides["o"], self.sides["p"]
        lead = me.total() - opp.total()
        hand = me.hand
        units = [(i, CARDS[n][0]) for i, n in enumerate(hand) if CARDS[n][1] == "unit"]
        specials = {CARDS[n][1]: i for i, n in enumerate(hand) if CARDS[n][1] != "unit"}
        last_life = me.lives == 1
        if opp.passed:
            if lead > 0:
                return self.pass_round("o")
            need = 1 - lead
            fits = sorted((p, i) for i, p in units if p >= need)
            if fits:
                return self.play("o", fits[0][1])
            if "frost" in specials and opp.board and max(u[1] for u in opp.board) - 1 >= need:
                return self.play("o", specials["frost"])
            if last_life and units:
                return self.play("o", max(units, key=lambda u: u[1])[0])
            return self.pass_round("o")
        if "spy" in specials and len(hand) >= 3 and self.round < 3:
            return self.play("o", specials["spy"])
        if "frost" in specials and opp.board and max(u[1] for u in opp.board) >= 6:
            return self.play("o", specials["frost"])
        if "horn" in specials and len(me.board) >= 3:
            return self.play("o", specials["horn"])
        if not last_life and lead > 8 and len(hand) <= len(opp.hand):
            return self.pass_round("o")
        if not units:
            return self.pass_round("o")
        units.sort(key=lambda u: u[1])
        pick = units[len(units) // 2] if last_life else units[0]
        return self.play("o", pick[0])


# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------

CW, CH = 62, 88
_TIER = [(110, 110, 120), (120, 150, 110), (90, 140, 190), (160, 110, 190), (210, 150, 60), (200, 60, 60)]


def draw_card(surf, name, rect, power=None, hover=False, back=False):
    rect = pygame.Rect(rect)
    if back:
        pygame.draw.rect(surf, (60, 40, 90), rect, border_radius=6)
        pygame.draw.rect(surf, (200, 180, 255), rect, 2, border_radius=6)
        draw_text(surf, "?", rect.center, 26, (200, 180, 255), center=True)
        return
    base, kind, rarity = CARDS[name]
    shown = base if power is None else power
    tier = 5 if rarity == "boss" else min(4, (base + 1) // 2) if kind == "unit" else 3
    col = _TIER[tier]
    pygame.draw.rect(surf, col, rect, border_radius=6)
    pygame.draw.rect(surf, (255, 225, 110) if rarity != "common" else (230, 230, 230), rect,
                     3 if hover else 2, border_radius=6)
    if kind in ("unit", "spy"):
        color = (120, 255, 140) if power is not None and power > base else \
            (255, 120, 120) if power is not None and power < base else (255, 255, 255)
        draw_text(surf, str(shown), (rect.x + 7, rect.y + 3), 22, color, bold=True)
    else:
        draw_text(surf, "★", (rect.x + 7, rect.y + 4), 20, (255, 240, 150))
    draw_text(surf, name, (rect.centerx, rect.bottom - 18), 13 if len(name) <= 3 else 11, center=True)


class CardPanel:
    """Full-screen modal: choose a stake, play the match, settle coins."""
    pauses = True

    def __init__(self, game, npc):
        self.game = game
        self.npc = npc
        self.state = "bet"
        self.match = None
        self.bet = 0
        self.ai_timer = 0
        coins = game.player.inventory.count("coin")
        cx = SCREEN_WIDTH // 2
        self.bet_buttons = [(Button(f"下注 {b}" if b else "不下注", (cx - 240 + i * 160, 330), (140, 44), 18), b)
                            for i, b in enumerate((0, 20, 50, 100)) if b <= coins]
        self.leave = Button("离开", (cx, 420), (140, 44), 18)
        self.pass_btn = Button("放弃本局", (SCREEN_WIDTH - 100, 330), (150, 44), 18)
        self.done_btn = Button("结束", (cx, 400), (160, 44), 20)

    def _hand_rects(self):
        hand = self.match.sides["p"].hand
        x0 = SCREEN_WIDTH // 2 - len(hand) * (CW + 6) // 2
        return [pygame.Rect(x0 + i * (CW + 6), SCREEN_HEIGHT - CH - 24, CW, CH) for i in range(len(hand))]

    def handle_event(self, event):
        """Returns True when the panel closes."""
        if self.state == "bet":
            for b, amount in self.bet_buttons:
                if b.clicked(event):
                    self.bet = amount
                    deck = self.game.player.cards
                    self.match = CardGame(deck, NPC_DECKS[self.npc.kind])
                    self.state = "play"
                    return False
            return self.leave.clicked(event)
        if self.state == "over":
            return self.done_btn.clicked(event)
        m = self.match
        if m.turn != "p":
            return False
        if self.pass_btn.clicked(event):
            m.pass_round("p")
            self._check_end()
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._hand_rects()):
                if r.collidepoint(event.pos):
                    m.play("p", i)
                    self._check_end()
                    break
        return False

    def update(self):
        if self.state != "play":
            return
        m = self.match
        if m.turn == "o" and m.winner is None:
            self.ai_timer += 1
            if self.ai_timer >= 40:
                self.ai_timer = 0
                m.ai_move()
                self._check_end()

    def _check_end(self):
        m = self.match
        if m.winner is None:
            return
        self.state = "over"
        g = self.game
        p = g.player
        if m.winner == "p":
            g.give("coin", self.bet)
            self.result = f"你赢了！获得 {self.bet} 金币" if self.bet else "你赢了！"
            reward = NPC_REWARD.get(self.npc.kind)
            key = f"card_win_{self.npc.kind}"
            if reward and not g.world.flags.get(key):
                g.world.flags[key] = True
                p.cards.append(reward)
                self.result += f"，{self.npc.name} 把稀有牌「{reward}」送给了你"
            g.quest_event("card_win", self.npc.kind)
        elif m.winner == "o":
            p.inventory.remove("coin", self.bet)
            self.result = f"你输了，付给 {self.npc.name} {self.bet} 金币" if self.bet else "你输了"
        else:
            self.result = "平局"

    def draw(self, surf):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((10, 30, 20, 235))
        surf.blit(dim, (0, 0))
        cx = SCREEN_WIDTH // 2
        if self.state == "bet":
            draw_text(surf, f"和 {self.npc.name} 打牌", (cx, 160), 34, (255, 235, 140), center=True, bold=True)
            draw_text(surf, f"你的牌组：{len(self.game.player.cards)} 张。三局两胜，开局抓 10 张牌用到底。",
                      (cx, 220), 16, center=True)
            draw_text(surf, "；".join(CARD_HELP.values()), (cx, 250), 14, (200, 230, 200), center=True)
            for b, _ in self.bet_buttons:
                b.draw(surf)
            self.leave.draw(surf)
            return
        m = self.match
        p, o = m.sides["p"], m.sides["o"]
        draw_text(surf, f"{self.npc.name}  " + "♦" * o.lives + f"   手牌 {len(o.hand)}" +
                  ("   已放弃" if o.passed else ""), (20, 16), 18, (255, 200, 200))
        draw_text(surf, f"第 {m.round} 局" + (f"   赌注 {self.bet}" if self.bet else ""), (cx, 22), 20,
                  (255, 235, 140), center=True)
        panel(surf, (20, 60, SCREEN_WIDTH - 40, CH + 20), 120)
        panel(surf, (20, 200, SCREEN_WIDTH - 40, CH + 20), 120)
        for i, (name, pw) in enumerate(o.board):
            draw_card(surf, name, (30 + i * (CW + 6), 70, CW, CH), pw)
        for i, (name, pw) in enumerate(p.board):
            draw_card(surf, name, (30 + i * (CW + 6), 210, CW, CH), pw)
        draw_text(surf, str(o.total()), (SCREEN_WIDTH - 70, 100), 34, (255, 170, 170), center=True, bold=True)
        draw_text(surf, str(p.total()), (SCREEN_WIDTH - 70, 240), 34, (170, 255, 170), center=True, bold=True)
        draw_text(surf, "你  " + "♦" * p.lives + ("   已放弃" if p.passed else ""), (20, 314), 18, (200, 255, 200))
        for i, line in enumerate(m.log[-4:]):
            draw_text(surf, line, (cx, 330 + i * 22), 15, (230, 230, 230), center=True)
        mouse = pygame.mouse.get_pos()
        for name, r in zip(p.hand, self._hand_rects()):
            hover = r.collidepoint(mouse) and m.turn == "p" and self.state == "play"
            draw_card(surf, name, r.move(0, -10) if hover else r, hover=hover)
            if hover and CARDS[name][1] in CARD_HELP:
                draw_text(surf, CARD_HELP[CARDS[name][1]], (cx, SCREEN_HEIGHT - CH - 56), 15,
                          (255, 240, 150), center=True)
        if self.state == "play":
            if m.turn == "p":
                self.pass_btn.draw(surf)
                draw_text(surf, "轮到你：点击手牌出牌", (SCREEN_WIDTH - 100, 300), 14, center=True)
            else:
                draw_text(surf, "对手思考中……", (SCREEN_WIDTH - 100, 330), 16, center=True)
        else:
            box = pygame.Rect(cx - 280, 300, 560, 140)
            panel(surf, box, 235)
            draw_text(surf, self.result, (cx, 340), 18, (255, 235, 140), center=True)
            self.done_btn.draw(surf)
