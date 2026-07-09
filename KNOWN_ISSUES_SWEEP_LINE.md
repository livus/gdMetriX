# Bentley–Ottmann sweep: debugging history

Status as of this debugging pass: nine distinct bugs have been found and fixed
across `sweep_line.py`, `avl_tree.py`, `crossings.py` and
`crossing_data_types.py`, most recently a randomized stress-test suite
(`tests/unit/crossings/test_crossings_stress.py`, run via `pytest --runslow`)
that throws many small, deliberately degenerate random graphs at
`get_crossings()` and compares against the brute-force
`get_crossings_quadratic()` reference - see below for what was found and how
each was fixed, in case something similar resurfaces. **If you find a new
disagreement via the stress suite, add it here too**, with the minimal repro
that found it - that repro is what makes the next bug fast to track down.

Two corrections to earlier status notes in this file, found by going back and
re-testing each fix in isolation rather than trusting that "stress suite is
green" meant every individual change was load-bearing for the right reason:

- The full-traversal rewrite of `avl_tree.py`'s `get_left`/`get_right`/
  `get_range` (described below under "get_range could miss edges on a
  structurally stale sweep-line tree" and the two `get_left`/`get_right`
  entries) turned out to be compensating for a real but different bug - see
  "`_handle_event`'s interior-list reorder corrupted the tree via interleaved
  remove+add" further down. With that bug fixed, `avl_tree.py` has been
  **reverted to its original pruning-based `get_left`/`get_right`/`get_range`**
  (confirmed via the full stress suite: 160/160 passed with pruning once the
  real fix was in place, vs. 63 failures with pruning alone). Do not
  reintroduce full traversal as a default fix for a disagreement found via the
  stress suite - first check whether the disagreement survives a clean,
  two-phase remove-all-then-add-all reorder; only fall back to full traversal
  if it demonstrably doesn't.
- `consider_singletons=True` combined with `include_node_crossings=True` is a
  **currently open, unfixed bug** - see "Open: singleton handling disagrees
  with quadratic reference" at the end of this file. It is not covered by any
  fix described below.

## Fixed: `SweepLineEdgeInfo.less_than()` tie-break at shared endpoints

`src/gdMetriX/utils/sweep_line.py`

When two edges tie at the queried height, the comparator disambiguates by
probing slightly below. That's safe for a genuine crossing (two straight,
non-identical lines cross at most once, so the sign of `x_self - x_other`
can't flip again below it). It was **not** safe when both edges end at
exactly the queried point (e.g. two edges sharing a node) - there the old code
extrapolated past where the lines actually end and could report the order
backwards. Fixed by falling back to probing slightly *above* the tie point in
that case. Covered by new tests in `test_sweep_line_status.py`
(`test_less_than_at_shared_endpoint_is_consistent*`,
`test_remove_edges_sharing_endpoint_*`, `test_minimal_repro_no_force_remove_needed`).

This eliminated several (but not all) `force_remove` fallbacks and one class
of silently-missing crossings.

## Fixed: `crossings.py` didn't reorder every tied edge at a multi-way crossing

Confirmed and fixed. `test_crossing_line_crossed_by_two_edges` now passes.

### Symptom

`SweepLineStatus.remove()` (and `find()`) occasionally can't locate an edge
that is genuinely still present, falling back to `force_remove()`. In some
cases the edge is never found at all by the surrounding range queries either,
so a crossing point is reported with one fewer edge than it should have
(or, rarely, an entire crossing point is dropped).

### Root cause

`SweepLineStatus` documents that whenever two edges change relative order
(cross), the caller must explicitly delete and reinsert them - the structure
itself never reorders on its own. `_CrossingSweep._handle_event` honors this
for `current_event_point.interior_list`, but **that list is incomplete** when
several edges at a crossing point are collinear/overlapping with each other.

`_get_extreme_edges` (`crossings.py:330-347`) reduces a group of tied edges
down to a single "leftmost" and "rightmost" representative, and
`_append_crossing_to_queue` (`crossings.py:349-383`) only ever tests
`(left_edge, leftmost)` and `(right_edge, rightmost)` against the sweep
status's outer neighbors (`crossings.py:442-461`). If three edges are
collinear (e.g. all going from the same node to the same coincident point),
only one of them is ever paired against the other side of the crossing and
gets a crossing event queued for it. Its tied siblings never get a crossing
event of their own, so they never go through the explicit
delete-and-reinsert in the `interior_list` loop - they stay at their
pre-crossing position in the tree forever after, becoming structurally
inconsistent for later queries at that height.

### Confirmation

Reproduced directly against `SweepLineStatus` (no `crossings.py` involved) by
replaying the exact `add`/`remove` sequence from a failing graph: edges that
were supposed to be reordered at a shared crossing point but weren't later
failed `remove()`. Patching the sequence to explicitly reorder *every* member
of each tied group at the crossing (not just the one `crossings.py` currently
picks) made all removals succeed with no `force_remove` needed - see
`test_minimal_repro_no_force_remove_needed` in `test_sweep_line_status.py`,
which encodes this corrected sequence.

### Fix applied

`_append_crossing_to_queue` now takes an optional `candidate_siblings` set (the
same `union` of `interior_list | start_list` that `_get_extreme_edges` picks its
representative from). When a future crossing is found between the representative
pair `(e1, e2)`, every other edge in `candidate_siblings` is checked geometrically
via `check_lines(sibling, e1)`: if it lands on the exact same crossing point, it is
added to the same `add_crossing()` call so it goes through the explicit
delete-and-reinsert in the `interior_list` loop alongside its representative.

Note this validates geometrically rather than trusting "tied at the same x at the
probed height" - an earlier attempt at this fix grouped edges purely by x-value
equality at the probe height, which incorrectly swept in unrelated edges that
merely had a close (but not actually collinear) x at that one sampled height,
corrupting unrelated crossings. `_get_extreme_edges` itself was left unchanged.

`test_crossing_line_crossed_by_two_edges` now passes, with no regressions
elsewhere in `tests/unit/crossings/` (380 passed before and after, modulo the
2 grid tests below, which fail for an unrelated reason).

## Fixed: spurious edges in node-crossings due to incomplete `Crossing.prune()`

`test_random_graph_small_grid` and `test_random_graph_small_grid_2` still failed
after the fix above, but no longer for the reordering bug - this is a distinct,
second bug only visible with `include_node_crossings=True`.

### Symptom

A reported crossing point includes edges that don't actually take part in it.
Minimal repro:

```python
g = nx.Graph()
g.add_edges_from([(4, 8), (6, 7), (6, 8)])
nx.set_node_attributes(g, {4: [1, -1], 6: [1, -1], 7: [0, -1], 8: [0, 1]}, "pos")
# get_crossings_quadratic(..., include_node_crossings=True) reports:
#   point (1,-1): {(4, 8), (6, 7)}
#   line  (0,1)-(1,-1): {(4, 8), (6, 8)}
# get_crossings(..., include_node_crossings=True) incorrectly merged them into:
#   point (1,-1): {(4, 8), (6, 7), (6, 8)}
```

Nodes 4 and 6 coincide at `(1, -1)`. `(6, 8)` is collinear with `(4, 8)` (already
reported as the Line crossing) and merely shares node 6 with `(6, 7)` - it has no
genuine point-crossing role at `(1, -1)` and should not appear there.

### Root cause

`_handle_event` bundles every edge touching the event point (`get_range` plus, for
node crossings, `start_list | end_list | horizontal_list`) into one `Crossing`,
then relies on `Crossing.prune()` / `_prune_crossing_point`
(`utils/crossing_data_types.py`) to remove false positives. That pruning only
handled two cases: all involved edges share a common node, or all pairs are
collinear ("just_lines"). It had no rule for a *mixed* set where some edges
genuinely cross at the point and others are only there incidentally (shared node,
or already-captured-elsewhere overlap) - so nothing got removed and the bundle was
reported as-is.

The quadratic algorithm doesn't have this problem because it builds crossings
pairwise via `check_lines()` first (which already excludes pairs that merely
`share_endpoint()`) and only merges pairs that land on the exact same `pos`.

### Fix applied

`_prune_crossing_point` now drops any edge that has no genuine `CrossingPoint`
partner (matching `self.pos` exactly) among the *other* edges still in the bundle,
checked pairwise via `check_lines`. An edge that's only related to the rest of the
bundle by sharing a node or by being collinear (`CrossingLine`) with something no
longer survives. This mirrors the quadratic algorithm's pairwise-then-merge
approach instead of trying to special-case every possible shape of false positive.

## Fixed: collinear-group detection in "Check for crossing lines" missed edges

After the two fixes above, the grid tests still failed, now showing a `Line`
crossing with fewer edges than expected, e.g. expected
`Line((0,1),(0,-1)): {(0,2),(0,7),(2,3),(2,5),(2,8),(5,7),(7,8)}` but only 2 of
the 7 edges were reported.

### Root cause

The old grouping algorithm in the "Check for crossing lines" region of
`_handle_event` walked `start_list`/interior candidates in sorted-by-x order and
chained together only *adjacent* pairs that overlap. With several edges sharing a
node (or zero-length edges from coincident nodes) sorted in between the genuinely
overlapping group, an adjacent pair could fail to overlap (e.g. excluded by
`share_endpoint`) even though both ends of that broken link *do* overlap with the
rest of the group - silently splitting the group and dropping members.

### Fix applied

Replaced the adjacency-chain walk with a full pairwise scan (`itertools.combinations`)
over all edges touching the point (`edges_from_sweepline | start_list`), mirroring
`get_crossings_quadratic`'s approach exactly: every pair gets `check_lines()`
called on it directly, and `CrossingLine` results are appended individually for
`_finalize` to merge by exact extent. This also correctly handles edges that
overlap over *different* sub-ranges depending on their other endpoint (a long edge
and a short edge sharing one tip only overlap over the short edge's extent) -
something a single representative-based clustering pass would have collapsed
incorrectly.

## Fixed: `get_range` could miss edges on a structurally stale sweep-line tree

Still on the grid tests: a node-crossing bundle was missing an edge that
genuinely passes through the point, even though it was confirmed present in the
tree (`avl_tree.py`'s `get_range`/`find` couldn't locate it; the exhaustive
`get_left`/`get_right` confirmed it wasn't tied with anything actually adjacent).

### Root cause

`SweepLineStatus` documents that an edge's relative order is only correct where
it has been explicitly reordered via delete+reinsert. An edge that never crosses
an *immediate* neighbour directly - e.g. three lines meeting at one point, where
two of the three pairs are excluded from direct comparison because they share an
endpoint - is never reordered, so its position in the tree can be locally stale
at the height being queried. `get_range` (and `find`) used bounding-box pruning
during tree descent that assumed the tree's structure matches sorted order at the
queried height; when that assumption breaks, pruning can skip the subtree holding
the edge entirely, even though the (already correct, *exhaustive*) `get_left`/
`get_right` would have found it as a non-match.

### Fix applied

`get_range` in `utils/avl_tree.py` now does a full in-order traversal with the
same membership test, instead of pruning subtrees by bounding keys - matching the
trade-off `get_left`/`get_right` already make (those are exhaustive full scans
too). `get_range` is only called a couple of times per event point, so this isn't
a new complexity class for the algorithm as a whole.

## Fixed: `get_left`/`get_right` only return one of several exactly-tied edges

Last grid-test failure (at the time): a crossing between an edge and a
*different* collinear group several steps further down the sweep was missing
entirely - not just from one bundle, but never discovered as an event at all.

### Root cause

`_handle_event` computes `left_edge`/`right_edge` once via `get_left`/`get_right`
and tests them against the current event's own tied group (`union`). But
`get_left`/`get_right` explicitly exclude exact ties and can only return a single
edge - if *several* unrelated edges happen to be exactly tied with `left_edge`/
`right_edge` at that x (a coincidence elsewhere on the sweep line, unrelated to
the current event), only the one `get_left`/`get_right` happened to pick gets
tested. Any other edge tied with it - which might be the one that actually goes
on to cross the current event's group - was silently skipped, and since this is
the *only* place that pairing would ever get tested, the crossing was never
queued at all (no later safety net catches it, unlike the `get_range` case
above).

### Fix applied (later superseded - see further down)

The first fix added `_CrossingSweep._get_ties()`, gathering every edge exactly
tied with a given outer edge via `get_range`, and a symmetric `outer_siblings`
parameter on `_append_crossing_to_queue()` checked against `e2`. This made the
grid tests pass at the time, but turned out to be incomplete - see "Fixed:
representative-pair selection could miss a crossing that a sibling pairing would
have found" below, which replaced this approach with something more general.
`_get_ties()` itself survived that redesign; the `outer_siblings` parameter on
`_append_crossing_to_queue()` did not.

## Fixed: `get_left`/`get_right` weren't actually exhaustive

Found by the new randomized stress suite (small, exact integer coordinates -
lots of coincident nodes). A crossing between two perfectly ordinary, non-tied
edges went missing, and tracing it down showed `get_right()` returning an edge
that was provably *not* the closest match - while a brute-force scan of the same
tree at the same height found the genuinely closest (and truly adjacent, with
nothing between) edge instead.

### Root cause

Both `get_range()` (see above) and `get_left()`/`get_right()` share the
*purpose* of tolerating a structurally stale tree - an edge that was never
explicitly reordered at the queried height can be anywhere in the tree's
structure relative to where it would actually sort there. `get_range()`'s old
bounding-box pruning broke that tolerance and was fixed (above) by making it a
full traversal. `get_left()`/`get_right()` were *assumed*, while fixing
`get_range()`, to already be such a full traversal - they're not: both descend
into only *one* subtree per node, chosen by comparing the key against that one
node, exactly the same kind of single-comparison-based pruning that made
`get_range()` unsafe.

### Fix applied

Rewrote both `get_left()` and `get_right()` in `utils/avl_tree.py` to visit every
node and track the best (closest) qualifying candidate directly, matching
`get_range()`'s now-exhaustive approach. Confirmed via a 9-edge, 15-node minimal
repro (`test_get_left_get_right_find_closest_match_not_just_any_match`) where
two edges are genuinely, simply adjacent at the crossing height, but one of them
was last reordered at an earlier, unrelated 5-way crossing and the stale
structural position caused the old descent to return a different, wrong-but-
technically-valid neighbour instead.

## Fixed: a zero-length edge could steal the "extreme" slot from the edge that actually needs testing

Also found by the stress suite. A crossing between two genuinely simple,
sloped edges went missing whenever a zero-length edge (both endpoints
coincident) happened to start at the same event point.

### Root cause

When several edges start/interior at the same event point, `_get_extreme_edges`
picks a "leftmost" and "rightmost" representative by comparing each edge's x at
a probe height slightly off the event - and only that one representative gets
tested against the outer neighbour. A zero-length edge's x is *constant*,
identical to its single point, regardless of the probe height; a genuinely
sloped edge's x at the same probe is some small but nonzero offset. Depending on
which side of zero that offset falls, the zero-length edge can look "more
extreme" than the sloped edge that's actually the one needing to be tested
against the outer neighbour for the real crossing - and once picked, nothing
else in the union got tried.

### Fix applied

Zero-length edges (`start_position == end_position`) are now excluded before
picking leftmost/rightmost (falling back to the full union only if *every*
member happens to be zero-length). They were never inserted into the sweep
status tree itself anyway (see the `start_list` insertion loop further down in
`_handle_event`), so excluding them from this representative selection doesn't
lose anything - it just stops them from displacing the edge that needs to be
tested. Regression test: `test_zero_length_edge_does_not_steal_the_extreme_slot`.

## Fixed: representative-pair selection could miss a crossing that a sibling pairing would have found

The deepest and most general of the bugs found here, and the one that finally
made the whole approach robust. Found via a 6-edge minimal repro: an edge
crossing one specific member of a collinear group (several edges on the same
infinite line, but with *different finite extents*) was missed because the
group's chosen representative had the wrong extent.

### Root cause

`_get_extreme_edges` and `get_left`/`get_right` each only ever return *one*
representative on their respective side (the union's extreme member, or the
single outer neighbour) - even when several edges are exactly tied there. The
two fixes above (`candidate_siblings` and `outer_siblings` on
`_append_crossing_to_queue`) tried to compensate by checking the *other* tied
edges too, but only *after* the originally-chosen representative pair already
produced a genuine crossing. If the chosen representative pair's `check_lines()`
came back `None` - e.g. because the geometric intersection of the two infinite
lines falls outside one representative's finite segment, while a *tied sibling*
with a different finite extent would have covered it - the method did nothing
at all, never reaching the sibling-checking code that would have tried the
sibling instead. Concretely: three collinear vertical edges with different
y-ranges, plus one diagonal edge crossing the line only within the range of one
specific member - whichever of the three got arbitrarily picked as "the"
representative decided whether the crossing was found, and two out of three
choices got it wrong.

### Fix applied

Replaced the "pick one representative, then conditionally expand to siblings on
success" pattern with exhaustive pairing: for each side, gather *every* edge
tied with the outer neighbour (`_get_ties`) and *every* member of the union tied
with the chosen extreme (`_get_tied_group`, new), then call
`_append_crossing_to_queue()` for every combination of the two groups
independently. Each call does its own simple `check_lines()` test with no
internal sibling logic any more; `EventQueue.add_crossing()` already merges
multiple independent discoveries of the same point into one event, so trying
every relevant pairing directly is both simpler and strictly more correct than
trying to expand only from whichever single pair happened to be chosen first.
This also made `_append_crossing_to_queue()` itself considerably simpler (back
down to just `e1`, `e2`, the event, and the output list - no more
`candidate_siblings`/`outer_siblings` parameters), and the whole suite runs
*faster* than with the sibling-expansion approach, since most events have
trivial (single-element) candidate sets and the old code did extra, usually
wasted, sibling-comparison work on every single one of them. Regression test:
`test_collinear_group_member_with_matching_extent_not_skipped`.

## Fixed: `_handle_event`'s interior-list reorder corrupted the tree via interleaved remove+add

Found while re-examining whether `avl_tree.py`'s full-traversal rewrite of
`get_left`/`get_right`/`get_range` (described above) was actually fixing a tree
problem, or just papering over a `crossings.py` bug that was feeding it a
structurally-inconsistent tree in the first place. It was the latter, at least
for this specific mechanism.

### Symptom

With `avl_tree.py` reverted to its original pruning-based `get_left`/
`get_right`/`get_range` (i.e. *before* the full-traversal rewrite), a perfectly
ordinary, non-degenerate crossing between two edges goes missing entirely - not
because anything about that crossing is itself unusual, but because the tree
was left in a structurally wrong state by something unrelated earlier in the
sweep. Minimal repro: four edges - `(0,1)`, `(2,3)`, `(4,5)`, `(6,7)` - all
passing through the exact same point `(0, 0)` (three distinct slopes plus the
vertical `(6, 7)`), followed by a fifth edge `(8, 9)` crossing three of those
four further down the sweep. `get_crossings()` silently drops the crossing
with `(4, 5)` specifically, even though it's an entirely ordinary intersection
on its own. See `test_interior_list_reorder_is_not_corrupted_by_interleaving`
in `test_crossings.py`.

### Root cause

`_handle_event`'s "reverse the order of interior edges" loop
(`crossings.py`, the loop over `current_event_point.interior_list` just before
`get_left`/`get_right` are called) processed the tied/crossing group **one
edge at a time**: remove the edge, then immediately reinsert it, then move on
to the next edge in the group. `current_event_point.interior_list` is a
`set`, so this happens in arbitrary iteration order.

For a single two-edge crossing this is harmless (removing and reinserting one
edge against an otherwise-untouched, correctly-ordered tree always lands it
correctly, since the comparison against whatever it's inserted next to is
evaluated fresh, at the current height). But for a multi-way tie (three or
more edges simultaneously interior at one point), interleaving the remove and
the reinsert *per edge* means that, while edge A is being reinserted, some of
its true new neighbours (other members of the same tied group) may already be
back in their new position while others are still missing from the tree
entirely - a transient, inconsistent intermediate state. Reinserting against
that inconsistent state, with AVL rebalancing rotations potentially firing
mid-way, can structurally misplace an edge relative to others it was never
directly compared to at the current height. The tree's in-order sequence can
come out of this loop already wrong, before `get_left`/`get_right` are even
called - so no amount of fixing *those two methods* could have addressed this
particular case; they were being handed bad input.

This is also the reason the full-traversal rewrite of `get_left`/`get_right`/
`get_range` made the symptoms go away: exhaustive search doesn't trust the
tree's structural shape at all, so it can't be misled by *this* kind of
corruption either. That made it look like a tree-level fix, but the actual
defect was here, in how `crossings.py` called `add`/`remove`.

### Fix applied

Split the loop into two passes: remove every edge in
`current_event_point.interior_list` first, and only *then* reinsert all of
them. This matches the textbook Bentley–Ottmann semantics of reordering a
multi-way tied group as a single atomic operation (reversing a contiguous
block) rather than as several independent operations that can observe each
other's half-finished state.

Confirmed by reverting `avl_tree.py` to plain pruning and running the full
randomized stress suite: 63 of 160 chunks failed with pruning alone; 0 failed
with pruning plus this two-phase fix. `avl_tree.py` has accordingly been
reverted to its original pruning-based implementation - the full-traversal
rewrite is no longer carrying its weight now that the actual cause is fixed.
Regression test: `test_interior_list_reorder_is_not_corrupted_by_interleaving`.

## Open: singleton handling disagrees with quadratic reference

Not yet investigated. Found by the randomized stress suite:
`test_tiny_coordinate_range_with_singletons` in `test_crossings_stress.py`
fails for chunk ids `[0-50]` through `[950-1000]` (20 of its 20 chunks, i.e. it
currently fails consistently rather than intermittently) when run with
`consider_singletons=True` combined with `include_node_crossings=True`. This
is unrelated to anything else in this file - none of the fixes above touch
singleton handling - and is not covered by `test_interior_list_reorder_is_not_corrupted_by_interleaving`
or any other existing regression test. Whoever picks this up next should
start by minimizing one of the failing chunk's random graphs the same way the
fixes above did, then add the minimal repro as a new section here.

## Open: `horizontal_edges.remove()` fails for a near-collinear, non-exactly-horizontal pair

Found while replacing `check_lines()`'s shapely-based implementation with a
precision-aware one (`utils/intersections.py`). Not yet root-caused - this is
a `crossings.py` event-handling bug, unrelated to the new `check_lines()`
itself, that the more accurate overlap detection now actually exercises.

### Symptom

`get_crossings()` raises `ValueError: list.remove(x): x not in list` at
`crossings.py:624` (`self.horizontal_edges.remove(horizontal)`). Minimal
repro - two edges, one exactly horizontal, the other tilted by less than the
default precision across its length so it's collinear with the first *within
precision* but not exactly:

```python
g = nx.Graph()
g.add_node(1, pos=(0, 0))
g.add_node(2, pos=(10, 0))
g.add_node(3, pos=(2, 6e-10))
g.add_node(4, pos=(8, -6e-10))
g.add_edges_from([(1, 2), (3, 4)])
crossings.get_crossings(g)  # raises
```

`get_crossings_quadratic()` handles the same graph fine and correctly reports
the overlap as a `CrossingLine((2,0), (8,0))` - see
`test_segment_shifted_within_precision_of_collinear_should_overlap` in
`test_crossings_quadratic.py`. The sweep-line equivalent in
`test_crossings.py` (`TestKnownPrecisionGaps`) is left failing as the marker
for this issue.

### Working hypothesis (unconfirmed)

`SweepLineEdgeInfo.is_horizontal()` uses a strict `numeric_eq(start.y, end.y)`
check: edge `(1, 2)` (`y=0` at both ends) qualifies; edge `(3, 4)` (`y=6e-10`
vs. `y=-6e-10`) does not, since `6e-10 - (-6e-10) = 1.2e-9` is just *outside*
the default `1e-9` precision - even though *both* of those y-values are
individually within precision of `0`. That's a non-transitive `numeric_eq`
comparison (`0 ~ 6e-10`, `0 ~ -6e-10`, but `6e-10 !~ -6e-10`) across the four
points actually involved in this event - the same general category of bug
documented several times above (a precision-based tie not forming a
consistent total order), just not yet traced through to the exact point
where `self.horizontal_edges` ends up missing the edge `_handle_event` expects
to find there. Whoever picks this up next should start by tracing the
`horizontal_list`/`self.horizontal_edges` add/remove sequence for this exact
repro, the same way `test_minimal_repro_no_force_remove_needed` did for the
`SweepLineStatus` reordering bug.
