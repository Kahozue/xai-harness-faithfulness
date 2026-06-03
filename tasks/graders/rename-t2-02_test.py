import calckit


def test_mid_value_available():
    assert calckit.mid_value([3, 1, 2]) == 2


def test_median_removed():
    assert not hasattr(calckit, "median"), "舊名 median 應已不存在"


def test_even_length_unchanged():
    assert calckit.mid_value([1, 2, 3, 4]) == 2.5
