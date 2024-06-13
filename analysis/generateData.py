import os
import pickle

import networkx as nx

from gdMetriX import boundary, crossings, distribution, symmetry as sym


def _load_graph_from_file(path):
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


spring_graphs = "./SpringEmbedder/"


def save_data(data, filename, property_name, function, overwrite=False):
    if filename not in data:
        data[filename] = {}

    graph_data = data[filename]

    if property_name not in graph_data or overwrite:
        print(f"Obtaining {property_name} of {filename}")
        graph_data[property_name] = function()

        with open('data.pkl', 'wb') as pickle_file:
            pickle.dump(data, pickle_file)


data = {}

try:
    with open('data.pkl', 'rb') as pickle_file:
        data = pickle.load(pickle_file)
except:
    pass

print(data)

for filename in os.listdir(spring_graphs):
    print(filename)
    file_path = os.path.join(spring_graphs, filename)
    if not os.path.isfile(file_path):
        continue

    g = _load_graph_from_file(file_path)
    print(g.order())

    save_data(data, filename, "n", lambda: g.order())
    save_data(data, filename, "m", lambda: g.number_of_edges())
    save_data(data, filename, "m_dens", lambda: g.number_of_edges() / (g.order() * g.order()))
    save_data(data, filename, "area", lambda: boundary.area(g))
    save_data(data, filename, "area_tight", lambda: boundary.area_tight(g))
    save_data(data, filename, "concentration", lambda: distribution.concentration(g))
    save_data(data, filename, "crossings", lambda: crossings.number_of_crossings(g))


    if g.order() <= 1:
        save_data(data, filename, "pur",
                  lambda: sym.reflective_symmetry(g, tolerance=0.085, fraction=0.5, threshold=4))

    save_data(data, filename, "ref",
              lambda: sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE, pixel_merge=5, x_min=1,
                                              y_min=1))

    save_data(data, filename, "tra",
              lambda: sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL, pixel_merge=5, x_min=1,
                                              y_min=1))

    save_data(data, filename, "rot",
              lambda: sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL, pixel_merge=5, x_min=1,
                                              y_min=1))

    save_data(data, filename, "str", lambda: sym.stress(g))
    save_data(data, filename, "for", lambda: sym.even_neighborhood_distribution(g))
    save_data(data, filename, "viz", lambda: sym.visual_symmetry(g))
