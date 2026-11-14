from collections.abc import Mapping

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate
from services.ai.search import run_search
from services.ai.search_utils import SearchInputError


class SearchWorker(QObject):
	completed = pyqtSignal(int, object)
	failed = pyqtSignal(int, str)

	def __init__(
		self,
		generation: int,
		grid: OccupancyGrid,
		start: CellCoordinate,
		goal: CellCoordinate,
		algorithm: str = "BFS",
		max_depth: int | None = None,
		move_costs: Mapping[CellCoordinate, int] | None = None,
	) -> None:
		super().__init__()
		self._generation = generation
		self._grid = grid
		self._start = start
		self._goal = goal
		self._algorithm = algorithm
		self._max_depth = max_depth
		self._move_costs = move_costs

	@pyqtSlot()
	def run(self) -> None:
		try:
			result = run_search(
				self._algorithm,
				self._grid,
				self._start,
				self._goal,
				max_depth=self._max_depth,
				move_costs=self._move_costs,
				should_cancel=QThread.currentThread().isInterruptionRequested,
			)
		except (SearchInputError, ValueError) as error:
			self.failed.emit(self._generation, str(error))
		except Exception as error:
			self.failed.emit(self._generation, f"{self._algorithm} failed: {error}")
		else:
			self.completed.emit(self._generation, result)
