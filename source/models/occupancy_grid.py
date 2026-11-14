from dataclasses import dataclass

import numpy as np


MAX_GRID_CELLS = 1_000_000
MAX_CELL_SIZE_PX = 512


class OccupancyGridError(ValueError):
	"""Raised when an occupancy grid or its source image is invalid."""


@dataclass(frozen=True)
class OccupancyGrid:
	"""2D Boolean grid: True is occupied; False is free; origin is top-left."""

	cells: np.ndarray
	cell_size_px: int
	obstacle_threshold_percent: int
	source_width_px: int
	source_height_px: int

	def __post_init__(self) -> None:
		if not isinstance(self.cells, np.ndarray) or self.cells.ndim != 2 or self.cells.size == 0:
			raise OccupancyGridError("Grid cells must be a non-empty 2D array.")
		if self.cells.dtype != np.bool_:
			raise OccupancyGridError("Grid cells must use Boolean values (True=occupied, False=free).")
		for name in ("cell_size_px", "obstacle_threshold_percent", "source_width_px", "source_height_px"):
			value = getattr(self, name)
			if isinstance(value, bool) or not isinstance(value, int):
				raise OccupancyGridError(f"{name} must be an integer.")
		if not 1 <= self.cell_size_px <= MAX_CELL_SIZE_PX:
			raise OccupancyGridError(f"Cell size must be between 1 and {MAX_CELL_SIZE_PX} pixels.")
		if not 1 <= self.obstacle_threshold_percent <= 100:
			raise OccupancyGridError("Obstacle threshold must be between 1 and 100 percent.")
		if self.source_width_px < 1 or self.source_height_px < 1:
			raise OccupancyGridError("Source image dimensions must be positive.")
		expected_rows = (self.source_height_px + self.cell_size_px - 1) // self.cell_size_px
		expected_columns = (self.source_width_px + self.cell_size_px - 1) // self.cell_size_px
		if self.cells.shape != (expected_rows, expected_columns):
			raise OccupancyGridError("Grid dimensions do not match the source image and cell size.")
		if self.cells.size > MAX_GRID_CELLS:
			raise OccupancyGridError(f"Grid exceeds the {MAX_GRID_CELLS:,}-cell safety limit.")

		# Back with immutable bytes so callers cannot re-enable writes with setflags.
		immutable_cells = np.frombuffer(self.cells.tobytes(order="C"), dtype=np.bool_).reshape(self.cells.shape)
		object.__setattr__(self, "cells", immutable_cells)

	@property
	def rows(self) -> int:
		return int(self.cells.shape[0])

	@property
	def columns(self) -> int:
		return int(self.cells.shape[1])

	@property
	def occupied_count(self) -> int:
		return int(np.count_nonzero(self.cells))

	@property
	def free_count(self) -> int:
		return int(self.cells.size - self.occupied_count)

	def is_occupied(self, row: int, column: int) -> bool:
		if not 0 <= row < self.rows or not 0 <= column < self.columns:
			raise IndexError("Grid coordinate is outside the grid bounds.")
		return bool(self.cells[row, column])

	def to_flat_list(self) -> list[bool]:
		"""Return row-major values suitable for QML models and simple serialization."""
		return self.cells.ravel().tolist()
