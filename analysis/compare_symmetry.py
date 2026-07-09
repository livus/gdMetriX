"""
Compare gdMetriX reflective_symmetry against Mooney's MetricsSuite.symmetry.

Key design choices:
- Only planar drawings (no crossings): avoids Mooney's crosses_promotion blowup.
  After crosses_promotion a graph with k crossings gets k extra nodes; Mooney's
  O(n²·m²) then runs on that enlarged graph, making it O(n⁸) in the worst case.
- Bypass Mooney's edge_crossing recomputation by replacing the stored func with a
  no-op — symmetry() calls calculate_metric("edge_crossing") which would otherwise
  import matplotlib/seaborn and run O(m⁴) crossing detection.
- Pass the original graph G directly to ms.symmetry(G=H) to skip crosses_promotion
  (safe because all drawings here are crossing-free).
"""

import sys, os, types, math, random

MOONEY_PATH = os.path.join(os.path.dirname(__file__), "graph_metrics")
sys.path.insert(0, MOONEY_PATH)

# Stub the two local Mooney helper modules (file I/O only, not needed here)
for _mod in ("write_graph", "parse_graph"):
    _s = types.ModuleType(_mod)
    _s.write_graphml     = lambda *a, **kw: None
    _s.write_graphml_pos = lambda *a, **kw: None
    _s.read_graphml      = lambda *a, **kw: None
    sys.modules.setdefault(_mod, _s)

from metrics_suite import MetricsSuite  # noqa: E402

import gdMetriX  # noqa: E402
import networkx as nx


# ── helpers ────────────────────────────────────────────────────────────────────

def mooney_sym(g, pos, threshold=2, tolerance=3):
    """Run Mooney's symmetry metric on a crossing-free drawing.

    Bypasses edge_crossing recomputation (replaces func with a no-op) and
    passes the graph directly to symmetry() to skip crosses_promotion.
    tolerance=3 is Mooney's default (absolute signed-distance from the axis).
    """
    H = g.copy()
    for n in H.nodes():
        H.nodes[n]["x"] = float(pos[n][0])
        H.nodes[n]["y"] = float(pos[n][1])
        H.nodes[n]["type"] = "major"

    ms = MetricsSuite(H, sym_threshold=threshold, sym_tolerance=tolerance)
    # Replace the func so calculate_metric("edge_crossing") inside symmetry()
    # never imports edge_crossing_metric (which would import matplotlib/seaborn
    # and run O(m^4) crossing detection).
    ms.metrics["edge_crossing"]["func"] = lambda: 1.0
    ms.metrics["edge_crossing"]["num_crossings"] = 0

    # Pass H directly so symmetry() skips crosses_promotion (safe: no crossings).
    return ms.symmetry(G=H)


def gdm_sym(g, pos, threshold=2, tolerance=1e-2, fraction=0.5):
    return gdMetriX.reflective_symmetry(
        g, pos, threshold=threshold, tolerance=tolerance, fraction=fraction
    )


# ── explicit test graphs (all planar drawings) ─────────────────────────────────

def make_rectangle():
    g = nx.cycle_graph(4)
    pos = {0: (-1,-1), 1: (-1,1), 2: (1,1), 3: (1,-1)}
    return "rectangle", g, pos

def make_cycle10():
    g = nx.cycle_graph(10)
    pos = {i: (math.sin(math.radians(i*36)), math.cos(math.radians(i*36)))
           for i in range(10)}
    return "10-cycle", g, pos

def make_cross():
    # Two separate edges forming a "+" shape — drawn without a graph-level
    # crossing (the visual intersection is not a node).
    g = nx.Graph()
    g.add_edges_from([(1,2),(3,4)])
    pos = {1:(-1,0), 2:(1,0), 3:(0,-1), 4:(0,1)}
    return "right-angle cross (2 edges)", g, pos

def make_two_mirrored_verticals():
    g = nx.Graph()
    g.add_edges_from([("A","B"),("C","D")])
    pos = {"A":(-1,1),"B":(-1,-1),"C":(1,1),"D":(1,-1)}
    return "two mirrored verticals", g, pos

def make_one_diagonal():
    g = nx.Graph()
    g.add_nodes_from(["A","B","C","D"])
    g.add_edge("A","D")
    pos = {"A":(-1,1),"B":(1,1),"C":(-1,-1),"D":(1,-1)}
    return "single diagonal (no mirror)", g, pos

def make_both_diagonals():
    # Collinear layout so the two edges don't cross visually.
    g = nx.Graph()
    g.add_edges_from([("A","C"),("B","D")])
    pos = {"A":(-2,0),"B":(-1,0),"C":(1,0),"D":(2,0)}
    return "both diagonals collinear (symmetric)", g, pos

def make_star():
    g = nx.star_graph(4)
    pos = {0:(0,0), 1:(1,0), 2:(0,1), 3:(-1,0), 4:(0,-1)}
    return "star K1,4", g, pos

def make_path_asym():
    g = nx.path_graph(4)
    pos = {0:(0,0), 1:(1,0.3), 2:(2.5,0), 3:(3,0.7)}
    return "path P4 asymmetric", g, pos

def make_triangle():
    g = nx.cycle_graph(3)
    pos = {0:(0,1), 1:(-1,-1), 2:(1,-1)}
    return "triangle K3", g, pos

def make_path3_sym():
    g = nx.path_graph(3)
    pos = {0:(-1,0), 1:(0,0), 2:(1,0)}
    return "path P3 symmetric", g, pos

EXPLICIT = [
    make_rectangle(),
    make_cycle10(),
    make_cross(),
    make_two_mirrored_verticals(),
    make_one_diagonal(),
    make_both_diagonals(),
    make_star(),
    make_path_asym(),
    make_triangle(),
    make_path3_sym(),
]


# ── random planar drawings ─────────────────────────────────────────────────────

def random_planar_drawing(n, rng):
    """Return (g, pos) where g is a random connected planar graph drawn with
    planar_layout (guaranteed crossing-free).  Retry until connected."""
    for _ in range(200):
        g = nx.fast_gnp_random_graph(n, 0.6, seed=rng.randint(0, 99999))
        if not nx.is_connected(g) or g.number_of_edges() < 2:
            continue
        if not nx.is_planar(g):
            continue
        pos_raw = nx.planar_layout(g)
        # Scale to a reasonable coordinate range to match Mooney's tolerance=3
        pos = {v: (x * 10, y * 10) for v, (x, y) in pos_raw.items()}
        return g, pos
    return None, None


# ── run ────────────────────────────────────────────────────────────────────────

W = 72
print("=" * W)
print(f"{'Graph':<34} {'gdMetriX':>9} {'Mooney':>9} {'diff':>9}")
print("=" * W)

print("\n--- Explicit graphs (threshold=2) ---")
for name, g, pos in EXPLICIT:
    gdm = gdm_sym(g, pos)
    try:
        moon = mooney_sym(g, pos)
        diff_s = f"{gdm - moon:+.4f}"
        moon_s = f"{moon:.4f}"
    except Exception as e:
        diff_s = "n/a"
        moon_s = f"ERR({e})"
    print(f"  {name:<32} {gdm:>9.4f} {moon_s:>9} {diff_s:>9}", flush=True)

print("\n--- Random planar graphs (seed=42, 40 trials, n=5..8) ---")
print(f"  {'trial':<30} {'gdMetriX':>9} {'Mooney':>9} {'diff':>9}")

rng = random.Random(42)
diffs = []
errors = 0
skipped = 0
trial = 0
for i in range(40):
    n = rng.randint(5, 8)
    g, pos = random_planar_drawing(n, rng)
    if g is None:
        skipped += 1
        continue
    trial += 1

    gdm = gdm_sym(g, pos)
    try:
        moon = mooney_sym(g, pos)
        d = gdm - moon
        diffs.append(abs(d))
        diff_s = f"{d:+.4f}"
        moon_s = f"{moon:.4f}"
    except Exception as e:
        errors += 1
        diff_s = "n/a"
        moon_s = "ERR"
        print(f"  trial {trial:02d} n={g.order()} m={g.number_of_edges():<3} "
              f"                          ERR: {e}", flush=True)
        continue
    print(f"  trial {trial:02d} n={g.order()} m={g.number_of_edges():<3} "
          f"{gdm:>9.4f} {moon_s:>9} {diff_s:>9}", flush=True)

print()
if diffs:
    print(f"  trials={trial}  skipped={skipped}  errors={errors}")
    print(f"  mean |diff| = {sum(diffs)/len(diffs):.4f}   "
          f"max |diff| = {max(diffs):.4f}")
print("=" * W)
