# Phase 03: Image Loading and OpenCV Preprocessing

## Supported Input

Load local PNG, JPG, or JPEG images through the environment-image picker. The loader decodes file bytes with OpenCV, which also supports paths containing non-ASCII characters on Windows. Empty, unreadable, or unsupported files produce a visible error; a failed selection does not discard an image that is already loaded.

The original is previewed beside the processed image. Preview data is kept in a temporary directory and removed when the application exits.

## Processing

The independently testable functions are in `services/image_processing/preprocessing.py`:

- Convert 8-bit grayscale, BGR, or BGRA image arrays to grayscale.
- Apply a fixed binary threshold (0-255), or Gaussian adaptive thresholding with an odd block size and configurable C value.
- Optionally apply morphological opening or closing to the obstacle mask with an odd-sized kernel.
- Return a binary `uint8` image containing only 0 and 255.

The processed preview has one stable convention: **black (0) is obstacle; white (255) is free space**. By default, dark source pixels are obstacles. Enable “White source pixels are obstacles” to invert the source interpretation. Morphology operates on the obstacle mask so opening removes small obstacle specks and closing fills small gaps.

Controls immediately reprocess the currently loaded image. Reset restores fixed threshold 128, adaptive threshold off, block size 11, C 2, morphology none, kernel size 3, and dark pixels as obstacles.

Thresholding is classical image processing, not scene understanding. A photograph may not produce a reliable navigation map; inspect and validate the binary preview before using it as navigation input. This phase does not create an occupancy grid or run pathfinding.

## Verification

From the project directory, run the preprocessing and application smoke tests:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```