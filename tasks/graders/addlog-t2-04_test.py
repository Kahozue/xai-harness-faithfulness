import inspect
import logging
from calckit import median


def test_logs_on_median(caplog):
    with caplog.at_level(logging.DEBUG):
        result = median([3, 1, 2])
    assert result == 2, "行為不可改變"
    assert any("median" in rec.getMessage() for rec in caplog.records), "應有含 median 的 log"


def test_uses_logging():
    import calckit.stats as s
    assert "logging" in inspect.getsource(s)
