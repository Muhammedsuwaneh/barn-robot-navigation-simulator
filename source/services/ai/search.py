from collections.abc import Callable, Mapping
from typing import Literal

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.bfs import breadth_first_search
from services.ai.dfs import depth_first_search
from services.ai.dls import depth_limited_search
from services.ai.ids import iterative_deepening_search
from services.ai.search_utils import SearchInputError, cancellation_check, check_cancellation
from services.ai.ucs import uniform_cost_search


AlgorithmName = Literal["BFS", "DFS", "DLS", "IDS", "UCS"]
ALGORITHMS: tuple[AlgorithmName, ...] = ("BFS", "DFS", "DLS", "IDS", "UCS")


def run_search(
	algorithm: str,
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	*,
	max_depth: int | None = None,
	move_costs: Mapping[CellCoordinate, int] | None = None,
	should_cancel: Callable[[], bool] | None = None,
) -> SearchResult:
	"""Dispatch a search using the common occupancy-grid/result contract."""
	token = cancellation_check.set(should_cancel)
	try:
		check_cancellation()
		return _run_search(algorithm, grid, start, goal, max_depth=max_depth, move_costs=move_costs)
	finally:
		cancellation_check.reset(token)


def _run_search(
	algorithm: str,
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	*,
	max_depth: int | None,
	move_costs: Mapping[CellCoordinate, int] | None,
) -> SearchResult:
	if algorithm == "BFS":
		return breadth_first_search(grid, start, goal)
	if algorithm == "DFS":
		return depth_first_search(grid, start, goal)
	if algorithm == "DLS":
		if max_depth is None:
			raise SearchInputError("DLS requires a configured depth limit.")
		return depth_limited_search(grid, start, goal, max_depth)
	if algorithm == "IDS":
		return iterative_deepening_search(grid, start, goal, max_depth)
	if algorithm == "UCS":
		return uniform_cost_search(grid, start, goal, move_costs)
	raise SearchInputError(f"Unknown search algorithm: {algorithm}.")
