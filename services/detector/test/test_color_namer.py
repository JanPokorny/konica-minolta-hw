from color_namer import guess_color_name
import numpy as np
import pytest


def test_guess_color_name():
    assert guess_color_name((230, 0, 0)) == "red"
    assert guess_color_name([0, 241, 0]) == "lime"
    assert guess_color_name(np.array([0, 0, 237])) == "blue"
    assert guess_color_name((4, 2, 11)) == "black"
    assert guess_color_name((220, 245, 251)) == "white"
    with pytest.raises(ValueError):
        guess_color_name((0, 0, 0, 0))
    with pytest.raises(ValueError):
        guess_color_name((0, 0))
