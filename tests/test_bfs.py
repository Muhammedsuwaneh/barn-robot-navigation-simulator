import unittest

import numpy as np

from models.occupancy_grid import OccupancyGrid
from models.search_result import SearchResult
from services.ai.bfs import SearchInputError, breadth_first_search


def make_grid(cells: list[list[bool]]) -> OccupancyGrid:
	array = np.asarray(cells, dtype=np.bool_)
	return OccupancyGrid(
		cells=array,
		cell_size_px=1,
		obstacle_threshold_percent=50,
		source_width_px=array.shape[1],
		source_height_px=array.shape[0],
	)


class BreadthFirstSearchTests(unittest.TestCase):
	def test_large_rectangular_grid_matches_unit_cost_ucs(self) -> None:
		from services.ai.ucs import uniform_cost_search
		grid = OccupancyGrid(np.zeros((160, 240), dtype=np.bool_), 1, 50, 240, 160)
		for search in (breadth_first_search, uniform_cost_search):
			with self.subTest(algorithm=search.__name__):
				result = search(grid, (0, 0), (159, 239))
				self.assert_valid_path(grid, result, (0, 0), (159, 239))
				self.assertEqual(result.path_length, 398)

	def assert_valid_path(self, grid: OccupancyGrid, result: SearchResult, start: tuple[int, int], goal: tuple[int, int]) -> None:
		self.assertTrue(result.found)
		self.assertEqual(result.path[0], start)
		self.assertEqual(result.path[-1], goal)
		for cell in result.path:
			self.assertFalse(grid.is_occupied(*cell))
		for current, following in zip(result.path, result.path[1:]):
			self.assertEqual(abs(current[0] - following[0]) + abs(current[1] - following[1]), 1)
		self.assertEqual(result.path_length, len(result.path) - 1)
		self.assertEqual(result.path_cost, result.path_length)

	def test_direct_route_and_metrics(self) -> None:
		grid = make_grid([[False, False, False, False]])
		result = breadth_first_search(grid, (0, 0), (0, 3))

		self.assert_valid_path(grid, result, (0, 0), (0, 3))
		self.assertEqual(result.path, ((0, 0), (0, 1), (0, 2), (0, 3)))
		self.assertEqual(result.expanded_nodes, 3)
		self.assertEqual(result.peak_frontier_size, 1)
		self.assertGreaterEqual(result.elapsed_ms, 0)
		self.assertEqual(result.termination_reason, "found")

	def test_finds_shortest_detour_around_obstacles(self) -> None:
		grid = make_grid(
			[
				[False, False, False, False, False],
				[False, True, True, True, False],
				[False, False, False, False, False],
			]
		)
		result = breadth_first_search(grid, (1, 0), (1, 4))

		self.assert_valid_path(grid, result, (1, 0), (1, 4))
		self.assertEqual(result.path_length, 6)
		self.assertEqual(result.path[1], (0, 0))

	def test_neighbor_order_is_deterministic(self) -> None:
		grid = make_grid([[False, False], [False, False], [False, False]])
		result = breadth_first_search(grid, (1, 0), (0, 1))
		self.assertEqual(result.path, ((1, 0), (0, 0), (0, 1)))

	def test_unreachable_goal_returns_failure_without_path_cost(self) -> None:
		grid = make_grid(
			[
				[False, True, False],
				[False, True, False],
				[False, True, False],
			]
		)
		result = breadth_first_search(grid, (1, 0), (1, 2))

		self.assertFalse(result.found)
		self.assertEqual(result.path, ())
		self.assertIsNone(result.path_cost)
		self.assertIsNone(result.path_length)
		self.assertEqual(result.termination_reason, "unreachable")
		self.assertEqual(set(result.explored), {(0, 0), (1, 0), (2, 0)})

	def test_start_equal_to_goal_has_zero_cost(self) -> None:
		grid = make_grid([[False]])
		result = breadth_first_search(grid, (0, 0), (0, 0))
		self.assert_valid_path(grid, result, (0, 0), (0, 0))
		self.assertEqual(result.path, ((0, 0),))
		self.assertEqual(result.expanded_nodes, 0)
		self.assertEqual(result.peak_frontier_size, 1)

	def test_invalid_or_occupied_endpoints_are_rejected(self) -> None:
		grid = make_grid([[False, True], [False, False]])
		with self.assertRaises(SearchInputError):
			breadth_first_search(grid, (-1, 0), (1, 1))
		with self.assertRaises(SearchInputError):
			breadth_first_search(grid, (0, 0), (2, 0))
		with self.assertRaises(SearchInputError):
			breadth_first_search(grid, (0, 1), (1, 1))
		with self.assertRaises(SearchInputError):
			breadth_first_search(grid, (0, 0), [1, 1])

	def test_boundary_route_never_wraps_between_rows(self) -> None:
		grid = make_grid([[False, True], [False, False]])
		result = breadth_first_search(grid, (0, 0), (1, 1))
		self.assert_valid_path(grid, result, (0, 0), (1, 1))
		self.assertEqual(result.path, ((0, 0), (1, 0), (1, 1)))


if __name__ == "__main__":
	unittest.main()
