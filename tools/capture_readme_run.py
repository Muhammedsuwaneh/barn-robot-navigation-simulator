"""Run the real Qt pages and save validated comparison exports and screenshots."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--desktop", action="store_true", help="Show the native application window")
    args = parser.parse_args()
    if not args.desktop:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        os.environ["QT_QUICK_BACKEND"] = "software"

    import cv2
    import numpy as np
    from PyQt6.QtCore import QObject, QMetaObject, PYQT_VERSION_STR, QT_VERSION_STR
    from PyQt6.QtTest import QTest
    from PyQt6.QtQuick import QQuickWindow
    from PyQt6.QtGui import QFontDatabase, QGuiApplication
    from PyQt6 import sip
    from app.application import create_application
    from services.ai.search import ALGORITHMS
    from services.evaluation import experiment_store

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    # Keep this documentation run separate from the user's experiment history.
    experiment_store.DEFAULT_EXPERIMENT_LOG = output / "experiments.csv"
    def application_with_fonts(argv):
        application = QGuiApplication(argv)
        # Load fonts before QML resolves them in offscreen Windows sessions.
        for font in ("segoeui.ttf", "arial.ttf", "bahnschrift.ttf"):
            font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / font
            if font_path.is_file():
                QFontDatabase.addApplicationFont(str(font_path))
        return application

    with patch("app.application.QGuiApplication", side_effect=application_with_fonts):
        application, engine, custom = create_application([])
    window = sip.cast(engine.rootObjects()[0], QQuickWindow)
    barn = window.property("barnViewModel")
    window.resize(1600, 1000)
    metadata = {
        "python": platform.python_version(), "platform": platform.platform(),
        "opencv": cv2.__version__, "numpy": np.__version__,
        "pyqt": PYQT_VERSION_STR, "qt": QT_VERSION_STR,
        "qt_platform": application.platformName(),
        "movement": "Up, Down, Left, Right; unit costs",
        "custom_processing": {
            "otsu": True, "adaptive": False, "morphology": "none",
            "light_pixels_are_obstacles": False,
            "cell_size_px": 64, "obstacle_threshold_percent": 50,
        },
        "depth_limit": 30, "maps": {},
    }

    def settle():
        application.processEvents()
        QTest.qWait(250)

    def wait_for_result(model):
        deadline = time.monotonic() + 60
        while model.searchBusy and time.monotonic() < deadline:
            application.processEvents()
            QTest.qWait(5)
        if model.searchBusy:
            model.cancelSearch()
            raise RuntimeError("Search exceeded the 60-second documentation-run limit")
        if model.errorMessage:
            raise RuntimeError(model.errorMessage)

    def capture(name):
        settle()
        image = window.grabWindow()
        if image.isNull() or not image.save(str(output / name)):
            raise RuntimeError(f"Could not capture {name}")

    def compare(model, label, source, start, goal):
        model.clearSelection()
        for mode, cell in (("start", start), ("goal", goal)):
            model.setSelectionMode(mode)
            model.selectGridCell(*cell)
        assert model.canRunSearch, model.errorMessage
        model.depthLimit = 30
        model.runComparison()
        wait_for_result(model)
        assert [row["algorithm"] for row in model.comparisonRows] == list(ALGORITHMS)
        assert all(row["success"] for row in model.comparisonRows)
        for row in model.comparisonRows:
            model.inspectComparisonPath(row["record_id"])
            path = model.pathCells
            assert path[0] == list(start) and path[-1] == list(goal)
            assert len(path) - 1 == row["path_length"] == row["path_cost"]
            for r, c in path:
                assert not model._occupancy_grid.is_occupied(r, c)
            assert all(abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1 for a, b in zip(path, path[1:]))
        for fmt in ("json", "csv"):
            model.exportComparison(str(output / f"{label}-comparison.{fmt}"), fmt)
            assert not model.errorMessage, model.errorMessage
        # Display the shortest BFS path on each page.
        model.selectedAlgorithm = "BFS"
        model.inspectComparisonPath(model.comparisonRows[0]["record_id"])
        model.showExploredCells = True
        metadata["maps"][label] = {
            "source": source.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "start": start, "goal": goal,
            "grid_rows": model.gridRows, "grid_columns": model.gridColumns,
        }
        print(label, json.dumps(model.comparisonRows), flush=True)

    try:
        source = ROOT / "data/maps/map_1.png"
        custom.resetProcessing()
        custom.loadImage(str(source))
        custom.gridCellSizePx = 64
        custom.obstacleThresholdPercent = 50
        custom.generateOccupancyGrid()
        compare(custom, "custom", source, (10, 4), (4, 15))
        capture("custom-images.png")
        dialog = window.findChild(QObject, "comparisonDialog")
        QMetaObject.invokeMethod(dialog, "open")
        capture("algorithm-comparison.png")
        QMetaObject.invokeMethod(dialog, "close")
        settle()

        source = ROOT / "data/dataset/grid_files/grid_0.npy"
        custom.selectSection("barn")
        barn.importBarnMap(str(source))
        compare(barn, "barn", source, (3, 3), (10, 10))
        capture("barn-library.png")
        QMetaObject.invokeMethod(dialog, "open")
        capture("barn-comparison.png")
        QMetaObject.invokeMethod(dialog, "close")
        settle()

        source = ROOT / "data/dataset/cspace_files/cspace_0.npy"
        barn.importBarnMap(str(source))
        # Keep the map selector consistent with the programmatically imported map.
        selector = window.findChild(QObject, "barnMapSelector")
        for index, entry in enumerate(barn.barnMaps):
            if Path(entry["path"]) == source:
                selector.setProperty("currentIndex", index)
                break
        compare(barn, "barn-cspace", source, (5, 8), (15, 22))
        capture("barn-cspace-library.png")
        QMetaObject.invokeMethod(dialog, "open")
        capture("barn-cspace-comparison.png")
        QMetaObject.invokeMethod(dialog, "close")
        (output / "setup.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    finally:
        custom.cleanup()
        barn.cleanup()
        window.close()
        application.processEvents()


if __name__ == "__main__":
    main()
