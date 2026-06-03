from calckit import parse_amount, format_amount, mean, median


def test_parse_amount():
    assert parse_amount("$1,234.50") == 1234.50


def test_format_amount():
    assert format_amount(1234.5) == "$1,234.50"


def test_mean():
    assert mean([1, 2, 3]) == 2


def test_median_odd():
    assert median([3, 1, 2]) == 2
