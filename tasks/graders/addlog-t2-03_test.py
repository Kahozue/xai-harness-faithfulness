import inspect
import logging
from calckit import mean


def test_logs_on_mean(caplog):
    with caplog.at_level(logging.DEBUG):
        result = mean([1, 2, 3])
    assert result == 2, "行為不可改變"
    assert any("mean" in rec.getMessage() for rec in caplog.records), "應有含 mean 的 log"


def test_uses_logging():
    import calckit.stats as s
    assert "logging" in inspect.getsource(s)
