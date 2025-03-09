# gdMetriX
#
# Copyright (C) 2025  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
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
Unittests for datasets.py
"""
import itertools
import unittest

import networkx

# noinspection PyUnresolvedReferences
import pytest

# noinspection PyUnresolvedReferences
import pytest_socket

from gdMetriX import datasets


def _test_graph_loaded(graph, test_attributes=False):
    assert graph is not None
    assert graph.order() > 0
    assert len(graph.edges()) > 0

    if test_attributes:

        for attr in networkx.get_edge_attributes(graph, "weight").values():
            assert attr is None or isinstance(attr, (int, float, complex))
        for attr in networkx.get_node_attributes(graph, "weight").values():
            assert attr is None or isinstance(attr, (int, float, complex))
        for attr in networkx.get_node_attributes(graph, "x").values():
            assert attr is None or isinstance(attr, (int, float, complex))
        for attr in networkx.get_node_attributes(graph, "y").values():
            assert attr is None or isinstance(attr, (int, float, complex))
        for attr in networkx.get_node_attributes(graph, "pos").values():
            assert attr is None or (
                len(attr) == 2
                and isinstance(attr[0], (int, float, complex))
                and isinstance(attr[1], (int, float, complex))
            )

        if len(networkx.get_node_attributes(graph, "x")) > 0 and len(
            networkx.get_node_attributes(graph, "y")
        ):
            assert len(networkx.get_node_attributes(graph, "pos")) > 0


class TestDatasetLoading(unittest.TestCase):

    @pytest.mark.xdist_group("benchmark_group")
    def test_get_list_of_available_files(self):
        available_datasets = datasets.get_available_datasets()
        assert len(available_datasets) > 0

        for dataset in available_datasets:
            assert dataset != ""

        assert len(available_datasets) == len(set(available_datasets))

    @pytest.mark.xdist_group("benchmark_group")
    def test_try_getting_non_existent_dataset(self):
        def _call_non_existent_list():
            for _ in datasets.iterate_dataset("I definitely do not exist"):
                pass

        self.assertRaises(KeyError, _call_non_existent_list)

    @pytest.mark.xdist_group("benchmark_group")
    def test_disable_sockets_should_not_throw_after_cache(self):
        pytest_socket.enable_socket()
        datasets.get_available_datasets()
        pytest_socket.disable_socket()
        available_datasets = datasets.get_available_datasets()
        assert len(available_datasets) > 0
        pytest_socket.enable_socket()


class TestDatasetIterateGraphs(unittest.TestCase):

    @pytest.mark.xdist_group("benchmark_group")
    def test_iterate_dataset_adapt_parameters(self):
        available_datasets = datasets.get_available_datasets()
        assert len(available_datasets) > 0

        for dataset_name in available_datasets:
            print(dataset_name)
            has_elements = False
            for name, graph in itertools.islice(
                datasets.iterate_dataset(dataset_name), 5
            ):
                assert name is not None
                assert len(name) > 0
                _test_graph_loaded(graph, test_attributes=True)
                has_elements = True

            assert has_elements

    @pytest.mark.xdist_group("benchmark_group")
    def test_iterate_dataset_do_not_adapt_parameters(self):
        available_datasets = datasets.get_available_datasets()
        assert len(available_datasets) > 0

        for dataset_name in available_datasets:
            print(dataset_name)
            has_elements = False
            for name, graph in itertools.islice(
                datasets.iterate_dataset(dataset_name, adapt_attributes=False), 5
            ):
                assert name is not None
                _test_graph_loaded(graph)
                has_elements = True

            assert has_elements

    @pytest.mark.xdist_group("benchmark_group")
    def test_disable_sockets_should_not_throw_after_cache(self):
        pytest_socket.enable_socket()

        dataset_name = datasets.get_available_datasets()[0]

        # Make sure all graphs are downloaded from that dataset
        for _ in datasets.iterate_dataset(dataset_name):
            pass

        pytest_socket.disable_socket()

        for _, _ in itertools.islice(
            datasets.iterate_dataset(dataset_name, adapt_attributes=False), 2
        ):
            pass

        pytest_socket.enable_socket()


class TestAvailableGraphNames(unittest.TestCase):

    @pytest.mark.xdist_group("benchmark_group")
    def test_existing_dataset(self):
        dataset_name = datasets.get_available_datasets()[3]
        graph_names = list(datasets.get_available_graph_names(dataset_name))

        assert graph_names is not None
        assert len(graph_names) > 0

        for graph_name in graph_names:
            assert isinstance(graph_name, str)
            assert len(graph_name) > 0

    @pytest.mark.xdist_group("benchmark_group")
    def test_non_existent_dataset(self):
        dataset_name = "I definitely do not exist"

        with pytest.raises(KeyError):
            list(datasets.get_available_graph_names(dataset_name))

    @pytest.mark.xdist_group("benchmark_group")
    def test_disable_sockets_should_not_throw_after_cache(self):
        pytest_socket.enable_socket()

        dataset_name = datasets.get_available_datasets()[3]
        list(datasets.get_available_graph_names(dataset_name))

        pytest_socket.disable_socket()

        list(datasets.get_available_graph_names(dataset_name))

        pytest_socket.enable_socket()


class TestLoadingSpecificGraph(unittest.TestCase):

    @pytest.mark.xdist_group("benchmark_group")
    def test_existing_dataset_and_graph(self):
        dataset_name = datasets.get_available_datasets()[2]

        graph_name = None
        for name in datasets.get_available_graph_names(dataset_name):
            graph_name = name
            break

        assert graph_name is not None
        assert isinstance(graph_name, str)
        assert len(graph_name) > 0

        graph = datasets.get_specific_graph(
            dataset_name, graph_name, adapt_attributes=False
        )

        _test_graph_loaded(graph)

    @pytest.mark.xdist_group("benchmark_group")
    def test_existing_dataset_and_graph_adapt_attributes(self):
        dataset_name = datasets.get_available_datasets()[2]

        graph_name = None
        for name in datasets.get_available_graph_names(dataset_name):
            graph_name = name
            break

        assert graph_name is not None
        assert isinstance(graph_name, str)
        assert len(graph_name) > 0

        graph = datasets.get_specific_graph(dataset_name, graph_name)

        _test_graph_loaded(graph, True)

    @pytest.mark.xdist_group("benchmark_group")
    def test_non_existent_database(self):
        dataset_name = "I definitely do not exist"

        with pytest.raises(KeyError):
            datasets.get_specific_graph(dataset_name, "graph_name")

    @pytest.mark.xdist_group("benchmark_group")
    def test_non_existent_graph(self):
        dataset_name = datasets.get_available_datasets()[1]

        with pytest.raises(KeyError):
            datasets.get_specific_graph(dataset_name, "I definitely do not exist")

    @pytest.mark.xdist_group("benchmark_group")
    def test_disable_sockets_should_not_throw_after_cache(self):
        pytest_socket.enable_socket()

        dataset_name = datasets.get_available_datasets()[1]
        graph_name = None
        for name in datasets.get_available_graph_names(dataset_name):
            graph_name = name
            break

        pytest_socket.disable_socket()

        graph = datasets.get_specific_graph(dataset_name, graph_name)
        assert graph is not None

        pytest_socket.enable_socket()
