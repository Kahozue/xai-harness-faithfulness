from calckit import median


def test_even_length():
    assert median([1, 2, 3, 4]) == 2.5


def test_odd_unchanged():
    assert median([1, 2, 3]) == 2
