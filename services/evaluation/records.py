from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate, SearchResult


@dataclass(frozen=True)
class ExperimentRecord:
	record_id: str
	timestamp_utc: str
	map_identifier: str
	dataset_source: str
	grid_rows: int
	grid_columns: int
	start: CellCoordinate
	goal: CellCoordinate
	algorithm: str
	parameters: dict[str, Any]
	result: SearchResult

	@classmethod
	def create(
		cls,
		grid: OccupancyGrid,
		start: CellCoordinate,
		goal: CellCoordinate,
		algorithm: str,
		parameters: dict[str, Any],
		result: SearchResult,
		map_identifier: str,
		dataset_source: str = "local_image",
	) -> "ExperimentRecord":
		return cls(
			record_id=str(uuid4()),
			timestamp_utc=datetime.now(timezone.utc).isoformat(),
			map_identifier=map_identifier,
			dataset_source=dataset_source,
			grid_rows=grid.rows,
			grid_columns=grid.columns,
			start=start,
			goal=goal,
			algorithm=algorithm,
			parameters=deepcopy(parameters),
			result=result,
		)

	@property
	def success_rate(self) -> float:
		"""Fraction of successful trials (one trial per record)."""
		return float(self.result.found)

	def to_dict(self) -> dict[str, Any]:
		return {
			"record_id": self.record_id,
			"timestamp_utc": self.timestamp_utc,
			"map_identifier": self.map_identifier,
			"dataset_source": self.dataset_source,
			"grid_rows": self.grid_rows,
			"grid_columns": self.grid_columns,
			"start_row": self.start[0],
			"start_column": self.start[1],
			"goal_row": self.goal[0],
			"goal_column": self.goal[1],
			"algorithm": self.algorithm,
			"parameters": deepcopy(self.parameters),
			"success": self.result.found,
			"success_rate": self.success_rate,
			"path_length": self.result.path_length,
			"path_cost": self.result.path_cost,
			"execution_time_ms": self.result.elapsed_ms,
			"nodes_expanded": self.result.expanded_nodes,
			"peak_frontier_size": self.result.peak_frontier_size,
		}
