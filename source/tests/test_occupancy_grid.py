import unittest
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QUrl

from models.occupancy_grid import OccupancyGrid, OccupancyGridError
from services.image_processing.occupancy_grid import binary_image_to_grid
from viewmodels.navigation_view_model import NavigationViewModel


class OccupancyGridTests(unittest.TestCase):
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
			self.assertTrue(view_model.gridReady)
			self.assertEqual(view_model.gridDimensions, "2 rows x 2 columns")
			self.assertEqual(view_model.gridOccupiedCount, 2)
			self.assertEqual(view_model.gridFreeCount, 2)
			preview_path = Path(QUrl(view_model.occupancyGridPreviewUrl).toLocalFile())
			self.assertTrue(preview_path.is_file())

			view_model.gridCellSizePx = 2
			self.assertEqual(view_model.gridDimensions, "4 rows x 4 columns")
			self.assertEqual(view_model.gridOccupiedCount, 8)


if __name__ == "__main__":
	unittest.main()
