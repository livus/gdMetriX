import os
import random

import networkx as nx

from gdMetriX import boundary

# Random
for i in range(0, 80):
    print(i)
    for density in range(10, 100, 10):
        try:
            os.makedirs(f"./RandomGraphs/{density}")
        except:
            pass
        random_graph = nx.fast_gnp_random_graph(i, density / 100.0, random.randint(1, 10000000))
        random_embedding = {n: [random.uniform(0, 1), random.uniform(0, 1)] for n in range(0, i + 1)}
        # nx.set_node_attributes(random_graph, random_embedding, "pos")
        # pos2 = nx.spring_layout(g)
        # pos2 = boundary.normalize_positions(g, pos2, (0, 0, 1, 1))
        # nx.set_node_attributes(g, pos2, "pos")

        for node in random_graph.nodes:
            random_graph.nodes[node]['x'] = random_embedding[node][0]
            random_graph.nodes[node]['y'] = random_embedding[node][1]

        nx.write_graphml(random_graph, f"./RandomGraphs/{density}/{i:03}.graphml")

x = 1 / 0
# Spring embedder
for i in range(0, 255):
    print(i)
    g = nx.fast_gnp_random_graph(random.randint(5, 12), random.uniform(0, 1), random.randint(1, 10000000))
    pos2 = nx.spring_layout(g)
    pos2 = boundary.normalize_positions(g, pos2, (0, 0, 1, 1))
    # nx.set_node_attributes(g, pos2, "pos")

    for node in g.nodes:
        g.nodes[node]['x'] = pos2[node][0]
        g.nodes[node]['y'] = pos2[node][1]

    nx.write_graphml(g, f"./SpringEmbedder/{i}.graphml")
