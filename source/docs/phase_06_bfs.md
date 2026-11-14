# Phase 06: BFS Baseline

## Search Contract

`breadth_first_search(grid, start, goal)` in `services/ai/bfs.py` accepts an `OccupancyGrid` and zero-based `(row, column)` integer tuples. It traverses only `False` (free) cells and uses four-directional movement in deterministic **Up, Down, Left, Right** order. Invalid coordinate types, out-of-bounds endpoints, and occupied endpoints raise `SearchInputError`.

A reachable result contains the path from start through goal, inclusive. If start equals goal, that path has one cell and zero edges/cost. An unreachable result has an empty path and `None` path length and cost.

## Metric Definitions

- **Success:** `found` is true exactly when the goal is dequeued and a path is reconstructed.
- **Path length:** number of edges/moves, not number of cells; unavailable (`None`) on failure.
- **Path cost:** sum of unit move costs; equal to path length for this grid; unavailable on failure.
- **Explored:** cells dequeued from the BFS frontier, in dequeue order, including the goal when reached.
- **Nodes expanded:** dequeued non-goal cells whose four neighbors are examined. The goal is not expanded; start-equals-goal has zero expanded nodes.
- **Peak frontier size:** largest queue size during the run, including the initial queue containing the start (minimum 1).
- **Execution time:** `perf_counter_ns` duration in milliseconds, measured after input validation through BFS and path reconstruction; excludes UI rendering and worker scheduling.

## Path Visualization

The **Run BFS** action is enabled only with a grid and distinct selected endpoints. The search executes on a worker thread. When BFS returns, only its shortest path is drawn, immediately, as a red center-to-center line from start to goal. The same ordered path is rendered over both the occupancy grid and original source image; the latter maps grid-cell centers through source pixel dimensions and fit-to-view bounds.

Explored cells are retained in the search result and can be drawn using **Show explored cells**, added with the shared algorithm interface. No alternate routes or filled path-cell overlays are shown. Start/goal markers remain visible above the route. Reset clears the result and line without clearing start and goal. Unreachable searches show no line and report that no route was found.

## Default Map Preparation and Start

Preprocessing defaults to a lightly Gaussian-smoothed Otsu threshold to separate grayscale obstacle regions without requiring a fixed threshold guess. Fixed and adaptive threshold modes remain available for maps that need manual tuning. Once a grid is generated, the robot start is placed at the first free cell in row-major order (top-left to bottom-right); the user selects the goal. Regenerating a grid chooses a new valid default start and clears the previous goal.

Run the complete test suite from the `source` directory:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```