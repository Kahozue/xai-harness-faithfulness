from calckit import format_amount


def test_negative_keeps_sign():
    assert format_amount(-12.5) == "$-12.50"


def test_positive_unchanged():
    assert format_amount(1234.5) == "$1,234.50"
