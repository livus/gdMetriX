import os
import pickle
import subprocess
import sys
import time

import networkx as nx

METRIC_TIMEOUT_SECONDS = 120
HEARTBEAT_SECONDS = 15
METRIC_WORKER = os.path.join(os.path.dirname(__file__), "_metric_worker.py")


def _compute_with_timeout(file_path, metric_name):
    start = time.time()
    proc = subprocess.Popen(
        [sys.executable, METRIC_WORKER, file_path, metric_name],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    while True:
        try:
            stdout, stderr = proc.communicate(timeout=HEARTBEAT_SECONDS)
            break
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            if elapsed >= METRIC_TIMEOUT_SECONDS:
                proc.kill()
                proc.wait()
                print(f"  {metric_name} timed out after {METRIC_TIMEOUT_SECONDS}s on {file_path}, skipping",
                      flush=True)
                return None
            print(f"  ...still computing {metric_name} on {file_path} ({elapsed:.0f}s elapsed)", flush=True)

    if proc.returncode != 0 or not stdout.strip():
        print(f"  {metric_name} failed on {file_path}: {stderr.strip()}", flush=True)
        return None

    return float(stdout.strip())


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
        print(f"Obtaining {property_name} of {filename}", flush=True)
        result = function()

        # Don't cache a timeout/failure (None) as if it were a real result -
        # leave the property absent so it gets retried on the next run.
        if result is None:
            return

        graph_data[property_name] = result

        with open('data.pkl', 'wb') as pickle_file:
            pickle.dump(data, pickle_file)


data = {}

try:
    with open('data.pkl', 'rb') as pickle_file:
        data = pickle.load(pickle_file)
except:
    pass

print(data, flush=True)

for filename in os.listdir(spring_graphs):
    print(filename, flush=True)
    file_path = os.path.join(spring_graphs, filename)
    if not os.path.isfile(file_path):
        continue

    g = _load_graph_from_file(file_path)
    print(g.order(), flush=True)

    save_data(data, filename, "n", lambda: g.order())
    save_data(data, filename, "m", lambda: g.number_of_edges())
    save_data(data, filename, "m_dens", lambda: g.number_of_edges() / (g.order() * g.order()))
    save_data(data, filename, "area", lambda: _compute_with_timeout(file_path, "area"))
    save_data(data, filename, "area_tight", lambda: _compute_with_timeout(file_path, "area_tight"))
    save_data(data, filename, "concentration", lambda: _compute_with_timeout(file_path, "concentration"))

    if g.order() <= 70:
        save_data(data, filename, "crossings", lambda: _compute_with_timeout(file_path, "crossings"))

    if g.order() <= 60:
        save_data(data, filename, "pur", lambda: _compute_with_timeout(file_path, "pur"))

    if g.order() <= 100:
        save_data(data, filename, "ref", lambda: _compute_with_timeout(file_path, "ref"))
        save_data(data, filename, "tra", lambda: _compute_with_timeout(file_path, "tra"))
        save_data(data, filename, "rot", lambda: _compute_with_timeout(file_path, "rot"))

    save_data(data, filename, "str", lambda: _compute_with_timeout(file_path, "str"))
    save_data(data, filename, "for", lambda: _compute_with_timeout(file_path, "for"))
    save_data(data, filename, "viz", lambda: _compute_with_timeout(file_path, "viz"))
