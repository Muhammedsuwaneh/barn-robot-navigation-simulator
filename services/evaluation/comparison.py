from collections.abc import Callable

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate
from services.ai.search import ALGORITHMS, run_search
from services.ai.search_utils import SearchInputError, validate_depth_limit, validate_search_input
from services.evaluation.records import ExperimentRecord


def compare_algorithms(
	grid: OccupancyGrid,
	start: CellCoordinate,
	goal: CellCoordinate,
	algorithms: tuple[str, ...],
	max_depth: int,
	map_identifier: str,
	dataset_source: str = "local_image",
	*,
	should_cancel: Callable[[], bool] | None = None,
) -> tuple[ExperimentRecord, ...]:
	"""Run each selected algorithm against the exact same immutable inputs."""
	if not algorithms:
		raise SearchInputError("Select at least one algorithm to compare.")
	if len(set(algorithms)) != len(algorithms):
		raise SearchInputError("An algorithm can appear only once in a comparison.")
	unknown = set(algorithms) - set(ALGORITHMS)
	if unknown:
		raise SearchInputError(f"Unknown algorithms: {', '.join(sorted(unknown))}.")
	validate_search_input(grid, start, goal)
	if any(algorithm in ("DLS", "IDS") for algorithm in algorithms):
		validate_depth_limit(max_depth)

	records: list[ExperimentRecord] = []
	for algorithm in algorithms:
		parameters: dict[str, int] = {}
		if algorithm in ("DLS", "IDS"):
			parameters["max_depth"] = max_depth
		result = run_search(
			algorithm,
			grid,
			start,
			goal,
			max_depth=max_depth if algorithm in ("DLS", "IDS") else None,
			should_cancel=should_cancel,
		)
		records.append(
			ExperimentRecord.create(
				grid=grid,
				start=start,
				goal=goal,
				algorithm=algorithm,
				parameters=parameters,
				result=result,
				map_identifier=map_identifier,
				dataset_source=dataset_source,
			)
		)
	return tuple(records)
