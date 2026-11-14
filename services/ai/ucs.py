import heapq
from collections.abc import Mapping
from itertools import count
from time import perf_counter_ns
from services.ai.search_utils import check_cancellation

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult
from services.ai.search_utils import NEIGHBOR_STEPS, SearchInputError, reconstruct_path, validate_search_input


def uniform_cost_search(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	move_costs: Mapping[CellCoordinate, int] | None = None,
) -> SearchResult:
	"""Find a minimum-cost path with positive destination-cell entry costs.

	Missing cell costs default to one. With all costs equal, UCS matches BFS in
	solution cost; ties follow Up, Down, Left, Right deterministically.
	"""
	validate_search_input(grid, start, goal)
	costs = _validate_cell_costs(grid, move_costs)
	started_at = perf_counter_ns()
	order = count()
	frontier: list[tuple[int, int, CellCoordinate]] = [(0, next(order), start)]
	best_cost = {start: 0}
	predecessor: dict[CellCoordinate, CellCoordinate] = {}
	settled: set[CellCoordinate] = set()
	explored: list[CellCoordinate] = []
	expanded_nodes = 0
	peak_frontier_size = 1
	found = False

	while frontier:
		check_cancellation()
		current_cost, _, current = heapq.heappop(frontier)
		if current in settled or current_cost != best_cost.get(current):
			continue
		settled.add(current)
		explored.append(current)
		if current == goal:
			found = True
			break

		expanded_nodes += 1
		for direction, row_offset, column_offset in NEIGHBOR_STEPS:
			neighbor = (current[0] + row_offset, current[1] + column_offset)
			if not 0 <= neighbor[0] < grid.rows or not 0 <= neighbor[1] < grid.columns:
				continue
			if grid.is_occupied(*neighbor) or neighbor in settled:
				continue
			new_cost = current_cost + costs.get(neighbor, 1)
			if new_cost >= best_cost.get(neighbor, new_cost + 1):
				continue
			best_cost[neighbor] = new_cost
			predecessor[neighbor] = current
			heapq.heappush(frontier, (new_cost, next(order), neighbor))
			peak_frontier_size = max(peak_frontier_size, len(frontier))

	path = reconstruct_path(predecessor, start, goal) if found else ()
	return SearchResult(
		algorithm="UCS",
		found=found,
		path=path,
		explored=tuple(explored),
		path_cost=best_cost[goal] if found else None,
		expanded_nodes=expanded_nodes,
		elapsed_ms=(perf_counter_ns() - started_at) / 1_000_000,
		peak_frontier_size=peak_frontier_size,
		termination_reason="found" if found else "unreachable",
	)


def _validate_cell_costs(
	grid: OccupancyGrid,
	move_costs: Mapping[CellCoordinate, int] | None,
) -> dict[CellCoordinate, int]:
	costs: dict[CellCoordinate, int] = {}
	if move_costs is None:
		return costs
	if not isinstance(move_costs, Mapping):
		raise SearchInputError("Movement costs must map (row, column) cells to positive integers.")
	for cell, cost in move_costs.items():
		if (
			not isinstance(cell, tuple)
			or len(cell) != 2
			or any(isinstance(value, bool) or not isinstance(value, int) for value in cell)
			or not 0 <= cell[0] < grid.rows
			or not 0 <= cell[1] < grid.columns
		):
			raise SearchInputError("Movement-cost cells must be valid (row, column) grid coordinates.")
		if isinstance(cost, bool) or not isinstance(cost, int) or cost <= 0:
			raise SearchInputError("Movement costs must be positive integers.")
		costs[cell] = cost
	return costs
