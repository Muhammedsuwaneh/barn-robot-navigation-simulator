from time import perf_counter_ns

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.dls import depth_limited_search
from services.ai.search_utils import check_cancellation, validate_depth_limit, validate_search_input


def iterative_deepening_search(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	max_depth: int | None = None,
) -> SearchResult:
	"""Run DLS from depth zero through the maximum; metrics aggregate all iterations."""
	validate_search_input(grid, start, goal)
	if max_depth is None:
		max_depth = grid.rows * grid.columns - 1
	validate_depth_limit(max_depth)

	started_at = perf_counter_ns()
	all_explored: list[CellCoordinate] = []
	explored_set: set[CellCoordinate] = set()
	expanded_nodes = 0
	peak_frontier_size = 1
	last_result: SearchResult | None = None

	for depth_limit in range(max_depth + 1):
		check_cancellation()
		result = depth_limited_search(grid, start, goal, depth_limit)
		last_result = result
		expanded_nodes += result.expanded_nodes
		peak_frontier_size = max(peak_frontier_size, result.peak_frontier_size)
		for cell in result.explored:
			if cell not in explored_set:
				explored_set.add(cell)
				all_explored.append(cell)
		if result.found or result.termination_reason == "unreachable":
			break

	assert last_result is not None
	return SearchResult(
		algorithm="IDS",
		found=last_result.found,
		path=last_result.path,
		explored=tuple(all_explored),
		path_cost=last_result.path_cost,
		expanded_nodes=expanded_nodes,
		elapsed_ms=(perf_counter_ns() - started_at) / 1_000_000,
		peak_frontier_size=peak_frontier_size,
		termination_reason=last_result.termination_reason,
	)
