from time import perf_counter_ns
from services.ai.search_utils import check_cancellation

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.search_utils import neighbors, reconstruct_path, validate_search_input


def depth_first_search(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
) -> SearchResult:
	"""Return a deterministic DFS route; DFS does not guarantee an optimal route."""
	validate_search_input(grid, start, goal)
	started_at = perf_counter_ns()
	frontier = [start]
	visited = {start}
	predecessor: dict[CellCoordinate, CellCoordinate] = {}
	explored: list[CellCoordinate] = []
	expanded_nodes = 0
	peak_frontier_size = 1
	found = False

	while frontier:
		check_cancellation()
		current = frontier.pop()
		explored.append(current)
		if current == goal:
			found = True
			break
		expanded_nodes += 1
		for _, neighbor in reversed(list(neighbors(grid, current))):
			if neighbor in visited:
				continue
			visited.add(neighbor)
			predecessor[neighbor] = current
			frontier.append(neighbor)
		peak_frontier_size = max(peak_frontier_size, len(frontier))

	path = reconstruct_path(predecessor, start, goal) if found else ()
	return SearchResult(
		algorithm="DFS",
		found=found,
		path=path,
		explored=tuple(explored),
		path_cost=len(path) - 1 if found else None,
		expanded_nodes=expanded_nodes,
		elapsed_ms=(perf_counter_ns() - started_at) / 1_000_000,
		peak_frontier_size=peak_frontier_size,
		termination_reason="found" if found else "unreachable",
	)
