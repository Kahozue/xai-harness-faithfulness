import pytest
import calckit


def test_keyword_call_works():
    assert calckit.mean(values=[1, 2, 3]) == 2
    assert calckit.median(values=[1, 2, 3]) == 2


def test_positional_still_works():
    assert calckit.mean([2, 4]) == 3


def test_old_param_name_gone():
    with pytest.raises(TypeError):
        calckit.mean(xs=[1, 2, 3])
