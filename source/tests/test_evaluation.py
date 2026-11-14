import csv
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from models.occupancy_grid import OccupancyGrid
from services.evaluation.comparison import compare_algorithms
from services.evaluation.experiment_store import append_experiments, export_experiments
from services.ai.search import ALGORITHMS, run_search
from services.ai.search_utils import SearchCancelled, SearchInputError
from unittest.mock import patch
from viewmodels.navigation_view_model import NavigationViewModel


class EvaluationTests(unittest.TestCase):
	def setUp(self) -> None:
		cells = np.zeros((3, 5), dtype=np.bool_)
		cells[1, 1:4] = True
		self.grid = OccupancyGrid(cells, 1, 50, 5, 3)
		self.start = (1, 0)
		self.goal = (1, 4)

	def test_invalid_depth_is_rejected_before_any_comparison_work(self) -> None:
		with patch("services.evaluation.comparison.run_search") as search:
			with self.assertRaises(SearchInputError):
				compare_algorithms(self.grid, self.start, self.goal, ("BFS", "DLS"), -1, "fixture")
			search.assert_not_called()

	def test_bad_metadata_does_not_create_partial_exports_or_append_partial_history(self) -> None:
		from dataclasses import replace
		records = compare_algorithms(self.grid, self.start, self.goal, ("BFS",), 8, "fixture")
		bad = replace(records[0], parameters={"invalid": object()})
		with tempfile.TemporaryDirectory() as directory:
			log = Path(directory) / "history.csv"
			append_experiments(records, log)
			before = log.read_bytes()
			with self.assertRaises(TypeError):
				append_experiments(records + (bad,), log)
			self.assertEqual(log.read_bytes(), before)
			for format in ("csv", "json"):
				path = Path(directory) / f"bad.{format}"
				with self.assertRaises(TypeError):
					export_experiments((bad,), path, format)
				self.assertFalse(path.exists())

	def test_serialized_parameters_cannot_mutate_the_record(self) -> None:
		record = compare_algorithms(self.grid, self.start, self.goal, ("DLS",), 8, "fixture")[0]
		row = record.to_dict()
		row["parameters"]["max_depth"] = 0
		self.assertEqual(record.parameters["max_depth"], 8)

	def test_comparison_runs_identical_inputs_and_records_parameters(self) -> None:
		records = compare_algorithms(
			self.grid,
			self.start,
			self.goal,
			("BFS", "DFS", "DLS", "IDS", "UCS"),
			max_depth=12,
			map_identifier="fixture-map",
		)
		self.assertEqual({record.algorithm for record in records}, {"BFS", "DFS", "DLS", "IDS", "UCS"})
		for record in records:
			self.assertEqual((record.grid_rows, record.grid_columns), (3, 5))
			self.assertEqual(record.start, self.start)
			self.assertEqual(record.goal, self.goal)
			self.assertEqual(record.map_identifier, "fixture-map")
			self.assertTrue(record.result.found)
			self.assertEqual(record.result.path_length, 6)
			self.assertGreaterEqual(record.result.elapsed_ms, 0)
			self.assertEqual(record.success_rate, 1.0)
		self.assertEqual(record.result.path_cost, record.result.path_length)
		self.assertEqual(next(record for record in records if record.algorithm == "DLS").parameters, {"max_depth": 12})
		self.assertEqual(next(record for record in records if record.algorithm == "IDS").parameters, {"max_depth": 12})

	def test_csv_log_appends_and_exports_do_not_overwrite(self) -> None:
		records = compare_algorithms(self.grid, self.start, self.goal, ("BFS", "UCS"), 8, "fixture-map")
		with tempfile.TemporaryDirectory() as directory:
			log_path = Path(directory) / "history.csv"
			append_experiments(records, log_path)
			fresh_records = compare_algorithms(self.grid, self.start, self.goal, ("BFS", "UCS"), 8, "fixture-map")
			append_experiments(fresh_records, log_path)
			with log_path.open("r", newline="", encoding="utf-8") as source:
				rows = list(csv.DictReader(source))
			self.assertEqual(len(rows), 4)
			self.assertEqual(rows[0]["map_identifier"], "fixture-map")
			self.assertEqual(rows[0]["success"], "True")
			self.assertEqual(rows[0]["success_rate"], "1.0")
			self.assertNotEqual(rows[0]["record_id"], rows[2]["record_id"])

			csv_export = Path(directory) / "comparison.csv"
			json_export = Path(directory) / "comparison.json"
			export_experiments(records, csv_export, "csv")
			export_experiments(records, json_export, "json")
			with csv_export.open("r", newline="", encoding="utf-8") as source:
				self.assertEqual(len(list(csv.DictReader(source))), 2)
			self.assertEqual(len(json.loads(json_export.read_text(encoding="utf-8"))), 2)
			with self.assertRaises(FileExistsError):
				export_experiments(records, json_export, "json")
			with self.assertRaises(FileExistsError):
				export_experiments(records, csv_export, "csv")
			self.assertEqual(len(json.loads(json_export.read_text(encoding="utf-8"))), 2)

	def test_failure_and_cutoff_export_null_path_metrics(self) -> None:
		blocked = OccupancyGrid(np.array([[False, True, False]]), 1, 50, 3, 1)
		records = compare_algorithms(blocked, (0, 0), (0, 2), ALGORITHMS, 4, "blocked", "test_fixture")
		cutoff = compare_algorithms(self.grid, self.start, self.goal, ("DLS", "IDS"), 1, "limited")
		for record in records + cutoff:
			row = record.to_dict()
			self.assertFalse(row["success"])
			self.assertEqual(row["success_rate"], 0.0)
			self.assertIsNone(row["path_length"])
			self.assertIsNone(row["path_cost"])
		for record in records:
			self.assertEqual(record.dataset_source, "test_fixture")
			self.assertEqual(record.result.termination_reason, "unreachable")
		with tempfile.TemporaryDirectory() as directory:
			json_path = Path(directory) / "failed.json"
			export_experiments(records, json_path, "json")
			self.assertIsNone(json.loads(json_path.read_text())[0]["path_cost"])
			csv_path = append_experiments(records, Path(directory) / "failed.csv")
			with csv_path.open(newline="", encoding="utf-8") as source:
				self.assertEqual(next(csv.DictReader(source))["path_length"], "")

	def test_comparison_rejects_empty_duplicate_unknown_algorithms(self) -> None:
		for algorithms in ((), ("BFS", "BFS"), ("unknown",)):
			with self.subTest(algorithms=algorithms), self.assertRaises(SearchInputError):
				compare_algorithms(self.grid, self.start, self.goal, algorithms, 8, "fixture")

	def test_incompatible_log_remains_unchanged(self) -> None:
		records = compare_algorithms(self.grid, self.start, self.goal, ("BFS",), 8, "fixture")
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "old.csv"
			path.write_text("old,header\n1,2\n", encoding="utf-8")
			before = path.read_bytes()
			with self.assertRaises(ValueError):
				append_experiments(records, path)
			self.assertEqual(path.read_bytes(), before)

	def test_all_searches_support_cooperative_cancellation_and_reset_context(self) -> None:
		for algorithm in ALGORITHMS:
			calls = 0
			def cancel_after_start() -> bool:
				nonlocal calls
				calls += 1
				return calls > 1
			with self.subTest(algorithm=algorithm), self.assertRaises(SearchCancelled):
				run_search(algorithm, self.grid, self.start, self.goal, max_depth=8, should_cancel=cancel_after_start)
		self.assertTrue(run_search("BFS", self.grid, self.start, self.goal).found)

	def test_ids_stops_after_proven_exhaustion(self) -> None:
		blocked = OccupancyGrid(np.array([[False, True, False]]), 1, 50, 3, 1)
		from services.ai.dls import depth_limited_search
		with patch("services.ai.ids.depth_limited_search", wraps=depth_limited_search) as dls:
			result = run_search("IDS", blocked, (0, 0), (0, 2), max_depth=512)
		self.assertEqual(dls.call_count, 1)
		self.assertEqual(result.termination_reason, "unreachable")

	def test_view_model_rejects_stale_results_and_keeps_results_on_logging_failure(self) -> None:
		view_model = NavigationViewModel()
		self.addCleanup(view_model.cleanup)
		records = compare_algorithms(self.grid, self.start, self.goal, ("BFS",), 8, "fixture")
		with patch("viewmodels.navigation_view_model.append_experiments", side_effect=OSError("read only")) as log:
			view_model._receive_comparison(view_model._comparison_generation, records)
			self.assertTrue(view_model.hasComparisonResults)
			self.assertIn("could not be logged", view_model.errorMessage)
			generation = view_model._comparison_generation
			view_model._clear_search_state()
			view_model._receive_comparison(generation, records)
			self.assertFalse(view_model.hasComparisonResults)
			self.assertEqual(log.call_count, 1)

	def test_failed_path_inspection_clears_a_previous_successful_path(self) -> None:
		view_model = NavigationViewModel()
		self.addCleanup(view_model.cleanup)
		records = compare_algorithms(self.grid, self.start, self.goal, ("BFS", "DLS"), 1, "fixture")
		with patch("viewmodels.navigation_view_model.append_experiments"):
			view_model._receive_comparison(view_model._comparison_generation, records)
		view_model.inspectComparisonPath(records[0].record_id)
		self.assertTrue(view_model.pathCells)
		view_model.depthLimit = 12
		view_model.inspectComparisonPath(records[1].record_id)
		self.assertFalse(view_model.pathCells)
		self.assertFalse(view_model.searchSucceeded)
		self.assertIn("within 1", view_model.searchSummary)


if __name__ == "__main__":
	unittest.main()
