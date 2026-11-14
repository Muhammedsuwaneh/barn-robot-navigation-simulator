# Phase 10: Integration validation and final refinement

## Scope and outcome

All ten phase prompts were reviewed, with particular attention to evaluation
(08), separate BARN integration (09), and complete workflow validation (10).
The desktop application retains separate Custom images and BARN library pages,
independent page state, and one interactive BARN grid viewer.

The validation run on 2026-11-14 passed **70 tests** using:

```powershell
python -m unittest discover -s tests -q
python -m compileall -q app models services viewmodels
python -m pip check
```

`unittest` reported `Ran 70 tests in 9.193s` and `OK`. Bytecode compilation
completed without errors. Dependency checking reported `No broken requirements
found.` Test-suite duration is not an algorithm benchmark result.

Environment: Windows, Python 3.13.12, PyQt6/Qt 6.12.0, opencv-python 5.0.0.93,
NumPy 2.5.4. GUI integration tests used Qt's offscreen platform. These checks
do not substitute for interactive native-dialog and display-scaling checks on
the desktop used for the presentation.

## Refactoring and fixes

- DLS now prunes equivalent arrivals at the same or greater depth, reopening a
  cell only for a shallower arrival. This prevents unbounded enumeration of
  equivalent cyclic routes while preserving depth-bounded reachability.
  Deterministically seeded map tests compare DLS/IDS reachability with BFS at
  several depth limits and verify valid bounded paths.
- Search and comparison workers share lifecycle/ownership wiring. Individual
  searches now expose cancellation, in addition to comparison cancellation.
  Obsolete/cancelled results cannot become current results or logged trials.
  Cleanup is idempotent and interrupts/joins active workers.
- Preview encoding and versioned file replacement share one implementation.
  Existing previews remain available if a new preview cannot be written.
- **Clear** now removes both endpoints, as requested by the endpoint-selection
  specification. New grids still initialize the first free cell as the start.
- Grid and preprocessing configuration types are validated before NumPy/OpenCV
  operations. Grid storage is backed by immutable bytes so write access cannot
  be re-enabled by callers. Invalid grid coordinate types are rejected.
- Comparisons validate endpoints and depth settings before running any
  algorithm. CSV serialization is shared between history/export, and metadata
  is serialized before writing so invalid metadata cannot append partial rows
  or create partial export files. Serialized parameter dictionaries are copied.
- Removed the obsolete hidden navigation/results layouts, an unused metric-card
  component, and the disabled history-page placeholder. CSV history remains a
  supported feature; there is no historical-results browser.
- Existing tests now intercept normal history writes, while workflow tests
  exercise real CSV/JSON output in temporary directories.

## Tested coverage

| Area | Verification |
| --- | --- |
| Startup and UI | QML window loads; navigation selects the intended independent page; no detected QML script/binding errors. |
| Full custom workflow | Real grid mouse clicks, preprocessing, grid generation, occupied-cell rejection, start/goal, all five worker searches, exploration, comparison, path inspection, actual CSV/JSON output, and invalid-image state preservation. |
| Input validation | Invalid/empty images and grids, noninteger settings, malformed arrays, invalid endpoints, occupied endpoints, and the million-cell limit. |
| Resolution and scale | Non-square and partial-edge inputs at 7×13, 65×101, 320×480, and 1080×1920; valid paths on a 160×240 grid; rejection above the grid size limit. |
| Search correctness | Direct routes, detours, unreachable goals, start equal to goal at API level, deterministic neighbors, DLS cutoffs, IDS expansion totals, and uniform/weighted UCS. |
| Concurrency | A Qt timer continues firing during worker execution; cancellation stops work without logging; a late old-map result is rejected; shutdown stops active work. |
| Evaluation/storage | Identical comparison inputs, correct source/parameters, null failed-path metrics, append-only history, incompatible headers, exclusive exports, bad-metadata rejection, and logging-failure result retention. |
| BARN | All 600 supplied occupancy files imported and checked with before/after hashes; all five algorithms validated on six real maps under a documented common endpoint rule. |
| Layout | One BARN viewer; page/control separation; nonoverlap checks from 1080×720 through 3840×2160, including visible depth inputs and comparison controls. |

The small BARN route subset verifies integration, not benchmark difficulty or
universal algorithm superiority. See `phase_09_barn_integration.md` for its exact
selection rule. Synthetic arrays are temporary validation fixtures, not BARN
files or published experimental results.

## Files and operation

- Launch from `source` using `python main.py` after installing
  `source/requirements.txt` in a virtual environment.
- Automatic experiment history is exactly `source/data/experiments.csv` under
  this repository. The application resolves it from the module location,
  independently of the shell's working directory.
- Comparison exports are written to the exact new CSV/JSON path selected in
  the save dialog. No fixed export directory is configured.
- Source maps remain in `source/data/maps` and `source/data/dataset`.
  Previews use temporary `ai-navigation-*` directories, cleaned on shutdown.
- Tests' export/history files are temporary and cleaned automatically. Existing
  user history is not deleted by the refactor.
- The repository README describes installation, workflows, conventions,
  algorithms, metrics, structure, dataset support, and limitations. Local prompt
  directories should remain ignored rather than included with application code.

## Screenshots to capture for the course report

Use actual application runs and retain their source map/settings and exported
results. Suggested captures:

1. **Custom-image preparation:** original image, binary preview, generated grid,
   and the threshold/resolution controls used to create it.
2. **A successful route:** visible start/goal markers, red path, enabled explored
   cells, selected algorithm, and the corresponding measured metrics.
3. **Depth behavior:** DLS with an insufficient depth limit, then a sufficient
   DLS/IDS limit on the same endpoints. Keep the cutoff label visible.
4. **Algorithm comparison:** all five genuine rows, timing chart, timing warning,
   and shared-map identifier. Maximize the window or scroll as necessary.
5. **Failure handling:** an unreachable goal showing no path and N/A path metrics
   in the comparison table.
6. **BARN library:** an imported grid/C-space map, its identifier, the single grid
   viewer, endpoint/search controls, and real results. Keep custom-image controls
   out of this capture.

## Limitations and optional work

The required image/grid/search/comparison/BARN workflows are implemented.
Optional animation playback, repeated-trial aggregation (mean/standard
deviation), PGM/YAML import, and a history browser are not implemented. Unit
costs and four-directional movement are used in the UI; weighted costs are
available only through the UCS API. The application does not implement the full
BARN robot-navigation benchmark, semantic map understanding, or real robot
dynamics. Very large searches/overlays can still consume substantial resources.
