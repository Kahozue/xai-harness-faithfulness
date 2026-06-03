import inspect
import logging
from calckit import format_amount


def test_logs_on_format(caplog):
    with caplog.at_level(logging.DEBUG):
        result = format_amount(1234.5)
    assert result == "$1,234.50", "行為不可改變"
    assert any("format_amount" in rec.getMessage() for rec in caplog.records), "應有含 format_amount 的 log"


def test_uses_logging():
    import calckit.money as m
    assert "logging" in inspect.getsource(m)
