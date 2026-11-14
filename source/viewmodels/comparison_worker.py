from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from models.occupancy_grid import OccupancyGrid
from models.search_result import CellCoordinate
from services.evaluation.comparison import compare_algorithms
from services.evaluation.records import ExperimentRecord


class ComparisonWorker(QObject):
	completed = pyqtSignal(int, object)
	failed = pyqtSignal(int, str)

	def __init__(
		self,
		generation: int,
		grid: OccupancyGrid,
		start: CellCoordinate,
		goal: CellCoordinate,
		algorithms: tuple[str, ...],
		max_depth: int,
		map_identifier: str,
		dataset_source: str = "local_image",
	) -> None:
		super().__init__()
		self._generation = generation
		self._grid = grid
		self._start = start
		self._goal = goal
		self._algorithms = algorithms
		self._max_depth = max_depth
		self._map_identifier = map_identifier
		self._dataset_source = dataset_source

	@pyqtSlot()
	def run(self) -> None:
		try:
			records: tuple[ExperimentRecord, ...] = compare_algorithms(
				self._grid,
				self._start,
				self._goal,
				self._algorithms,
				self._max_depth,
				self._map_identifier,
				dataset_source=self._dataset_source,
				should_cancel=QThread.currentThread().isInterruptionRequested,
			)
		except Exception as error:
			self.failed.emit(self._generation, str(error))
		else:
			self.completed.emit(self._generation, records)
