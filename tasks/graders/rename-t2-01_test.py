import calckit


def test_average_available():
    assert calckit.average([1, 2, 3]) == 2


def test_mean_removed():
    assert not hasattr(calckit, "mean"), "舊名 mean 應已不存在"


def test_behavior_unchanged():
    assert calckit.average([10, 20]) == 15
