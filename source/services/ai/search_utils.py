from collections.abc import Callable, Iterator
from contextvars import ContextVar

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate


class SearchInputError(ValueError):
	"""Raised when a search grid, endpoint, or algorithm option is invalid."""


class SearchCancelled(RuntimeError):
	"""A worker was interrupted; no experimental result should be recorded."""


cancellation_check: ContextVar[Callable[[], bool] | None] = ContextVar("search_cancellation", default=None)


def check_cancellation() -> None:
	check = cancellation_check.get()
	if check is not None and check():
		raise SearchCancelled("Search cancelled.")


NEIGHBOR_STEPS: tuple[tuple[str, int, int], ...] = (
	("up", -1, 0),
	("down", 1, 0),
	("left", 0, -1),
	("right", 0, 1),
)


def validate_search_input(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
) -> None:
	if not isinstance(grid, OccupancyGrid):
		raise SearchInputError("Search requires an OccupancyGrid instance.")
	_validate_endpoint(grid, start, "Start")
	_validate_endpoint(grid, goal, "Goal")
	if grid.is_occupied(*start):
		raise SearchInputError("Start cell is occupied.")
	if grid.is_occupied(*goal):
		raise SearchInputError("Goal cell is occupied.")


def validate_depth_limit(max_depth: int) -> None:
	if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
		raise SearchInputError("Depth limit must be a non-negative integer.")


def neighbors(
	grid: OccupancyGrid,
	cell: CellCoordinate,
) -> Iterator[tuple[str, CellCoordinate]]:
	for direction, row_offset, column_offset in NEIGHBOR_STEPS:
		row = cell[0] + row_offset
		column = cell[1] + column_offset
		if 0 <= row < grid.rows and 0 <= column < grid.columns:
			neighbor = (row, column)
			if not grid.is_occupied(row, column):
				yield direction, neighbor


def reconstruct_path(
	predecessor: dict[CellCoordinate, CellCoordinate],
	start: CellCoordinate,
	goal: CellCoordinate,
) -> tuple[CellCoordinate, ...]:
	path = [goal]
	while path[-1] != start:
		path.append(predecessor[path[-1]])
	path.reverse()
	return tuple(path)


def _validate_endpoint(grid: OccupancyGrid, endpoint: object, label: str) -> None:
	if (
		not isinstance(endpoint, tuple)
		or len(endpoint) != 2
		or any(isinstance(value, bool) or not isinstance(value, int) for value in endpoint)
	):
		raise SearchInputError(f"{label} must be a (row, column) integer tuple.")
	row, column = endpoint
	if not 0 <= row < grid.rows or not 0 <= column < grid.columns:
		raise SearchInputError(f"{label} is outside the occupancy grid.")
