# gdMetriX
#
# Copyright (C) 2026  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Runtime experiment for the crossing detection algorithms in gdMetriX.crossings.

get_crossings() (Bentley-Ottmann sweep) is documented to run in O((n+k) log(n+k))
time, where k is the number of reported crossings, while get_crossings_quadratic()
runs in O(m^2) regardless of k. To see whether the sweep keeps that promise - and
where the quadratic reference actually wins, as its docstring warns it can when
k = Theta(m^2) - this script measures both on two graph families that share the
same edge count m = O(n) but differ in how many crossings actually occur:

  * "local"  - nx.random_geometric_graph: edges only join nearby nodes, so the
               drawing is close to planar and k stays small (~O(n)).
  * "random" - same number of edges, but node positions are independent of the
               graph structure, so edges become random chords and k blows up
               to Theta(m^2).

Holding m fixed across both families isolates the effect of k on the sweep's
runtime: the quadratic algorithm's time should barely differ between the two
(it never looks at k), while the sweep should be much faster on "local" than on
"random".

CPU time (time.process_time) is used instead of wall-clock time, since this is
run on a laptop where other processes/throttling would otherwise pollute a
wall-clock measurement.

Each series grows n (doubling, or x1.4 for the steep high-crossing sweep case)
until a single measurement exceeds a per-point time budget, so the experiment
self-limits to a few minutes total regardless of machine speed. Results are
cached in crossing_runtime_data.pkl so the script can be re-run/extended without
re-measuring existing points.

On top of that, the sweep is also re-measured against the version of
gdMetriX.crossings committed at HEAD (i.e. without the working-tree changes),
at the same n values, so a regression or improvement from the in-progress edit
shows up directly instead of being guessed at. That committed version is
loaded from a `git archive HEAD` snapshot extracted to a temp directory and
run in a subprocess with that snapshot's src/ put first on sys.path - the
current process already has the working-tree package imported (and editable
installs resolve straight to src/gdMetriX), so getting the committed code into
the same process isn't possible without that kind of isolation. The quadratic
reference is not re-measured against HEAD since it is untouched by the
working-tree diff - it would just be a noisy repeat of the same code.

Run with:

    python crossing_runtime.py
"""

import io
import json
import math
import os
import pickle
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

import networkx as nx
import numpy as np

from gdMetriX import crossings as cr

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(ANALYSIS_DIR, "crossing_runtime_data.pkl")
OUTPUT_PLOT = os.path.join(ANALYSIS_DIR, "crossing_runtime.svg")

AVERAGE_DEGREE = 4  # same target degree for both graph families -> same m for a given n
COMMITTED_REF = "HEAD"


# region Graph families


def _local_graph(n: int, seed: int):
    """Spatially local edges -> close to planar, k stays small."""
    radius = math.sqrt(AVERAGE_DEGREE / (math.pi * n))
    g = nx.random_geometric_graph(n, radius, seed=seed)
    pos = nx.get_node_attributes(g, "pos")
    return g, pos


def _random_position_graph(n: int, seed: int):
    """Same edge count as _local_graph, but positions are unrelated to the
    graph structure -> edges become random chords, so k = Theta(m^2)."""
    m = max(1, int(n * AVERAGE_DEGREE / 2))
    g = nx.gnm_random_graph(n, m, seed=seed)
    rng = random.Random(seed)
    pos = {node: (rng.random(), rng.random()) for node in g.nodes()}
    return g, pos


# endregion

# region Measurement


def _best_of(func, max_repeats: int = 5, repeat_time_budget: float = 2.0):
    """Runs func() repeatedly and returns (minimum CPU time, last result).

    Stops early once a single repeat already exceeds repeat_time_budget - at
    that point the measurement is no longer dominated by timer noise, and
    repeating it further would only waste the time budget for the rest of the
    sweep.
    """
    best_time = math.inf
    result = None
    total = 0.0
    for _ in range(max_repeats):
        start = time.process_time()
        result = func()
        elapsed = time.process_time() - start
        best_time = min(best_time, elapsed)
        total += elapsed
        if elapsed > repeat_time_budget or total > repeat_time_budget * 2:
            break
    return best_time, result


def _measure(cache: dict, series: str, n: int, graph_factory, algorithm: str):
    key = (series, n)
    if key in cache:
        return cache[key]

    g, pos = graph_factory(n, seed=1234 + n)

    if algorithm == "sweep":
        func = lambda: cr.get_crossings(g, pos)
    else:
        func = lambda: cr.get_crossings_quadratic(g, pos)

    elapsed, crossing_list = _best_of(func)
    record = {
        "n": n,
        "m": g.number_of_edges(),
        "k": len(crossing_list),
        "time": elapsed,
    }
    cache[key] = record
    _save_cache(cache)
    print(
        f"{series:>18s}  n={n:<7d} m={record['m']:<8d} k={record['k']:<8d} "
        f"time={record['time']:.4f}s"
    )
    return record


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)


def _run_series(
    cache, series, graph_factory, algorithm, n_start, growth, n_cap, per_point_time_limit, total_time_budget
):
    n = n_start
    total = 0.0
    results = []
    while n <= n_cap:
        record = _measure(cache, series, n, graph_factory, algorithm)
        results.append(record)
        total += record["time"]
        if record["time"] > per_point_time_limit or total > total_time_budget:
            break
        n = max(n + 1, int(round(n * growth)))
    return results


# endregion

# region Committed-vs-working comparison


def _git_head_hash(ref: str = COMMITTED_REF) -> str:
    return subprocess.run(
        ["git", "rev-parse", ref], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _extract_committed_snapshot(ref: str = COMMITTED_REF) -> str:
    """Exports the gdMetriX package as committed at ref into a temp directory
    (via `git archive`, so the working tree itself is never touched) and
    returns the directory that should be put on sys.path to import it."""
    archive = subprocess.run(
        ["git", "archive", ref, "--", "src/gdMetriX"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout
    snapshot_dir = tempfile.mkdtemp(prefix="gdmetrix_committed_")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(snapshot_dir)
    return os.path.join(snapshot_dir, "src")


_COMMITTED_CHILD_SCRIPT = """
import sys, json
sys.path.insert(0, {snapshot_src!r})
sys.path.insert(0, {analysis_dir!r})
import crossing_runtime as cr_exp

graph_factory = {{"local": cr_exp._local_graph, "random": cr_exp._random_position_graph}}[{family!r}]
g, pos = graph_factory({n!r}, seed=1234 + {n!r})

import gdMetriX.crossings as committed_cr
if {algorithm!r} == "sweep":
    func = lambda: committed_cr.get_crossings(g, pos)
else:
    func = lambda: committed_cr.get_crossings_quadratic(g, pos)

elapsed, result = cr_exp._best_of(func)
print(json.dumps({{"n": {n!r}, "m": g.number_of_edges(), "k": len(result), "time": elapsed}}))
"""


def _measure_committed(
    cache: dict, series: str, n: int, family: str, algorithm: str, snapshot_src: str, head_hash: str
):
    key = (series, n)
    cached = cache.get(key)
    if cached is not None and cached.get("ref") == head_hash:
        return cached

    script = _COMMITTED_CHILD_SCRIPT.format(
        snapshot_src=snapshot_src,
        analysis_dir=ANALYSIS_DIR,
        family=family,
        algorithm=algorithm,
        n=n,
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], check=True, capture_output=True, text=True
    )
    record = json.loads(completed.stdout.strip().splitlines()[-1])
    record["ref"] = head_hash
    cache[key] = record
    _save_cache(cache)
    print(
        f"{series:>18s}  n={record['n']:<7d} m={record['m']:<8d} k={record['k']:<8d} "
        f"time={record['time']:.4f}s  [committed @ {head_hash[:8]}]"
    )
    return record


def _run_series_committed(cache, series, family, algorithm, n_values, snapshot_src, head_hash):
    """Re-measures the exact same n values an existing working-tree series
    settled on, but against the code committed at head_hash - so the two
    series are directly comparable point for point."""
    return [
        _measure_committed(cache, series, n, family, algorithm, snapshot_src, head_hash)
        for n in n_values
    ]


# endregion

# region Plotting


def _fit_reference(xs, ys, exponent: float, with_log: bool):
    """A dotted reference curve c * x^exponent * [log2(x)], anchored to match
    the series' own last data point so it overlays as a slope comparison."""

    def f(x):
        value = x**exponent
        if with_log:
            value *= np.log2(x)
        return value

    c = ys[-1] / f(xs[-1])
    return [c * f(x) for x in xs]


DASHED = (0, (6, 3))  # wide on/off pattern so dashes still read clearly at legend size

# Color encodes the algorithm/version; line style encodes the crossing regime -
# that way a color is "the same code path" across both panels and both
# regimes, while solid-vs-dashed is "the same input family" across all three
# algorithms.
ALGORITHM_COLORS = {
    "working tree": "tab:blue",
    "committed": "tab:orange",
    "quadratic (unchanged)": "tab:green",
}
REGIME_LINESTYLES = {
    "low crossings": "-",
    "high crossings": DASHED,
}


def _plot_series(ax, results, label, color, linestyle):
    ns = [r["n"] for r in results]
    times = [r["time"] for r in results]
    ax.plot(ns, times, marker="o", markersize=4, color=color, linestyle=linestyle, linewidth=1.8, label=label)
    return ns, times


def _plot_algorithm(ax, series_results, key_low, key_high, algorithm_label, color):
    """Plots one algorithm's low- and high-crossings series in its color,
    distinguished from each other by line style. Returns both (ns, times)."""
    low = _plot_series(
        ax, series_results[key_low], f"{algorithm_label} - low crossings", color, REGIME_LINESTYLES["low crossings"]
    )
    high = _plot_series(
        ax, series_results[key_high], f"{algorithm_label} - high crossings", color, REGIME_LINESTYLES["high crossings"]
    )
    return low, high


def _plot_algorithm_with_reference(
    ax, series_results, key_low, key_high, algorithm_label, color, ref_regime, ref_exponent, ref_with_log, ref_color, ref_label
):
    """Same as _plot_algorithm, but immediately follows with that algorithm's
    reference curve - so that, plotted right after one another, the three
    algorithms each contribute one (low, high, reference) triple in handle
    order. With ncol=3 that fills the legend column-major: one column per
    algorithm, one row each for low crossings / high crossings / reference.
    """
    low, high = _plot_algorithm(ax, series_results, key_low, key_high, algorithm_label, color)
    ref_ns, ref_times = low if ref_regime == "low crossings" else high
    reference = _fit_reference(ref_ns, ref_times, exponent=ref_exponent, with_log=ref_with_log)
    ax.plot(ref_ns, reference, color=ref_color, linestyle=":", linewidth=1.3, alpha=0.8, label=ref_label)
    return low, high


def _draw_series(ax, series_results):
    """Plots every available series on ax (no reference curves) and returns
    their (ns, times) for reference-curve fitting by the caller."""
    series = {}
    series["sweep_local"], series["sweep_random"] = _plot_algorithm(
        ax, series_results, "sweep_local", "sweep_random", "sweep (working tree)", ALGORITHM_COLORS["working tree"]
    )
    if "sweep_local_committed" in series_results:
        series["sweep_local_committed"], series["sweep_random_committed"] = _plot_algorithm(
            ax, series_results, "sweep_local_committed", "sweep_random_committed", "sweep (committed)", ALGORITHM_COLORS["committed"]
        )
    series["quad_local"], series["quad_random"] = _plot_algorithm(
        ax, series_results, "quad_local", "quad_random", "quadratic (unchanged)", ALGORITHM_COLORS["quadratic (unchanged)"]
    )
    return series


def _draw_series_with_references(ax, series_results):
    """Like _draw_series, but interleaves each algorithm's reference curve
    right after its own (low, high) pair - see _plot_algorithm_with_reference
    for why the order matters for the legend layout."""
    series = {}
    series["sweep_local"], series["sweep_random"] = _plot_algorithm_with_reference(
        ax, series_results, "sweep_local", "sweep_random", "sweep (working tree)", ALGORITHM_COLORS["working tree"],
        ref_regime="low crossings", ref_exponent=1, ref_with_log=True, ref_color="gray", ref_label=r"reference: $n \log n$",
    )
    if "sweep_local_committed" in series_results:
        series["sweep_local_committed"], series["sweep_random_committed"] = _plot_algorithm_with_reference(
            ax, series_results, "sweep_local_committed", "sweep_random_committed", "sweep (committed)", ALGORITHM_COLORS["committed"],
            ref_regime="high crossings", ref_exponent=2, ref_with_log=True, ref_color="dimgray", ref_label=r"reference: $n^2 \log n$",
        )
    series["quad_local"], series["quad_random"] = _plot_algorithm_with_reference(
        ax, series_results, "quad_local", "quad_random", "quadratic (unchanged)", ALGORITHM_COLORS["quadratic (unchanged)"],
        ref_regime="low crossings", ref_exponent=2, ref_with_log=False, ref_color="black", ref_label=r"reference: $n^2$",
    )
    return series


def _draw_k_panel(ax, series_results):
    """How many crossings k actually get reported per regime, as a function of
    n. This is the input-size-driven part of the (n+k) log(n+k) bound: once k
    is Theta(n^2), no algorithm can avoid paying for it, so this panel exists
    to show that the runtime blow-up in the high-crossings regime is a
    property of what's being asked for, not of the implementation.

    There is no algorithm dimension here (k agrees across all of them for a
    given graph - sanity-checked against the cache), so a single neutral
    color is used and only line style (matching the regime convention used
    elsewhere) distinguishes low from high crossings.
    """
    ns_local = [r["n"] for r in series_results["sweep_local"]]
    ks_local = [r["k"] for r in series_results["sweep_local"]]
    ns_random = [r["n"] for r in series_results["sweep_random"]]
    ks_random = [r["k"] for r in series_results["sweep_random"]]

    color = "tab:purple"
    ax.plot(ns_local, ks_local, marker="o", markersize=4, color=color, linestyle=REGIME_LINESTYLES["low crossings"], linewidth=1.8, label="low crossings (local layout)")
    ax.plot(ns_random, ks_random, marker="o", markersize=4, color=color, linestyle=REGIME_LINESTYLES["high crossings"], linewidth=1.8, label="high crossings (random layout)")

    ref_n = _fit_reference(ns_local, ks_local, exponent=1, with_log=False)
    ax.plot(ns_local, ref_n, color="gray", linestyle=":", linewidth=1.3, alpha=0.8, label=r"reference: $n$")

    ref_n2 = _fit_reference(ns_random, ks_random, exponent=2, with_log=False)
    ax.plot(ns_random, ref_n2, color="black", linestyle=":", linewidth=1.3, alpha=0.8, label=r"reference: $n^2$")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("number of nodes $n$ (avg. degree = {})".format(AVERAGE_DEGREE))
    ax.set_ylabel("crossings reported $k$")
    ax.set_title("crossings to report, per regime")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5)


def make_plot(series_results):
    import matplotlib.pyplot as plt  # kept out of module scope: child subprocesses only need the graph helpers

    fig, (ax_log, ax_linear, ax_k) = plt.subplots(1, 3, figsize=(18, 5.5))

    # Left: log-log - the right scale to check the asymptotic complexity claims
    series = _draw_series_with_references(ax_log, series_results)

    ax_log.set_xscale("log")
    ax_log.set_yscale("log")
    ax_log.set_xlabel("number of nodes $n$ (avg. degree = {})".format(AVERAGE_DEGREE))
    ax_log.set_ylabel("CPU time [s]")
    ax_log.set_title("log-log: asymptotic scaling vs. reference curves")
    ax_log.grid(True, which="both", linestyle=":", linewidth=0.5)

    # Right: linear - the scale that shows whether the runtime is reasonable in
    # absolute, practical terms. Cropped to the range where the quadratic
    # reference still has data, since beyond that there is nothing to compare
    # against and the large sweep-only times would squash this region flat.
    linear_x_limit = max(
        max(series["quad_local"][0]), max(series["quad_random"][0])
    ) * 1.15
    _draw_series(ax_linear, series_results)
    visible_times = [
        t
        for ns, times in series.values()
        for n, t in zip(ns, times)
        if n <= linear_x_limit
    ]

    ax_linear.set_xlim(0, linear_x_limit)
    ax_linear.set_ylim(0, max(visible_times) * 1.1)
    ax_linear.set_xlabel("number of nodes $n$ (avg. degree = {})".format(AVERAGE_DEGREE))
    ax_linear.set_ylabel("CPU time [s]")
    ax_linear.set_title("linear: same data, practical scale")
    ax_linear.grid(True, linestyle=":", linewidth=0.5)

    # Far right: k itself, on the same x-axis as the left panel - lets the eye
    # line up "runtime climbs steeply here" with "k climbs steeply here too".
    _draw_k_panel(ax_k, series_results)

    handles, labels = ax_log.get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=8, loc="lower center", ncol=3, handlelength=3.2, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("get_crossings() vs. get_crossings_quadratic(): runtime scaling")
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(OUTPUT_PLOT)
    plt.show()


# endregion


def main():
    cache = _load_cache()

    series_results = {
        "sweep_local": _run_series(
            cache,
            "sweep_local",
            _local_graph,
            "sweep",
            n_start=64,
            growth=2.0,
            n_cap=200_000,
            per_point_time_limit=20.0,
            total_time_budget=90.0,
        ),
        "sweep_random": _run_series(
            cache,
            "sweep_random",
            _random_position_graph,
            "sweep",
            n_start=20,
            growth=1.4,
            n_cap=20_000,
            per_point_time_limit=18.0,
            total_time_budget=90.0,
        ),
        "quad_local": _run_series(
            cache,
            "quad_local",
            _local_graph,
            "quadratic",
            n_start=32,
            growth=2.0,
            n_cap=20_000,
            per_point_time_limit=20.0,
            total_time_budget=60.0,
        ),
        "quad_random": _run_series(
            cache,
            "quad_random",
            _random_position_graph,
            "quadratic",
            n_start=32,
            growth=2.0,
            n_cap=20_000,
            per_point_time_limit=18.0,
            total_time_budget=45.0,
        ),
    }

    head_hash = _git_head_hash()
    snapshot_src = _extract_committed_snapshot(COMMITTED_REF)
    try:
        series_results["sweep_local_committed"] = _run_series_committed(
            cache,
            "sweep_local_committed",
            "local",
            "sweep",
            [r["n"] for r in series_results["sweep_local"]],
            snapshot_src,
            head_hash,
        )
        series_results["sweep_random_committed"] = _run_series_committed(
            cache,
            "sweep_random_committed",
            "random",
            "sweep",
            [r["n"] for r in series_results["sweep_random"]],
            snapshot_src,
            head_hash,
        )
    finally:
        shutil.rmtree(os.path.dirname(snapshot_src), ignore_errors=True)

    make_plot(series_results)


if __name__ == "__main__":
    main()
