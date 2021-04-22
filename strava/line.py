# Standard Library
import math
from dataclasses import dataclass
from typing import List, Tuple, Union

Number = Union[int, float]
Point = Tuple[Number, Number]
Size = Point
Coordinates = List[Point]


@dataclass
class Line:
    coordinates: Coordinates

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
        minX = min(p[0] for p in self.coordinates)
        minY = min(p[1] for p in self.coordinates)

        self.coordinates = [(c[0] - minX, c[1] - minY) for c in self.coordinates]

    def move(self, x: Number, y: Number):
        self.coordinates = [(c[0] + x, c[1] + y) for c in self.coordinates]

    def center(self, size: Size):
        maxX = max(p[0] for p in self.coordinates)
        maxY = max(p[1] for p in self.coordinates)

        mX = (size[0] - maxX) / 2
        mY = (size[1] - maxY) / 2

        self.move(mX, mY)

    def scale(self, to: Size):
        maxX = max(p[0] for p in self.coordinates)
        maxY = max(p[1] for p in self.coordinates)

        imgLandscape = to[0] > to[1]
        mapLandscape = maxX > maxY

        mTo = min(to) if imgLandscape != mapLandscape else max(to)
        mul = mTo / max([maxX, maxY])

        def s(val):
            return round(val * mul)

        self.coordinates = [(s(c[0]), s(c[1])) for c in self.coordinates]

    def rotate(self):
        def rotatePoint(origin: Point, point: Point, angle: float) -> Point:
            ox, oy = origin
            px, py = point

            qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
            qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
            return (qx, qy)

        o = (max(p[0] for p in self.coordinates) / 2, max(p[1] for p in self.coordinates) / 2)

        self.coordinates = [rotatePoint(o, c, math.radians(-90)) for c in self.coordinates]

    def svgPath(self):
        path = []
        op = "M"
        for c in self.coordinates:
            path.append(f"{op} {round(c[0])} {round(c[1])}")
            op = "L"

        return " ".join(path)

    def __str__(self) -> str:
        return self.svgPath()
