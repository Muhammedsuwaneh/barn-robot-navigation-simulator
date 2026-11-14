import unittest

import numpy as np

from models.occupancy_grid import OccupancyGrid
from services.ai.dfs import depth_first_search
from services.ai.dls import depth_limited_search
from services.ai.ids import iterative_deepening_search
from services.ai.search_utils import SearchInputError
from services.ai.ucs import uniform_cost_search


def make_grid(cells: list[list[bool]]) -> OccupancyGrid:
	array = np.asarray(cells, dtype=np.bool_)
	return OccupancyGrid(
		cells=array,
		cell_size_px=1,
		obstacle_threshold_percent=50,
		source_width_px=array.shape[1],
		source_height_px=array.shape[0],
	)


class AdditionalSearchAlgorithmTests(unittest.TestCase):
	def test_depth_searches_match_bfs_reachability_under_the_depth_bound(self) -> None:
		from services.ai.bfs import breadth_first_search
		random = np.random.default_rng(539)
		for sample in range(35):
			cells = random.random((4, 5)) < 0.3
			cells[0, 0] = cells[3, 4] = False
			grid = make_grid(cells.tolist())
			baseline = breadth_first_search(grid, (0, 0), (3, 4))
			for bound in (3, 7, 12):
				expected = baseline.found and baseline.path_length <= bound
				for search in (depth_limited_search, iterative_deepening_search):
					with self.subTest(sample=sample, bound=bound, algorithm=search.__name__):
						result = search(grid, (0, 0), (3, 4), bound)
						self.assertEqual(result.found, expected)
						if result.found:
							self.assert_valid_result(grid, result, (0, 0), (3, 4))
							self.assertLessEqual(result.path_length, bound)

	def test_dls_bounds_revisiting_on_a_large_cyclic_map(self) -> None:
		cells = np.zeros((20, 20), dtype=np.bool_)
		cells[18, 19] = cells[19, 18] = True
		grid = make_grid(cells.tolist())
		result = depth_limited_search(grid, (0, 0), (19, 19), 30)
		self.assertFalse(result.found)
		self.assertLessEqual(result.expanded_nodes, grid.free_count * 31)

	def assert_valid_result(
		self,
		grid: OccupancyGrid,
		result,
		start: tuple[int, int],
		goal: tuple[int, int],
	) -> None:
		self.assertTrue(result.found)
		self.assertEqual(result.path[0], start)
		self.assertEqual(result.path[-1], goal)
		for cell in result.path:
			self.assertFalse(grid.is_occupied(*cell))
		for current, following in zip(result.path, result.path[1:]):
			self.assertEqual(abs(current[0] - following[0]) + abs(current[1] - following[1]), 1)
		self.assertEqual(result.path_length, len(result.path) - 1)
		self.assertGreaterEqual(result.elapsed_ms, 0)
		self.assertGreaterEqual(result.peak_frontier_size, 1)

	def test_dfs_finds_valid_routes_and_handles_unreachable_maps(self) -> None:
		grid = make_grid(
			[
				[False, False, False, False],
				[False, True, True, False],
				[False, False, False, False],
			]
		)
		result = depth_first_search(grid, (0, 0), (0, 3))
		self.assert_valid_result(grid, result, (0, 0), (0, 3))
		self.assertEqual(result.algorithm, "DFS")

		blocked = make_grid([[False, True, False]])
		unreachable = depth_first_search(blocked, (0, 0), (0, 2))
		self.assertFalse(unreachable.found)
		self.assertEqual(unreachable.termination_reason, "unreachable")

	def test_dls_distinguishes_depth_cutoff_from_exhaustion(self) -> None:
		grid = make_grid([[False, False, False, False, False]])
		cutoff = depth_limited_search(grid, (0, 0), (0, 4), max_depth=2)
		self.assertFalse(cutoff.found)
		self.assertEqual(cutoff.termination_reason, "depth_limit")

		found = depth_limited_search(grid, (0, 0), (0, 4), max_depth=4)
		self.assert_valid_result(grid, found, (0, 0), (0, 4))
		self.assertEqual(found.algorithm, "DLS")

		blocked = make_grid([[False, True, False]])
		unreachable = depth_limited_search(blocked, (0, 0), (0, 2), max_depth=4)
		self.assertEqual(unreachable.termination_reason, "unreachable")

		with self.assertRaises(SearchInputError):
			depth_limited_search(grid, (0, 0), (0, 4), max_depth=-1)

	def test_ids_finds_route_deeper_than_early_iterations(self) -> None:
		grid = make_grid([[False, False, False, False, False]])
		result = iterative_deepening_search(grid, (0, 0), (0, 4), max_depth=4)
		self.assert_valid_result(grid, result, (0, 0), (0, 4))
		self.assertEqual(result.algorithm, "IDS")
		self.assertEqual(result.path_length, 4)
		self.assertGreater(result.expanded_nodes, 4)

		limited = iterative_deepening_search(grid, (0, 0), (0, 4), max_depth=2)
		self.assertFalse(limited.found)
		self.assertEqual(limited.termination_reason, "depth_limit")

	def test_ucs_uniform_cost_matches_bfs_solution_cost(self) -> None:
		from services.ai.bfs import breadth_first_search

		grid = make_grid(
			[
				[False, False, False, False],
				[False, True, True, False],
				[False, False, False, False],
			]
		)
		start, goal = (0, 0), (0, 3)
		bfs_result = breadth_first_search(grid, start, goal)
		ucs_result = uniform_cost_search(grid, start, goal)
		self.assertEqual(ucs_result.path_cost, bfs_result.path_cost)
		self.assert_valid_result(grid, ucs_result, start, goal)

	def test_ucs_uses_non_uniform_direction_costs(self) -> None:
		grid = make_grid(
			[
				[False, False, False],
				[False, False, False],
			]
		)
		result = uniform_cost_search(
			grid,
			(0, 0),
			(0, 2),
			move_costs={(0, 1): 10},
		)
		self.assert_valid_result(grid, result, (0, 0), (0, 2))
		self.assertEqual(result.path_cost, 4)
		self.assertGreater(result.path_length, 2)

		with self.assertRaises(SearchInputError):
			uniform_cost_search(grid, (0, 0), (0, 2), move_costs={(0, 1): 0})

	def test_all_algorithms_handle_start_equal_to_goal(self) -> None:
		grid = make_grid([[False]])
		results = (
			depth_first_search(grid, (0, 0), (0, 0)),
			depth_limited_search(grid, (0, 0), (0, 0), 0),
			iterative_deepening_search(grid, (0, 0), (0, 0)),
			uniform_cost_search(grid, (0, 0), (0, 0)),
		)
		for result in results:
			with self.subTest(algorithm=result.algorithm):
				self.assertTrue(result.found)
				self.assertEqual(result.path, ((0, 0),))
				self.assertEqual(result.path_length, 0)
				self.assertEqual(result.path_cost, 0)


if __name__ == "__main__":
	unittest.main()
