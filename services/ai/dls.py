from time import perf_counter_ns

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.search_utils import check_cancellation, neighbors, validate_depth_limit, validate_search_input


def depth_limited_search(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	max_depth: int,
) -> SearchResult:
	"""Run depth-first search bounded by edge depth, reporting cutoffs separately."""
	validate_search_input(grid, start, goal)
	validate_depth_limit(max_depth)

	started_at = perf_counter_ns()
	frontier = [(start, 0, (start,))]
	best_depth: dict[CellCoordinate, int] = {}
	explored: list[CellCoordinate] = []
	explored_set: set[CellCoordinate] = set()
	expanded_nodes = 0
	peak_frontier_size = 1
	cutoff = False
	found_path: tuple[CellCoordinate, ...] = ()

	while frontier:
		check_cancellation()
		current, depth, current_path = frontier.pop()
		# A shallower arrival leaves at least as much depth for every continuation.
		# Reopen a cell only when it improves its depth; path enumeration otherwise
		# grows exponentially on cyclic occupancy maps.
		if depth >= best_depth.get(current, depth + 1):
			continue
		best_depth[current] = depth
		if current not in explored_set:
			explored_set.add(current)
			explored.append(current)
		if current == goal:
			found_path = current_path
			break

		available = [
			neighbor for _, neighbor in neighbors(grid, current)
			if neighbor not in current_path and best_depth.get(neighbor, depth + 2) > depth + 1
		]
		if depth >= max_depth:
			if available:
				cutoff = True
			continue

		expanded_nodes += 1
		for neighbor in reversed(available):
			next_depth = depth + 1
			frontier.append((neighbor, next_depth, current_path + (neighbor,)))
		peak_frontier_size = max(peak_frontier_size, len(frontier))

	found = bool(found_path)
	return SearchResult(
		algorithm="DLS",
		found=found,
		path=found_path,
		explored=tuple(explored),
		path_cost=len(found_path) - 1 if found else None,
		expanded_nodes=expanded_nodes,
		elapsed_ms=(perf_counter_ns() - started_at) / 1_000_000,
		peak_frontier_size=peak_frontier_size,
		termination_reason="found" if found else "depth_limit" if cutoff else "unreachable",
	)
