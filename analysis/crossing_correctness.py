# gdMetriX
#
# Copyright (C) 2026  Martin Nöllenburg, Sebastian Röder, Markus Wallinger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Correctness experiment for the crossing detection algorithms in gdMetriX.crossings.

get_crossings() (Bentley-Ottmann sweep) is the optimized, harder-to-get-right
implementation; get_crossings_quadratic() is the brute-force pairwise reference
that tests/unit/crossings/test_crossings*.py already treat as ground truth (see
crossing_test_helper.assert_crossing_equality, which is exactly the
sorted(crossings_a) == sorted(crossings_b) comparison reused here). This script
runs that same comparison over many random graphs and reports the percentage
that agree exactly, instead of a pass/fail on a fixed set of cases.

The bugs fixed in this area historically (re-ordering the AVL tree, collinear
edges, multiple edges ending at the same height, ...) are all about degenerate
configurations - ties on the sweep line, overlapping edges, several edges
meeting at one point - which become common only when many points are squeezed
into a small coordinate range. That's why the x-axis here is the coordinate
range graphs are drawn from (mirroring _random_graph in
test_crossings_stress.py), not n like in crossing_runtime.py: a small range is
where these bugs actually bite, and a huge range is close to "general
position", where ties are vanishingly unlikely.

Graphs are kept small (n <= 20) so the quadratic reference - and the experiment
as a whole - stays fast even with several hundred samples per coordinate range.

Like crossing_runtime.py, the sweep is also checked against the version
committed at HEAD (via the same git-archive-to-subprocess trick - see that
script for why this needs a subprocess at all), so a correctness change from
the in-progress edit shows up directly.

Run with:

    python crossing_correctness.py
"""

import io
import json
import os
import pickle
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile

import networkx as nx

from gdMetriX import crossings as cr

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(ANALYSIS_DIR, "crossing_correctness_data.pkl")
OUTPUT_PLOT = os.path.join(ANALYSIS_DIR, "crossing_correctness.svg")

COMMITTED_REF = "HEAD"
SAMPLES_PER_RANGE = 250
MAX_NODES = 10
# Fibonacci-ish spacing for even log coverage of the "lots of ties" regime,
# plus two large values as a general-position sanity check.
COORDINATE_RANGES = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 233, 1000, 100_000]


# region Sampling and comparison


def _random_graph(n, p, coordinate_range, rng):
    g = nx.fast_gnp_random_graph(n, p, seed=rng.randint(1, 10**8))
    pos = {
        node: [
            rng.randint(-coordinate_range, coordinate_range),
            rng.randint(-coordinate_range, coordinate_range),
        ]
        for node in range(n)
    }
    nx.set_node_attributes(g, pos, "pos")
    return g


def _sample_graphs(coordinate_range, count, seed):
    rng = random.Random(seed)
    samples = []
    for _ in range(count):
        n = rng.randint(3, MAX_NODES)
        p = rng.uniform(0.1, 0.5)
        include_node_crossings = rng.random() < 0.5
        g = _random_graph(n, p, coordinate_range, rng)
        samples.append((g, include_node_crossings))
    return samples


def _matches_quadratic(g, include_node_crossings):
    """True if get_crossings() agrees exactly with get_crossings_quadratic(),
    mirroring crossing_test_helper._equal_crossings. A raised exception counts
    as disagreement too - that's a correctness failure, not something to hide.
    """
    try:
        sweep = sorted(cr.get_crossings(g, include_node_crossings=include_node_crossings))
        quadratic = sorted(cr.get_crossings_quadratic(g, include_node_crossings=include_node_crossings))
        return sweep == quadratic
    except Exception:
        return False


def _match_rate(coordinate_range, count, seed):
    samples = _sample_graphs(coordinate_range, count, seed)
    matches = sum(_matches_quadratic(g, include_node_crossings) for g, include_node_crossings in samples)
    return matches / len(samples)


# endregion

# region Caching and the committed-HEAD comparison (see crossing_runtime.py for why a subprocess is needed)


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)


def _measure_working(cache, coordinate_range, count, seed):
    key = ("working", coordinate_range)
    cached = cache.get(key)
    if cached is not None and cached.get("count") == count and cached.get("seed") == seed:
        return cached["match_rate"]

    rate = _match_rate(coordinate_range, count, seed)
    cache[key] = {"match_rate": rate, "count": count, "seed": seed}
    _save_cache(cache)
    print(f"{'working tree':>13s}  coordinate_range={coordinate_range:<8d} match_rate={rate * 100:6.2f}%")
    return rate


def _git_head_hash(ref: str = COMMITTED_REF) -> str:
    return subprocess.run(
        ["git", "rev-parse", ref], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _extract_committed_snapshot(ref: str = COMMITTED_REF) -> str:
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
import crossing_correctness as cc

rate = cc._match_rate({coordinate_range!r}, {count!r}, {seed!r})
print(json.dumps({{"match_rate": rate}}))
"""


def _measure_committed(cache, coordinate_range, count, seed, snapshot_src, head_hash):
    key = ("committed", coordinate_range)
    cached = cache.get(key)
    if cached is not None and cached.get("ref") == head_hash and cached.get("count") == count and cached.get("seed") == seed:
        return cached["match_rate"]

    script = _COMMITTED_CHILD_SCRIPT.format(
        snapshot_src=snapshot_src, analysis_dir=ANALYSIS_DIR, coordinate_range=coordinate_range, count=count, seed=seed
    )
    completed = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)
    rate = json.loads(completed.stdout.strip().splitlines()[-1])["match_rate"]
    cache[key] = {"match_rate": rate, "ref": head_hash, "count": count, "seed": seed}
    _save_cache(cache)
    print(f"{'committed':>13s}  coordinate_range={coordinate_range:<8d} match_rate={rate * 100:6.2f}%  [@ {head_hash[:8]}]")
    return rate


# endregion

# region Plotting


def make_plot(coordinate_ranges, working_rates, committed_rates):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5.5))

    ax.plot(coordinate_ranges, [r * 100 for r in working_rates], marker="o", markersize=5, color="tab:blue", linewidth=1.8, label="sweep (working tree) vs. quadratic")
    ax.plot(coordinate_ranges, [r * 100 for r in committed_rates], marker="o", markersize=5, color="tab:orange", linewidth=1.8, label="sweep (committed) vs. quadratic")
    ax.axhline(100, color="gray", linestyle=":", linewidth=1.3, alpha=0.8, label="100% (always agrees)")

    lowest = min(min(working_rates), min(committed_rates)) * 100
    ax.set_xscale("log")
    ax.set_ylim(min(lowest - 3, 96), 101)
    ax.set_xlabel(f"coordinate range (integer grid half-width; {SAMPLES_PER_RANGE} random graphs/point, n <= {MAX_NODES})")
    ax.set_ylabel("exact agreement with get_crossings_quadratic() [%]")
    ax.set_title("Correctness: how often does the sweep line agree with the quadratic reference?")
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, which="both", linestyle=":", linewidth=0.5)

    fig.tight_layout()
    fig.savefig(OUTPUT_PLOT)
    plt.show()


# endregion


def main():
    cache = _load_cache()

    working_rates = []
    for coordinate_range in COORDINATE_RANGES:
        working_rates.append(_measure_working(cache, coordinate_range, SAMPLES_PER_RANGE, seed=coordinate_range))

    head_hash = _git_head_hash()
    snapshot_src = _extract_committed_snapshot()
    try:
        committed_rates = [
            _measure_committed(cache, coordinate_range, SAMPLES_PER_RANGE, coordinate_range, snapshot_src, head_hash)
            for coordinate_range in COORDINATE_RANGES
        ]
    finally:
        shutil.rmtree(os.path.dirname(snapshot_src), ignore_errors=True)

    make_plot(COORDINATE_RANGES, working_rates, committed_rates)


if __name__ == "__main__":
    main()
