from itertools import combinations

import pytest

from poker import HandCategory, best_hand, category, evaluate, evaluate_five

CATEGORY_EXAMPLES = {
    HandCategory.STRAIGHT_FLUSH: ["As", "Ks", "Qs", "Js", "Ts"],
    HandCategory.FOUR_OF_A_KIND: ["9s", "9h", "9c", "9d", "2s"],
    HandCategory.FULL_HOUSE: ["9s", "9h", "9c", "2d", "2s"],
    HandCategory.FLUSH: ["As", "Ks", "Qs", "Js", "9s"],
    HandCategory.STRAIGHT: ["Ah", "Ks", "Qs", "Js", "Ts"],
    HandCategory.THREE_OF_A_KIND: ["9s", "9h", "9c", "3d", "2s"],
    HandCategory.TWO_PAIR: ["9s", "9h", "3c", "3d", "2s"],
    HandCategory.ONE_PAIR: ["9s", "9h", "4c", "3d", "2s"],
    HandCategory.HIGH_CARD: ["Ks", "9h", "4c", "3d", "2s"],
}


@pytest.mark.parametrize(("expected", "hand"), CATEGORY_EXAMPLES.items())
def test_categories(expected, hand):
    assert category(evaluate_five(hand)) is expected


def test_category_ordering():
    values = [evaluate_five(CATEGORY_EXAMPLES[c]) for c in sorted(HandCategory)]
    assert values == sorted(values)


def test_wheel_is_lowest_straight():
    wheel = evaluate_five(["Ah", "2s", "3c", "4d", "5s"])
    six_high = evaluate_five(["2s", "3c", "4d", "5s", "6h"])
    assert category(wheel) is HandCategory.STRAIGHT
    assert wheel < six_high


def test_kickers_break_ties():
    assert evaluate_five(["As", "Ah", "Kc", "3d", "2s"]) > evaluate_five(
        ["Ac", "Ad", "Qc", "Jd", "9s"]
    )


def test_suits_do_not_break_ties():
    assert evaluate_five(["As", "Ah", "Kc", "3d", "2s"]) == evaluate_five(
        ["Ac", "Ad", "Kh", "3s", "2c"]
    )


def test_best_hand_from_seven():
    value, hand = best_hand(["As", "Ah", "Ac", "Kd", "Ks", "2c", "3d"])
    assert category(value) is HandCategory.FULL_HOUSE
    assert sorted(hand) == sorted(["As", "Ah", "Ac", "Kd", "Ks"])
    assert evaluate(["As", "Ah", "Ac", "Kd", "Ks", "2c", "3d"]) == value


def test_five_card_category_counts_on_reduced_deck():
    # exhaustive check over a 20-card deck (ranks T-A, all suits)
    deck = [r + s for r in "TJQKA" for s in "shcd"]
    counts = {c: 0 for c in HandCategory}
    for hand in combinations(deck, 5):
        counts[category(evaluate_five(hand))] += 1
    assert sum(counts.values()) == 15504
    assert counts[HandCategory.STRAIGHT_FLUSH] == 4
    assert counts[HandCategory.FOUR_OF_A_KIND] == 5 * 16
    assert counts[HandCategory.FULL_HOUSE] == 5 * 4 * 4 * 6
    assert counts[HandCategory.STRAIGHT] == 4**5 - 4
    assert counts[HandCategory.FLUSH] == 0  # only one 5-rank flush per suit: the straight flush
