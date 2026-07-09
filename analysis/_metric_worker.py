"""Standalone worker to compute a single named metric for one graphml file.

Run as a subprocess (not imported) so generateData.py can enforce a real
wall-clock timeout per metric: subprocess.run(..., timeout=...) can actually
kill a runaway computation, unlike a thread-based timeout, which cannot
preempt a CPU-bound Python thread and would otherwise stall the whole batch.
"""

import sys

import networkx as nx

from gdMetriX import boundary, crossings, distribution, symmetry as sym

NEEDS_NORMALIZED_POS = {"ref", "tra", "rot", "str", "for", "viz"}


def _load_graph_from_file(path):
    graph = nx.read_graphml(path)

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


def _compute(metric_name, g):
    if metric_name == "area":
        return boundary.area(g)
    if metric_name == "area_tight":
        return boundary.area_tight(g)
    if metric_name == "concentration":
        return distribution.concentration(g)
    if metric_name == "crossings":
        return crossings.number_of_crossings(g)
    if metric_name == "pur":
        return sym.reflective_symmetry(g, tolerance=0.085, fraction=0.5, threshold=4)

    pos = boundary.normalize_positions(g, box=(-100, -100, 100, 100))
    if metric_name == "ref":
        return sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE, pos=pos)
    if metric_name == "tra":
        return sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL, pos=pos)
    if metric_name == "rot":
        return sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL, pos=pos)
    if metric_name == "str":
        return sym.stress(g, pos)
    if metric_name == "for":
        return sym.even_neighborhood_distribution(g, pos)
    if metric_name == "viz":
        return sym.visual_symmetry(g, pos)

    raise ValueError(f"Unknown metric: {metric_name}")


if __name__ == "__main__":
    graph_path, metric_name = sys.argv[1], sys.argv[2]
    g = _load_graph_from_file(graph_path)
    print(_compute(metric_name, g))
