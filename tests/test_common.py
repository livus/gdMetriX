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
Unittests for common.py
"""
import math
import random
import unittest

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX.common import *


class TestGetNodePosition(unittest.TestCase):

    def test_get_pos_from_None(self):
        g = nx.random_geometric_graph(25, 0.5)
        pos = get_node_positions(g)

        assert pos is not None
        assert isinstance(pos, dict)
        assert len(pos) == 25

    def test_get_pos_from_string(self):
        g = nx.random_geometric_graph(25, 0.5)
        pos = get_node_positions(g, "pos")

        assert pos is not None
        assert isinstance(pos, dict)
        assert len(pos) == 25

    def test_get_pos_from_string_2(self):
        random.seed(0)
        name = "pi90iu90u3908rujoieratsouzh"
        random_graph = nx.fast_gnp_random_graph(10, 0.5, 1000)
        random_embedding = {
            n: [random.randint(-100, 100), random.randint(-100, 100)]
            for n in range(0, 10)
        }
        nx.set_node_attributes(random_graph, random_embedding, name)

        pos = get_node_positions(random_graph, name)

        assert pos is not None
        assert isinstance(pos, dict)
        assert len(pos) == 10

    def test_get_pos_from_pos(self):
        random.seed(0)
        random_graph = nx.fast_gnp_random_graph(10, 0.5, 1000)
        random_embedding = {
            n: [random.randint(-100, 100), random.randint(-100, 100)]
            for n in range(0, 10)
        }
        nx.set_node_attributes(random_graph, random_embedding, "pos")

        pos = get_node_positions(random_graph, random_embedding)

        assert pos == random_embedding
        assert isinstance(pos, dict)
        assert len(pos) == 10


class TestVectorClass(object):

    def test_init(self):
        vec = Vector(1, 1.2)
        assert vec.x == 1
        assert vec.y == 1.2

    def test_creation_from_tuple(self):
        tup = [-3.7, 750]
        vec = Vector.from_point(tup)

        assert vec.x == tup[0]
        assert vec.y == tup[1]

    def test_upward_and_forward_direction_quadrant_1(self):
        vec = Vector(1.3, 1.5)

        flipped_vec = vec.upward_and_forward_direction()

        assert vec.x == flipped_vec.x
        assert vec.y == flipped_vec.y

    def test_upward_and_forward_direction_quadrant_2(self):
        vec = Vector(1.1, -1.2)
        flipped_vec = vec.upward_and_forward_direction()

        assert flipped_vec.x == -1.1
        assert flipped_vec.y == 1.2

    def test_upward_and_forward_direction_quadrant_3(self):
        vec = Vector(-1.4, -1.3)
        flipped_vec = vec.upward_and_forward_direction()

        assert flipped_vec.x == 1.4
        assert flipped_vec.y == 1.3

    def test_upward_and_forward_direction_quadrant_4(self):
        vec = Vector(-1.2, 1.7)
        flipped_vec = vec.upward_and_forward_direction()

        assert flipped_vec.x == -1.2
        assert flipped_vec.y == 1.7

    @pytest.mark.parametrize(
        "vec_a, vec_b, angle",
        [
            [Vector(0, 0), Vector(6, 12), 0],
            [Vector(49, 19), Vector(49, 19) * 2.4, 0],
            [Vector(543.2, 94.73), Vector(543.2, 94.73) * -0.45, math.pi],
            [Vector(1, 0), Vector(1, 1), 7 * math.pi / 4],
            [Vector(1, 1), Vector(1, 0), math.pi / 4],
        ],
    )
    def test_angle_between_vectors(self, vec_a, vec_b, angle):
        assert vec_a.angle(vec_b) == Angle(angle)

    @pytest.mark.parametrize(
        "x, y, rad",
        [
            [0, 0, 0],
            [1, 0, 0],
            [1, -1, 7 * math.pi / 4],
            [0, -1, 3 * math.pi / 2],
            [-1, -1, 5 * math.pi / 4],
            [-1, 0, math.pi],
            [-1, 1, 3 * math.pi / 4],
            [0, 1, math.pi / 2],
            [1, 1, math.pi / 4],
        ],
    )
    def test_radians(self, x, y, rad):
        vec = Vector(x, y)
        assert vec.rad() == Angle(rad)

    def test_rotate(self):
        random.seed(905809890)

        vec = Vector(random.uniform(0, 100), random.uniform(0, 100))
        for i in range(1, 25):
            print(i)
            angle = Angle(random.uniform(math.pi * -2, math.pi * 2))
            vec_rot = vec.rotate(angle)

            assert math.isclose(vec_rot.angle(vec).rad(), angle.rad() % (math.pi * 2))

    @pytest.mark.parametrize(
        "vec_a, vec_b, mid",
        [
            [Vector(0, 0), Vector(1, 1), Vector(0.5, 0.5)],
            [Vector(-1, 0), Vector(1, 1), Vector(0, 0.5)],
            [Vector(27, 5348), Vector(27969, 5), Vector(13998, 2676.5)],
            [Vector(0, 0), Vector(0, 0), Vector(0, 0)],
        ],
    )
    def test_mid(self, vec_a, vec_b, mid):
        mid_a = vec_a.mid(vec_b)
        assert math.isclose(mid_a.x, mid.x)
        assert math.isclose(mid_a.y, mid.y)

        mid_b = vec_b.mid(vec_a)
        assert math.isclose(mid_b.x, mid.x)
        assert math.isclose(mid_b.y, mid.y)

    @pytest.mark.parametrize(
        "vec_a, vec_b, dist",
        [
            [Vector(0, 0), Vector(0, 0), 0],
            [Vector(-1, 3.2), Vector(-1, 3.2), 0],
            [Vector(-1, -5), Vector(-1.75, -5), 0.75],
            [Vector(-1, -5), Vector(-1, -4.4), 0.6],
            [Vector(-0.5, -0.5), Vector(0.5, 0.5), math.sqrt(2)],
        ],
    )
    def test_euclidean_distance(self, vec_a, vec_b, dist):
        assert math.isclose(vec_a.distance(vec_b), dist)
        assert math.isclose(vec_b.distance(vec_a), dist)

    @pytest.mark.parametrize(
        "vec_a, vec_b, dot",
        [
            [Vector(0, 0), Vector(0, 0), 0],
            [Vector(1, 1), Vector(1, 1), 2],
            [Vector(2, 3), Vector(7, 4), 26],
            [Vector(-2, 3), Vector(-7, 4), 26],
            [Vector(-2, 3), Vector(7, -4), -26],
            [Vector(-2, -3), Vector(7, 4), -26],
            [Vector(0, 7), Vector(3, 0), 0],
        ],
    )
    def test_dot(self, vec_a, vec_b, dot):
        assert vec_a.dot(vec_b) == dot
        assert vec_b.dot(vec_a) == dot

    @pytest.mark.parametrize(
        "vec_a, vec_b, cross",
        [
            [Vector(0, 0), Vector(0, 0), 0],
            [Vector(1, 1), Vector(1, 1), 0],
            [Vector(2, 3), Vector(7, 4), -13],
            [Vector(0, 7), Vector(3, 0), -21],
        ],
    )
    def test_cross(self, vec_a, vec_b, cross):
        assert vec_a.cross(vec_b) == cross
        assert vec_b.cross(vec_a) == -cross

    @pytest.mark.parametrize(
        "vec_a, vec_b, vec_sum",
        [
            [Vector(0, 0), Vector(0, 0), Vector(0, 0)],
            [Vector(1, 0), Vector(3, -7), Vector(4, -7)],
            [Vector(1, 4.5), Vector(-3, -4.5), Vector(-2, 0)],
        ],
    )
    def test_addition(self, vec_a, vec_b, vec_sum):
        assert vec_a + vec_b == vec_sum
        assert vec_b + vec_a == vec_sum

    @pytest.mark.parametrize(
        "vec_a, scalar, mul",
        [
            [Vector(0, 0), 3, Vector(0, 0)],
            [Vector(1, -2), 0, Vector(0, 0)],
            [Vector(1, 8), -2, Vector(-2, -16)],
            [Vector(-0.3, -12), 3, Vector(-0.9, -36)],
        ],
    )
    def test_multiplication(self, vec_a, scalar, mul):
        result = vec_a * scalar
        assert math.isclose(result.x, mul.x)
        assert math.isclose(result.y, mul.y)

    @pytest.mark.parametrize(
        "vec_a, vec_b, vec_sum",
        [
            [Vector(0, 0), Vector(0, 0), Vector(0, 0)],
            [Vector(1, 0), Vector(3, -7), Vector(-2, 7)],
            [Vector(1, 4.5), Vector(-3, -4.5), Vector(4, 9)],
        ],
    )
    def test_subtraction(self, vec_a, vec_b, vec_sum):
        assert vec_a - vec_b == vec_sum

    @pytest.mark.parametrize(
        "vec_a, scalar, div",
        [
            [Vector(0, 0), 3, Vector(0, 0)],
            [Vector(1, 8), -2, Vector(-0.5, -4)],
            [Vector(-0.3, -12), 3, Vector(-0.1, -4)],
        ],
    )
    def test_division(self, vec_a, scalar, div):
        result = vec_a / scalar
        assert isinstance(result, Vector)
        assert math.isclose(result.x, div.x)
        assert math.isclose(result.y, div.y)

    def test_division_by_zero(self):
        def _div_by_zero():
            div = Vector(7, -3) / 0

        pytest.raises(ValueError, _div_by_zero)

    @pytest.mark.parametrize(
        "vec, absolute",
        [
            [Vector(0, 0), 0],
            [Vector(1, 0), 1],
            [Vector(0, 1), 1],
            [Vector(3, 4), 5],
            [Vector(39, -80), 89],
        ],
    )
    def test_absolute(self, vec, absolute):
        assert abs(vec) == absolute


class TestAngleClass(object):

    def test_init(self):
        angle = Angle(math.pi / 2)

    def test_float_conversion(self):
        angle = Angle(math.pi * -5)

        assert float(angle) == math.pi * -5

    def test_addition_rad(self):
        angle = Angle(math.pi)
        sum = angle + 5

        assert sum.rad() == math.pi + 5

    @pytest.mark.parametrize(
        "angle_a, angle_b, angle_sum",
        [
            [Angle(0), Angle(0), Angle(0)],
            [Angle(3), Angle(-7), Angle(-4)],
            [Angle(7), Angle(-2), Angle(5)],
            [Angle(0), 0, Angle(0)],
            [Angle(12), 4, Angle(16)],
        ],
    )
    def test_addition(self, angle_a, angle_b, angle_sum):
        assert angle_a + angle_b == angle_sum
        assert angle_b + angle_a == angle_sum

    @pytest.mark.parametrize(
        "angle_a, factor, result",
        [
            [Angle(0), 0, Angle(0)],
            [Angle(12), 3, Angle(36)],
            [Angle(2), -2, Angle(-4)],
        ],
    )
    def test_multiplication(self, angle_a, factor, result):
        assert angle_a * factor == result

    @pytest.mark.parametrize(
        "angle_a, angle_b, angle_sum",
        [
            [Angle(0), Angle(0), Angle(0)],
            [Angle(3), Angle(-7), Angle(10)],
            [Angle(-7), Angle(3), Angle(-10)],
            [Angle(0), 0, Angle(0)],
            [Angle(12), 4, Angle(8)],
        ],
    )
    def test_subtraction(self, angle_a, angle_b, angle_sum):
        assert angle_a - angle_b == angle_sum

    @pytest.mark.parametrize(
        "angle_a, mod, result",
        [
            [Angle(12), 3, Angle(0)],
            [Angle(math.pi * 4.5), math.pi, Angle(0.5 * math.pi)],
        ],
    )
    def test_modulo(self, angle_a, mod, result):
        assert angle_a % mod == result

    @pytest.mark.parametrize(
        "pre, post",
        [
            [0, 0],
            [math.pi, math.pi],
            [10 * math.pi, 10 * math.pi],
            [-1000, -1000],
        ],
    )
    def test_get_rad(self, pre, post):
        assert Angle(pre).rad() == post

    @pytest.mark.parametrize(
        "pre, post",
        [
            [0, 0],
            [math.pi, math.pi],
            [10 * math.pi, 10 * math.pi],
            [-1000, -1000],
        ],
    )
    def test_float_conversion(self, pre, post):
        assert float(Angle(pre)) == post

    @pytest.mark.parametrize(
        "pre, post",
        [
            [-math.pi / 2, -90],
            [-math.pi, -180],
            [-3 * math.pi / 2, -270],
            [-2 * math.pi, -360],
            [-10 * math.pi, -1800],
            [0, 0],
            [math.pi / 2, 90],
            [math.pi, 180],
            [3 * math.pi / 2, 270],
            [2 * math.pi, 360],
            [10 * math.pi, 1800],
        ],
    )
    def test_get_deg(self, pre, post):
        assert Angle(pre).deg() == post

    @pytest.mark.parametrize(
        "pre, post",
        [
            [-math.pi / 2, 270],
            [-math.pi, 180],
            [-3 * math.pi / 2, 90],
            [-2 * math.pi, 0],
            [-10 * math.pi, 0],
            [0, 0],
            [math.pi / 2, 90],
            [math.pi, 180],
            [3 * math.pi / 2, 270],
            [2 * math.pi, 0],
            [3 * math.pi, 180],
            [10 * math.pi, 0],
        ],
    )
    def test_get_norm(self, pre, post):
        assert Angle(pre).norm().deg() == post


class TestEuclideanDistance(object):

    @pytest.mark.parametrize(
        "a, b, result",
        [
            [(0, 0), (0, 0), 0],
            [(-1, 3.2), (-1, 3.2), 0],
            [(-1, -5), (-1.75, -5), 0.75],
            [(-1, -5), (-1, -4.4), 0.6],
            [(-0.5, -0.5), (0.5, 0.5), math.sqrt(2)],
        ],
    )
    def test_euclidean_distance(self, a, b, result):
        assert math.isclose(euclidean_distance(a, b), result)
        assert math.isclose(euclidean_distance(b, a), result)


class TestCircleFromPoints(object):

    @pytest.mark.parametrize(
        "pos_a, pos_b, center, radius",
        [
            ((0, 0), (0, 0), (0, 0), 0),
            ((-3, 7), (-3, 7), (-3, 7), 0),
            ((0, 0), (0, 1), (0, 0.5), 0.5),
            ((0, 0), (1, 0), (0.5, 0), 0.5),
            ((0, 0), (0, -1), (0, -0.5), 0.5),
            ((0, 0), (-1, 0), (-0.5, 0), 0.5),
            ((0, 0), (1, 1), (0.5, 0.5), math.sqrt(2) / 2),
            ((0, 0), (1, -1), (0.5, -0.5), math.sqrt(2) / 2),
            ((0, 0), (-1, 1), (-0.5, 0.5), math.sqrt(2) / 2),
            ((0, 0), (-1, -1), (-0.5, -0.5), math.sqrt(2) / 2),
            ((3, 12), (-4, 11), (-0.5, 11.5), math.sqrt(7**2 + 1**2) / 2),
        ],
    )
    def test_two_points(self, pos_a, pos_b, center, radius):
        center_result, radius_result = circle_from_two_points(
            Vector.from_point(pos_a), Vector.from_point(pos_b)
        )
        assert center_result == Vector.from_point(center)
        assert radius_result == radius

    @pytest.mark.parametrize(
        "pos_a, pos_b, pos_c, center, radius",
        [
            ((0, 0), (1, 0), (0, 1), (0.5, 0.5), 0.7071067811865476),
            ((1, 1), (2, 1), (1, 2), (1.5, 1.5), 0.7071067811865476),
            ((-1, -1), (-2, -1), (-1, -2), (-1.5, -1.5), 0.7071067811865476),
            ((0, 0), (0, 2), (2, 0), (1, 1), 1.4142135623730951),
            ((-1, 0), (1, 0), (0, 1), (0, 0), 1),
        ],
    )
    def test_three_points(self, pos_a, pos_b, pos_c, center, radius):
        center = Vector.from_point(center)
        center_result, radius_result = circle_from_three_points(
            Vector.from_point(pos_a), Vector.from_point(pos_b), Vector.from_point(pos_c)
        )

        assert center_result.x == pytest.approx(center.x, abs=1e-05)
        assert center_result.y == pytest.approx(center.y, abs=1e-05)
        assert radius_result == pytest.approx(radius, abs=1e-05)

    def test_three_random_points_on_circle(self):
        random.seed(9324809)

        for i in range(0, 1000):
            centre = Vector(
                random.uniform(-10000, 10000), random.uniform(-10000, 10000)
            )
            radius = random.uniform(0, 10000)

            angles = [random.uniform(0, math.pi * 2) for i in range(0, 3)]

            points = [
                Vector(
                    centre.x + math.sin(angle) * radius,
                    centre.y + math.cos(angle) * radius,
                )
                for angle in angles
            ]

            centre_result, radius_result = circle_from_three_points(
                points[0], points[1], points[2]
            )

            distance = centre.distance(centre_result)

            assert math.isclose(distance, 0, abs_tol=0.0001)
            assert math.isclose(radius, radius_result, abs_tol=0.0001)
