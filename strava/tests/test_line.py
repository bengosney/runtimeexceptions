import pytest

from strava.line import Line


@pytest.mark.parametrize(
    "coordinates, expected",
    [
        ([(0, 0), (3, 4)], 5),
        ([(0, 0), (0, 1), (0, 4)], 4),
    ],
)
def test_length(coordinates, expected):
    line = Line(coordinates)
    assert line.length == expected


def test_swap():
    line = Line([(1, 2), (3, 4)])
    line.swap()
    assert line.coordinates == [(2, 1), (4, 3)]


def test_normalize():
    line = Line([(2, 3), (5, 7)])
    line.normalize()
    assert line.coordinates == [(0, 0), (3, 4)]


def test_move():
    line = Line([(1, 1), (2, 2)])
    line.move(3, 4)
    assert line.coordinates == [(4, 5), (5, 6)]


def test_center():
    line = Line([(0, 0), (2, 2)])
    line.center((6, 6))
    xs = [c[0] for c in line.coordinates]
    ys = [c[1] for c in line.coordinates]
    assert min(xs) == 2 and min(ys) == 2  # noqa: PLR2004
    assert max(xs) == 4 and max(ys) == 4  # noqa: PLR2004


def test_scale():
    line = Line([(0, 0), (2, 2)])
    line.scale((4, 4))
    assert (0, 0) in line.coordinates and (4, 4) in line.coordinates


def test_rotate():
    line = Line([(0, 0), (0, 2)])
    line.rotate()
    assert pytest.approx(line.coordinates[0][0]) == -1
    assert pytest.approx(line.coordinates[0][1]) == 1
    assert pytest.approx(line.coordinates[1][0]) == 1
    assert pytest.approx(line.coordinates[1][1]) == 1


def test_svg_path():
    line = Line([(0, 0), (1, 1), (2, 2)])
    path = line.svg_path()
    assert path.startswith("M 0 0 L 1 1 L 2 2")


def test_str():
    line = Line([(0, 0), (1, 1)])
    assert str(line) == line.svg_path()
