# Standard Library
import math
from dataclasses import dataclass

Number = int | float
Point = tuple[Number, Number]
Size = Point
Coordinates = list[Point]


@dataclass
class Line:
    coordinates: Coordinates

    @property
    def length(self):
        lengths = []
        pc = None
        for c in self.coordinates:
            if pc is not None:
                lengths.append(math.hypot(pc[0] - c[0], pc[1] - c[1]))
            pc = c

        return sum(lengths)

    def fit(self, size: Size, padding: Number = 5):
        self.rotate()
        self.normalize()

        def per(val):
            return round((val / 100) * padding)

        p = max([per(size[0]), per(size[0])])

        self.scale((size[0] - p, size[1] - p))
        self.center(size)

    def swap(self):
        self.coordinates = [(c[1], c[0]) for c in self.coordinates]

    def normalize(self):
        min_x = min(p[0] for p in self.coordinates)
        min_y = min(p[1] for p in self.coordinates)

        self.coordinates = [(c[0] - min_x, c[1] - min_y) for c in self.coordinates]

    def move(self, x: Number, y: Number):
        self.coordinates = [(c[0] + x, c[1] + y) for c in self.coordinates]

    def center(self, size: Size):
        max_x = max(p[0] for p in self.coordinates)
        max_y = max(p[1] for p in self.coordinates)

        m_x = (size[0] - max_x) / 2
        m_y = (size[1] - max_y) / 2

        self.move(m_x, m_y)

    def scale(self, to: Size):
        max_x = max(p[0] for p in self.coordinates)
        max_y = max(p[1] for p in self.coordinates)

        img_landscape = to[0] > to[1]
        map_landscape = max_x > max_y

        m_to = min(to) if img_landscape != map_landscape else max(to)
        mul = m_to / max([max_x, max_y])

        def s(val):
            return round(val * mul)

        self.coordinates = [(s(c[0]), s(c[1])) for c in self.coordinates]

    def rotate(self):
        def rotate_point(origin: Point, point: Point, angle: float) -> Point:
            ox, oy = origin
            px, py = point

            qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
            qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
            return (qx, qy)

        o = (max(p[0] for p in self.coordinates) / 2, max(p[1] for p in self.coordinates) / 2)

        self.coordinates = [rotate_point(o, c, math.radians(-90)) for c in self.coordinates]

    def svg_path(self):
        path = []
        op = "M"
        for c in self.coordinates:
            path.append(f"{op} {round(c[0])} {round(c[1])}")
            op = "L"

        return " ".join(path)

    def __str__(self) -> str:
        return self.svg_path()
