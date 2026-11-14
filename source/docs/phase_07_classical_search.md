# Phase 07: Classical Search Algorithms

## Algorithms

All algorithms consume the shared immutable occupancy grid and zero-based `(row, column)` start/goal coordinates. They use four-directional neighbors in deterministic Up, Down, Left, Right order, reject out-of-bounds or occupied endpoints, and return `SearchResult`.

- **BFS:** shortest path by edge count when each move costs one.
- **DFS:** stack-based depth-first traversal; a found path is valid but is not guaranteed shortest.
- **DLS:** depth-first traversal bounded by a configurable number of edges. `depth_limit` distinguishes a cutoff from proven unreachability. A cell is reopened only if reached at a shallower depth, avoiding repeated enumeration of equivalent paths in cyclic maps.
- **IDS:** repeats DLS from depth zero through the configured bound. `expanded_nodes` is summed across iterations; explored cells are reported once in first-seen order. IDS is not presented as generally optimal.
- **UCS:** priority-queue search minimizing accumulated positive movement cost. Optional costs map destination `(row, column)` cells to positive integer entry costs; unconfigured cells cost one and the start-cell entry is excluded. With uniform unit costs, UCS and BFS have the same optimal path cost.

DFS, DLS, and IDS are not guaranteed to return a shortest path. The path-length metric counts edges; for successful unit-cost searches, path cost equals path length. UCS reports its accumulated entry cost, which can differ from edge count.

## Metrics

- `found` reports whether a goal route was found.
- `path` is inclusive of start and goal; `path_length` counts edges, and `path_cost` is absent on failure.
- `explored` records cells removed from each algorithm's frontier; IDS deduplicates this list across iterations.
- `expanded_nodes` counts expanded non-goal states. IDS sums expansions over all iterations.
- `peak_frontier_size` is the maximum frontier/priority-queue size, including the initial start entry.
- `elapsed_ms` measures algorithm work and path reconstruction, excluding UI scheduling/rendering.

## Interface

Choose an algorithm in the grid panel. DLS and IDS reveal a depth-limit input. **Run** executes on a worker thread; the result path is drawn in red on the original map and occupancy grid. The optional **Show explored cells** checkbox displays visited cells as a secondary overlay; it does not replace the red selected path. Metrics show path edges/cost, expanded nodes, peak frontier, and elapsed time. Reset clears results without removing endpoints. **Clear** removes both endpoints. **Cancel** interrupts an individual search without logging a partial trial.

The UCS API accepts weighted cell-entry costs; the current UI uses its default unit costs. No other algorithm has weights or diagonal movement enabled.

Run all algorithm and interface tests from the `source` directory:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```
