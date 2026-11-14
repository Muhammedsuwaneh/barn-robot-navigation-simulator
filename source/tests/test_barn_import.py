import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from collections import deque

import cv2
import numpy as np

from services.datasets.barn import (
	DEFAULT_BARN_DIRECTORY, BarnImportError, describe_map, discover_maps, import_barn_map,
)
from services.ai.search import ALGORITHMS
from services.ai.search_utils import neighbors
from services.evaluation.comparison import compare_algorithms
from services.evaluation.experiment_store import append_experiments, export_experiments
from viewmodels.navigation_view_model import NavigationViewModel


class BarnImporterTests(unittest.TestCase):
	def test_discovery_sorts_scenarios_and_excludes_non_maps(self) -> None:
		# Temporary validation fixtures are not a replacement or copy of BARN data.
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			for folder in ("grid_files", "cspace_files", "path_files"):
				(root / folder).mkdir()
			for relative in ("grid_files/grid_10.npy", "grid_files/grid_2.npy", "cspace_files/cspace_0.npy", "path_files/path_0.npy", "grid_files/metrics_1.npy", "grid_files/grid_300.npy"):
				(root / relative).touch()
			entries = discover_maps(root)
			self.assertEqual([entry.identifier for entry in entries], ["BARN/grid_2", "BARN/grid_10", "BARN/cspace_0"])
			self.assertEqual(len(discover_maps(root / "cspace_files")), 1)
			self.assertEqual(discover_maps(root / "path_files"), ())
			with self.assertRaises(BarnImportError):
				discover_maps(root / "missing")

	def test_import_preserves_values_orientation_and_original_file(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "grid_0.npy"
			cells = np.array([[0, 1, 1], [1, 0, 0]], dtype=np.int64)
			np.save(path, cells)
			before = path.read_bytes()
			grid = import_barn_map(path)
			self.assertEqual((grid.rows, grid.columns, grid.cell_size_px), (2, 3, 1))
			np.testing.assert_array_equal(grid.cells, cells.astype(bool))
			self.assertFalse(grid.cells.flags.writeable)
			self.assertEqual(path.read_bytes(), before)

	def test_rejects_invalid_shapes_values_types_and_files(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "grid_0.npy"
			invalid = [np.zeros(3), np.zeros((0, 3)), np.zeros((2, 2, 2)), np.array([[0, 2]]), np.array([[0, -1]]), np.array([[np.nan]]), np.array([[np.inf]]), np.array([["0"]]), np.array([[1j]]), np.array([[object()]], dtype=object)]
			for array in invalid:
				np.save(path, array)
				with self.subTest(shape=array.shape, dtype=array.dtype), self.assertRaises(BarnImportError):
					import_barn_map(path)
			np.save(path, np.zeros((2, 3)))
			with patch("services.datasets.barn.MAX_GRID_CELLS", 5), self.assertRaises(BarnImportError):
				import_barn_map(path)
			path.write_bytes(b"not a numpy file")
			with self.assertRaises(BarnImportError):
				import_barn_map(path)
			with self.assertRaises(BarnImportError):
				import_barn_map(path.with_name("grid_1.npy"))
			for name in ("path_0.npy", "metrics_0.npy", "grid_0.pgm", "grid_300.npy"):
				with self.subTest(name=name), self.assertRaises(BarnImportError):
					describe_map(path.with_name(name))

	def test_binary_boolean_and_float_maps_are_compatible(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "cspace_1.npy"
			for dtype in (bool, np.uint8, np.float64):
				np.save(path, np.array([[0, 1]], dtype=dtype))
				self.assertEqual(import_barn_map(path).to_flat_list(), [False, True])

	def test_view_model_keeps_pipelines_separate_and_preserves_state_on_bad_import(self) -> None:
		view_model = NavigationViewModel()
		self.addCleanup(view_model.cleanup)
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			map_path = root / "grid_0.npy"
			np.save(map_path, np.array([[0, 0, 1], [1, 0, 0]]))
			with patch("viewmodels.navigation_view_model.preprocess_image") as preprocess:
				view_model.scanBarnDirectory(str(root))
				view_model.importBarnMap(str(map_path))
				preprocess.assert_not_called()
			self.assertTrue(view_model.isBarnMap)
			self.assertFalse(view_model.hasImage)
			self.assertEqual(view_model.datasetSource, "BARN")
			self.assertEqual(view_model.mapIdentifier, "BARN/grid_0")
			self.assertEqual(view_model.sourceImageWidth, 3)
			self.assertEqual(view_model.gridCellSizePx, 1)
			self.assertEqual(view_model.originalPreviewUrl, view_model.occupancyGridPreviewUrl)
			self.assertEqual(view_model.processedPreviewUrl, "")
			view_model.gridCellSizePx = 8
			view_model.threshold = 10
			self.assertEqual(view_model.gridCellSizePx, 1)
			view_model.importBarnMap(str(root / "grid_1.npy"))
			self.assertEqual(view_model.mapIdentifier, "BARN/grid_0")
			self.assertTrue(view_model.gridReady)
			image_path = root / "custom.png"
			ok, buffer = cv2.imencode(".png", np.full((8, 8), 255, dtype=np.uint8))
			self.assertTrue(ok)
			image_path.write_bytes(buffer.tobytes())
			view_model.loadImage(str(image_path))
			self.assertFalse(view_model.isBarnMap)
			self.assertEqual(view_model.datasetSource, "local_image")
			self.assertEqual(view_model.mapIdentifier, "custom")
			self.assertTrue(view_model.hasImage)
			self.assertFalse(view_model.gridReady)


@unittest.skipUnless(DEFAULT_BARN_DIRECTORY.is_dir(), "Local BARN dataset not installed")
class ProvidedBarnDatasetTests(unittest.TestCase):
	def test_all_provided_occupancy_maps_validate_without_modification(self) -> None:
		entries = discover_maps(DEFAULT_BARN_DIRECTORY)
		self.assertEqual(len(entries), 600)
		for entry in entries:
			with self.subTest(map=entry.identifier):
				before = hashlib.sha256(entry.path.read_bytes()).digest()
				grid = import_barn_map(entry.path)
				self.assertEqual((grid.rows, grid.columns), (30, 30))
				self.assertEqual(hashlib.sha256(entry.path.read_bytes()).digest(), before)

	def test_all_algorithms_on_documented_real_map_subset(self) -> None:
		# Shared protocol: first free cell, first U/D/L/R BFS cell at distance 4.
		for family in ("grid", "cspace"):
			for scenario in (0, 1, 2):
				path = DEFAULT_BARN_DIRECTORY / f"{family}_files" / f"{family}_{scenario}.npy"
				grid = import_barn_map(path)
				start = tuple(int(value) for value in np.argwhere(~grid.cells)[0])
				queue = deque([(start, 0)])
				visited = {start}
				goal = None
				while queue:
					cell, depth = queue.popleft()
					if depth == 4:
						goal = cell
						break
					for _, neighbor in neighbors(grid, cell):
						if neighbor not in visited:
							visited.add(neighbor)
							queue.append((neighbor, depth + 1))
				self.assertIsNotNone(goal)
				records = compare_algorithms(grid, start, goal, ALGORITHMS, 4, describe_map(path).identifier, "BARN")
				for record in records:
					with self.subTest(map=record.map_identifier, algorithm=record.algorithm):
						self.assertTrue(record.result.found)
						self.assertEqual(record.dataset_source, "BARN")
						self.assertEqual(record.start, start)
						self.assertEqual(record.goal, goal)
						self.assertEqual(record.result.path[0], start)
						self.assertEqual(record.result.path[-1], goal)
						for cell in record.result.path:
							self.assertFalse(grid.is_occupied(*cell))
						for a, b in zip(record.result.path, record.result.path[1:]):
							self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)
				with tempfile.TemporaryDirectory() as directory:
					append_experiments(records, Path(directory) / "history.csv")
					export_experiments(records, Path(directory) / "results.json", "json")


if __name__ == "__main__":
	unittest.main()
