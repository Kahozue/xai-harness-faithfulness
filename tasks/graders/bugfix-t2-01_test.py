from calckit import parse_amount


def test_parenthesized_negative():
    assert parse_amount("($1,234.50)") == -1234.50


def test_plain_negative_sign_still_works():
    assert parse_amount("-$50.00") == -50.00


def test_positive_unchanged():
    assert parse_amount("$1,234.50") == 1234.50
