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
Unit tests for the stress-based symmetry metric
"""

import random
import unittest

import networkx as nx

# noinspection PyUnresolvedReferences
import pytest

from gdMetriX import symmetry as sym
from gdMetriX import boundary


class TestStressBasedSymmetry(unittest.TestCase):

    def test_empty_graph(self):
        g = nx.Graph()
        symmetry = sym.stress(g)
        print(symmetry)
        assert symmetry == pytest.approx(0)

    def test_single_node(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        symmetry = sym.stress(g)
        print(symmetry)
        assert symmetry == pytest.approx(0)

    def test_single_edge(self):
        g = nx.Graph()
        g.add_node(1, pos=(123, -45))
        g.add_node(2, pos=(1, 1))
        g.add_edge(1, 2)
        symmetry = sym.stress(g)
        print(symmetry)
        assert symmetry == pytest.approx(0, abs=1e-05)

    def test_scale_independence(self):
        random.seed(32842)
        for i in range(1, 10):
            random_graph = nx.fast_gnp_random_graph(
                i * 5, random.uniform(0.1, 1), random.randint(1, 10000000)
            )
            random_embedding = {
                n: [random.uniform(-100, 100), random.uniform(-100, 100)]
                for n in range(0, i * 5 + 1)
            }
            random_embedding = boundary.normalize_positions(
                random_graph, random_embedding
            )

            symmetry = sym.stress(random_graph, random_embedding)
            print("Symmetry:", symmetry)

            for j in range(0, 3):
                scale_factor = random.uniform(0.0001, 1000)
                print("Scale factor", scale_factor)

                scaled_embedding = {
                    key: (p[0] * scale_factor, p[1] * scale_factor)
                    for key, p in random_embedding.items()
                }
                scaled_symmetry = sym.stress(random_graph, scaled_embedding)

                print("Scaled symmetry", scaled_symmetry)

                assert scaled_symmetry == pytest.approx(symmetry, abs=0.5)
