from collections import deque
from time import perf_counter_ns

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.search_utils import SearchInputError, check_cancellation, neighbors, reconstruct_path, validate_search_input


def breadth_first_search(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
) -> SearchResult:
	"""Find a shortest four-connected path through free occupancy-grid cells.

	Explored cells are dequeued cells in deterministic BFS order. Expanded nodes
	are dequeued non-goal cells whose neighbors are examined. Peak frontier size
	includes the initial start cell. Each move costs one; path length counts edges.
	"""
	validate_search_input(grid, start, goal)

	started_at = perf_counter_ns()
	frontier: deque[CellCoordinate] = deque([start])
	visited = {start}
	predecessor: dict[CellCoordinate, CellCoordinate] = {}
	explored: list[CellCoordinate] = []
	expanded_nodes = 0
	peak_frontier_size = 1
	found = False

	while frontier:
		check_cancellation()
		current = frontier.popleft()
		explored.append(current)
		if current == goal:
			found = True
			break

		expanded_nodes += 1
		for _, neighbor in neighbors(grid, current):
			if neighbor in visited:
				continue
			visited.add(neighbor)
			predecessor[neighbor] = current
			frontier.append(neighbor)
			peak_frontier_size = max(peak_frontier_size, len(frontier))

	path = reconstruct_path(predecessor, start, goal) if found else ()
	elapsed_ms = (perf_counter_ns() - started_at) / 1_000_000
	return SearchResult(
		algorithm="BFS",
		found=found,
		path=path,
		explored=tuple(explored),
		path_cost=len(path) - 1 if found else None,
		expanded_nodes=expanded_nodes,
		elapsed_ms=elapsed_ms,
		peak_frontier_size=peak_frontier_size,
		termination_reason="found" if found else "unreachable",
	)
