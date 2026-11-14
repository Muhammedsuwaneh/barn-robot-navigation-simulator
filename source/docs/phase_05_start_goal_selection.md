# Phase 05: Start and Goal Selection

## Interaction

Generate an occupancy grid, choose **Set Start** or **Set Goal**, then click a cell in the grid preview. The chosen mode returns to idle after a successful selection. Choose the mode again to change that endpoint. The robot start defaults to the first free cell in row-major order; the user must choose a goal. **Clear** removes both endpoints and cancels an active mode. Generating a new grid still chooses the default start.

The grid displays the start with an amber `S` marker and the goal with a teal `G` marker. The selected zero-based row and column are also shown below the grid. The grid remains zoomable and pannable; clicks are normalized against the displayed grid image bounds before being converted to row and column, so fit and zoom preserve cell mapping.

## Validation and Lifecycle

- Selection requires a generated grid and an active Start or Goal mode.
- Coordinates must fall inside the grid, and occupied cells are rejected.
- Start and goal cannot share a cell. A rejected click leaves the current selection unchanged and keeps the mode active for correction.
- Loading another image clears previous endpoints; generating/replacing a grid chooses a new first-free-cell start and clears the goal.
- Changing preprocessing settings on an existing grid regenerates it and invalidates endpoint selections.

Selection and validation are owned by `NavigationViewModel`; QML sends normalized click coordinates and does not infer occupancy. Phase 06 adds BFS pathfinding; no automatic endpoint detection is performed.

## Verification

Run the unit and UI smoke tests from the `source` directory:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```