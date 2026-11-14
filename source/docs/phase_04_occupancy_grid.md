# Phase 04: Occupancy-Grid Generation

## Representation

The application stores an occupancy grid as a two-dimensional `numpy.bool_` array with shape `(rows, columns)`:

- `True` means occupied (obstacle), and must not be traversed by future search algorithms.
- `False` means free space.
- `grid[row, column]` uses zero-based coordinates, with `(0, 0)` at the top-left. Rows increase downward; columns increase to the right.
- The array is row-major. The grid model validates and makes its cell array read-only after construction.

The original source image, its processed binary image, and the occupancy grid are held as separate representations. The processed binary-image convention is black (`0`) for obstacle pixels and white (`255`) for free pixels. A Boolean image accepted directly by the converter uses `True` for obstacle pixels.

## Pixel-to-Cell Rule

The configured cell size is measured in source-image pixels. For image width `W`, height `H`, and cell size `s`, grid dimensions are:

```text
columns = ceil(W / s)
rows    = ceil(H / s)
```

Partial cells at the right and bottom edges are retained. Their obstacle percentage is calculated using only the source pixels inside that partial region.

A cell is occupied when its obstacle-pixel fraction is **greater than or equal to** the configured threshold. The default is 50%, so a mixed region with at least half obstacle pixels is occupied. This conservative rule avoids labeling an obstacle-majority region as traversable. The user can set the threshold from 1% to 100%.

Cell size is configurable from 1 to 512 source pixels. The converter rejects empty or non-binary input, invalid settings, and grids exceeding one million cells. Increase cell size if an image would exceed that limit.

## Workflow and Visualization

1. Load a supported local environment image.
2. Inspect the original and tune the processed binary preview. Black is obstacle; white is free.
3. Choose cell size and obstacle percentage, then generate the grid.
4. Inspect the occupancy-grid preview, dimensions, and occupied/free counts. Use Fit or the zoom controls to inspect detail.

The grid preview is a separate image generated from the validated Boolean grid. It does not replace the source or binary preview. Grid settings can be changed and the grid regenerated; preprocessing changes also refresh an already generated grid. Start and goal selection are implemented in Phase 05; pathfinding is not implemented.

## Tests

Run the unit and UI smoke tests from the `source` directory:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```