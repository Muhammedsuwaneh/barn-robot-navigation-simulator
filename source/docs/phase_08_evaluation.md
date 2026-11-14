# Phase 08: Performance evaluation and algorithm comparison

The application is an offline image-to-grid navigation simulator. OpenCV converts
an uploaded image into a binary map; the immutable Boolean occupancy grid feeds
BFS, DFS, DLS, IDS, and UCS. Python services perform searches and evaluation;
PyQt worker threads keep execution outside the QML presentation layer.

## Running an experiment

1. Load an environment image, choose preprocessing options, and generate a grid.
2. Set distinct, free start and goal cells. Coordinates are zero-based
   `(row, column)`, with the origin at the top left.
3. Use **Run** for the selected algorithm, or **Compare** to open evaluation.
4. In the comparison dialog, select one or more algorithms and configure the
   common DLS/IDS maximum depth in moves. Click **Run comparison**.
5. Read the comparison table, success-count summary, and relative execution-time
   bars. Click a table row to close the dialog and show that run's exact path
   and metrics. Enable **Show explored cells** to inspect exploration.
   Unsuccessful searches show explored cells without a path.
6. Reopen **Compare** to inspect the retained table or export it to a new CSV or
   JSON file. Existing files are refused, even after a save-dialog overwrite
   confirmation. Choose another name to preserve earlier results.

All selected algorithms receive the same grid instance, endpoints, unit costs,
and four-directional movement (Up, Down, Left, Right, in deterministic order).
DLS and IDS share the configured maximum depth; other algorithms ignore it.
Weighted UCS is available through the search API, but comparison deliberately
uses unit movement costs for every algorithm. No diagonal moves are allowed.

Changing the image, grid, or endpoints invalidates the visible comparison and
interrupts any obsolete work. Historical CSV entries remain intact. Use
**Cancel** during an individual search or comparison to interrupt long searches; incomplete comparisons
are discarded and never logged as failed experimental trials. Closing the
application interrupts active searches and waits for worker threads to stop.

## Metric definitions

| Metric | Definition |
| --- | --- |
| Success | The algorithm returned a path reaching the selected goal. A depth cutoff is unsuccessful, but does not prove that the goal is unreachable. |
| Success rate | Successful trials divided by attempted trials for the same algorithm and experimental conditions. Each stored row is one trial, so its rate is 1.0 or 0.0 (100% or 0% in the UI). The summary counts successes across selected algorithms, not repeated trials of one algorithm. |
| Path length | Number of moves (edges), excluding the start cell. A zero-move successful search has length zero. |
| Path cost | Sum of movement costs along the returned path; in the comparison, each move costs one, so cost equals length. |
| Execution time | Algorithm-reported elapsed wall time in milliseconds using `perf_counter_ns`, including traversal and reconstruction, excluding worker scheduling, rendering, record creation, and disk I/O. Input validation precedes the timer. IDS includes its repeated DLS calls and aggregation. |
| Nodes expanded | Number of non-goal states whose successors are expanded. The start counts if expanded. DLS does not count depth-boundary states as expanded; a cell can be expanded again when reached at a shallower depth. IDS sums expansions across depth iterations. |
| Peak frontier size | Maximum simultaneous pending frontier entries, including the initial start entry. IDS takes the maximum across iterations, rather than summing. UCS counts priority-queue entries. This is a frontier-size metric, not total memory usage. |

Unsuccessful path length and cost are Python `None`, JSON `null`, empty CSV
fields, and **N/A** in the table. The explored-cell list is deduplicated for DLS
and IDS visualization and must not be used to reconstruct the expansion count.

## Storage and API

`services/evaluation/comparison.py` provides `compare_algorithms` for any
nonempty, distinct subset of supported algorithms. `dataset_source` defaults to
`local_image`, and API callers can supply their actual dataset source. Phase 09
adds BARN map import; see `phase_09_barn_integration.md`. `ExperimentRecord` preserves the complete search
result in memory for path inspection and serializes the required metrics.

Individual searches and completed comparisons append to
`source/data/experiments.csv`. Every new execution receives a UUID and UTC
timestamp. Records include map identifier (the image filename stem in the UI),
dataset source, grid rows/columns, endpoints, algorithm, relevant parameters,
success, success rate, path length/cost, execution time, expanded nodes, and peak
frontier size. Parameters are JSON objects, including inside CSV cells.

`append_experiments` preserves existing rows and checks the existing header
before appending. Re-appending an existing record preserves its identity;
executing a new trial produces a new ID. CSV/JSON exports contain the current
comparison's metric records, not images or path geometry. Export creation is
exclusive and never silently overwrites a file. Storage errors remain visible
in the UI while completed results remain available for inspection and export.

## Experimental protocol and interpretation

Keep the source map, preprocessing, grid resolution, obstacle threshold,
endpoints, movement costs, and depth limits fixed within a comparison. Preserve
the map and these settings alongside exports when reproducing an experiment;
the map identifier is a filename label, not a content hash.

The UI executes one trial per selected algorithm in selection order. It does
not implement repeated-run aggregation, so it does not report a timing mean or
standard deviation. For timing studies, repeat trials under the same conditions,
record system conditions, and compute per-algorithm sample mean and sample
standard deviation externally (at least two samples are needed for sample
standard deviation). Use varied algorithm orders to reduce order effects.
Execution time varies with system load, caching, and scheduling; one run is
insufficient for timing conclusions.

Compare a representative range of maps and endpoint distances, including
unreachable cases and depth cutoffs. BFS and unit-cost UCS find minimum-cost
routes; DFS and DLS can return longer valid routes. Avoid claims of universal
superiority based on a small sample. DLS/IDS can take substantial time on large
branching grids, so choose depth bounds carefully and use cancellation when
needed. No demonstration performance numbers are fabricated or preloaded.

## Validation

From `source`, run:

```powershell
python -m unittest discover -s tests -v
```

The suite runs QML smoke tests offscreen. Evaluation coverage includes identical
inputs, parameter capture, failed/cutoff null metrics, metadata, append-only
history, incompatible logs, exclusive exports, cancellation, IDS exhaustion,
comparison controls, path inspection, and result invalidation.
