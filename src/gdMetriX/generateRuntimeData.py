import random
import timeit

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from libpysal import weights
from libpysal.cg import voronoi_frames
from logConfig import logger

import boundary
import common
import crossings
import gdMetriX
import symmetry as sym

"""for name, graph in datasets.iterate_dataset('subways'):
    center = distribution.center_of_mass(graph)
    plt.figure(figsize=(20, 12))
    nx.draw_networkx(graph, common.get_node_positions(graph))
    plt.plot(center[0], center[1], 'ro', ms=24)
    plt.show()

x = 1 / 0
"""
# Draw visual symmetry plots
"""
ordered = list(datasets.iterate_dataset('subways'))
ordered.sort(key=lambda tuple: sym.visual_symmetry(tuple[1]))

sym_val = {}
for name, graph in ordered:
    x = sym.visual_symmetry(graph)
    print(name, x)
    if x == 0.0:
        x = 0.01
    sym_val[name] = x

plt.figure(figsize=(10, 6))
i = 0
for name, graph in ordered:
    # Setup the matplotlib axis
    ax = plt.subplot(3, 5, i + 1)
    ax.set_title("{} ({:1.2f})".format(name, sym_val[name]))
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(-0.55, 0.55)

    # Read the node positions from the graph
    pos = common.get_node_positions(graph)
    pos = boundary.normalize_positions(graph, pos)

    # Draw on the axis using networkX
    nx.draw_networkx_edges(graph, pos, ax=ax)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=5)

    i += 1
plt.show()
plt.savefig("overview.svg")
"""

random.seed(10023548)

purchase, trans, rot, refl, pixel = [], [], [], [], []
purchase_result, reflective_result, pixel_result = [], [], []

purchase_cutoff = 13

min_diff = 0
max_diff = 0
min_graph, max_graph = None, None
min_pur, min_ref, max_pur, max_ref = 0, 0, 0, 0


def __random_planar_graph__(n: int):
    coordinates = [(random.uniform(0, 1), random.uniform(0, 1)) for _ in range(0, n)]

    cells, generators = voronoi_frames(coordinates, clip="convex hull")
    delaunay = weights.Rook.from_dataframe(cells)

    # Once the graph is built, we can convert the graphs to networkx objects using the
    # relevant method.
    delaunay_graph = delaunay.to_networkx()

    pos_planar = dict(zip(delaunay_graph.nodes, coordinates))
    pos_random = {i: [random.uniform(-0.5, 0.5), random.uniform(0, 10)] for i in range(0, n)}

    pos_planar = boundary.normalize_positions(delaunay_graph, pos_planar, (-0.5, -0.5, 0.5, 0.5))

    directed = nx.DiGraph()

    for node in delaunay_graph.nodes():
        directed.add_node(node)
    for a, b in delaunay_graph.edges():
        directed.add_edge(a, b)

    nx.draw_networkx(directed, pos_planar)

    average_flow = gdMetriX.average_flow(directed, pos_planar)
    print(average_flow)

    plt.plot([0], [0], 'ro', size=5)
    plt.quiver([0], [0], [average_flow[0] / 2.5], [average_flow[1] / 2.5], color='r', angles='xy', scale_units='xy',
               scale=1)

    plt.show()
    # nx.draw_networkx(delaunay_graph, pos_random)
    # plt.show()

    return delaunay_graph, pos_planar, pos_random


def smooth(y, box_pts):
    box = np.ones(box_pts) / box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


__random_planar_graph__(30)
x = 1 / 0


def __draw_graph__(g: nx.Graph, purchase, kmp):
    # ax = plt.gca()
    # ax.set_title(title)

    plt.axis("off")

    pos = common.get_node_positions(g)
    # nx.draw(g, pos)
    nx.draw_networkx(g, pos=nx.get_node_attributes(g, "pos"))
    # nx.draw_networkx_edges(g, pos)
    # nx.draw_networkx_nodes(g, pos, node_size=5)
    # ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    # plt.axis("on"))

    plt.text(-0.2, 1.2, "Purchase {0:.3f}".format(purchase), ha='left', va='bottom', fontsize=16)
    plt.text(-0.2, 1.1, "KMP      {0:.3f}".format(kmp), ha='left', va='bottom', fontsize=16)
    plt.xlim([-0.2, 1.2])
    plt.ylim([-0.2, 1.2])
    plt.show()
    plt.clf()
    plt.cla()
    plt.close()


i = 5
# boundary = (0, 0, 1, 1)
quadratic_p, quadratic_r, efficient_p, efficient_r = [], [], [], []
crossings_p, crossings_r = [], []
graph_sizes = []
number_of_samples = 1
while i <= 200 and False:
    n = i
    graph_sizes.append(n)
    delaunay_graph, pos_planar, pos_random = __random_planar_graph__(n)

    # quadratic_time_p = timeit.timeit(
    #    lambda: crossings_p.append(len(crossings.get_crossings_quadratic(delaunay_graph, pos_planar))),
    #    number=number_of_samples) / number_of_samples
    efficient_time_p = timeit.timeit(lambda: crossings.get_crossings(delaunay_graph, pos_planar),
                                     number=number_of_samples) / number_of_samples
    #
    # quadratic_time_r = timeit.timeit(
    #    lambda: crossings_r.append(len(crossings.get_crossings_quadratic(delaunay_graph, pos_random))),
    #    number=number_of_samples) / number_of_samples
    # efficient_time_r = timeit.timeit(lambda: crossings.get_crossings(delaunay_graph, pos_random),
    #                                 number=number_of_samples) / number_of_samples

    # quadratic_p.append(quadratic_time_p)
    # quadratic_r.append(quadratic_time_r)
    efficient_p.append(efficient_time_p)
    # efficient_r.append(efficient_time_r)

    logger.info(quadratic_p)
    logger.info(quadratic_r)
    logger.info(efficient_p)
    logger.info(efficient_r)
    logger.info(crossings_p)
    logger.info(crossings_r)

    i += 1

    if i > 15 and i % 5 == 0:
        # Plotting
        # plt.plot(graph_sizes, smooth(quadratic_p, 4), label='Quadratic Planar')
        # plt.plot(graph_sizes, smooth(quadratic_r, 4), label='Quadratic Random')
        plt.plot(graph_sizes, smooth(efficient_p, 4), label='Efficient Planar')
        # plt.plot(graph_sizes, smooth(efficient_r, 4), label='Efficient Random')

        # Adding labels and legend
        plt.xlabel('n')
        plt.ylabel('Time [s]')
        # plt.legend()

        plt.show()

        # Plotting
        # plt.plot(crossings_r, label='Spring layout')
        # plt.plot(crossings_p, label='Random')

        # Adding labels and legend
        # plt.xlabel('n')
        # plt.ylabel('crossings')
        # plt.legend()

        # plt.show()

# Find differences
while False:
    n = random.randint(8, 8)
    g = nx.fast_gnp_random_graph(n, random.uniform(0.5, 0.75))
    # pos = {n: [random.uniform(0, 1), random.uniform(0, 1)] for n in range(0, n + 1)}
    pos2 = nx.spring_layout(g)
    pos2 = boundary.normalize_positions(g, pos2, (0, 0, 1, 1))
    nx.set_node_attributes(g, pos2, "pos")

    sym_ref = sym.edge_based_symmetry(g, sym.SymmetryType.REFLECTIVE)

    if sym_ref == 0.0 or sym_ref == 1.0:
        continue

    sym_pur = sym.reflective_symmetry(g, tolerance=0.15, fraction=0.5)
    if sym_pur == 0.0 or sym_ref == 0.0 or sym_pur == 1.0 or sym_ref == 1.0:
        continue

    nx.draw(g, pos2)

    diff = sym_pur - sym_ref

    if diff < min_diff:
        print("Purchase", sym_pur)
        print("Edge", sym_ref)
        print("Min", diff)
        min_diff = diff
        min_graph = g
        min_pur = sym_pur
        min_ref = sym_ref
        if max_graph is not None:
            __draw_graph__(max_graph, max_pur, max_ref)
            __draw_graph__(max_graph, max_pur, max_ref)
            __draw_graph__(min_graph, min_pur, min_ref)
            __draw_graph__(min_graph, min_pur, min_ref)

    if diff > max_diff:
        print("Purchase", sym_pur)
        print("Edge", sym_ref)
        print("Max", diff)
        max_diff = diff
        max_graph = g
        max_pur = sym_pur
        max_ref = sym_ref

        if min_graph is not None:
            __draw_graph__(min_graph, min_pur, min_ref)
            __draw_graph__(min_graph, min_pur, min_ref)
            __draw_graph__(max_graph, max_pur, max_ref)
            __draw_graph__(max_graph, max_pur, max_ref)

"""
purchase = [0.0, 0.1610148032895423, 0.5350908705937409, 0.0, 0.7916666666666666, 0.0, 0.808741418168069, 0.0,
            0.8411468954433489, 1.0, 0.07393942714337025, 0.777789361755772, 0.5935239935985229, 0.7977701214501646,
            0.7260206013263792, 0.6364051760989233, 0.0, 0.7125548410529723, 0.6208518500131086, 0.7799012501104399,
            0.7067112211597509, 0.0, 0.0, 0.0, 0.6236606127133962, 0.8059357630559513, 0.677827477990721, 0.0,
            0.72685457498634, 0.6523226513882706, 0.7821705296964111, 0.725295513521696, 0.697615419708403,
            0.7148999409989856, 0.7757278616785827, 0.7154815075565486, 0.7088970923632527, 0.7040582073969935,
            0.9048768674819525, 0.7420995842287978, 0.7294703891402878, 0.7697185906896811, 0.686413987283253,
            0.6939470636846586, 0.8103351130008929, 0.8047205154074144, 0.790020095831295, 0.7731900411752414,
            0.6480617956917708, 0.710575467484427]
kmp = [0.4, 1.0, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0, 0.875, 0.6666666666666666, 0.5714285714285714, 0.875, 0.6,
       0.6666666666666666, 0.5, 0.2727272727272727, 0.6666666666666666, 0.4444444444444444, 0.9, 0.6,
       0.8333333333333334, 1.0, 0.25, 1.0, 0.75, 1.0, 0.9285714285714286, 0.42857142857142855, 0.4444444444444444, 1.0,
       0.6666666666666666, 0.7, 0.4444444444444444, 0.9285714285714286, 0.8461538461538461, 0.7857142857142857,
       0.7647058823529411, 0.875, 0.5, 0.875, 0.8333333333333334, 0.2608695652173913, 0.8888888888888888, 1.0,
       0.8181818181818182, 1.0, 0.96, 0.8947368421052632, 0.625, 1.0]
pixel = [0.5006051878719673, 0.4135171212302329, 0.6059580725040454, 0.20748110214503923, 0.5354410001285743,
         0.2723970930775038, 0.6882923602322488, 0.35399581991964557, 0.5864198260678941, 0.6762253638884745,
         0.45257365068451627, 0.5757727845371825, 0.5893359501656565, 0.6976808519009663, 0.6193374364745219,
         0.6408344522667868, 0.45055227940860565, 0.6648296297181555, 0.6799194420657793, 0.4580163593168578,
         0.6750531475508569, 0.4945766260009392, 0.5313434349866659, 0.41948792525862844, 0.43983737417693103,
         0.6718713014175122, 0.7428309990727081, 0.5373337213783356, 0.7105095998893709, 0.4938351797872287,
         0.6605869838722086, 0.6657417591166104, 0.7197442078553844, 0.7125808555303854, 0.7530746345168172,
         0.7123583826438421, 0.6712573473292154, 0.6894018927136489, 0.45599614186402593, 0.759446804690569,
         0.7474997270594729, 0.8453529459583806, 0.6849217896284598, 0.6116272478537765, 0.8057718368199124,
         0.8105391002980377, 0.6902797430820728, 0.6415776048025565, 0.49577224925499475, 0.7779131841687823]
"""

pur_filt = []
kmp_filt = []
pix_filt = []
i = -1
while i < len(purchase) - 1 and False:
    i += 1
    if purchase[i] == 0.0 or purchase[i] == 1.0 or kmp[i] == 0.0 or kmp[i] == 1.0:
        continue
    else:
        pur_filt.append(purchase[i])
        kmp_filt.append(kmp[i])
        pix_filt.append(pixel[i])

# print(pearsonr(pur_filt, kmp_filt), pearsonr(pur_filt, pix_filt),
#      pearsonr(kmp_filt, pix_filt))

print(len(pur_filt))
plt.figure(figsize=(5, 5))
plt.plot(pur_filt, kmp_filt, 'bo')
plt.xlabel("Purchase")
plt.ylabel("KMP")
plt.show()

plt.figure(figsize=(5, 5))
plt.plot(pur_filt, pix_filt, 'bo')
plt.xlabel("Purchase")
plt.ylabel("Pixel")
plt.show()

plt.figure(figsize=(5, 5))
plt.plot(kmp_filt, pix_filt, 'bo')
plt.xlabel("KMP")
plt.ylabel("Pixel")
plt.show()

# Correlation
for i in range(5, 10000):  # TODO
    for j in range(0, 10):
        random_graph = nx.fast_gnp_random_graph(i, random.uniform(0.25, 0.75), random.randint(1, 10000000))
        random_embedding = {n: [random.uniform(0, 1), random.uniform(0, 10)] for n in range(0, i + 1)}
        pos2 = nx.spring_layout(random_graph)
        pos2 = boundary.normalize_positions(random_graph, pos2, (0, 0, 1, 1))
        nx.set_node_attributes(random_graph, pos2, "pos")
        logger.info(i * 10 + j)
        sym_pur = sym.reflective_symmetry(random_graph, tolerance=0.085, fraction=0.5, threshold=4)
        logger.info(sym_pur)
        sym_ref = sym.edge_based_symmetry(random_graph, sym.SymmetryType.REFLECTIVE, pixel_merge=5, x_min=1,
                                          y_min=1)
        logger.info(sym_ref)
        sym_vis = sym.visual_symmetry(random_graph, sigma=4)
        logger.info(sym_vis)

        purchase_result.append(sym_pur)
        reflective_result.append(sym_ref)
        pixel_result.append(sym_vis)

        print(i * 10 + j)
        print("Size", i)
        print(purchase_result)
        print(reflective_result)
        print(pixel_result)

        # if len(purchase_result) > 2:
        #    print(pearsonr(purchase_result, reflective_result), pearsonr(purchase_result, pixel_result),
        #          pearsonr(reflective_result, pixel_result))

    purchase_result = [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.876738162768404, 1.0, 1.0,
                       0.12095983744212074, 1.0, 0.25745125726407764, 0.0, 1.0, 1.0, 0.7424836174477438,
                       0.7751250553734651, 0.0, 0.7825572719016386, 0.6600911621557516, 1.0, 0.906694231558481, 1.0,
                       0.8821698319440324, 0.9172082924667868, 0.7895462583904563, 0.7500436399187641,
                       0.2922136270273413, 0.874557411625607, 0.6818854456991124, 0.9159164831433545,
                       0.8332329722689915, 0.7976013740441086, 0.7865076247017407, 0.9549917724800053,
                       0.6204372195688901, 0.8484869094969321, 0.749607153205249, 0.8375754358370031,
                       0.7569528715802427, 0.7496539184378762, 0.7218922750615948, 0.6891082392299482,
                       0.7551181740385902, 0.7571364254043873, 0.7220618453327158, 0.743426484700869, 1.0,
                       0.7919224555014548, 0.8312835142387711, 1.0, 1.0, 0.8090701366504348, 0.6896822033083091,
                       0.7338121086763251, 0.7962312488093708, 0.6967900765374497, 0.8591930577974761,
                       0.7328924841983782, 0.882353395967427, 0.7142078790916917, 0.7895015720717472,
                       0.6700692574409471, 0.8434646387315223, 0.790068071775303, 0.7652268933631307,
                       0.7378294550066962, 0.7485452431172454, 0.8893420662842687, 0.893286615024378,
                       0.8395951105997097, 0.8526313115390327]
    reflective_result = [0.0, 0.5, 0.42857142857142855, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.15384615384615385,
                         0.0, 1.0, 0.0, 0.0, 0.75, 0.25, 0.0, 1.0, 0.16666666666666666, 0.1, 0.0, 0.5833333333333334,
                         0.0, 0.0, 0.3, 0.0, 0.16666666666666666, 0.0, 0.9047619047619048, 0.05555555555555555, 0.0,
                         0.3, 0.0, 0.23076923076923078, 0.11764705882352941, 0.2, 0.5, 0.0, 0.125, 0.15,
                         0.17647058823529413, 0.7037037037037037, 0.3181818181818182, 0.25, 0.2, 0.34782608695652173,
                         0.1, 0.1, 0.52, 0.44, 0.0, 0.1935483870967742, 0.29411764705882354, 0.0, 0.3333333333333333,
                         0.5, 0.5, 0.0, 0.29411764705882354, 0.07407407407407407, 0.47619047619047616, 0.0,
                         0.09523809523809523, 0.28, 0.22580645161290322, 0.10526315789473684, 0.55, 0.4375, 0.2,
                         0.3548387096774194, 0.25925925925925924, 0.4444444444444444, 0.10526315789473684,
                         0.3191489361702128, 0.5106382978723404]
    pixel_result = [0.0, 0.0, 0.23061011238766937, 0.17271584165645248, 0.2967163794493286, 0.0, 0.09891252253371552,
                    0.8402817810603362, 0.0, 0.10340471443628652, 0.3416085113932853, 0.7536274710830537,
                    0.12565852385931275, 0.0, 0.5658094336838573, 0.2828377709893596, 0.0, 0.1516178939286278,
                    0.3939984470453397, 0.0, 0.14557430595798404, 0.4302157294145229, 0.0, 0.0, 0.6742058001080323,
                    0.530418628506766, 0.26014275211481575, 0.18263625398256644, 0.46339240707285234,
                    0.5124753820592143, 0.5823136344118927, 0.5127226228769888, 0.47924250126899637, 0.3987451860099762,
                    0.29780369707960286, 0.6720676007026642, 0.6554809335970007, 0.732632806303002, 0.48701176655882916,
                    0.5238809825653666, 0.5515514247975906, 0.7388122446632395, 0.5569809903934948, 0.68117765208398,
                    0.7979664710562401, 0.7194476012435277, 0.597329193766178, 0.7417387776630822, 0.613494957701348,
                    0.6707372305660929, 0.7447278009779116, 0.7265514787156026, 0.0, 0.8554981652932675,
                    0.76172988742645, 0.0, 0.24153933259449967, 0.2520191046791005, 0.673283873820319,
                    0.7612931545588394, 0.8324707686316395, 0.8544576141258906, 0.8806216197651323, 0.5382342206629878,
                    0.736136278309153, 0.7560906696136838, 0.7625554048119491, 0.31330838883300205, 0.886733771369118,
                    0.780757529968289, 0.7157613632159712, 0.6220982515222316, 0.8437861716440761, 0.3893639046219688,
                    0.5461146289983114, 0.8881574330115193, 0.9058596635843348]

    plt.figure(figsize=(3, 3), dpi=200)
    plt.plot(purchase_result, reflective_result, 'bo', markersize=2.5)
    # plt.xlabel("Purchase")
    # plt.ylabel("KMP")
    plt.show()

    plt.figure(figsize=(3, 3), dpi=200)
    plt.plot(purchase_result, pixel_result, 'bo', markersize=2.5)
    # plt.xlabel("Purchase")
    # plt.ylabel("Pixel")
    plt.show()

    plt.figure(figsize=(3, 3), dpi=200)
    plt.plot(reflective_result, pixel_result, 'bo', markersize=2.5)
    # plt.xlabel("KMP")
    # plt.ylabel("Pixel")
    plt.show()

for i in range(0, 1):
    size = i
    random_graph = nx.fast_gnp_random_graph(i, 0.25, random.randint(1, 10000000))
    random_embedding = {n: [random.uniform(-100, 100), random.uniform(-100, 100)] for n in range(0, i + 1)}

    nx.set_node_attributes(random_graph, random_embedding, "pos")

    time_purchase = 0 if i > purchase_cutoff else timeit.timeit(lambda: sym.reflective_symmetry(random_graph), number=1)
    time_translational = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.TRANSLATIONAL),
                                       number=3) / 3
    time_rotational = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.ROTATIONAL),
                                    number=3) / 3
    time_reflective = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.REFLECTIVE),
                                    number=3) / 3
    time_pixel = timeit.timeit(lambda: sym.visual_symmetry(random_graph), number=3) / 3

    print(purchase)
    print()
    print(trans)
    print()
    print(rot)
    print()
    print(refl)
    print()
    print(pixel)

    print("Size:", i)
    print(time_purchase)
    print(time_translational)
    print(time_rotational)
    print(time_reflective)
    print(time_pixel)
    print()
    print()

    if i <= purchase_cutoff:
        purchase.append(time_purchase)
    trans.append(time_translational)
    rot.append(time_rotational)
    refl.append(time_reflective)
    pixel.append(time_pixel)

edge_graph_size = 10
for i in range(0, 1):
    i *= 4
    size = i
    random_graph = nx.fast_gnp_random_graph(edge_graph_size, i / 100.0, random.randint(1, 10000000))
    random_embedding = {n: [random.uniform(-100, 100), random.uniform(-100, 100)] for n in range(0, edge_graph_size)}

    nx.set_node_attributes(random_graph, random_embedding, "pos")

    time_purchase = timeit.timeit(lambda: sym.reflective_symmetry(random_graph), number=1)
    time_translational = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.TRANSLATIONAL),
                                       number=3) / 3
    time_rotational = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.ROTATIONAL),
                                    number=3) / 3
    time_reflective = timeit.timeit(lambda: sym.edge_based_symmetry(random_graph, sym.SymmetryType.REFLECTIVE),
                                    number=3) / 3
    # time_pixel = timeit.timeit(lambda: sym.visual_symmetry(random_graph), number=3) / 3

    print(purchase)
    print()
    print(trans)
    print()
    print(rot)
    print()
    print(refl)
    print()
    # print(pixel)

    print("Size:", i)
    print(time_purchase)
    print(time_translational)
    print(time_rotational)
    print(time_reflective)
    # print(time_pixel)
    print()
    print()

    # if i <= purchase_cutoff:
    purchase.append(time_purchase)
    trans.append(time_translational)
    rot.append(time_rotational)
    refl.append(time_reflective)
    # pixel.append(time_pixel)

print(purchase)
print(trans)
print(rot)
print(refl)
print(pixel)

purchase = [6.5999999998567205e-06, 4.4999999997408224e-06, 0.002871299999999799, 0.0032377999999999574,
            0.002221699999999771, 0.040195300000000156, 0.01036600000000032, 0.004151000000000238, 0.041603499999999904,
            1.0979177999999994, 0.6551106999999998, 1.7047142000000006, 3.7848644, 76.57242360000001]

trans = [1.4000000000032506e-05, 8.80000000010502e-06, 1.6633333333201012e-05, 0.00021696666666655892,
         0.00015046666666673758, 0.0003421999999999592, 0.0004412333333333092, 0.00021740000000007123,
         0.00044103333333348854, 0.0008568666666667705, 0.0007063666666666061, 0.0009502333333332539,
         0.0014537000000001872, 0.002728833333335956, 0.004327399999998723, 0.0027951333333362527, 0.005182233333333859,
         0.010115833333334953, 0.009661200000001221, 0.019130166666665598, 0.015330633333329994, 0.01573323333333576,
         0.026389133333334296, 0.035022266666662936, 0.05992563333333578, 0.02434949999999958, 0.04368919999999813,
         0.05151126666666528, 0.04605909999999843, 0.07571710000000091, 0.08187503333333268, 0.08803019999999624,
         0.09242929999999679, 0.109271233333331, 0.09584180000000231, 0.11707593333333459, 0.1695504000000009,
         0.17927560000000162, 0.15175263333333078, 0.16934673333333686, 0.23598170000000115, 0.2535693666666627,
         0.23993593333332797, 0.2818109333333325, 0.32410853333333495, 0.3590556666666676, 0.3507763333333287,
         0.45040450000000004, 0.4048165000000002, 0.7451966000000046, 0.6396600999999956, 0.6471277333333395,
         0.7776824666666661, 0.6829330999999949, 0.7948982666666685, 0.7985710666666629, 0.9409023333333266,
         0.8818214666666601, 1.0337564666666594, 1.110912600000006, 1.1627134666666545, 1.840136100000014,
         1.374199200000002, 1.4985059333333386, 1.601506633333334, 1.4148153000000054, 1.7994500666666984,
         2.10734263333336, 2.0272812333333454, 2.2497714333333456, 2.517407299999983, 2.2826251333333403,
         2.765218533333344, 2.6034743000000162, 3.000814233333358, 2.890561733333319, 3.639007066666674,
         3.3338496666666138, 3.2372594333332927, 3.6157810666666896]

rot = [4.866666666547559e-06, 5.50000000002863e-06, 6.733333333415932e-06, 0.0002159000000000096,
       0.00017380000000007575, 0.0004988000000000584, 0.0006545999999999866, 0.0002565666666665874,
       0.000593266666666814, 0.001234866666666612, 0.0011585666666666938, 0.0016182333333330707, 0.0022552666666667185,
       0.004323100000002948, 0.00841570000000047, 0.0039635333333336575, 0.009199066666667477, 0.024593666666665587,
       0.018182933333335427, 0.03756626666666326, 0.0307898999999973, 0.028616999999997006, 0.044838366666667184,
       0.07410246666666846, 0.08816150000000296, 0.04787563333333367, 0.08916290000000042, 0.08611470000000072,
       0.10299373333333506, 0.1503711666666637, 0.13360976666666602, 0.15859503333333672, 0.21282673333333454,
       0.21701203333333297, 0.20942026666666416, 0.219468166666663, 0.31584803333333394, 0.3619976999999987,
       0.28792300000000165, 0.32996453333332926, 0.4464685000000041, 0.49913843333333335, 0.4650816999999942,
       0.5446760666666629, 0.5874961999999945, 0.6896756666666685, 0.7798827000000017, 0.8704636999999972,
       0.7699998333333345, 1.2873316333333378, 1.1034288000000079, 1.1430390333333378, 1.5963856333333315,
       1.5322888999999975, 1.6515052999999966, 1.7282206666666677, 1.9606074333333368, 1.6614646333333287,
       2.1034667333333346, 2.274704566666666, 2.3351207666666673, 3.591120066666671, 2.842554866666679,
       3.1735317000000123, 3.163199866666654, 3.4638148333333447, 3.5216184000000035, 4.323401266666679,
       4.401857566666649, 4.437015133333337, 4.9306048333333665, 4.646220833333359, 5.369624466666703,
       5.233840233333315, 6.234997466666641, 6.008883666666672, 6.068860733333319, 6.446835199999971, 6.744189466666664,
       6.928756933333337]

refl = [4.266666666641328e-06, 4.93333333340118e-06, 6.833333333400304e-06, 0.0004929666666666499,
        0.00031696666666662193, 0.0009417666666666769, 0.0012410333333334005, 0.0007222666666666377,
        0.0012191666666666972, 0.002678966666666819, 0.002114666666666487, 0.002980866666666415, 0.0033832333333331612,
        0.008368966666665756, 0.013805400000000153, 0.007898333333334525, 0.016274233333329374, 0.03866260000000447,
        0.029927333333333195, 0.053534933333333846, 0.04134479999999977, 0.045064966666667296, 0.08292090000000012,
        0.10269386666666946, 0.11505093333333605, 0.07563093333333389, 0.13450183333333143, 0.12569866666666485,
        0.1708630333333332, 0.22243096666666418, 0.19915696666666824, 0.2312053666666666, 0.2657972333333352,
        0.3057202666666683, 0.3123719666666697, 0.34273420000000004, 0.4174874999999976, 0.51995096666667,
        0.4354509666666691, 0.5323975000000019, 0.7116571333333374, 0.765305033333334, 0.6776452000000006,
        0.831780900000003, 0.9099710666666662, 1.078828033333328, 1.1093028333333355, 1.3599937000000086,
        1.5743350999999943, 2.022182799999996, 1.875923700000006, 1.654526599999997, 2.4047502000000045,
        2.2329691666666633, 2.460342799999997, 2.5448518999999883, 2.8671634000000004, 2.7935992666666607,
        3.158148399999997, 3.3994778666666625, 3.5627519000000043, 4.614432366666658, 4.23979483333333,
        4.455197100000002, 4.893535100000008, 4.3691945000000105, 5.061423066666673, 6.541604800000035,
        6.235933533333347, 6.732281499999999, 7.957233733333358, 7.200112700000015, 8.127948066666667,
        8.441458233333302, 8.984914333333336, 14.456832566666662, 9.362281000000015, 9.850930800000015,
        10.242874500000047, 10.833754166666646]

pixel = [3.533333333471944e-06, 3.5000000000451337e-06, 0.11376966666666677, 0.11184153333333342, 0.1057928333333334,
         0.10409759999999994, 0.10418216666666662, 0.10217549999999982, 0.1001452666666669, 0.0951762666666669,
         0.09293589999999992, 0.08970779999999993, 0.08808416666666652, 0.08800713333333476, 0.09903130000000242,
         0.09942093333333446, 0.09714036666666459, 0.1114410333333306, 0.10014226666666559, 0.10004246666666934,
         0.09757889999999729, 0.10140576666666827, 0.09423263333333409, 0.09149499999999951, 0.09804446666666422,
         0.1059868333333327, 0.09246293333333237, 0.08898233333333394, 0.09211799999999926, 0.08655010000000136,
         0.10047869999999648, 0.08488069999999936, 0.084778666666665, 0.08600503333333147, 0.08498656666666686,
         0.09111016666666671, 0.09485536666666405, 0.08875896666666468, 0.09205573333333443, 0.08624213333333348,
         0.08812459999999571, 0.08487766666666137, 0.08782576666666841, 0.08533993333333001, 0.08532879999999447,
         0.09420990000000036, 0.08866470000000011, 0.11501033333333528, 0.19559063333333407, 0.13772043333333764,
         0.1349958666666661, 0.09694036666667216, 0.10999023333332995, 0.10038413333333551, 0.11178346666666054,
         0.11101466666667648, 0.11076399999999846, 0.11451419999999264, 0.10425776666666782, 0.12299460000000788,
         0.12149079999998473, 0.10285176666665545, 0.12948396666666895, 0.10661216666666935, 0.10438073333333857,
         0.10765313333331505, 0.1113366000000345, 0.11613183333334594, 0.10726066666666156, 0.11393156666664102,
         0.11589093333335161, 0.1547715666666439, 0.10835596666667395, 0.10494343333330865, 0.10843756666668014,
         0.13931510000001404, 0.1211796666666487, 0.10354133333332054, 0.13322509999996632, 0.09615633333335911]

# purchase = np.random.rand(100)
# trans = np.random.rand(100)
# rot = np.random.rand(100)
# refl = np.random.rand(100)
# pixel = np.random.rand(100)

plt.figure(figsize=(7, 4))

# Plotting
plt.plot(purchase, label='Node-based')
plt.plot(trans, label='Edge-based - translational')
plt.plot(rot, label='Edge-based - rotational')
plt.plot(refl, label='Edge-based - reflective')
plt.plot(pixel, label='Visual')

plt.ylim(0, 11)

# Adding labels and legend
plt.xlabel('n')
plt.ylabel('Time [s]')
# plt.title('Symmetry metrics - Runtime comparision')
plt.legend()

plt.text(len(trans) - 1, trans[-1], f'{trans[-1]:.1f}', ha='left', va='bottom')
plt.text(len(trans) - 1, rot[-1], f'{rot[-1]:.1f}', ha='left', va='bottom')
plt.text(len(trans) - 1, refl[-1] - 0.5, f'{refl[-1]:.1f}', ha='left', va='bottom')
plt.text(len(trans) - 1, pixel[-1], f'{pixel[-1]:.1f}', ha='left', va='bottom')
plt.grid(True, linestyle='dotted')

# Display the plot
plt.savefig("runtime.svg")
plt.show()
