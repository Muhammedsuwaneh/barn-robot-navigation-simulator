import unittest
import tempfile
import time
from unittest.mock import patch
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QCoreApplication, QUrl
from PyQt6.QtTest import QTest

from models.occupancy_grid import OccupancyGrid, OccupancyGridError
from services.image_processing.occupancy_grid import binary_image_to_grid
from viewmodels.navigation_view_model import NavigationViewModel


class OccupancyGridTests(unittest.TestCase):
	def setUp(self) -> None:
		log_patch = patch("viewmodels.navigation_view_model.append_experiments")
		log_patch.start()
		self.addCleanup(log_patch.stop)

	def test_grid_model_rejects_non_integer_configuration_and_oversized_grids(self) -> None:
		from dataclasses import replace
		grid = OccupancyGrid(np.zeros((2, 3), dtype=np.bool_), 1, 50, 3, 2)
		with self.assertRaises(ValueError):
			grid.cells.setflags(write=True)
		for name in ("cell_size_px", "obstacle_threshold_percent", "source_width_px", "source_height_px"):
			for value in (True, 1.5, "2"):
				with self.subTest(name=name, value=value), self.assertRaises(OccupancyGridError):
					replace(grid, **{name: value})
		with self.assertRaises(OccupancyGridError):
			OccupancyGrid(np.zeros((1001, 1000), dtype=np.bool_), 1, 50, 1000, 1001)

	def test_different_resolutions_preserve_partial_edge_dimensions(self) -> None:
		for height, width in ((7, 13), (65, 101), (320, 480), (1080, 1920)):
			with self.subTest(resolution=(height, width)):
				image = np.full((height, width), 255, dtype=np.uint8)
				image[:min(8, height), :min(8, width)] = 0
				grid = binary_image_to_grid(image, cell_size_px=8)
				self.assertEqual(grid.rows, (height + 7) // 8)
				self.assertEqual(grid.columns, (width + 7) // 8)
				self.assertTrue(grid.is_occupied(0, 0))
				self.assertEqual(grid.occupied_count, 1)

	def test_conversion_uses_majority_rule_and_partial_edge_pixels(self) -> None:
		binary = np.array(
			[
				[0, 0, 255],
				[0, 255, 255],
				[255, 255, 0],
			],
			dtype=np.uint8,
		)
		grid = binary_image_to_grid(binary, cell_size_px=2, obstacle_threshold_percent=50)

		self.assertEqual((grid.rows, grid.columns), (2, 2))
		self.assertEqual(grid.cells.tolist(), [[True, False], [False, True]])
		self.assertEqual((grid.occupied_count, grid.free_count), (2, 2))
		self.assertTrue(grid.is_occupied(0, 0))
		self.assertFalse(grid.is_occupied(0, 1))

	def test_threshold_is_inclusive_and_uses_actual_edge_area(self) -> None:
		binary = np.array([[0, 255], [255, 255]], dtype=np.uint8)
		self.assertTrue(binary_image_to_grid(binary, 2, 25).is_occupied(0, 0))
		self.assertFalse(binary_image_to_grid(binary, 2, 26).is_occupied(0, 0))

	def test_boolean_input_means_true_is_occupied(self) -> None:
		binary = np.array([[True, False], [False, False]], dtype=np.bool_)
		grid = binary_image_to_grid(binary, 1, 50)
		self.assertEqual(grid.cells.tolist(), [[True, False], [False, False]])

	def test_grid_data_is_immutable_and_row_major(self) -> None:
		grid = binary_image_to_grid(np.array([[0, 255], [255, 0]], dtype=np.uint8), 1)
		self.assertEqual(grid.to_flat_list(), [True, False, False, True])
		with self.assertRaises(ValueError):
			grid.cells[0, 0] = False
		with self.assertRaises(IndexError):
			grid.is_occupied(2, 0)

	def test_invalid_images_and_parameters_are_rejected(self) -> None:
		with self.assertRaises(OccupancyGridError):
			binary_image_to_grid(np.empty((0, 0), dtype=np.uint8))
		with self.assertRaises(OccupancyGridError):
			binary_image_to_grid(np.array([[127]], dtype=np.uint8))
		with self.assertRaises(OccupancyGridError):
			binary_image_to_grid(np.zeros((2, 2, 3), dtype=np.uint8))
		with self.assertRaises(OccupancyGridError):
			binary_image_to_grid(np.zeros((2, 2), dtype=np.uint8), cell_size_px=0)
		with self.assertRaises(OccupancyGridError):
			binary_image_to_grid(np.zeros((2, 2), dtype=np.uint8), obstacle_threshold_percent=101)

	def test_grid_model_validates_shape_type_and_source_dimensions(self) -> None:
		with self.assertRaises(OccupancyGridError):
			OccupancyGrid(np.array([[0]], dtype=np.uint8), 1, 50, 1, 1)
		with self.assertRaises(OccupancyGridError):
			OccupancyGrid(np.ones((1, 1), dtype=np.bool_), 2, 50, 3, 3)

	def test_view_model_generates_grid_preview_and_updates_resolution(self) -> None:
		image = np.full((8, 8), 255, dtype=np.uint8)
		image[:, :4] = 0
		encoded, buffer = cv2.imencode(".png", image)
		self.assertTrue(encoded)

		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "environment.png"
			image_path.write_bytes(buffer.tobytes())
			view_model = NavigationViewModel()
			self.addCleanup(view_model.cleanup)
			view_model.loadImage(str(image_path))
			self.assertFalse(view_model.gridReady)

			view_model.gridCellSizePx = 4
			view_model.generateOccupancyGrid()
			self.assertTrue(view_model.hasStart)
			self.assertEqual(view_model.startCoordinate, "row 0, col 1")
			self.assertTrue(view_model.gridReady)
			self.assertEqual(view_model.gridDimensions, "2 rows x 2 columns")
			self.assertEqual(view_model.gridOccupiedCount, 2)
			self.assertEqual(view_model.gridFreeCount, 2)
			preview_path = Path(QUrl(view_model.occupancyGridPreviewUrl).toLocalFile())
			self.assertTrue(preview_path.is_file())

			view_model.gridCellSizePx = 2
			self.assertEqual(view_model.gridDimensions, "4 rows x 4 columns")
			self.assertEqual(view_model.gridOccupiedCount, 8)

	def test_start_goal_selection_validation_change_clear_and_invalidation(self) -> None:
		image = np.full((8, 12), 255, dtype=np.uint8)
		image[:, :4] = 0
		encoded, buffer = cv2.imencode(".png", image)
		self.assertTrue(encoded)

		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "environment.png"
			image_path.write_bytes(buffer.tobytes())
			view_model = NavigationViewModel()
			self.addCleanup(view_model.cleanup)
			view_model.loadImage(str(image_path))
			view_model.gridCellSizePx = 4
			view_model.generateOccupancyGrid()
			self.assertTrue(view_model.hasStart)
			self.assertEqual(view_model.startCoordinate, "row 0, col 1")

			view_model.setSelectionMode("start")
			view_model.selectGridPosition(0.1, 0.1)
			self.assertIn("occupied", view_model.errorMessage)
			self.assertEqual(view_model.selectionMode, "start")

			view_model.selectGridPosition(0.5, 0.1)
			self.assertTrue(view_model.hasStart)
			self.assertEqual(view_model.startCoordinate, "row 0, col 1")
			self.assertEqual(view_model.selectionMode, "none")

			view_model.setSelectionMode("goal")
			view_model.selectGridCell(0, 1)
			self.assertIn("different", view_model.errorMessage)
			self.assertEqual(view_model.selectionMode, "goal")
			view_model.selectGridCell(1, 2)
			self.assertTrue(view_model.hasGoal)
			self.assertEqual(view_model.goalCoordinate, "row 1, col 2")

			view_model.setSelectionMode("start")
			view_model.selectGridPosition(0.9, 0.9)
			self.assertIn("different", view_model.errorMessage)
			view_model.selectGridPosition(0.5, 0.9)
			self.assertEqual(view_model.startCoordinate, "row 1, col 1")

			view_model.clearSelection()
			self.assertFalse(view_model.hasStart)
			self.assertFalse(view_model.hasGoal)
			self.assertEqual(view_model.startCoordinate, "Not set")
			view_model.setSelectionMode("goal")
			view_model.selectGridPosition(0.5, 0.1)
			view_model.generateOccupancyGrid()
			self.assertTrue(view_model.hasStart)
			self.assertFalse(view_model.hasGoal)
			self.assertEqual(view_model.startCoordinate, "row 0, col 1")
			self.assertEqual(view_model.selectionMode, "none")

	def test_view_model_runs_bfs_and_returns_shortest_path_immediately(self) -> None:
		image = np.full((8, 8), 255, dtype=np.uint8)
		image[:, :4] = 0
		encoded, buffer = cv2.imencode(".png", image)
		self.assertTrue(encoded)

		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "bfs-environment.png"
			image_path.write_bytes(buffer.tobytes())
			view_model = NavigationViewModel()
			self.addCleanup(view_model.cleanup)
			view_model.loadImage(str(image_path))
			view_model.gridCellSizePx = 4
			view_model.generateOccupancyGrid()
			view_model.setSelectionMode("start")
			view_model.selectGridCell(0, 1)
			view_model.setSelectionMode("goal")
			view_model.selectGridCell(1, 1)

			application = QCoreApplication.instance()
			if application is None:
				application = QCoreApplication([])
			self._application = application
			view_model.runBfs()

			deadline = time.monotonic() + 5
			while view_model.searchBusy and time.monotonic() < deadline:
				application.processEvents()
				QTest.qWait(5)
			self.assertFalse(view_model.searchBusy)
			self.assertTrue(view_model.hasSearchResult)
			self.assertTrue(view_model.searchSucceeded)
			self.assertEqual(view_model.pathLength, 1)
			self.assertEqual(view_model.pathCost, 1)
			self.assertEqual(view_model.nodesExpanded, 1)

			self.assertEqual(view_model.pathCells, [[0, 1], [1, 1]])

			view_model.resetSearchVisualization()
			self.assertFalse(view_model.hasSearchResult)
			self.assertTrue(view_model.hasStart)
			self.assertTrue(view_model.hasGoal)

			for algorithm in ("DFS", "DLS", "IDS", "UCS"):
				with self.subTest(algorithm=algorithm):
					view_model.selectedAlgorithm = algorithm
					view_model.depthLimit = 1
					view_model.runSearch()
					deadline = time.monotonic() + 5
					while view_model.searchBusy and time.monotonic() < deadline:
						application.processEvents()
						QTest.qWait(5)
					self.assertFalse(view_model.searchBusy)
					self.assertTrue(view_model.searchSucceeded)
					self.assertEqual(view_model.searchSummary.split()[0], algorithm)


if __name__ == "__main__":
	unittest.main()
