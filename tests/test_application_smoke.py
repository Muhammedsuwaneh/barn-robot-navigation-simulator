import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QMetaObject, QPointF, QRectF, Qt, QTimer, qInstallMessageHandler
from PyQt6.QtTest import QTest
from PyQt6.QtQuick import QQuickItem

from app.application import create_application


class ApplicationSmokeTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.qt_messages = []
		cls.old_message_handler = qInstallMessageHandler(lambda kind, context, message: cls.qt_messages.append(message))
		cls.addClassCleanup(lambda: qInstallMessageHandler(cls.old_message_handler))
		cls.log_patch = patch("viewmodels.navigation_view_model.append_experiments")
		cls.log_patch.start()
		cls.addClassCleanup(cls.log_patch.stop)
		cls.application, cls.engine, cls.view_model = create_application([])
		cls.window = cls.engine.rootObjects()[0]
		cls.startup_geometry = cls.window.geometry()
		# The offscreen monitor can be smaller than the workflow's test layout.
		cls.window.resize(1440, 900)
		cls.application.processEvents()
		cls.barn_view_model = cls.window.property("barnViewModel")
		control_names = (
			"loadImageButton",
			"generateGridButton",
			"setStartButton",
			"setGoalButton",
			"clearSelectionButton",
			"gridSelectionMouseArea",
			"algorithmSelector",
			"runSearchButton",
		)
		cls.initial_enabled_states = {
			name: cls.window.findChild(QObject, name).property("enabled")
			for name in control_names
		}

	@classmethod
	def tearDownClass(cls) -> None:
		cls.window.close()
		cls.view_model.cleanup()
		cls.barn_view_model.cleanup()
		cls.engine.deleteLater()
		cls.application.processEvents()
		super().tearDownClass()

	def test_qml_window_loads_with_backend_context(self) -> None:
		self.assertEqual(self.window.property("title"), "AI Robot Navigation Simulator")
		self.assertEqual(self.view_model.property("activeSection"), "workspace")

	def test_window_fills_work_area_with_custom_title_bar(self) -> None:
		self.assertEqual(self.startup_geometry, self.window.screen().availableGeometry())
		self.assertTrue(self.window.flags() & Qt.WindowType.FramelessWindowHint)
		self.assertFalse(self.window.windowState() & Qt.WindowState.WindowFullScreen)
		self.assertIsNotNone(self.window.findChild(QObject, "customTitleBar"))
		self.assertEqual(len(self.window.findChildren(QObject, "closeWindowButton")), 1)

	def test_preprocessing_settings_expand_without_moving_grid_controls(self) -> None:
		page = self.window.findChild(QObject, "customImagesPage")
		panel = page.findChild(QObject, "processingPanel")
		frame = page.findChild(QObject, "gridViewportFrame")
		toggle = page.findChild(QObject, "toggleProcessingButton")
		self.view_model.selectSection("workspace")
		self.application.processEvents()
		collapsed_height = panel.height()
		grid_height = frame.height()
		try:
			QMetaObject.invokeMethod(toggle, "clicked")
			QTest.qWait(30)
			self.assertTrue(page.property("processingExpanded"))
			self.assertGreater(panel.height(), collapsed_height)
			self.assertAlmostEqual(frame.height(), grid_height, delta=1)
			self.assertTrue(page.findChild(QObject, "thresholdSlider").property("visible"))
		finally:
			page.setProperty("processingExpanded", False)
			self.application.processEvents()

	def wait_for_search(self, model, timeout: float = 5) -> None:
		deadline = time.monotonic() + timeout
		while model.searchBusy and time.monotonic() < deadline:
			self.application.processEvents()
			QTest.qWait(5)
		self.application.processEvents()
		self.assertFalse(model.searchBusy, model.errorMessage)

	def test_cleanup_interrupts_an_active_worker_and_is_repeatable(self) -> None:
		from models.occupancy_grid import OccupancyGrid
		from viewmodels.navigation_view_model import NavigationViewModel
		from services.ai.search_utils import SearchCancelled
		model = NavigationViewModel()
		self.addCleanup(model.cleanup)
		model._occupancy_grid = OccupancyGrid(np.zeros((1, 2), dtype=np.bool_), 1, 50, 2, 1)
		model._start_cell, model._goal_cell = (0, 0), (0, 1)
		def interrupted(*args, should_cancel, **kwargs):
			while not should_cancel():
				time.sleep(0.001)
			raise SearchCancelled("Shutdown")
		with patch("viewmodels.search_worker.run_search", side_effect=interrupted):
			model.runBfs()
			thread = model._search_thread
			model.cleanup()
			self.assertFalse(thread.isRunning())
			model.cleanup()
		self.application.processEvents()

	def test_all_occupied_custom_map_has_no_default_endpoints(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "blocked.png"
			ok, buffer = cv2.imencode(".png", np.zeros((16, 24), dtype=np.uint8))
			self.assertTrue(ok)
			path.write_bytes(buffer.tobytes())
			self.view_model.resetProcessing()
			self.view_model.loadImage(str(path))
			self.view_model.gridCellSizePx = 4
			self.view_model.generateOccupancyGrid()
			self.assertEqual(self.view_model.gridFreeCount, 0)
			self.assertFalse(self.view_model.hasStart)
			self.assertFalse(self.view_model.hasGoal)
			self.assertFalse(self.view_model.canRunSearch)

	def test_full_custom_image_workflow_all_algorithms_and_exports(self) -> None:
		import csv
		import json
		from services.evaluation.experiment_store import append_experiments
		model = self.view_model
		self.view_model.selectSection("workspace")
		model.resetProcessing()
		model.otsuThreshold = False
		model.threshold = 128
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			image = np.full((60, 80), 255, dtype=np.uint8)
			image[20:30, 10:70] = 0
			ok, buffer = cv2.imencode(".png", image)
			self.assertTrue(ok)
			path = root / "workflow.png"
			path.write_bytes(buffer.tobytes())
			model.loadImage(str(path))
			model.gridCellSizePx = 10
			QMetaObject.invokeMethod(self.window.findChild(QObject, "generateGridButton"), "clicked")
			QTest.qWait(30)
			self.assertEqual((model.gridRows, model.gridColumns), (6, 8))
			area = self.window.findChild(QObject, "gridSelectionMouseArea")
			def click_cell(row, column):
				point = area.mapToScene(QPointF((column + 0.5) * area.width() / model.gridColumns, (row + 0.5) * area.height() / model.gridRows))
				QTest.mouseClick(self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point.toPoint())
			QMetaObject.invokeMethod(self.window.findChild(QObject, "setStartButton"), "clicked")
			# clicked() emits the handler without toggling the button itself.
			model.setSelectionMode("start")
			click_cell(2, 0)
			self.assertEqual(model.startCoordinate, "row 2, col 0")
			model.setSelectionMode("goal")
			click_cell(2, 2)
			self.assertIn("occupied", model.errorMessage)
			click_cell(2, 7)
			self.assertEqual(model.goalCoordinate, "row 2, col 7")
			model.depthLimit = 12
			log_path = root / "experiments.csv"
			with patch("viewmodels.navigation_view_model.append_experiments", side_effect=lambda records: append_experiments(records, log_path)):
				for algorithm in ("BFS", "DFS", "DLS", "IDS", "UCS"):
					model.selectedAlgorithm = algorithm
					QMetaObject.invokeMethod(self.window.findChild(QObject, "runSearchButton"), "clicked")
					self.wait_for_search(model)
					self.assertTrue(model.searchSucceeded, model.searchSummary)
					self.assertEqual(model.pathCells[0], [2, 0])
					self.assertEqual(model.pathCells[-1], [2, 7])
					model.showExploredCells = True
					self.assertTrue(model.exploredCells)
				model.runComparison()
				self.wait_for_search(model)
			self.assertEqual(len(model.comparisonRows), 5)
			for format in ("csv", "json"):
				output = root / f"comparison.{format}"
				model.exportComparison(str(output), format)
				self.assertTrue(output.is_file(), model.errorMessage)
			self.assertEqual(len(json.loads((root / "comparison.json").read_text())), 5)
			with log_path.open(newline="", encoding="utf-8") as source:
				rows = list(csv.DictReader(source))
			self.assertEqual(len(rows), 10)
			self.assertEqual({row["dataset_source"] for row in rows}, {"local_image"})
			for record in model.comparisonRows:
				model.inspectComparisonPath(record["record_id"])
				self.assertTrue(model.pathCells)
			bad = root / "invalid.png"
			bad.write_bytes(b"not an image")
			previous_path = model.pathCells
			model.loadImage(str(bad))
			self.assertEqual(model.pathCells, previous_path)
			self.assertIn("readable image", model.errorMessage)
			model.threshold = 129
			self.assertFalse(model.hasSearchResult)
			self.assertFalse(model.hasComparisonResults)
			self.assertEqual(model.exploredCells, [])
			self.assertFalse(model.hasGoal)
			model.clearSelection()
			self.assertFalse(model.hasStart)
			self.assertFalse(model.hasGoal)

	def test_worker_keeps_ui_responsive_cancel_and_map_change_reject_stale_results(self) -> None:
		from threading import Event
		from services.ai.search import run_search
		from services.ai.search_utils import SearchCancelled
		model = self.view_model
		model.resetProcessing()
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			ok, buffer = cv2.imencode(".png", np.full((8, 8), 255, dtype=np.uint8))
			self.assertTrue(ok)
			for name in ("before.png", "after.png"):
				(root / name).write_bytes(buffer.tobytes())
			model.loadImage(str(root / "before.png"))
			model.gridCellSizePx = 4
			model.generateOccupancyGrid()
			model.setSelectionMode("goal")
			model.selectGridCell(1, 1)
			def wait_for_cancel(*args, should_cancel, **kwargs):
				while not should_cancel():
					time.sleep(0.001)
				raise SearchCancelled("Cancelled")
			ticks = []
			timer = QTimer()
			timer.setInterval(5)
			timer.timeout.connect(lambda: ticks.append(True))
			with patch("viewmodels.search_worker.run_search", side_effect=wait_for_cancel), patch("viewmodels.navigation_view_model.append_experiments") as log:
				model.runBfs()
				timer.start()
				try:
					deadline = time.monotonic() + 2
					while len(ticks) < 3 and time.monotonic() < deadline:
						QTest.qWait(10)
					self.assertGreaterEqual(len(ticks), 2)
					cancel = self.window.findChild(QObject, "cancelSearchButton")
					self.assertTrue(cancel.property("visible"))
					QMetaObject.invokeMethod(cancel, "clicked")
					self.wait_for_search(model)
					self.assertFalse(model.hasSearchResult)
					log.assert_not_called()
				finally:
					timer.stop()
					model.cancelSearch()
			old_result = run_search("BFS", model._occupancy_grid, (0, 0), (1, 1))
			release = Event()
			def delayed_old_result(*args, **kwargs):
				release.wait(2)
				return old_result
			with patch("viewmodels.search_worker.run_search", side_effect=delayed_old_result), patch("viewmodels.navigation_view_model.append_experiments") as log:
				model.runBfs()
				model.loadImage(str(root / "after.png"))
				release.set()
				self.wait_for_search(model)
				self.assertEqual(model.imageName, "after.png")
				self.assertFalse(model.gridReady)
				self.assertFalse(model.hasStart)
				self.assertFalse(model.hasGoal)
				self.assertFalse(model.hasSearchResult)
				self.assertEqual(model.exploredCells, [])
				log.assert_not_called()

	def test_z_no_qml_binding_or_script_errors(self) -> None:
		unexpected = [message for message in self.qt_messages if any(
			marker in message for marker in ("ReferenceError", "TypeError", "Binding loop", "Cannot assign", "is not a function")
		)]
		self.assertEqual(unexpected, [])

	def test_responsive_layouts_keep_one_barn_viewer_and_controls_separate(self) -> None:
		barn_page = self.window.findChild(QObject, "barnLibraryPage")
		self.assertEqual(len(barn_page.findChildren(QObject, "occupancyGridPreview")), 1)
		self.assertIsNone(barn_page.findChild(QObject, "originalPathOverlay"))
		def scene_rect(item):
			return QRectF(item.mapToScene(QPointF(0, 0)), item.size())
		try:
			for width, height in ((1080, 720), (1440, 900), (1920, 1080), (2560, 1440), (3840, 2160)):
				self.window.resize(width, height)
				for section, page_name, model in (("workspace", "customImagesPage", self.view_model), ("barn", "barnLibraryPage", self.barn_view_model)):
					with self.subTest(size=(width, height), section=section):
						self.view_model.selectSection(section)
						model.selectedAlgorithm = "DLS"
						QTest.qWait(30)
						page = self.window.findChild(QObject, page_name)
						frame = page.findChild(QObject, "gridViewportFrame")
						controls = page.findChild(QObject, "gridControlsScroll")
						self.assertFalse(scene_rect(frame).intersects(scene_rect(controls)))
						self.assertGreaterEqual(frame.height(), 180)
						for name in ("runSearchButton", "compareAlgorithmsButton", "depthLimitInput"):
							control = page.findChild(QObject, name)
							self.assertGreater(control.width(), 0)
							self.assertLessEqual(control.x() + control.width(), control.parentItem().width() + 1)
						if section == "workspace":
							preview = page.findChild(QObject, "customPreviewPanel")
							processing = page.findChild(QObject, "processingPanel")
							self.assertFalse(scene_rect(preview).intersects(scene_rect(processing)))
							self.assertLessEqual(scene_rect(controls).bottom(), scene_rect(preview).bottom())
							source = page.findChild(QObject, "originalImagePreview").parentItem()
							processed = page.findChild(QObject, "processedImagePreview").parentItem()
							self.assertAlmostEqual(source.width(), processed.width(), delta=1)
							self.assertAlmostEqual(source.height(), processed.height(), delta=1)
							self.assertGreaterEqual(source.height(), 280)
							self.assertFalse(scene_rect(source).intersects(scene_rect(processed)))
							self.assertLessEqual(scene_rect(source).bottom(), scene_rect(processed).top())
							self.assertLessEqual(scene_rect(source).right(), scene_rect(frame).left())
							self.assertLessEqual(scene_rect(processed).right(), scene_rect(frame).left())
							self.assertAlmostEqual(source.parentItem().width(), frame.parentItem().parentItem().width(), delta=1)
							for name in ("setStartButton", "setGoalButton", "runSearchButton", "compareAlgorithmsButton"):
								self.assertLessEqual(page.findChild(QObject, name).height(), 34)
						else:
							viewer = page.findChild(QObject, "barnGridViewer")
							self.assertEqual(viewer.property("wideLayout"), viewer.width() >= 600)
							image = page.findChild(QObject, "occupancyGridPreview")
							if model.gridReady:
								marker = page.findChild(QObject, "startCellMarker")
								self.assertAlmostEqual(marker.x() + marker.width() / 2, image.x() + (model.startColumn + 0.5) * image.width() / model.gridColumns, places=3)
				dialog = self.window.findChild(QObject, "comparisonDialog")
				QMetaObject.invokeMethod(dialog, "open")
				QTest.qWait(30)
				items = [dialog.property("contentItem")]
				depth_input = None
				while items:
					item = items.pop()
					if item.objectName() == "comparisonDepthInput":
						depth_input = item
						break
					items.extend(item.childItems())
				self.assertIsNotNone(depth_input)
				flow = depth_input.parentItem()
				choices = [item for item in flow.childItems() if item.isVisible() and item.width() > 0 and item.height() > 0]
				for index, choice in enumerate(choices):
					self.assertLessEqual(choice.x() + choice.width(), flow.width() + 1)
					for other in choices[index + 1:]:
						self.assertFalse(scene_rect(choice).intersects(scene_rect(other)))
				QMetaObject.invokeMethod(dialog, "close")
		finally:
			self.window.resize(1440, 900)
			self.view_model.selectSection("workspace")

	def test_pages_keep_custom_image_and_barn_state_independent(self) -> None:
		custom_page = self.window.findChild(QObject, "customImagesPage")
		barn_page = self.window.findChild(QObject, "barnLibraryPage")
		self.assertIsNone(custom_page.findChild(QObject, "barnMapSelector"))
		self.assertIsNone(barn_page.findChild(QObject, "loadImageButton"))
		self.assertIsNone(barn_page.findChild(QObject, "generateGridButton"))
		self.assertIsNot(self.view_model, self.barn_view_model)
		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "independent.png"
			ok, buffer = cv2.imencode(".png", np.full((8, 8), 255, dtype=np.uint8))
			self.assertTrue(ok)
			image_path.write_bytes(buffer.tobytes())
			self.view_model.loadImage(str(image_path))
			self.view_model.gridCellSizePx = 4
			self.view_model.generateOccupancyGrid()
			self.view_model.setSelectionMode("goal")
			self.view_model.selectGridCell(1, 1)
			self.view_model.depthLimit = 9
			self.barn_view_model.depthLimit = 4
			QMetaObject.invokeMethod(self.window.findChild(QObject, "barnLibraryNavigation"), "clicked")
			self.application.processEvents()
			self.assertEqual(self.view_model.activeSection, "barn")
			self.assertTrue(barn_page.property("visible"))
			self.assertFalse(custom_page.property("visible"))
			self.assertIs(self.window.property("activeViewModel"), self.barn_view_model)
			QMetaObject.invokeMethod(barn_page.findChild(QObject, "compareAlgorithmsButton"), "clicked")
			self.application.processEvents()
			dialog = self.window.findChild(QObject, "comparisonDialog")
			self.assertIs(dialog.property("viewModel"), self.barn_view_model)
			QMetaObject.invokeMethod(dialog, "close")
			QMetaObject.invokeMethod(self.window.findChild(QObject, "customImagesNavigation"), "clicked")
			self.application.processEvents()
			self.assertTrue(custom_page.property("visible"))
			self.assertFalse(barn_page.property("visible"))
			self.assertIs(self.window.property("activeViewModel"), self.view_model)
			self.assertEqual(self.view_model.mapIdentifier, "independent")
			self.assertEqual(self.view_model.goalCoordinate, "row 1, col 1")
			self.assertEqual(self.view_model.gridCellSizePx, 4)
			self.assertEqual(self.view_model.depthLimit, 9)
			self.assertEqual(self.barn_view_model.depthLimit, 4)
			self.assertEqual(self.view_model.gridRows, 2)

	def test_barn_selection_runs_search_and_comparison_with_source_metadata(self) -> None:
		barn_model = self.barn_view_model
		from services.datasets.barn import DEFAULT_BARN_DIRECTORY
		from services.ai.search_utils import neighbors
		if not DEFAULT_BARN_DIRECTORY.is_dir():
			self.skipTest("Local BARN dataset not installed")
		QMetaObject.invokeMethod(self.window.findChild(QObject, "barnLibraryNavigation"), "clicked")
		barn_model.scanBarnDirectory(str(DEFAULT_BARN_DIRECTORY))
		self.application.processEvents()
		selector = self.window.findChild(QObject, "barnMapSelector")
		self.assertEqual(selector.property("count"), 600)
		selector.setProperty("currentIndex", 0)
		QMetaObject.invokeMethod(self.window.findChild(QObject, "importBarnMapButton"), "clicked")
		self.application.processEvents()
		self.assertTrue(barn_model.isBarnMap, barn_model.errorMessage)
		self.assertEqual(barn_model.imageName, "BARN/grid_0")
		self.assertFalse(self.window.findChild(QObject, "customImagesPage").property("visible"))
		self.assertTrue(self.window.findChild(QObject, "barnLibraryPage").property("visible"))
		self.assertEqual(barn_model.gridRows, 30)
		start = (barn_model.startRow, barn_model.startColumn)
		_, goal = next(neighbors(barn_model._occupancy_grid, start))
		barn_model.setSelectionMode("goal")
		barn_model.selectGridCell(*goal)
		barn_model.depthLimit = 4
		with patch("viewmodels.navigation_view_model.append_experiments") as log:
			for run in (barn_model.runBfs, barn_model.runComparison):
				run()
				deadline = time.monotonic() + 5
				while barn_model.searchBusy and time.monotonic() < deadline:
					self.application.processEvents()
					QTest.qWait(5)
				self.assertFalse(barn_model.searchBusy)
			self.assertEqual(log.call_count, 2)
			for call in log.call_args_list:
				for record in call.args[0]:
					self.assertEqual(record.dataset_source, "BARN")
					self.assertEqual(record.map_identifier, "BARN/grid_0")
		self.assertEqual(len(barn_model.comparisonRows), 5)
		self.assertTrue(all(row["success"] for row in barn_model.comparisonRows))
		import json
		with tempfile.TemporaryDirectory() as directory:
			output_path = Path(directory) / "barn-results.json"
			barn_model.exportComparison(str(output_path), "json")
			self.assertEqual(json.loads(output_path.read_text())[0]["dataset_source"], "BARN")
			image_path = Path(directory) / "custom.png"
			ok, buffer = cv2.imencode(".png", np.full((8, 8), 255, dtype=np.uint8))
			self.assertTrue(ok)
			image_path.write_bytes(buffer.tobytes())
			self.view_model.loadImage(str(image_path))
			QMetaObject.invokeMethod(self.window.findChild(QObject, "customImagesNavigation"), "clicked")
			self.application.processEvents()
			self.assertEqual(self.view_model.datasetSource, "local_image")
			self.assertFalse(self.view_model.hasComparisonResults)
			self.assertTrue(barn_model.hasComparisonResults)
			self.assertEqual(barn_model.mapIdentifier, "BARN/grid_0")

	def test_comparison_controls_run_export_and_inspect_results(self) -> None:
		image = np.full((3, 5), 255, dtype=np.uint8)
		encoded, buffer = cv2.imencode(".png", image)
		self.assertTrue(encoded)
		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "comparison.png"
			image_path.write_bytes(buffer.tobytes())
			self.view_model.loadImage(str(image_path))
			self.view_model.gridCellSizePx = 1
			self.view_model.generateOccupancyGrid()
			self.view_model.setSelectionMode("goal")
			self.view_model.selectGridCell(0, 4)
			self.application.processEvents()
			button = self.window.findChild(QObject, "compareAlgorithmsButton")
			self.assertTrue(button.property("enabled"))
			QMetaObject.invokeMethod(button, "clicked")
			self.application.processEvents()
			dialog = self.window.findChild(QObject, "comparisonDialog")
			self.assertTrue(dialog.property("visible"))
			def find_control(name):
				items = [dialog.property("contentItem")]
				while items:
					item = items.pop()
					if item.objectName() == name:
						return item
					items.extend(item.childItems())
				self.fail(f"Comparison control not found: {name}")
			for algorithm in ("DLS", "IDS", "DFS"):
				choice = find_control("compare" + algorithm + "CheckBox")
				choice.setProperty("checked", False)
			QMetaObject.invokeMethod(find_control("runComparisonButton"), "clicked")
			deadline = time.monotonic() + 5
			while self.view_model.searchBusy and time.monotonic() < deadline:
				self.application.processEvents()
				QTest.qWait(5)
			self.application.processEvents()
			self.assertFalse(self.view_model.searchBusy)
			rows = self.view_model.comparisonRows
			self.assertEqual([row["algorithm"] for row in rows], ["BFS", "UCS"])
			self.assertEqual(find_control("comparisonResultsTable").property("count"), 2)
			for format in ("csv", "json"):
				destination = Path(directory) / ("comparison." + format)
				self.view_model.exportComparison(str(destination), format)
				self.assertTrue(destination.exists(), self.view_model.errorMessage)
				before = destination.read_bytes()
				self.view_model.exportComparison(str(destination), format)
				self.assertIn("Unable to export", self.view_model.errorMessage)
				self.assertEqual(destination.read_bytes(), before)
			self.view_model.inspectComparisonPath(rows[1]["record_id"])
			self.assertEqual(self.view_model.selectedAlgorithm, "UCS")
			self.assertEqual(self.view_model.pathLength, 4)
			self.assertEqual(len(self.view_model.pathCells), 5)
			self.view_model.setSelectionMode("goal")
			self.view_model.selectGridCell(0, 3)
			self.assertFalse(self.view_model.hasComparisonResults)
			self.assertFalse(self.view_model.hasSearchResult)
			QMetaObject.invokeMethod(dialog, "close")

	def test_comparison_cancel_stops_worker_without_logging_partial_results(self) -> None:
		from services.ai.search_utils import SearchCancelled
		from models.occupancy_grid import OccupancyGrid
		def interrupted_comparison(*args, should_cancel, **kwargs):
			while not should_cancel():
				time.sleep(0.001)
			raise SearchCancelled("Cancelled")
		self.view_model._occupancy_grid = OccupancyGrid(np.zeros((1, 2), dtype=np.bool_), 1, 50, 2, 1)
		self.view_model._start_cell = (0, 0)
		self.view_model._goal_cell = (0, 1)
		with patch("viewmodels.comparison_worker.compare_algorithms", side_effect=interrupted_comparison), patch("viewmodels.navigation_view_model.append_experiments") as log:
			self.view_model.runComparison()
			self.assertTrue(self.view_model.comparisonBusy)
			self.view_model.cancelComparison()
			deadline = time.monotonic() + 5
			while self.view_model.comparisonBusy and time.monotonic() < deadline:
				self.application.processEvents()
				QTest.qWait(5)
			self.assertFalse(self.view_model.comparisonBusy)
			self.assertFalse(self.view_model.hasComparisonResults)
			log.assert_not_called()

	def test_algorithm_selector_and_depth_limit_follow_selection(self) -> None:
		selector = self.window.findChild(QObject, "algorithmSelector")
		depth_input = self.window.findChild(QObject, "depthLimitInput")
		self.assertIsNotNone(selector)
		self.assertIsNotNone(depth_input)
		self.assertEqual(selector.property("count"), 5)

		self.view_model.selectedAlgorithm = "DLS"
		self.view_model.depthLimit = 12
		self.application.processEvents()
		self.assertEqual(selector.property("currentText"), "DLS")
		self.assertTrue(depth_input.property("visible"))
		self.assertEqual(depth_input.property("value"), 12)

		self.view_model.selectedAlgorithm = "DFS"
		self.application.processEvents()
		self.assertFalse(depth_input.property("visible"))

	def test_grid_selection_controls_and_marker_follow_view_model(self) -> None:
		image = np.full((8, 8), 255, dtype=np.uint8)
		image[:, :4] = 0
		encoded, buffer = cv2.imencode(".png", image)
		self.assertTrue(encoded)

		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "selection-grid.png"
			image_path.write_bytes(buffer.tobytes())
			self.view_model.loadImage(str(image_path))
			self.view_model.gridCellSizePx = 4
			self.view_model.generateOccupancyGrid()
			self.application.processEvents()

			set_start = self.window.findChild(QObject, "setStartButton")
			mouse_area = self.window.findChild(QObject, "gridSelectionMouseArea")
			start_marker = self.window.findChild(QObject, "startCellMarker")
			self.assertTrue(set_start.property("enabled"))
			self.assertFalse(mouse_area.property("enabled"))
			self.assertTrue(start_marker.property("visible"))

			self.view_model.setSelectionMode("start")
			self.application.processEvents()
			self.assertTrue(mouse_area.property("enabled"))
			self.view_model.selectGridPosition(0.75, 0.25)
			self.application.processEvents()
			self.assertTrue(start_marker.property("visible"))
			self.assertEqual(self.view_model.startCoordinate, "row 0, col 1")

			self.view_model.setSelectionMode("goal")
			self.view_model.selectGridPosition(0.75, 0.75)
			self.view_model.runBfs()
			deadline = time.monotonic() + 5
			while self.view_model.searchBusy and time.monotonic() < deadline:
				self.application.processEvents()
				QTest.qWait(5)
			self.application.processEvents()
			original_path_overlay = self.window.findChild(QObject, "originalPathOverlay")
			self.assertTrue(self.view_model.gridReady, self.view_model.searchSummary)
			self.assertTrue(self.view_model.searchSucceeded)
			self.assertGreater(len(self.view_model.pathCells), 0)
			self.assertIsNotNone(original_path_overlay)
			self.assertTrue(original_path_overlay.property("visible"))
			self.assertGreater(original_path_overlay.property("width"), 0)

	def test_image_loading_is_enabled_but_pathfinding_is_disabled(self) -> None:
		self.assertTrue(self.initial_enabled_states["loadImageButton"])
		self.assertFalse(self.initial_enabled_states["generateGridButton"])
		grid_preview = self.window.findChild(QObject, "occupancyGridPreview")
		self.assertIsNotNone(grid_preview)
		for object_name in ("setStartButton", "setGoalButton", "clearSelectionButton"):
			with self.subTest(control=object_name):
				self.assertFalse(self.initial_enabled_states[object_name])

		for object_name in ("algorithmSelector",):
			with self.subTest(control=object_name):
				self.assertFalse(self.initial_enabled_states[object_name])
		self.assertFalse(self.initial_enabled_states["runSearchButton"])


if __name__ == "__main__":
	unittest.main()
