import calckit


def test_to_float_available():
    assert calckit.to_float("$1,234.50") == 1234.5


def test_parse_amount_removed():
    assert not hasattr(calckit, "parse_amount"), "舊名 parse_amount 應已不存在"


def test_format_amount_still_works():
    assert calckit.format_amount(1234.5) == "$1,234.50"
