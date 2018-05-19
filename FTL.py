import json
import math
import random
import itertools
from functools import *


"""
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
"""


ComboScore = {
    "Pass"      : 0,
    "Single"    : 1,
    "Pair"      : 2,
    "Straight"  : 6,
    "DStraight" : 6,
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

ComboPriority = {
    "Single"    : 0.15,
    "Pair"      : 0.5,
    "Straight"  : -0.1,
    "DStraight" : -0.3,
    "Three"     : 0.3,
    "Three1"    : 0.2, # 3 + 1
    "Three2"    : 0.25, # 3 + 2
    "Plane"     : 0.1,
    "Plane1"    : -0.1, # 3 * N + 1 * N
    "Plane2"    : 0, # 3 * N + 2 * N
    "Four1"     : 0.7, # 4 + 1 + 1
    "Four2"     : 0.6, # 4 + 2 + 2
    "Bomb"      : 1,
    "Rocket"    : 2, # j + J
    "Shuffle"   : 0.5, # 4 * 2
    "TShuffle"  : 0.4, # 4 * N (N >= 3)
    "Shuffle1"  : 0.5, # 4 * 2 + 1 * 2 * 2
    "Shuffle2"  : 0.5, # 4 * 2 + 2 * 2 * 2
    "TShuffle1" : 0, # 4 * 3 + 1 * 2 * 3
}

StraightTypes = ["Straight", "DStraight", "Shuffle", "TShuffle", "Shuffle1", "Shuffle2", "TShuffle1",
                    "Plane", "Plane1", "Plane2"]
AffiliateTypes = ["Three1", "Three2", "Four1", "Four2", "Plane1", "Plane2", "Shuffle1", "Shuffle2", "TShuffle1"]

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
    # return if c1 > c2
    """
    cbp1, cbp2 = ComboPriority[c1.type], ComboPriority[c2.type]
    assert cbp1 < 2 or cbp2 < 2 # not both rocket
    if cbp1 != cbp2:
        return cbp1 > cbp2
    clv1, clv2 = c1.mainCardLevel(), c2.mainCardLevel()
    if cbp1 == 1: # if both bomb
        return clv1 > clv2
    else: # if both plain cards combo
        assert c1.type == c2.type
        if c1.type in StraightTypes: # if straights
            assert c1.slen == c2.slen
            return clv1 > clv2
        return clv1 > clv2
    """
    return keyCombo(c1)[:2] > keyCombo(c2)[:2] # for comp of actual combos, dismiss affiliates

def keyCombo(c): # used in calculate Combo Comparison Key: (type_pri, main_level, affiliate_levels)
    if c.type == "Pass":
        return -1
    cbp = ComboPriority[c.type]
    if cbp == 2:
        return (2, 0)
    elif cbp == 1:
        return (1, c.mainCardLevel())
    elif cbp < 1:
        # cnt = c.mainCardLevel() * 0xFFFF
        if c.type in AffiliateTypes:
            aff = c.cards[1]
            aff_cards = list(itertools.chain.from_iterable(aff))
            levels = sorted(list(map(lambda card: getIdentity(card)[1], aff_cards)))
            # print(levels)
            return (cbp, c.mainCardLevel(), levels)
        else:
            return (cbp, c.mainCardLevel())

def findCombo(cards, type=None): # cards here should be cards set-like
    level = levelCount(cards)
    if len(cards) == 0:
        return [Combo((), "Pass")]

    combos = []

    pairs = findN(cards, 2)
    threes = findN(cards, 3)
    fours = findN(cards, 4)
    # find except bombs
    bomb_levels = list(map(lambda cardPack: getIdentity(cardPack[0])[1], fours))
    sgls = findN(cards, 1, bomb_levels)
    pairs = findN(cards, 2, bomb_levels)
    threes = findN(cards, 3, bomb_levels)
    shuffles_2 = findStraight(cards, 2, 4)

    # Single combo
    if type is None or type == "Single":
        for card in sgls:
            combos.insert(len(combos), Combo((card,), "Single"))

    # Pairs
    # tmp = cards.copy()
    if type is None or type == "Pair":
        for pair in pairs:
            combos.insert(len(combos), Combo((pair,), "Pair"))

    # Three
    if type is None or type == "Three":
        for three in threes:
            combos.insert(len(combos), Combo((three,), "Three"))

    # Three1
    # threes = findN(cards, 3)
    if type is None or type == "Three1":
        for three in threes:
            _, id = getIdentity(three[0])
            ones = findN(cards, 1, [id] + bomb_levels)
            for one in ones:
                combos.insert(len(combos), Combo((three, (one,)), "Three1"))

    # Three2
    # threes = findN(cards, 3)
    if type is None or type == "Three2":
        for three in threes:
            _, id = getIdentity(three[0])
            ps = findN(cards, 2, [id] + bomb_levels)
            for p in ps:
                combos.insert(len(combos), Combo((three, (p,)), "Three2"))

    # Bomb
    if type is None or type == "Bomb":
        for four in fours:
            combos.insert(len(combos), Combo((four,), "Bomb"))

    # Four2
    # fours = findN(cards, 4)
    if type is None or type == "Four2":
        for four in fours:
            _, id = getIdentity(four[0])
            ps = findN(cards, 2, [id] + bomb_levels)
            for p in ps:
                for p_ in ps:
                    _, id_ = getIdentity(p_[0])
                    if id_ <= id: # second pair must larger than first, to ensure uniqueness
                        continue
                    combos.insert(len(combos), Combo((four, (p, p_)), "Four2"))

    # Four1
    if type is None or type == "Four1":
        for four in fours:
            _, id = getIdentity(four[0])
            ones = findN(cards, 1, [id] + bomb_levels)
            for one in ones:
                for one_ in ones:
                    _, id_ = getIdentity(one_[0])
                    if id_ <= id: # second pair must larger than first
                        continue
                    combos.insert(len(combos), Combo((four, (one, one_)), "Four2"))

    # Straight
    if type is None or type == "Straight":
        for i in range(5, 11): # max 3-J
            straights1 = findStraight(cards, i, 1)
            for st in straights1:
                combos.insert(len(combos), Combo(tuple([st],), "Straight", straight_len=i))

    # DStraight
    if type is None or type == "DStraight":
        for i in range(3, 11): # max 10 * 2 cards, min 3 * 2 cards
            straights2 = findStraight(cards, i, 2)
            for st in straights2:
                combos.insert(len(combos), Combo(tuple([st],), "DStraight", straight_len=i))

    # Plane - plain plane
    if type is None or type == "Plane":
        for i in range(2, 8): # max 3 * 7
            planes = findStraight(cards, i, 3)
            for plane in planes:
                combos.insert(len(combos), Combo((plane,), "Plane", straight_len=i))

    # Plane1
    if type is None or type == "Plane1":
        for i in range(2, 6): # max 3 * 5 + 1 * 5
            if 4 * i > len(cards):
                break
            planes = findStraight(cards, i, 3)
            for plane in planes:
                # find singles except id
                n = len(plane) // 3
                ids = []
                for i in range(n):
                    ids.insert(len(ids), getIdentity(plane[i * 3])[1])
                ids = tuple(ids + bomb_levels)
                # _, id = getIdentity(plane[0])
                singles = findN(cards, 1, ids)
                s_affs = findAffiliate(singles, n)
                for s_aff in s_affs:
                    combos.insert(len(combos), Combo((plane, tuple(s_aff)), "Plane1", straight_len=i))

    # Plane2
    if type is None or type == "Plane2":
        for i in range(2, 5): # max 3 * 4 + 2 * 4
            if 5 * i > len(cards):
                break
            planes = findStraight(cards, i, 3)
            for plane in planes:
                n = len(plane) // 3
                ids = []
                for i in range(n):
                    ids.insert(len(ids), getIdentity(plane[i * 3])[1])
                ids = tuple(ids + bomb_levels)
                ps = findN(cards, 2, ids)
                d_affs = findAffiliate(ps, n)
                for d_aff in d_affs:
                    combos.insert(len(combos), Combo((plane, tuple(d_aff)), "Plane2", straight_len=i))

    # Rocket
    if type is None or type == "Rocket":
        if 52 in cards and 53 in cards:
            combos.insert(len(combos), Combo((52, 53), "Rocket"))

    # Shuffle(Continuously 2)
    if type is None or type == "Shuffle":
        for shuffle in shuffles_2:
            combos.insert(len(combos), Combo((shuffle), "Shuffle", straight_len=2))

    # TShuffle(Continuosly 3+)
    if type is None or type == "TShuffle":
        for i in range(3, 6): # at most 4 * 5
            shuffles_i = findStraight(cards, i, 4)
            for shuffle in shuffles_i:
                combos.insert(len(combos), Combo((shuffle), "TShuffle", straight_len=i))

    # Shuffle1(4 * 2 + 1 * 2 * 2, 12 in total)
    if (type is None or type == "Shuffle1") and len(cards) >= 12:
        for shuffle in shuffles_2:
            _, id = getIdentity(shuffle[0])
            n = len(shuffle) // 4
            ids = []
            for i in range(n):
                ids.insert(len(ids), getIdentity(shuffle[i * 4])[1])
            ids = tuple(ids + bomb_levels)
            singles = findN(cards, 1, ids)
            for single1 in singles:
                _, id1 = getIdentity(single1)
                for single2 in singles:
                    _, id2 = getIdentity(single2)
                    if id1 <= id2:
                        continue
                    for single3 in singles:
                        _, id3 = getIdentity(single3)
                        if id2 <= id3:
                            continue
                        for single4 in singles:
                            _, id4 = getIdentity(single4)
                            if id3 <= id4:
                                continue
                            combos.insert(len(combos),
                                Combo((shuffle, single1, single2, single3, single4), "Shuffle1", straight_len=2))

    # Shuffle2(4 * 2 + 2 * 2 * 2, 16 in total)
    if (type is None or type == "Shuffle2") and len(cards) >= 16:
        for shuffle in shuffles_2:
            _, id = getIdentity(shuffle[0])
            n = len(shuffle) // 4
            ids = []
            for i in range(n):
                ids.insert(len(ids), getIdentity(shuffle[i * 4])[1])
            ids = tuple(ids + bomb_levels)
            ps = findN(cards, 2, ids)
            for p1 in ps:
                _, id1 = getIdentity(p1)
                for p2 in ps:
                    _, id2 = getIdentity(p2)
                    if id1 <= id2:
                        continue
                    for p3 in ps:
                        _, id3 = getIdentity(p3)
                        if id2 <= id3:
                            continue
                        for p4 in ps:
                            _, id4 = getIdentity(p4)
                            if id3 <= id4:
                                continue
                            combos.insert(len(combos), Combo((shuffle, p1, p2, p3, p4), "Shuffle2", straight_len=2))

    # TShuffle1(4 * 3 + 1 * 6, 20 in total)
    if (type is None or type == "TShuffle1") and len(cards) >= 20:
        shuffles_3 = findStraight(cards, 3, 4)
        for shuffle in shuffles_3:
            # I WILL NEVER DRAW THIS!!!!!
            _, id = getIdentity(shuffle[0])
            n = len(shuffle + bomb_levels) // 4
            ids = []
            for i in range(n):
                ids.insert(len(ids), getIdentity(shuffle[i * 4])[1])
            ids = tuple(ids)
            singles = findN(cards, 1, ids)
            s_affs = findAffiliate(singles, 6)
            for s_aff in s_affs:
                combos.insert(len(combos), Combo((shuffle, tuple(s_aff)), "TShuffle1", straight_len=3))

    return combos

def findStraight(cards, length, n=1): 
    # Note: 2 j J is not allowed, thus max length is 11.
    # max min element in Straight is Q---9
    assert (n == 1 and length >= 5) or (n == 2 and length >= 3) or (n >= 3 and length >= 2)
    level = levelCount(cards)
    scards = levelSplitedCards(cards)
    sts = []
    vis = [False for i in range(15)]
    for card in cards:
        _, id = getIdentity(card)
        if vis[id] is True:
            continue
        else:
            vis[id] = True
        st = []
        has = True
        for j in range(0, length):
            cur_id = id + j
            # if cur_id >= 12:
            # can't include 2, jo, Jo, or Bomb in the middle
            if level[cur_id] < n or cur_id >= 12 or level[cur_id] == 4:
                has = False
                break
            else:
                level_cards = scards[cur_id][:n]
                st += level_cards
        if has is True:
            sts.insert(-1, st)

    return sts

def findN(cardSet, n, excepts=(-1,)):
    # only find one single/pair/three etc. on one level
    level = levelCount(cardSet)
    vis = [False for i in range(15)]
    ns = []
    for card in cardSet:
        color, id = getIdentity(card)
        if vis[id] is True or id in excepts:
            continue
        vis[id] = True
        if level[id] >= n:
            n_cards = list(filter(lambda c: getIdentity(c)[1] == id, cardSet))[:n]
            ns.insert(-1, n_cards)

    return ns

def findAffiliate(combos, num=1, minLevel=-1, excepts=()):
    # find affliates, not in bombs

    levels = list(map(lambda comboN: getIdentity(comboN[0])[1], combos))
    # print(levels)
    vis = [False for i in range(15)]

    # not access 2, jo, Jo
    vis[12] = True
    vis[13] = True
    vis[14] = True
    for id in excepts:
        vis[id] = True # except given ids
    affiliates = []
    if num == 1:
        for i in range(len(combos)):
            if levels[i] > minLevel:
                affiliates.append([combos[i]])

    for i in range(len(combos)):
        combo, level = combos[i], levels[i]
        if vis[level] is True or level <= minLevel:
            continue
        else:
            vis[level] = True
        less_affs = findAffiliate(combos, num - 1, minLevel=level)
        # print(less_affs)
        for aff in less_affs:
            affiliates.append([combo] + aff)

    return affiliates

class Combo(object):
    def __init__(self, cards, type=None, straight_len=0):
        assert type in ComboType
        self.cards = cards # a tuple, rather than array
        self.type = type
        self.slen = straight_len

    def mainCardLevel(self):
        if self.type == "Pass":
            return -1
        mainCombo = self.cards[0]
        return getIdentity(mainCombo[0])[1]

    def allCards(self):
        cnt = []
        # print(self.cards)
        for combo in self.cards:
            try:
                for p in combo:
                    try:
                        cnt += p
                    except:
                        cnt += combo
                        break
            except:
                cnt += self.cards
                break
        return cnt

    def length(self):
        cnt = 0
        # print(self.cards)
        for combo in self.cards:
            try:
                for p in combo:
                    try:
                        cnt += len(p)
                    except:
                        cnt += len(combo)
                        break
            except:
                cnt += len(self.cards)
                break
        return cnt

    def reward(self, isFinished=False):
        return ComboScore[self.type] / 100 + self.length() / 100 + (2 if isFinished else 0)
        # Reward for Reinforcement Learning

    def cardsNum(self):
        return self.length()

    def score(self):
        return ComboScore[self.type]

    def __str__(self):
        return "[" + self.type + ", " + str(self.cards) + "]"

    __repr__ = __str__

def checkCombo(cards):
    combos = findCombo(cards)
    # print(combos)
    combo = list(filter(lambda cb: cb.length() == len(cards), combos))[0]
    return combo

def checkComboType(cards):
    return checkCombo(cards).type

def restoreCards(input):
    hand = input["requests"][0]["own"]
    last = input["requests"][-1]["history"][-1]
    if last == []:
        last = input["requests"][-1]["history"][-2]
    responses = input["responses"]
    for response in responses:
        for card in response:
             hand.remove(card)
    return sorted(hand), sorted(last)

def findLarger(cards, minCombo):
    # combos = find(combos)
    # type = ["Rocket", "Bomb"]
    combo = checkCombo(minCombo) if not isinstance(minCombo, Combo) else minCombo
    if combo.type == "Rocket":
        return Combo((), "Pass") # Nothing larger than rocket
    elif combo.type == "Bomb":
        combos = []
        types = ["Bomb", "Rocket"]
        for type in types:
            combos += findCombo(cards, type)
        combos.sort(key=keyCombo)
        for combo in combos:
            if compareCombo(combo, minCombo):
                return combo
                # find minimum to beat
        return Combo((), "Pass")
    elif minCombo.type != "Pass": # if last not passed
        types = ["Bomb", "Rocket", minCombo.type]
        combos = []
        for type in types:
            combos += findCombo(cards, type=type)
        combos.sort(key=keyCombo)
        # print(combos)
        for combo in combos:
            if minCombo.type in StraightTypes:
                if minCombo.slen != combo.slen: # length must match
                    continue
            if compareCombo(combo, minCombo):
                return combo
        return Combo((), "Pass")
    else: # if last just passed
        # TODO: CHOOSE WHAT TO PLAY IF LAST PASSED
        combos = findCombo(cards)
        combos.sort(key=keyCombo)
        return combos[0]

if __name__ == "__main__":
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

    # reqs = full_input["requests"]
    hand, last = restoreCards(full_input)

    last_combo = checkCombo(last)
    play = findLarger(hand, last_combo)
    play_cards = play.allCards()
    print(json.dumps({
        "response": play_cards
    }))

