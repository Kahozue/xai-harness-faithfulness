from calckit import mean


def test_fractional():
    assert mean([1, 2]) == 1.5


def test_integer_unchanged():
    assert mean([1, 2, 3]) == 2
