# AI-Based Robot Navigation Simulator

## Phase 04: Occupancy-Grid Generation

The application loads local PNG, JPG, and JPEG environment images, previews the original and OpenCV-processed binary image, and generates a separate occupancy grid. Thresholding and grid-resolution controls update the previews; pathfinding is not implemented yet.

### Requirements

- Python 3.10 or newer
- Windows, macOS, or Linux with a desktop environment for the graphical interface

Create and activate a virtual environment, then install the project dependencies:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

### Run

From the `source` directory, with the environment activated:

```powershell
python main.py
```

The application runs locally and does not connect to a network service. Preprocessing uses the existing `opencv-python` and `numpy` requirements; no additional runtime packages are needed.

### Tests

Run the preprocessing unit tests and QML smoke tests without opening a desktop window:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```

See [Phase 04 occupancy-grid conventions](source/docs/phase_04_occupancy_grid.md) for the cell encoding, coordinate system, and mixed-pixel rule.
