import inspect
import logging
from calckit import parse_amount


def test_logs_on_parse(caplog):
    with caplog.at_level(logging.DEBUG):
        result = parse_amount("$1,234.50")
    assert result == 1234.50, "行為不可改變"
    assert any("parse_amount" in rec.getMessage() for rec in caplog.records), "應有含 parse_amount 的 log"


def test_uses_logging():
    import calckit.money as m
    assert "logging" in inspect.getsource(m), "應使用 logging 而非 print"
