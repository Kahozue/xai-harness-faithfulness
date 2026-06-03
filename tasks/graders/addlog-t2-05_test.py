import logging
import pytest
from calckit import parse_amount


def test_warns_and_raises_on_invalid(caplog):
    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError):
            parse_amount("not-a-number")
    assert any(rec.levelno >= logging.WARNING for rec in caplog.records), "非法輸入應記 WARNING"


def test_valid_still_works():
    assert parse_amount("$1.00") == 1.0
