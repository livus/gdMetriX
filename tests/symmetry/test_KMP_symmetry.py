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
    Unit tests for the edge-based symmetry by Klapaukh, Marshalh and Pearce
"""

import os
import random
import unittest

import networkx as nx
# noinspection PyUnresolvedReferences
import pytest
# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import symmetry as sym


class TestKlapaukhMarshallPearceSymmetry(unittest.TestCase):

    def test_empty_graph_translational(self):
        g = nx.Graph()

        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_empty_graph_rotational(self):
        g = nx.Graph()

        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_empty_graph_reflective(self):
        g = nx.Graph()

        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE)
        print(symmetry)
        assert symmetry == 1

    def test_single_node_translational(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_single_node_rotational(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_single_node_reflective(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE)
        print(symmetry)
        assert symmetry == 1

    def test_single_edge_translational(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL)
        print(symmetry)
        assert symmetry == 0

    def test_single_edge_rotational(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_single_edge_reflective(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE)
        print(symmetry)
        assert symmetry == 1

    def test_simple_rectangle_translational(self):
        g = nx.Graph()
        g.add_node(1, pos=(-1, -1))
        g.add_node(2, pos=(-1, 1))
        g.add_node(3, pos=(1, 1))
        g.add_node(4, pos=(1, -1))
        g.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])
        symmetry = sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL)
        print(symmetry)
        assert symmetry == 1

    def test_random_graph_stress_test_translational(self):
        random.seed(942589273489)
        for i in range(0, 50):
            random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.1, 0.3), random.randint(1, 10000000))
            random_embedding = {n: [random.randint(-100, 100), random.randint(-100, 100)] for n in range(0, i + 1)}
            nx.set_node_attributes(random_graph, random_embedding, "pos")

            symmetry = sym.edge_based_symmetry(random_graph, sym.SymmetryType.TRANSLATIONAL)
            print(symmetry)

            assert 0 <= symmetry <= 1

    def test_random_graph_stress_test_rotational(self):
        random.seed(942589273489)
        for i in range(0, 50):
            random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.1, 0.3), random.randint(1, 10000000))
            random_embedding = {n: [random.randint(-100, 100), random.randint(-100, 100)] for n in range(0, i + 1)}
            nx.set_node_attributes(random_graph, random_embedding, "pos")

            symmetry = sym.edge_based_symmetry(random_graph, sym.SymmetryType.ROTATIONAL)
            print(symmetry)

            assert 0 <= symmetry <= 1

    def test_random_graph_stress_test_reflective(self):
        random.seed(942589273489)
        for i in range(0, 50):
            random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.1, 0.3), random.randint(1, 10000000))
            random_embedding = {n: [random.randint(-100, 100), random.randint(-100, 100)] for n in range(0, i + 1)}
            nx.set_node_attributes(random_graph, random_embedding, "pos")

            symmetry = sym.edge_based_symmetry(random_graph, sym.SymmetryType.REFLECTIVE)
            print(symmetry)

            assert 0 <= symmetry <= 1


def _load_graph_from_file(file):
    path = os.path.dirname(__file__)
    path = os.path.join(path, "../data/", file)
    # with open(path) as f:

    #    graph = json.load(f)

    graph = nx.read_graphml(path)  # nx.node_link_graph(graph)

    def _convert_to_float(parameter: str):
        for edge, to_convert in nx.get_edge_attributes(graph, parameter).items():
            try:
                graph.edges[edge][parameter] = float(to_convert)
            except ValueError:
                pass

    _convert_to_float("x")
    _convert_to_float("y")

    x = nx.get_node_attributes(graph, "x")
    y = nx.get_node_attributes(graph, "y")

    pos = {key: [float(x_value), float(y[key])] for key, x_value in x.items()}
    nx.set_node_attributes(graph, pos, "pos")

    return graph


class TestEquivalenceToOriginalJavaImplementation_Reflective(object):

    @pytest.mark.parametrize("filename, expected_result", [
        ["symmetry-test-0.graphml", 1],
        ["symmetry-test-1.graphml", 1],
        ["symmetry-test-2.graphml", 1],
        ["symmetry-test-3.graphml", 1],
        ["symmetry-test-4.graphml", 1],
        ["symmetry-test-5.graphml", 1],
        ["symmetry-test-6.graphml", 0.5],
        ["symmetry-test-7.graphml", 1],
        ["symmetry-test-8.graphml", 1],
        ["symmetry-test-9.graphml", 0.333],
        ["symmetry-test-10.graphml", 1],
        # ["symmetry-test-11.graphml", 0.5],
        ["symmetry-test-12.graphml", 0.429],
        ["symmetry-test-13.graphml", 1],
        # ["symmetry-test-14.graphml", 0.167],
        # ["symmetry-test-15.graphml", 0.3],
        ["symmetry-test-16.graphml", 0.667],
        ["symmetry-test-17.graphml", 0.333],
        ["symmetry-test-18.graphml", 0.348],
        ["symmetry-test-19.graphml", 0.12],
        ["symmetry-test-20.graphml", 0.667],
        ["symmetry-test-21.graphml", 0.444],
        ["symmetry-test-22.graphml", 0.25],
        # ["symmetry-test-23.graphml", 0.222],
        ["symmetry-test-24.graphml", 0.583],
        # ["symmetry-test-25.graphml", 0.4],
        ["symmetry-test-26.graphml", 0.25],
        ["symmetry-test-27.graphml", 0.25],
        ["symmetry-test-28.graphml", 0.5],
        ["symmetry-test-29.graphml", 0.64],
        # ["symmetry-test-30.graphml", 0.571],
        ["symmetry-test-31.graphml", 0.396],
        ["symmetry-test-32.graphml", 0.686],
        # ["symmetry-test-33.graphml", 0.553],
        ["symmetry-test-34.graphml", 0.5],
        # ["symmetry-test-35.graphml", 0.621],
        ["symmetry-test-36.graphml", 0.467],
        # ["symmetry-test-37.graphml", 0.125],
        ["symmetry-test-38.graphml", 0.536],
        ["symmetry-test-39.graphml", 0.922],
        ["symmetry-test-40.graphml", 0.926],
        # ["symmetry-test-41.graphml", 0.846],
        ["symmetry-test-42.graphml", 0.382],
        # ["symmetry-test-43.graphml", 0.538],
        # ["symmetry-test-44.graphml", 0.858],
        ["symmetry-test-45.graphml", 0.895],
        ["symmetry-test-46.graphml", 0.913],
        ["symmetry-test-47.graphml", 0.771],
        ["symmetry-test-48.graphml", 0.5],
        ["symmetry-test-49.graphml", 0.967],
        ["symmetry-test-50.graphml", 0.834],
        ["symmetry-test-51.graphml", 0.968],
        # ["symmetry-test-52.graphml", 0.273],
        ["symmetry-test-53.graphml", 0.59],
        ["symmetry-test-54.graphml", 0.383],
        ["symmetry-test-55.graphml", 0.925],
        # ["symmetry-test-56.graphml", 0.188],
        ["symmetry-test-57.graphml", 0.913],
        # ["symmetry-test-58.graphml", 0.771],
        # ["symmetry-test-59.graphml", 0.975],
        ["symmetry-test-60.graphml", 0.902],
        ["symmetry-test-61.graphml", 0.85],
        ["symmetry-test-62.graphml", 0.798],
        # ["symmetry-test-63.graphml", 0.86],
        # ["symmetry-test-64.graphml", 0.897],
    ])
    def test_reflective_symmetry_default_parameters(self, filename, expected_result):
        graph = _load_graph_from_file(filename)
        symmetry = sym.edge_based_symmetry(graph, sym.SymmetryType.REFLECTIVE)

        print("Expected symmetry:", expected_result)
        print("Actual symmetry:", symmetry)

        assert abs(expected_result - symmetry) < 0.002


class TestEquivalenceToOriginalJavaImplementation_Translational(object):

    @pytest.mark.parametrize("filename, expected_result", [
        ["symmetry-test-0.graphml", 1],
        ["symmetry-test-1.graphml", 1],
        ["symmetry-test-2.graphml", 1],
        ["symmetry-test-3.graphml", 1],
        # ["symmetry-test-4.graphml", 1],
        ["symmetry-test-5.graphml", 1],
        ["symmetry-test-6.graphml", 1],
        ["symmetry-test-7.graphml", 1],
        ["symmetry-test-8.graphml", 1],
        ["symmetry-test-9.graphml", 0.667],
        ["symmetry-test-10.graphml", 1],
        ["symmetry-test-12.graphml", 0.429],
        ["symmetry-test-11.graphml", 0.667],
        ["symmetry-test-13.graphml", 1],
        ["symmetry-test-14.graphml", 0.333],
        ["symmetry-test-15.graphml", 0.7],
        ["symmetry-test-16.graphml", 0.5],
        ["symmetry-test-18.graphml", 0.261],
        ["symmetry-test-17.graphml", 0.667],
        ["symmetry-test-19.graphml", 0.6],
        ["symmetry-test-20.graphml", 0.667],
        ["symmetry-test-21.graphml", 0.481],
        ["symmetry-test-22.graphml", 0.125],
        ["symmetry-test-23.graphml", 0.778],
        ["symmetry-test-24.graphml", 0.417],
        ["symmetry-test-25.graphml", 0.267],
        ["symmetry-test-26.graphml", 0.75],
        ["symmetry-test-27.graphml", 0.5],
        ["symmetry-test-28.graphml", 1],
        ["symmetry-test-29.graphml", 0.32],
        ["symmetry-test-30.graphml", 0.805],
        ["symmetry-test-31.graphml", 0.792],
        ["symmetry-test-32.graphml", 0.725],
        ["symmetry-test-33.graphml", 0.638],
        ["symmetry-test-34.graphml", 1],
        ["symmetry-test-35.graphml", 0.727],
        ["symmetry-test-36.graphml", 0.578],
        ["symmetry-test-37.graphml", 0.375],
        ["symmetry-test-38.graphml", 0.429],
        ["symmetry-test-39.graphml", 0.883],
        ["symmetry-test-40.graphml", 0.91],
        ["symmetry-test-41.graphml", 0.846],
        ["symmetry-test-42.graphml", 0.471],
        ["symmetry-test-43.graphml", 0.154],
        ["symmetry-test-44.graphml", 0.92],
        ["symmetry-test-45.graphml", 0.816],
        ["symmetry-test-46.graphml", 0.855],
        ["symmetry-test-47.graphml", 0.905],
        ["symmetry-test-48.graphml", 0.417],
        ["symmetry-test-49.graphml", 0.905],
        ["symmetry-test-50.graphml", 0.905],
        ["symmetry-test-51.graphml", 0.956],
        ["symmetry-test-52.graphml", 0.182],
        ["symmetry-test-53.graphml", 0.795],
        ["symmetry-test-54.graphml", 0.723],
        ["symmetry-test-55.graphml", 0.916],
        ["symmetry-test-56.graphml", 0.5],
        ["symmetry-test-57.graphml", 0.959],
        ["symmetry-test-58.graphml", 0.934],
        ["symmetry-test-59.graphml", 0.947],
        ["symmetry-test-60.graphml", 0.922],
        ["symmetry-test-61.graphml", 0.875],
        ["symmetry-test-62.graphml", 0.974],
        ["symmetry-test-63.graphml", 0.754],
        ["symmetry-test-64.graphml", 0.921],
    ])
    def test_translational_symmetry_default_parameters(self, filename, expected_result):
        graph = _load_graph_from_file(filename)
        symmetry = sym.edge_based_symmetry(graph, sym.SymmetryType.TRANSLATIONAL)

        print("Expected symmetry:", expected_result)
        print("Actual symmetry:", symmetry)

        assert abs(expected_result - symmetry) < 0.002


class TestEquivalenceToOriginalJavaImplementation_Rotational(object):

    @pytest.mark.parametrize("filename, expected_result", [
        ["symmetry-test-0.graphml", 1],
        ["symmetry-test-1.graphml", 1],
        ["symmetry-test-2.graphml", 1],
        ["symmetry-test-3.graphml", 1],
        ["symmetry-test-4.graphml", 1],
        ["symmetry-test-5.graphml", 1],
        ["symmetry-test-6.graphml", 0.5],
        ["symmetry-test-7.graphml", 1],
        ["symmetry-test-8.graphml", 1],
        ["symmetry-test-9.graphml", 0.333],
        ["symmetry-test-10.graphml", 1],
        ["symmetry-test-11.graphml", 0.667],
        ["symmetry-test-12.graphml", 0.429],
        ["symmetry-test-13.graphml", 1],
        ["symmetry-test-14.graphml", 0.167],
        ["symmetry-test-15.graphml", 0.2],
        ["symmetry-test-16.graphml", 0.278],
        ["symmetry-test-17.graphml", 0.667],
        ["symmetry-test-18.graphml", 0.348],
        ["symmetry-test-19.graphml", 0.6],
        ["symmetry-test-20.graphml", 0.333],
        ["symmetry-test-21.graphml", 0.556],
        ["symmetry-test-22.graphml", 0.375],
        ["symmetry-test-23.graphml", 0.194],
        ["symmetry-test-24.graphml", 0.667],
        ["symmetry-test-25.graphml", 0.467],
        ["symmetry-test-26.graphml", 0.5],
        # ["symmetry-test-27.graphml", 0.25],
        ["symmetry-test-28.graphml", 0.5],
        ["symmetry-test-29.graphml", 0.76],
        ["symmetry-test-30.graphml", 0.857],
        ["symmetry-test-31.graphml", 0.896],
        ["symmetry-test-32.graphml", 0.902],
        ["symmetry-test-33.graphml", 0.766],
        ["symmetry-test-34.graphml", 0.5],
        ["symmetry-test-35.graphml", 0.97],
        ["symmetry-test-36.graphml", 0.911],
        # ["symmetry-test-37.graphml", 0.125],
        ["symmetry-test-38.graphml", 0.429],
        ["symmetry-test-39.graphml", 0.981],
        ["symmetry-test-40.graphml", 0.992],
        ["symmetry-test-41.graphml", 0.985],
        ["symmetry-test-42.graphml", 0.647],
        ["symmetry-test-43.graphml", 0.308],
        ["symmetry-test-44.graphml", 0.994],
        ["symmetry-test-45.graphml", 0.965],
        ["symmetry-test-46.graphml", 0.988],
        ["symmetry-test-47.graphml", 0.995],
        ["symmetry-test-48.graphml", 0.639],
        ["symmetry-test-49.graphml", 0.972],
        ["symmetry-test-50.graphml", 0.976],
        ["symmetry-test-51.graphml", 0.984],
        ["symmetry-test-52.graphml", 0.455],
        ["symmetry-test-53.graphml", 0.928],
        ["symmetry-test-54.graphml", 0.915],
        ["symmetry-test-55.graphml", 0.991],
        ["symmetry-test-56.graphml", 0.75],
        ["symmetry-test-57.graphml", 0.968],
        ["symmetry-test-58.graphml", 0.964],
        ["symmetry-test-59.graphml", 1],
        ["symmetry-test-60.graphml", 0.963],
        ["symmetry-test-61.graphml", 0.8],
        ["symmetry-test-62.graphml", 0.984],
        ["symmetry-test-63.graphml", 0.912],
        ["symmetry-test-64.graphml", 0.976]
    ])
    def test_rotational_symmetry_default_parameters(self, filename, expected_result):
        graph = _load_graph_from_file(filename)
        symmetry = sym.edge_based_symmetry(graph, sym.SymmetryType.ROTATIONAL)

        print("Expected symmetry:", expected_result)
        print("Actual symmetry:", symmetry)

        assert abs(expected_result - symmetry) < 0.002

    # def test_gen_files(self):

    #     for i in range(0, 256):
    #         size = random.randint(0, i * 2)
    #         random_graph = nx.fast_gnp_random_graph(i, random.uniform(0, 0.2), random.randint(1, 10000000))
    #         random_embedding = {n: [random.uniform(-100, 100), random.uniform(-100, 100)] for n in range(0, i + 1)}
    #         # nx.set_node_attributes(random_graph, random_embedding, "pos")

    #         for node in random_graph.nodes:
    #             random_graph.nodes[node]['x'] = random_embedding[node][0]
    #             random_graph.nodes[node]['y'] = random_embedding[node][1]

    #         for node in random_graph.nodes:
    #             for attrib in random_graph.nodes[node]:
    #                 print(attrib)
    #                 print(random_graph.nodes[node][attrib])
    #                 print(type(random_graph.nodes[node][attrib]))

    #         nx.write_graphml(random_graph, "./data/symmetry-test-{}.graphml".format(i))
