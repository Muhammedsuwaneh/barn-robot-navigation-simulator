# Phase 09: BARN dataset integration

This application imports compatible occupancy representations from the local
Benchmark for Autonomous Robot Navigation (BARN) dataset for classical grid
search. The supplied dataset contains **300 scenarios**, with multiple files
per scenario. It is not a collection of 300 interchangeable images. This
integration does not reproduce the complete BARN autonomous navigation benchmark.

## Inspection of the supplied files

The actual dataset at `source/data/dataset` was inspected before implementation:

| Directory | Local files | Inspection and use |
| --- | --- | --- |
| `grid_files` | 300 `grid_i.npy` | All 300 arrays are 30×30 `int64`, with values 0 and 1. Directly importable raw occupancy grids. |
| `cspace_files` | 300 `cspace_i.npy` | All 300 arrays are 30×30 `int64`, with values 0 and 1. Directly importable Jackal C-space occupancy grids. |
| `map_files` | 300 `.pgm` and 300 `.yaml` | Map-server representations; not imported by this pipeline. The inspected `map_pgm_0.pgm` is 66×30 `uint8` with values 0 and 255, unlike its 30×30 NumPy grid. |
| `path_files` | 300 `path_i.npy` | Reference point sequences, not occupancy maps. Inspected scenarios 0–2 have shapes 43×2, 37×2, and 45×2. They include repeated points and are not injected as search results. |
| `metrics_files` | 300 `metrics_i.npy` | Existing environment descriptors, not search performance results or occupancy maps; inspected examples have shape `(5,)`. |
| `norm_metrics_files` | 300 `norm_metrics_i.npy` | Normalized environment descriptors; not imported as maps. |
| `world_files` | 300 `world_i.world` | Gazebo environment files; not loaded or executed. |

The inspected `yaml_0.yaml` references `map_pgm_0.pgm`, with resolution 0.15,
origin `[-4.5, 0.0, 0]`, occupied/free thresholds 0.50, and negate 0. These
map-server fields are not applied to the NumPy grids. PGM/YAML dimensions and
coordinate conventions must not be assumed equivalent to direct grid indices.
Counts and formats above describe the supplied files, not downloaded substitutes.

## Supported importer

`services/datasets/barn.py` provides:

- `discover_maps(directory)`: find occupancy candidates in a dataset root or
  directly selected `grid_files`/`cspace_files` directory. Candidates are sorted
  by map family and numeric scenario, rather than alphabetically (2 before 10).
- `describe_map(path)`: retain source path, map family, scenario, and an
  identifier such as `BARN/grid_0` or `BARN/cspace_0`.
- `import_barn_map(path)`: validate and convert to the same immutable
  `OccupancyGrid` consumed by all five search algorithms.

Only `grid_i.npy` and `cspace_i.npy`, for scenario indices 0–299, are recognized.
Files are opened using NumPy with `allow_pickle=False` and read-only memory
mapping. Validation rejects corrupt/missing files, object/string/complex arrays,
empty or non-2D arrays, nonbinary values (including NaN and infinity), and maps
over the existing 1,000,000-cell limit. Binary Boolean, integer, or floating-point
arrays are accepted; the supplied arrays are integers. Compatible alternate
dimensions are accepted within the limit; dimensions are never silently resized.
Catalog entries are validated when imported, so a corrupt map receives a visible
error and cannot replace the current valid map.

**0 means free; 1 means occupied.** Conversion produces Boolean cells, with
`False` free and `True` occupied. Rows/columns retain their original array order:
top-left origin, zero-based `(row, column)`, no rotation, transpose, or vertical
flip. One imported cell becomes one internal cell, with `cell_size_px=1` and
matching logical source dimensions. The required occupancy-threshold field is
set to 50 for model compatibility; no threshold classification is performed.
Path length and unit path cost remain measured in grid moves, not meters.

C-space maps already encode their dataset-specific clearance assumptions. The
importer applies no additional robot-radius inflation or learned interpretation.
It does not infer physical clearance guarantees from raw grids.

## UI and separate input pipelines

The **BARN library** page automatically catalogs the supplied `data/dataset` folder
if it exists. Its selector shows 600 occupancy maps representing 300 scenarios in two
families. Choose a family/scenario and click **Import BARN map**. **Dataset
folder** selects another local root or map-family folder; an empty/missing
dataset is reported without downloading or synthesizing files.

Custom images follow `Image → OpenCV preprocessing → Occupancy grid`.
BARN maps follow `BARN NumPy map → validation/conversion → Occupancy grid`.
Uploads and preprocessing live on the **Custom images** page; dataset-folder and
BARN map selection live on the **BARN library** page. Each page retains its own
map, endpoints, algorithm settings, paths, comparisons, and status when switching
pages. Loading a map on one page does not replace or clear the other page's work.
Both pages use the same endpoint controls, four-directional movement, algorithms,
comparison dialog, and exports. BARN import never invokes the image thresholding
pipeline. It immediately supplies the grid and a raster preview generated only
in the application's temporary preview directory. Image processing controls are
only available on Custom images, and grid-resolution changes are refused for
imported BARN maps. Comparison and export use the active page's results.

BARN uses one interactive grid viewer. On wider pages, search controls sit beside
the grid; on narrower pages they sit below it. Custom-image original/binary
previews remain on Custom images. Page content and comparison dialogs scroll
when needed, and preprocessing sections grow to fit their controls rather than
using fixed heights. Layout checks cover 1080×720 through 3840×2160 windows.

The first row-major free cell becomes the default start, consistent with custom
grids. Users explicitly select distinct free endpoints and may change the start.
An all-occupied map has no default start. Importing/replacing a map clears that
page's old endpoints, paths, and comparisons, and interrupts its obsolete searches.
Invalid imports preserve the previously loaded map and its results.

## Experiment metadata and preservation

Individual search records and every comparison trial use `dataset_source=BARN`
and `map_identifier=BARN/<family>_<scenario>`. Custom-image records retain
`dataset_source=local_image` and their existing image identifier. CSV history and
CSV/JSON exports carry these fields, so results remain separable by source and
map family. DLS/IDS parameters and the same grid dimensions/endpoints are logged
as in Phase 08. Source identifiers are labels, not dataset content hashes.

Original dataset files are only read. No `.npy`, `.pgm`, `.yaml`, `.world`,
reference path, or metric file is rewritten or converted in place. Search logs
remain in `data/experiments.csv`, outside the dataset tree. The tests compare
SHA-256 hashes before/after importing all 600 provided occupancy maps.

## Documented evaluation subset

`tests/test_barn_import.py` executes **BFS, DFS, DLS, IDS, and UCS** on the actual
supplied `grid_0`, `grid_1`, `grid_2`, `cspace_0`, `cspace_1`, and `cspace_2`
maps. The reproducible endpoint protocol is:

1. Start at the first free cell in row-major order.
2. Traverse free cells by BFS in Up, Down, Left, Right order; choose the first
   cell reached at exactly four moves as the goal.
3. Give all five algorithms these exact endpoints and the unmodified map, with
   unit costs and no diagonal movement. Set the DLS/IDS maximum depth to four.
4. Verify success, endpoints, free-cell membership, adjacent moves, source
   metadata, and temporary CSV/JSON storage.

These short local routes verify interoperability and reproducibility, not
navigation difficulty or performance rankings. They do not use BARN's full
navigation protocol or claim whole-environment benchmark success. Longer routes
can be selected interactively; DLS/IDS may require larger limits and substantially
more time. Reference paths are not treated as solutions produced by this app.
No experimental timing values are invented or preloaded. See
`phase_08_evaluation.md` for timing variability and metric definitions.

Run from `source`:

```powershell
python -m unittest discover -s tests -v
```

Validation-fixture tests use clearly temporary arrays to test invalid inputs;
they do not add fabricated BARN files to the dataset. Real-data integration tests
are skipped if the local dataset directory is absent. UI smoke tests exercise
map selection/import, direct grid use, searches, comparisons, exported source
metadata, and transition back to custom images. No ROS, Gazebo, physical robot,
deep learning, or learned navigation policy is involved.
