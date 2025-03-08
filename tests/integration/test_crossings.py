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
