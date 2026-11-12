# Phase 01: Repository Audit and Architecture

## Repository Audit

The current source tree is a small desktop-app scaffold:

- `main.py` creates a `QGuiApplication`, loads `views/main.qml`, and exits if the QML root fails to load.
- `views/main.qml` contains only a blank `ApplicationWindow`; its title is still `MonitorX`.
- `requirements.txt` lists `PyQt6`, `opencv-python`, and `numpy`.
- The remaining application, service, model, view-model, resource, and test directories are empty. There are no implemented image-processing or navigation algorithms to preserve.

The existing entry point and QML loading approach are suitable to retain. The `models` directory is appropriate for application data types; it is not a machine-learning model directory. The local `monitorxenv` virtual environment is developer tooling and is not part of the application architecture.

The project is an offline, static-image application. It needs no camera-capture service, training data, learned-model storage, network service, ROS, or Gazebo. Those empty scaffolding folders, along with generic `utils`, event/log data folders, and generated `__pycache__`, were removed. The virtual environment and existing source files were left intact.

## Proposed Architecture

Keep responsibilities separate without adding a framework layer for each operation:

- **Application/bootstrap (`main.py`, `app/`)**: construct the Qt application, QML engine, view-model, and shared services.
- **Domain models (`models/`)**: define the occupancy grid, cell coordinate, image-processing options, and search result types. Keep these independent of QML.
- **Image processing (`services/image_processing/`)**: load a static image, convert it to grayscale, apply configurable thresholding/polarity, and generate an occupancy grid.
- **Search (`services/ai/`)**: implement BFS, DFS, DLS, IDS, and UCS against one shared grid and result interface.
- **Map import (`services/maps/`)**: adapt compatible BARN map files separately to the same occupancy-grid model; do not make BARN-specific assumptions part of the search algorithms.
- **Evaluation (`services/evaluation/`)**: run comparable searches and collect their metrics without coupling benchmark logic to the UI.
- **View-model (`viewmodels/`)**: validate user actions, call services, hold current image/grid/endpoints/results, and expose state to QML.
- **QML (`views/`)**: provide image/map selection, endpoint selection, algorithm controls, grid/path rendering, and comparison views.
- **Tests and assets (`tests/`, `data/`, `resources/`)**: keep fixtures separate from user-selected input and use resources for application assets.

```text
main.py
app/
models/
  cell.py
  occupancy_grid.py
  search_result.py
services/
  ai/
    search.py
    bfs.py
    dfs.py
    dls.py
    ids.py
    ucs.py
  evaluation/
  image_processing/
  maps/
viewmodels/
  navigation_view_model.py
views/
  main.qml
  components/
  pages/
resources/
  fonts/
  icons/
  images/
data/
  datasets/
  testing/
tests/
docs/
  phase_01_architecture.md
requirements.txt
```

This is a destination structure, not a request to create empty packages now. Keep the existing folders that fit it and add modules only as their phase is implemented.

## Core Data Contracts

### Occupancy grid

Represent a map as a two-dimensional NumPy boolean array with shape `(rows, columns)`: `True` means occupied/blocked and `False` means traversable. A `Cell` is an immutable `(row, column)` coordinate and indexes the array as `grid[row, column]`. The model should validate that the array is two-dimensional and endpoints are in bounds and traversable. Use four-connected movement (up, right, down, left) consistently for the initial version; diagonal motion can be a later, explicit option.

Store image threshold and obstacle-polarity settings with processing options, not inside the grid. Both custom-image processing and BARN import must produce this same grid representation. For initial searches, every traversable move has cost 1. This keeps the occupancy model simple and makes UCS valid, while documenting that UCS and BFS have equivalent optimal cost behavior on this unweighted grid.

### Shared search interface and result

All algorithms should accept the same inputs and return the same result shape. DLS/IDS additionally accept a depth bound; it is optional for other algorithms.

```python
search(grid, start, goal, *, max_depth=None) -> SearchResult
```

`SearchResult` should contain:

- `algorithm`: stable algorithm identifier.
- `found`: whether a route was found.
- `path`: ordered cells from start through goal, inclusive; empty when not found.
- `explored`: cells visited by the search in first-visit order for visualization.
- `path_cost`: number of moves for the initial unit-cost grid; `None` when no path exists.
- `expanded_nodes`: number of nodes expanded, using the same definition across algorithms.
- `elapsed_ms`: measured with a monotonic high-resolution timer.
- `termination_reason`: for example, `found`, `unreachable`, or `depth_limit`.

Use a typed dataclass (and an enum or literal type for stable identifiers/reasons) so algorithms, evaluation code, and the UI share one contract. IDS should report aggregate work and elapsed time across its depth-limited iterations; its `explored` sequence should avoid duplicate cells so rendering stays clear.

## Python and QML Communication

Keep Python as the owner of the map and search state. Expose one `QObject` view-model to QML using a root context property on `QQmlApplicationEngine`. Use `pyqtProperty` for observable state, `pyqtSignal` for state/result/error notifications, and `pyqtSlot` for user actions such as loading an image, setting an endpoint, choosing an algorithm, and starting a search.

For grid rendering, expose cells through a small `QAbstractListModel` with row, column, and display-state roles rather than repeatedly serializing a NumPy array into nested QML arrays. QML sends endpoint coordinates back to Python; Python validates them against the grid. Keep NumPy and OpenCV types out of the QML API. If image processing or search becomes long-running, execute it off the GUI thread and deliver results back through Qt signals; keep the first implementation synchronous only while workloads are demonstrably small.

## Dependencies

The existing `requirements.txt` is already the appropriate minimal runtime proposal:

```text
PyQt6
opencv-python
numpy
```

Keep these as runtime dependencies. Add `pytest` as a development/test dependency when tests are introduced (prefer a separate development requirements file if runtime installs should remain minimal). Avoid adding plotting, deep-learning, robotics, camera, or network packages. Pin versions after the project has a selected Python version and a tested environment, rather than choosing unverified pins during the audit phase.

## Development Roadmap

1. **Phase 01 - Audit and architecture:** document the repository state, shared contracts, dependency scope, and implementation order.
2. **Phase 02 - Core models and search:** implement and test the occupancy grid, endpoint validation, shared result, and five algorithms on hand-authored grids.
3. **Phase 03 - Image and map inputs:** implement configurable static-image conversion and a separate BARN adapter, both producing the common grid; add representative fixtures.
4. **Phase 04 - Desktop workflow:** connect the view-model to QML; support image/map selection, endpoint selection, algorithm execution, and explored/path visualization.
5. **Phase 05 - Evaluation and polish:** add repeatable algorithm comparisons, edge-case and GUI integration tests, error handling, packaging checks, and user-facing documentation.

No application behavior beyond the existing launcher is implemented in this phase. Phase 02 should begin only after approval.