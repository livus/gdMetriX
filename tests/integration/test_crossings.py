import random

import networkx as nx
import pytest
import gdMetriX
from gdMetriX import datasets, crossings


class TestDatasetGraphs(object):

    @pytest.mark.parametrize(
        "dataset_name",
        ["graphviz examples", "subways", "airlines-migration-air traffic"],
    )
    def test_dataset(self, dataset_name):
        for name, graph in datasets.iterate_dataset(dataset_name):
            if len(graph.edges()) < 1000:
                pos = gdMetriX.get_node_positions(graph)
                if len(pos) > 0:
                    print(name)

                    crossings_a = sorted(crossings.get_crossings(graph, pos))
                    crossings_b = sorted(crossings.get_crossings_quadratic(graph, pos))

                    assert crossings_a == crossings_b


class TestLargerGraphs(object):

    def test_random_graph(self):
        random.seed(9018098129039)
        success_count = 0
        for i in range(100, 200):
            for j in range(0, 2):
                print(f"Current graph: {success_count}")
                random_graph = nx.fast_gnp_random_graph(
                    i, random.uniform(0.1, 1), random.randint(1, 10000000)
                )
                random_embedding = {
                    n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for n in range(0, i + 1)
                }

                crossings_a = sorted(crossings.get_crossings(random_graph, random_embedding))
                crossings_b = sorted(crossings.get_crossings_quadratic(random_graph, random_embedding))
                assert crossings_a == crossings_b

                success_count += 1

    def test_random_graph_2(self):
        random.seed(9018098129039)
        success_count = 0
        for i in range(100, 200):
            for j in range(0, 2):
                print(f"Current graph: {success_count}")
                random_graph = nx.fast_gnp_random_graph(
                    i, random.uniform(0.1, 1), random.randint(1, 10000000)
                )
                random_embedding = {
                    n: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for n in range(0, i + 1)
                }

                crossings_a = sorted(crossings.get_crossings(random_graph, random_embedding))
                crossings_b = sorted(crossings.get_crossings_quadratic(random_graph, random_embedding))
                assert crossings_a == crossings_b
                success_count += 1

    def test_random_line_graph(self):
        # Random graph that should be in normal position

        random.seed(38528349829348)
        success_count = 0
        for i in range(100, 200):
            for j in range(0, 2):
                print(f"Current graph: {success_count}")
                random_graph = nx.Graph()

                for node in range(i):
                    random_graph.add_nodes_from([f"{i}a", f"{j}b"])
                    random_graph.add_edge(f"{i}a", f"{j}b")

                random_embedding = {
                    node: [random.randint(-1000, 1000), random.randint(-1000, 1000)]
                    for node in random_graph.nodes()
                }

                crossings_a = sorted(crossings.get_crossings(random_graph, random_embedding))
                crossings_b = sorted(crossings.get_crossings_quadratic(random_graph, random_embedding))
                assert crossings_a == crossings_b

                success_count += 1