import json
import math
import random
from functools import *

full_input = json.loads(input())
"""
full_input example:
{"requests":
	[
		{"own":[25,12,38,41,27,20,48,36,17,34,51,52,37,45,31,6,46],
		"history":[[],[26,29,32,39,40]],
		"publiccard":[14,7,19]
		},
		{"history":[[],[4,7,8,9,10,13,14,15,18,19]]},
		{"history":[[],[0,1,2,3]]}
	],
"responses":[[],[]]}
"""

my_history = full_input["responses"]
use_info = full_input["requests"][0]
poker, history, publiccard = use_info["own"], use_info["history"], use_info["publiccard"]
last_history = full_input["requests"][-1]["history"]

currBotID = 0 # 判断自己是什么身份，地主0 or 农民甲1 or 农民乙2
if len(history[0]) == 0:
    if len(history[1]) != 0:
        currBotID = 1
else:
    currBotID = 2
history = history[2-currBotID:]

reqs = full_input["requests"]
played_cards = [False for i in range(54)]
owned_cards = [False for i in range(54)]

# State: levels-played (1 * 15) + levels-owned (1 * 15) => (2 * 15)

for card in reqs[0]["own"]:
    owned_cards[card] = True

for req in reqs:
    for cards in req["history"]:
        for card in cards:
            played_cards[card] = True
for response in full_input["responses"]:
    for card in response:
        played_cards[card] = False

ComboScore = {
    "Single"    : 1,
    "Pair"      : 2,
    "Straight"  : 6,
    "DStaight"  : 6,
    "Three"     : 4,
    "Three1"    : 4, # 3 + 1
    "Three2"    : 4, # 3 + 2
    "Plane"     : 8,
    "Plane1"    : 8, # 3 * N + 1 * N
    "Plane2"    : 8, # 3 * N + 2 * N
    "Four1"     : 8, # 4 + 1 + 1
    "Four2"     : 8, # 4 + 2 + 2
    "Bomb"      : 10,
    "Rocket"    : 16, # j + J
    "Shuffle"   : 10, # 4 * 2
    "TShuffle"  : 20, # 4 * N (N >= 3)
    "Shuffle1"  : 10, # 4 * 2 + 1 * 2 * 2
    "Shuffle2"  : 10, # 4 * 2 + 2 * 2 * 2
    "TShuffle1" : 20, # 4 * 3 + 1 * 2 * 3
}

ComboType = set(ComboScore.keys())

# 3 4 5 6 7 8 9 10 J Q K  A  2  jo Jo
# 0 1 2 3 4 5 6 7  8 9 10 11 12 13 14

# Colors:
# Heart, Diamond, Spade, Club, joker, Joker: 0, 1, 2, 3, 4, 5
# Numbers: 3, 4, 5,..., K, A, 2, joker, Joker:0, 1, 2,..., 13, 14
def getIdentity(card):
    # return color, number
    assert card < 54 and card >=0
    if card < 52: # if not jokers
        return card % 4, card // 4
    elif card == 52:
        return 4, 13
    elif card == 53:
        return 5, 14
    else:
        raise ValueError("Not Expected Card " + str(card))

# return count of cards of same level...
def levelCount(cards): # card is a set
    clvls = list(map(lambda card: getIdentity(card)[1], cards))
    level = [0 for i in range(15)]
    for clvl in clvls:
        level[clvl] += 1
    return level

def levelSplitedCards(cards):
    scards = [[] for i in range(15)]
    for card in cards: # level ranges from 0 to 14
        scards[getIdentity(card)[1]].insert(0, card)
    return scards


def compareCombo(c1, c2):
    # TODO: COMPARE COMBO
    pass

def findCombo(cards): # cards here should be cards set
    # TODO: FIND COMBOS, and TYPES
    level = levelCount(cards)
    combos = []

    # Single combo
    for card in cards:
        combos.insert(0, Combo([card], "Single"))

    # Pairs
    # tmp = cards.copy()
    pairs = findN(cards, 2)
    for pair in pairs:
        combos.insert(0, Combo(pair, "Pair"))

    # Three
    threes = findN(cards, 3)
    for three in threes:
        combos.insert(0, Combo(three, "Pair"))

    # Three1
    # threes = findN(cards, 3)
    for three in threes:
        _, id = getIdentity(three[0])
        ones = findN(cards, 1, [id])
        for one in ones:
            combos.insert(0, Combo(three + one, "Three1"))

    # Three2
    # threes = findN(cards, 3)
    for three in threes:
        _, id = getIdentity(three[0])
        ps = findN(cards, 2, [id])
        for p in ps:
            combos.insert(0, Combo(three + p, "Three1"))

    # Bomb
    fours = findN(cards, 4)
    for four in fours:
        combos.insert(0, Combo(four, "Bomb"))

    # Four2
    # fours = findN(cards, 4)
    for four in fours:
        _, id = getIdentity(four[0])
        ps = findN(cards, 2, [id])
        for p in ps:
            for p_ in ps:
                _, id_ = getIdentity(p_[0])
                if id_ <= id: # second pair must larger than first
                    continue
                combos.insert(0, Combo(four + p + p_, "Four2"))

    #Four1
    for four in fours:
        _, id = getIdentity(four[0])
        ones = findN(cards, 1, [id])
        for one in ones:
            for one_ in ones:
                _, id_ = getIdentity(one_[0])
                if id_ <= id: # second pair must larger than first
                    continue
                combos.insert(0, Combo(four + one + one_, "Four2"))

    # Straight
    for i in range(5, 11): # max 3-J
        starights1 = findStraight(cards, i, 1)
        for st in starights1:
            combos.insert(0, Combo(st, "Straight"))

    # DStraight
    for i in range(3, 11): # max 10 * 2 cards, min 3 * 2 cards
        starights2 = findStraight(cards, i, 2)
        for st in starights2:
            combos.insert(0, Combo(st, "DStraight"))

    # Plane - plain plane
    for i in range(3, 8): # max 3 * 7
        planes = findStraight(cards, i, 3)
        for plane in planes:
            combos.insert(0, Combo(plane, "Plane"))

    #Plane1
    for i in range(3, 6): # max 3 * 5 + 1 * 5
        planes = findStraight(cards, i, 3)
        for plane in planes:
            

    return combos

def findStraight(cards, length, n=1): 
    # Note: 2 j J is not allowed, thus max length is 11.
    # max min element in Straight is Q---9
    assert (n == 1 and length >= 5) or (n >= 2 and length >= 3)
    level = levelCount(cards)
    scards = levelSplitedCards(cards)
    sts = []
    vis = [False for i in range(10)]
    for card in cards:
        _, id = getIdentity(card)
        st = []
        has = True
        for j in range(0, length):
            cur_id = id + j
            # if cur_id >= 12:
            if level[cur_id] < n or cur_id >= 12: # can't include 2, jo, Jo
                has = False
                break
            else:
                level_cards = scards[cur_id][:n]
                st += level_cards
        if has is True:
            sts.insert(0, st)

    return sts


def findN(cardSet, n, excepts=[]):
    level = levelCount(cards)
    vis = [False for i in range(15)]
    ns = []
    for card in cardSet:
        color, id = getIdentity(card)
        if vis[id] is True or id in excepts:
            continue
        vis[id] = True
        if level[id] >= n:
            n_cards = list(filter(lambda c: getIdentity(c)[1] == id, cardSet))[:n]
            ns.insert(0, n_cards)

    return ns






class Combo(object):
    def __init__(self, cards, type = None):
        assert type in ComboType
        self.cards = cards # a set, rather than array
        self.type = type

    def reward(self, isFinished=False):
        return ComboScore[self.type] / 100 + len(cards) / 100 + (2 if isFinished else 0)
        # Reward for Reinforcement Learning

    def cardsNum(self):
        return len(self.cards)

    def score(self):
        return ComboScore[self.type]

    def __str__(self):
        return "[" + self.type + ", " + str(self.cards) + "]"

    __repr__ = __str__




