import math

import pytest
from numpy import ndarray
from filelock import FileLock

from gdMetriX import datasets
import gdMetriX
import networkx
import itertools

# TODO own test file for additional dataset tests (caching, deleting cache, adapting parameters, etc.)


def generate_test_data():
    """Generator function yielding large test cases one by one."""
    lock_datasets = FileLock("dataset_download.lock")
    with lock_datasets:
        available_datasets = datasets.get_available_datasets()

    for dataset_name in available_datasets:
        lock = FileLock(f"{dataset_name}.lock")
        with lock:
            for name in itertools.islice(
                datasets.get_available_graph_names(dataset_name), 2
            ):
                yield dataset_name, name


test_data = list(generate_test_data())
ids = [f"{dataset}_{graph}" for dataset, graph in test_data]


def pytest_generate_tests(metafunc):
    """Dynamically generate test cases lazily without preloading all of them."""
    if "test_case" in metafunc.fixturenames:
        metafunc.parametrize("test_case", test_data, ids=ids)


def get_embedded_graph(dataset: str, graph_name: str):
    g = datasets.get_specific_graph(dataset, graph_name)
    pos = gdMetriX.get_node_positions(g)

    if len(pos) == 0:
        pos = networkx.circular_layout(
            g
        )  # .spring_layout(g, iterations=(1 if g.order() > 100 else 10))
        networkx.set_node_attributes(g, pos, "pos")

    return g


def test_area_and_boundary(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    g_copy = g.copy()

    print(f"Graph with {g.order()} nodes and {len(g.edges())} edges")

    area = gdMetriX.area(g)
    print(f"Area: {area}")
    assert area is not None
    assert area >= 0
    assert isinstance(area, float)

    area_tight = gdMetriX.area_tight(g)
    print(f"Area tight: {area_tight}")
    assert area_tight is not None
    assert area_tight >= 0
    assert isinstance(area_tight, float)

    aspect_ratio = gdMetriX.aspect_ratio(g)
    print(f"Aspect ratio: {aspect_ratio}")
    assert aspect_ratio is not None
    assert aspect_ratio > 0
    assert isinstance(aspect_ratio, float)

    bounding_box = gdMetriX.bounding_box(g)
    print(f"Bounding box: {bounding_box}")
    assert bounding_box is not None

    height = gdMetriX.height(g)
    print(f"Bounding box: {height}")
    assert height is not None
    assert isinstance(height, float)
    assert height >= 0

    normalize_positions = gdMetriX.normalize_positions(g)
    print(f"Normalized positions: {normalize_positions}")
    assert normalize_positions is not None

    width = gdMetriX.width(g)
    print(f"Width: {width}")
    assert width is not None
    assert isinstance(width, float)
    assert width >= 0

    # Test that the graph is not modified at all
    assert networkx.utils.graphs_equal(g, g_copy)


def test_node_distribution(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    g_copy = g.copy()

    center_of_mass = gdMetriX.center_of_mass(g)
    print(f"Center of mass: {center_of_mass}")
    assert center_of_mass is not None
    assert isinstance(center_of_mass, gdMetriX.Vector)

    if g.order() <= 100:
        a, b, distance = gdMetriX.closest_pair_of_elements(g)
        print(f"Closest pair of elements: {a}, {b} (distance: {distance}")
        assert distance is not None
        assert isinstance(distance, float)
        assert distance >= 0
        assert a is not None
        assert b is not None
        assert a != b

    a, b, distance = gdMetriX.closest_pair_of_points(g)
    print(f"Closest pair of elements: {a}, {b} (distance: {distance}")
    assert distance is not None
    assert isinstance(distance, float)
    assert distance >= 0
    assert a is not None
    assert b is not None
    assert a != b

    concentration = gdMetriX.concentration(g)
    print(f"Concentration: {concentration}")
    assert concentration is not None
    assert isinstance(concentration, float)
    assert 0 <= concentration <= 1

    if g.order() <= 100:
        gabriel_ratio = gdMetriX.gabriel_ratio(g)
        print(f"Concentration: {gabriel_ratio}")
        assert gabriel_ratio is not None
        assert isinstance(gabriel_ratio, float)
        assert 0 <= gabriel_ratio <= 1

    heatmap = gdMetriX.heatmap(g, gdMetriX.get_node_positions(g), None, 5)
    print(f"Heatmap: {heatmap}")
    assert heatmap is not None
    assert isinstance(heatmap, ndarray)
    assert len(heatmap) > 0

    homogeneity = gdMetriX.homogeneity(g)
    print(f"Homogeneity: {homogeneity}")
    assert homogeneity is not None
    assert isinstance(homogeneity, float)
    assert 0 <= homogeneity <= 1

    horizontal_balance = gdMetriX.horizontal_balance(g)
    print(f"Horizontal balance: {horizontal_balance}")
    assert horizontal_balance is not None
    assert isinstance(horizontal_balance, float)
    assert -1 <= horizontal_balance <= 1

    node_orthogonality = gdMetriX.node_orthogonality(g)
    print(f"Node orthogonality: {node_orthogonality}")
    assert node_orthogonality is not None
    assert isinstance(node_orthogonality, float)
    assert 0 <= node_orthogonality <= 1

    smallest_enclosing_circle = gdMetriX.smallest_enclosing_circle(g)
    print(f"Smallest enclosing circle: {smallest_enclosing_circle}")
    assert smallest_enclosing_circle is not None

    vertical_balance = gdMetriX.vertical_balance(g)
    print(f"Vertical balance: {vertical_balance}")
    assert vertical_balance is not None
    assert isinstance(vertical_balance, float)
    assert -1 <= vertical_balance <= 1

    # Test that the graph is not modified at all
    assert networkx.utils.graphs_equal(g, g_copy)


def test_edge_direction(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    g_copy = g.copy()

    angular_resolution = gdMetriX.angular_resolution(g)
    print(f"Node orthogonality: {angular_resolution}")
    assert angular_resolution is not None
    assert isinstance(angular_resolution, (float, int))
    assert 0 <= angular_resolution <= 1

    if networkx.is_directed(g):
        average_flow = gdMetriX.average_flow(g)
        print(f"Node orthogonality: {average_flow}")
        assert average_flow is not None

    coherence_to_average_flow = gdMetriX.coherence_to_average_flow(g)
    print(f"Node orthogonality: {coherence_to_average_flow}")
    assert coherence_to_average_flow is not None
    assert isinstance(coherence_to_average_flow, (int, float))
    assert 0 <= coherence_to_average_flow <= 1

    combinatorial_embedding = gdMetriX.combinatorial_embedding(g)
    print(f"Node orthogonality: {combinatorial_embedding}")
    assert combinatorial_embedding is not None

    edge_angles = gdMetriX.edge_angles(g, list(g)[0])
    print(f"Edge angles: {edge_angles}")
    assert edge_angles is not None

    edge_length_deviation = gdMetriX.edge_length_deviation(g)
    print(f"Node orthogonality: {edge_length_deviation}")
    assert edge_length_deviation is not None
    assert isinstance(edge_length_deviation, float)
    assert 0 <= edge_length_deviation <= 1

    edge_orthogonality = gdMetriX.edge_orthogonality(g)
    print(f"Node orthogonality: {edge_orthogonality}")
    assert edge_orthogonality is not None
    assert isinstance(edge_orthogonality, float)
    assert 0 <= edge_orthogonality <= 1

    minimum_angle = gdMetriX.minimum_angle(g)
    print(f"Minimum angle: {minimum_angle}")
    assert minimum_angle is not None
    assert isinstance(minimum_angle, float)
    assert 0 <= minimum_angle <= math.pi * 2

    ordered_neighborhood = gdMetriX.ordered_neighborhood(g, list(g)[0])
    print(f"Ordered neighborhood: {ordered_neighborhood}")
    assert ordered_neighborhood is not None

    if networkx.is_directed(g) and len(g.edges()) > 0:
        upwards_flow = gdMetriX.upwards_flow(g)
        print(f"Upwards flow: {upwards_flow}")
        assert upwards_flow is not None
        assert isinstance(upwards_flow, float)
        assert 0 <= upwards_flow <= 1

    # Test that the graph is not modified at all
    assert networkx.utils.graphs_equal(g, g_copy)


def test_common(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    g_copy = g.copy()

    pos = gdMetriX.get_node_positions(g)
    assert pos is not None
    assert len(pos) == g.order()

    assert networkx.utils.graphs_equal(g, g_copy)


def test_crossings(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    if len(g.edges()) < 200:
        g_copy = g.copy()

        # "Fast" crossing algorithm
        crs = gdMetriX.get_crossings(g)
        print(f"Crossings: {crs}")
        assert crs is not None
        assert isinstance(crs, list)

        crs_2 = gdMetriX.get_crossings(g, include_node_crossings=True)
        print(f"Crossings including node crossings: {crs_2}")
        assert len(crs_2) >= len(crs)
        assert crs_2 is not None
        assert isinstance(crs_2, list)

        cr_density = gdMetriX.crossing_density(g)
        print(f"Crossing density: {cr_density}")
        assert cr_density is not None
        assert 0 <= cr_density <= 1

        cr_density_2 = gdMetriX.crossing_density(g, include_node_crossings=True)
        print(f"Crossing density: {cr_density_2}")
        assert cr_density_2 is not None
        assert 0 <= cr_density_2 <= 1

        cr_total = gdMetriX.number_of_crossings(g)
        print(f"Total number of crossings: {cr_total}")
        assert cr_total is not None
        assert 0 <= cr_total <= len(g.edges()) ** 2

        cr_total_2 = gdMetriX.number_of_crossings(g, include_node_crossings=True)
        print(f"Total number of crossings: {cr_total_2}")
        assert cr_total_2 is not None
        assert cr_total <= cr_total_2
        assert 0 <= cr_total_2 <= len(g.edges()) ** 2

        # Quadratic crossing algorithm
        if len(g.edges()) < 100:
            crs_quad = gdMetriX.get_crossings_quadratic(g)
            print(f"Crossings quadratic: {crs_quad}")
            assert crs_quad is not None
            assert isinstance(crs_quad, list)

            crs_quad_2 = gdMetriX.get_crossings_quadratic(
                g, include_node_crossings=True
            )
            print(f"Crossings quadratic: {crs_quad_2}")
            assert crs_quad_2 is not None
            assert isinstance(crs_quad_2, list)
            assert len(crs_quad_2) >= len(crs_quad)

            cr_angular_res = gdMetriX.crossing_angular_resolution(g)
            print(f"Angular resolution: {cr_angular_res}")
            assert cr_angular_res is not None
            assert 0 <= cr_angular_res <= 1

            cr_angular_res_2 = gdMetriX.crossing_angular_resolution(
                g, include_node_crossings=True
            )
            print(f"Angular resolution: {cr_angular_res_2}")
            assert cr_angular_res_2 is not None
            assert 0 <= cr_angular_res_2 <= 1
            assert cr_angular_res_2 <= cr_angular_res

            planarized_g = g.copy()
            gdMetriX.planarize(planarized_g)
            print(f"Planarized graph: {planarized_g}")
            assert isinstance(planarized_g, type(g))
            assert planarized_g.order() >= g.order()
            assert len(planarized_g.edges()) >= len(g.edges())

            if cr_total > 0:
                assert not networkx.utils.graphs_equal(planarized_g, g)
            else:
                assert networkx.utils.graphs_equal(planarized_g, g)

            planarized_g_2 = g.copy()
            gdMetriX.planarize(planarized_g_2, include_node_crossings=True)
            print(f"Planarized graph: {planarized_g_2}")
            assert isinstance(planarized_g_2, type(g))
            assert planarized_g_2.order() >= planarized_g.order()
            assert len(planarized_g_2.edges()) >= len(planarized_g_2.edges())

            if cr_total_2 > 0:
                assert not networkx.utils.graphs_equal(planarized_g_2, g)
            else:
                assert networkx.utils.graphs_equal(planarized_g_2, g)

        assert networkx.utils.graphs_equal(g, g_copy)


def test_symmetry(test_case):
    dataset, graph_name = test_case
    g = get_embedded_graph(dataset, graph_name)

    g_copy = g.copy()

    # Edge based symmetry
    if len(g.edges()) < 300:
        edge_symmetry_rot = gdMetriX.edge_based_symmetry(
            g, gdMetriX.SymmetryType.ROTATIONAL
        )
        print(f"Rotational symmetry: {edge_symmetry_rot}")
        assert 0 <= edge_symmetry_rot <= 1

        edge_symmetry_trans = gdMetriX.edge_based_symmetry(
            g, gdMetriX.SymmetryType.TRANSLATIONAL
        )
        print(f"Translational symmetry: {edge_symmetry_trans}")
        assert 0 <= edge_symmetry_trans <= 1

        edge_symmetry_refl = gdMetriX.edge_based_symmetry(
            g, gdMetriX.SymmetryType.REFLECTIVE
        )
        print(f"Reflective symmetry: {edge_symmetry_refl}")
        assert 0 <= edge_symmetry_refl <= 1

    # Even neighborhood distribution
    even_neighborhood = gdMetriX.even_neighborhood_distribution(g)
    print(f"Even neighborhood distribution: {even_neighborhood}")
    assert 0 <= even_neighborhood <= 1

    # Purchase symmetry
    if len(g.edges()) < 10:
        purchase = gdMetriX.reflective_symmetry(g)
        print(f"Purchase symmetry: {purchase}")
        assert 0 <= purchase <= 1

    # Stress
    stress = gdMetriX.stress(g)
    print(f"Stress: {stress}")
    assert stress >= 0

    # Custom symmetry
    visual_symmetry = gdMetriX.visual_symmetry(g)
    print(f"Visual symmetry: {visual_symmetry}")
    assert 0 <= visual_symmetry <= 1

    assert networkx.utils.graphs_equal(g, g_copy)
