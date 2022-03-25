import typing

import numpy as np
import scipy.spatial


# HTML4 named colors
_COLORS = [
    ("aqua", (0x00, 0xff, 0xff)),
    ("black", (0x00, 0x00, 0x00)),
    ("blue", (0x00, 0x00, 0xff)),
    ("fuchsia", (0xff, 0x00, 0xff)),
    ("green", (0x00, 0x80, 0x00)),
    ("gray", (0x80, 0x80, 0x80)),
    ("lime", (0x00, 0xff, 0x00)),
    ("maroon", (0x80, 0x00, 0x00)),
    ("navy", (0x00, 0x00, 0x80)),
    ("olive", (0x80, 0x80, 0x00)),
    ("purple", (0x80, 0x00, 0x80)),
    ("red", (0xff, 0x00, 0x00)),
    ("silver", (0xc0, 0xc0, 0xc0)),
    ("teal", (0x00, 0x80, 0x80)),
    ("white", (0xff, 0xff, 0xff)),
    ("yellow", (0xff, 0xff, 0x00))
]


_KDTREE = scipy.spatial.KDTree(
    np.array([list(color) for _, color in _COLORS], dtype=float)
)


def guess_color_name(color: typing.Iterable[int]) -> str:
    """
    Guess the name of an RGB color. Colors are based on the HTML4 named colors.

    :param color: three element tuple or array (range 0-255) representing the RGB color
    :return: name of the color as a string (e.g. "red")
    """
    color = np.array(color, dtype=float)
    if color.shape != (3,):
        raise ValueError("Color must have 3 components")
    _, color_index = _KDTREE.query(color)
    return _COLORS[color_index][0]
