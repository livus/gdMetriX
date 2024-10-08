# gdMetriX
#
# Copyright (C) 2024  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
    Collects some basic classes used in other modules as well as useful methods.
"""

from __future__ import annotations

import math
from typing import Union, Tuple, List

import networkx as nx
import numpy as np

numeric = Union[int, float]


def get_node_positions(g, pos: Union[str, dict, None] = None) -> dict:
    """
    Tries to obtain the node positions for the given graph.

    If
        - pos is not supplied: Returns the positions of the 'pos' property in the graph - if present
        - pos is given as a string: Returns the positions saved in the properties of the graph under the that name
        - pos is a dictionary: Simply returns the given dictionary
    
    :param g: A networkX graph
    :type g: nx.Graph
    :param pos: Optional position value
    :type pos: Union[str, dict, None]
    :return: The node positions of the given graph
    :rtype: dict
    """
    if pos is None:
        pos = "pos"
    if not isinstance(pos, str):
        return pos
    return nx.get_node_attributes(g, pos)


class Vector:
    """
    Represents a simple 2-dimensional vector
    """

    def __init__(self, x: numeric, y: numeric):
        self.x = x
        self.y = y

    @staticmethod
    def from_point(pos: Tuple[numeric, numeric]) -> Vector:
        """
        Converts a tuple into a vector.

        :param pos: position tuple
        :type pos:
        :return: the converted vector
        :rtype: Vector
        """
        return Vector(pos[0], pos[1])

    def upward_and_forward_direction(self) -> Vector:
        """
        Flips the vector in order to point upwards and to the left.

        :return: A vector pointing upwards and forwards
        :rtype: Vector
        """
        return self if (self.y > 0 or (self.y == 0 and self.x >= 0)) else Vector(-self.x, -self.y)

    def _to_array(self) -> np.array:
        return np.asarray((self.x, self.y))

    def angle(self, other) -> Angle:
        """
        Obtains the clockwise angle from the vector to the given vector

        :param other: The second vector
        :type other: Vector
        :return: An angle between 0° and 360°
        :rtype: Angle
        """
        a = self._to_array()
        b = other._to_array()

        if self.x == self.y == 0 or other.x == other.y == 0:
            return Angle(0)

        det = np.linalg.det(np.array([b, a]))
        dot = np.dot(b, a)
        angle = Angle(np.arctan2(det, dot))

        if angle < 0:
            return Angle(math.pi * 2) + angle
        else:
            return angle

    def rad(self) -> Angle:
        """
        Obtains the radian of the vector as an angle object.

        :return: An angle between 0° and 360°
        :rtype: Angle
        """
        return self.angle(Vector(1, 0))

    def len(self) -> float:
        """
        Obtains the length of the vector.

        :return: Length of the vector
        :rtype: float
        """
        return abs(self)

    def rotate(self, angle: Angle) -> Vector:
        """
        Rotates the vector by the given angle counter-clockwise.

        :param angle: Angle to rotate by
        :type angle: Angle
        :return: the rotated vector
        :rtype: Vector
        """
        sin = math.sin(angle.rad())
        cos = math.cos(angle.rad())
        return Vector(self.x * cos - self.y * sin, self.x * sin + self.y * cos)

    def mid(self, other) -> Vector:
        """
        Returns the vector that is equidistant to the two given vectors.

        :param other: The second vector
        :type other: Vector
        :return: The midpoint
        :rtype: Vector
        """
        return (self + other) / 2

    def distance(self: Vector, other: Vector) -> float:
        """
        Obtains the euclidean distance between the two given vertices.

        :param other: The second vector
        :type other: Vector
        :return: The euclidean distance
        :rtype: float
        """
        return abs(self - other)

    def dot(self, other) -> float:
        """
        Obtains the dot product of the two given vertices.

        :param other: The second vector
        :type other: Vector
        :return: The dot product
        :rtype: float
        """
        return self.x * other.x + self.y * other.y

    def cross(self, other) -> float:
        """
        Obtains the cross product of t.

        :param other: The second vector
        :type other: Vector
        :return: The cross product
        :rtype: float
        """
        return self.x * other.y - self.y * other.x

    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar: float) -> Vector:
        return Vector(self.x * scalar, self.y * scalar)

    def __sub__(self, other: Vector) -> Vector:
        return Vector(self.x - other.x, self.y - other.y)

    def __truediv__(self, scalar: float) -> Vector:
        if scalar == 0:
            raise ValueError("Division by zero")
        return Vector(self.x / scalar, self.y / scalar)

    def __abs__(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __eq__(self, other: Vector) -> bool:
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return f"v({self.x},{self.y})"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y

        raise IndexError


class Angle(float):
    """
    A simple angle class for representing an angle as both radians and degrees.
    """

    def __init__(self, rad: float):
        self._rad = rad

    def __float__(self):
        return float(self._rad)

    def __add__(self, other) -> Angle:
        if isinstance(other, Angle):
            return Angle(self._rad + other._rad)
        else:
            return Angle(self._rad + other)

    def __mul__(self, other: float) -> Angle:
        return Angle(self._rad * other)

    def __sub__(self, other: float) -> Angle:
        return self + -other

    def __mod__(self, other: float):
        return Angle(self._rad % other)

    def deg(self) -> float:
        """
        Get the angle in degrees
        :return: Degrees
        :rtype: float
        """
        return np.degrees(self._rad)

    def rad(self) -> float:
        """
        Get the angle in radians
        :return:
        :rtype:
        """
        return self._rad

    def norm(self) -> Angle:
        """
        Gets the normalized angle within the range of [0°, 360°]
        :return: The normalized angle
        :rtype: Angle
        """
        return Angle(self._rad % (2 * math.pi))

    def __str__(self):
        return f"{self.deg():.2f}°"

    def __hash__(self):
        return hash(self._rad)


def euclidean_distance(point_a: Tuple[numeric, numeric], point_b: Tuple[numeric, numeric]) -> float:
    """
    Obtains the euclidean distance between point_a and point_b.

    :param point_a: Point a
    :type point_a: Tuple[numeric]
    :param point_b: Point b
    :type point_b: Tuple[numeric]
    :return: Euclidean distance
    :rtype: float
    """
    return Vector.from_point(point_a).distance(Vector.from_point(point_b))


Circle = Tuple[Vector, float]


def circle_from_two_points(a: Vector, b: Vector) -> Circle:
    """
    Calculates the smallest circle :math:`C` with a and b on the perimeter of :math:`C`.

    :param a: Point a
    :type a: gdMetriX.Vector
    :param b: Point b
    :type b: gdMetriX.Vector
    :return: The circle :math:`C`
    :rtype: gdMetriX.Circle
    """
    return a.mid(b), a.distance(b) / 2


def circle_from_three_points(a: Vector, b: Vector, c: Vector) -> Circle:
    """
    Calculates the unique circle :math:`C` defined by a, b and c with all points on the perimeter of :math:`C`.

    :param a: Point a
    :type a: gdMetriX.Vector
    :param b: Point b
    :type b: gdMetriX.Vector
    :param c: Point c
    :type c: gdMetriX.Vector
    :return: The circle :math:`C`
    :rtype: gdMetriX.Circle
    """
    ax, ay = a.x, a.y
    bx, by = b.x, b.y
    cx, cy = c.x, c.y
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))

    if d == 0:
        return None

    def _calculate_center_coordinate(factor_1, factor_2, factor_3):
        return ((ax ** 2 + ay ** 2) * factor_1 + (bx ** 2 + by ** 2) * factor_2 + (cx ** 2 + cy ** 2) * factor_3) / d

    ux = _calculate_center_coordinate(by - cy, cy - ay, ay - by)
    uy = _calculate_center_coordinate(cx - bx, ax - cx, bx - ax)

    center = Vector(ux, uy)
    radius = center.distance(a)

    return Vector(ux, uy), radius


def barycenter(points: List) -> Vector:
    """
    Calculates the barycenter of the given point set, i.e. the average point.
    :param points: List of tuples representing the points
    :type points: List
    :return: The barycenter
    :rtype: List
    """
    if not points:
        raise ValueError("Empty point set")

    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]

    return Vector(sum(x_coords) / len(points), sum(y_coords) / len(points))
