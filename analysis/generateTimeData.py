import concurrent.futures
import os
import pickle
import timeit

import networkx as nx

from gdMetriX import symmetry as sym


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


purchase_node_cutoff = 5
purchase_edge_cutoff = 50
kmp_node_cutoff = 80000
kmp_edge_cutoff = 1000000000

spring_graphs = "./RandomGraphs/"


def save_data(data, filename, property_name, function, overwrite=False):
    if filename not in data:
        data[filename] = {}

    graph_data = data[filename]

    if property_name not in graph_data or overwrite:
        print(f"Obtaining {property_name} of {filename}")
        graph_data[property_name] = function()

        with open('timedata.pkl', 'wb') as pickle_file:
            pickle.dump(data, pickle_file)


data = {}
try:
    with open('timedata.pkl', 'rb') as pickle_file:
        data = pickle.load(pickle_file)
except:
    pass

print(data)


def target(func, result_queue):
    start_time = timeit.default_timer()
    func()
    end_time = timeit.default_timer()
    result_queue.put(end_time - start_time)


def time_function_with_timeout(func, returnValue):
    timeout = 12

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            start_time = timeit.default_timer()
            future.result(timeout=timeout)
            end_time = timeit.default_timer()
            return end_time - start_time
        except concurrent.futures.TimeoutError:
            returnValue.val = True
            print("Timeout")
            # for pid, process in executor._threads.items():
            #   process.terminate()
            return timeout

    # result_queue = multiprocessing.Queue()
    # process = multiprocessing.Process(target=target, args=(func, result_queue))
    # process.start()
    # process.join(timeout)


#
# if process.is_alive():
#    print("Timeout detected")
#    process.terminate()
#    process.join()
#    print("Timeout process killed")
#    returnValue.val = True
#    print("Result:", timeout)
#    return timeout
# else:
#    result = result_queue.get()
#    print("Result:", result)
#    return result


class ReturnValue:
    val = False


for filename in os.listdir(spring_graphs):
    folder_path = os.path.join(spring_graphs, filename)
    pur_timeouted = ReturnValue()
    tra_timeouted = ReturnValue()
    rot_timeouted = ReturnValue()
    ref_timeouted = ReturnValue()
    str_timeouted = ReturnValue()
    for_timeouted = ReturnValue()
    viz_timeouted = ReturnValue()

    for filename_2 in os.listdir(folder_path):
        filename_2 = os.path.join(folder_path, filename_2)

        g = _load_graph_from_file(filename_2)

        save_data(data, filename_2, "n", lambda: g.order())
        save_data(data, filename_2, "m", lambda: g.number_of_edges())
        save_data(data, filename_2, "den", lambda: int(filename))

        print(sym.even_neighborhood_distribution(g))

        """
        if not pur_timeouted.val:  # and g.order() <= purchase_node_cutoff and g.number_of_edges() <= purchase_edge_cutoff:
            save_data(data, filename_2, "pur",
                      lambda: time_function_with_timeout(
                          lambda: sym.reflective_symmetry(g), pur_timeouted),
                      overwrite=False)
        # if (g.order() <= kmp_node_cutoff and g.number_of_edges() <= kmp_edge_cutoff):
        if not tra_timeouted.val:
            save_data(data, filename_2, "tra",
                      lambda: time_function_with_timeout(
                          lambda: sym.edge_based_symmetry(g, sym.SymmetryType.TRANSLATIONAL), tra_timeouted))
        if not rot_timeouted.val:
            save_data(data, filename_2, "rot",
                      lambda: time_function_with_timeout(
                          lambda: sym.edge_based_symmetry(g, sym.SymmetryType.ROTATIONAL), rot_timeouted))
        if not ref_timeouted.val:
            save_data(data, filename_2, "ref",
                      lambda: time_function_with_timeout(
                          lambda: sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE), ref_timeouted))
        """
        if not str_timeouted.val:
            save_data(data, filename_2, "str",
                      lambda: time_function_with_timeout(
                          lambda : sym.stress(g), str_timeouted
                      ))
        if not for_timeouted.val:
            save_data(data, filename_2, "for",
                      lambda: time_function_with_timeout(
                          lambda: sym.even_neighborhood_distribution(g), for_timeouted
                      ))
        if not viz_timeouted.val:
            save_data(data, filename_2, "viz",
                      lambda: time_function_with_timeout(
                          lambda: sym.visual_symmetry(g), for_timeouted
                      ))