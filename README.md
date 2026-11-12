# AI-Based Robot Navigation Simulator

## Phase 03: Image Preprocessing

The application loads local PNG, JPG, and JPEG environment images and displays the original beside an OpenCV binary preview. Fixed and adaptive thresholding, morphology, and obstacle polarity can be adjusted live. Pathfinding is not implemented yet.

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

From the project directory, with the environment activated:

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

See [Phase 03 image preprocessing](source/docs/phase_03_image_preprocessing.md) for image conventions and processing behavior.
