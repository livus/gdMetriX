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
    Unittests for edge_directions.py
"""

import math
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import edge_directions


class TestUpwardsFlow(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.DiGraph()

        flow = edge_directions.upwards_flow(g)

        assert flow == 0

    def test_singleton(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(213, 1.2))

        flow = edge_directions.upwards_flow(g)

        assert flow == 0

    def test_undirected_graph(self):
        g = nx.Graph()
        g.add_node(1, pos=(21, 29))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(12, 0.4))
        g.add_edges_from([(1, 2), (1, 3), (2, 3)])

        # noinspection PyTypeChecker
        flow = edge_directions.upwards_flow(g)

        assert flow == 0

    def test_single_edge_1(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_edge(1, 2)

        flow = edge_directions.upwards_flow(g)

        assert flow == 1

    def test_single_edge_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)

        flow = edge_directions.upwards_flow(g)

        assert flow == 1

    def test_single_edge_different_upwards_direction(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_edge(1, 2)

        flow = edge_directions.upwards_flow(g, direction_vector=(0, -1))

        assert flow == 0

    def test_single_edge_different_upwards_direction_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)

        flow = edge_directions.upwards_flow(g, direction_vector=(0, -1))

        assert flow == 0

    def test_orthogonal_edge_not_counted(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(5, 5))
        g.add_node(4, pos=(6, 5))
        g.add_edges_from([(1, 2), (3, 4)])

        flow = edge_directions.upwards_flow(g)

        assert flow == 0.5

    def test_orthogonal_edge_not_counted_custom_direction(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(0, 1))
        g.add_node(3, pos=(5, 5))
        g.add_node(4, pos=(4, 6))
        g.add_edges_from([(1, 2), (3, 4)])

        flow = edge_directions.upwards_flow(g, direction_vector=(1, 1))

        assert flow == 0.5


class TestAverageFlow(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.DiGraph()

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow is None

    def test_singleton(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(213, 1.2))

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow is None

    def test_undirected_graph(self):
        g = nx.Graph()
        g.add_node(1, pos=(21, 29))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(12, 0.4))
        g.add_edges_from([(1, 2), (1, 3), (2, 3)])

        # noinspection PyTypeChecker
        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow is None

    def test_opposite_vectors(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(3, 1), (3, 2)])

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow[0] == 0
        assert average_flow[1] == 0

    def test_opposite_vectors_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(-2, -2))
        g.add_node(2, pos=(1, 1))
        g.add_node(3, pos=(0, 0))
        g.add_edges_from([(3, 1), (3, 2)])

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow[0] == 0
        assert average_flow[1] == 0

    def test_single_edge_1(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(5, 5))
        g.add_edge(1, 2)

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert math.isclose(average_flow[0], math.cos(math.pi / 4))
        assert math.isclose(average_flow[1], math.sin(math.pi / 4))

    def test_single_edge_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(1.1, 1.1))
        g.add_edge(1, 2)

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert math.isclose(average_flow[0], math.cos(math.pi / 4))
        assert math.isclose(average_flow[1], math.sin(math.pi / 4))

    def test_single_edge_3(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1.5, -1))
        g.add_edge(1, 2)

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow[0] == -1
        assert average_flow[1] == 0

    def test_single_edge_4(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, -0.9))
        g.add_edge(1, 2)

        average_flow = edge_directions.average_flow(g)
        print(average_flow)

        assert average_flow[0] == 0
        assert average_flow[1] == 1

    def test_coherence_to_average_flow(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_edge(1, 2)

        coherence = edge_directions.coherence_to_average_flow(g)

        assert coherence == 1

    def test_coherence_to_average_flow_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(0, 0))
        g.add_node(3, pos=(2, 2))
        g.add_edge(1, 2)
        g.add_edge(2, 3)

        coherence = edge_directions.coherence_to_average_flow(g)

        assert coherence is None


class TestMinimumAngle(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        min_angle = edge_directions.minimum_angle(g)
        assert min_angle == 2 * math.pi

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))

        min_angle = edge_directions.minimum_angle(g, deg=True)
        assert math.isclose(min_angle, 360)

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))
        g.add_node(2, pos=(-2, 1))
        g.add_edge(1, 2)

        min_angle = edge_directions.minimum_angle(g, deg=True)
        assert min_angle == 360

    def test_edge_pair_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-1, 0))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        min_angle = edge_directions.minimum_angle(g, deg=False)
        assert min_angle == math.pi

    def test_edge_pair_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        min_angle = edge_directions.minimum_angle(g, deg=True)
        assert min_angle == 90

    def test_circle(self):
        for i in range(0, 360):
            g = nx.Graph()
            g.add_node(1, pos=(0, 0))
            g.add_node(2, pos=(1, 0))
            g.add_node(3, pos=(math.cos(math.radians(i)), math.sin(math.radians(i))))

            g.add_edge(1, 2)
            g.add_edge(1, 3)

            print(math.cos(math.radians(i)), math.sin(math.radians(i)))

            min_angle = edge_directions.minimum_angle(g, deg=True)
            assert math.isclose(min_angle, min(i, 360 - i))

            min_angle = edge_directions.minimum_angle(g)
            assert math.isclose(min_angle, min(math.radians(i), math.radians(360 - i)))


class TestAngularResolution(unittest.TestCase):
    def test_empty_graph(self):
        g = nx.Graph()

        resolution = edge_directions.angular_resolution(g)
        assert resolution == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))

        resolution = edge_directions.angular_resolution(g)
        assert resolution == 0

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))
        g.add_node(2, pos=(-2, 1))
        g.add_edge(1, 2)

        resolution = edge_directions.angular_resolution(g)
        assert resolution == 0

    def test_edge_pair_1(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(-1, 0))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        resolution = edge_directions.angular_resolution(g)
        assert resolution == 0

    def test_edge_pair_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(0, 1))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        resolution = edge_directions.angular_resolution(g)
        assert math.isclose(resolution, 0.5)

    def test_edge_pair_3(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(math.cos(math.radians(45)), math.sin(math.radians(45))))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        resolution = edge_directions.angular_resolution(g)
        assert math.isclose(resolution, 0.75)

    def test_edge_pair_4(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(1, 0))
        g.add_node(3, pos=(math.cos(math.radians(135)), math.sin(math.radians(135))))
        g.add_edge(1, 2)
        g.add_edge(1, 3)

        resolution = edge_directions.angular_resolution(g)
        assert math.isclose(resolution, 0.25)


class TestEdgeOrthogonality(unittest.TestCase):

    def test_horizontal_edge(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(2, 1))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 1)

    def test_vertical_edge(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 2))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 1)

    def test_45_degree_edge(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(2, 2))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 0)

    def test_45_degree_edge_2(self):
        g = nx.DiGraph()
        g.add_node(1, pos=(1, 1))
        g.add_node(2, pos=(2, 0))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 0)

    def test_inbetween_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(math.cos(math.pi / 8), math.sin(math.pi / 8)))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 0.5)

    def test_inbetween_edge_2(self):
        g = nx.Graph()
        g.add_node(1, pos=(0, 0))
        g.add_node(2, pos=(math.sin(math.pi / 16), math.cos(math.pi / 16)))
        g.add_edge(1, 2)

        orthogonality = edge_directions.edge_orthogonality(g)

        assert math.isclose(orthogonality, 0.75)


class TestEdgeLengthDeviation(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()

        len_der = edge_directions.edge_length_deviation(g)
        assert len_der == 0

    def test_singleton(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))

        len_der = edge_directions.edge_length_deviation(g)
        assert len_der == 0

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(213, 1.2))
        g.add_node(2, pos=(-2, 1))
        g.add_edge(1, 2)

        len_der = edge_directions.edge_length_deviation(g)
        assert len_der == 0

    def test_multiple_equal_edges(self):
        g = nx.Graph()
        g.add_node('start', pos=(0, 0))
        for i in range(0, 360):
            g.add_node(i, pos=(math.cos(math.radians(i)), math.sin(math.radians(i))))
            g.add_edge('start', i)

        len_der = edge_directions.edge_length_deviation(g)
        print(len_der)
        assert math.isclose(len_der, 0, abs_tol=1e-10)

    def test_double_size(self):
        g = nx.Graph()
        g.add_node(0, pos=(0, 0))
        g.add_node(1, pos=(0, 1))
        g.add_node(2, pos=(2, 0))

        g.add_edge(0, 1)
        g.add_edge(0, 2)

        len_der = edge_directions.edge_length_deviation(g)
        assert math.isclose(len_der, 1 / 3)
