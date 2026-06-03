import calckit


def test_to_string_available():
    assert calckit.to_string(1234.5) == "$1,234.50"


def test_format_amount_removed():
    assert not hasattr(calckit, "format_amount"), "舊名 format_amount 應已不存在"


def test_parse_amount_still_works():
    assert calckit.parse_amount("$1,234.50") == 1234.5
