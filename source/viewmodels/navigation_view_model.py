import math
import tempfile
from dataclasses import replace
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtCore import QUrl

from models.occupancy_grid import OccupancyGrid, OccupancyGridError
from models.search_result import SearchResult
from services.datasets.barn import (
	DEFAULT_BARN_DIRECTORY, BarnImportError, BarnMap, describe_map, discover_maps, import_barn_map,
)
from services.ai.search import ALGORITHMS, AlgorithmName
from services.evaluation.experiment_store import append_experiments, export_experiments
from services.evaluation.records import ExperimentRecord
from services.image_processing.occupancy_grid import binary_image_to_grid
from services.image_processing.preprocessing import (
	ImageProcessingError,
	ProcessingOptions,
	load_image,
	preprocess_image,
)
from viewmodels.search_worker import SearchWorker
from viewmodels.comparison_worker import ComparisonWorker


class NavigationViewModel(QObject):
	activeSectionChanged = pyqtSignal()
	imageChanged = pyqtSignal()
	processingChanged = pyqtSignal()
	gridChanged = pyqtSignal()
	selectionChanged = pyqtSignal()
	searchChanged = pyqtSignal()
	comparisonChanged = pyqtSignal()
	datasetChanged = pyqtSignal()
	statusChanged = pyqtSignal()
	errorChanged = pyqtSignal()

	def __init__(self) -> None:
		super().__init__()
		self._active_section = "workspace"
		self._closed = False
		self._options = ProcessingOptions()
		self._image: np.ndarray | None = None
		self._processed_image: np.ndarray | None = None
		self._image_path: Path | None = None
		self._barn_map: BarnMap | None = None
		self._barn_directory = DEFAULT_BARN_DIRECTORY
		try:
			self._barn_maps = discover_maps(self._barn_directory) if self._barn_directory.is_dir() else ()
		except BarnImportError:
			self._barn_maps = ()
		self._occupancy_grid: OccupancyGrid | None = None
		self._selection_mode = "none"
		self._start_cell: tuple[int, int] | None = None
		self._goal_cell: tuple[int, int] | None = None
		self._search_generation = 0
		self._search_thread: QThread | None = None
		self._search_worker: SearchWorker | None = None
		self._search_busy = False
		self._search_result: SearchResult | None = None
		self._visible_path: tuple[tuple[int, int], ...] = ()
		self._comparison_generation = 0
		self._comparison_thread: QThread | None = None
		self._comparison_worker: ComparisonWorker | None = None
		self._comparison_busy = False
		self._comparison_records: tuple[ExperimentRecord, ...] = ()
		self._selected_algorithm: AlgorithmName = "BFS"
		self._depth_limit = 24
		self._search_depth_limit = 24
		self._show_explored_cells = False
		self._grid_cell_size_px = 8
		self._obstacle_threshold_percent = 50
		self._preview_directory = tempfile.TemporaryDirectory(prefix="ai-navigation-")
		self._preview_revision = 0
		self._processed_preview_path = Path(self._preview_directory.name) / "processed-0.png"
		self._grid_preview_revision = 0
		self._grid_preview_path = Path(self._preview_directory.name) / "occupancy-grid-0.png"
		self._status_message = "Ready. Load a PNG, JPG, or JPEG environment image."
		self._error_message = ""

	@pyqtProperty(str, constant=True)
	def applicationName(self) -> str:
		return "AI Robot Navigation Simulator"

	@pyqtProperty(str, constant=True)
	def phaseLabel(self) -> str:
		return "IMAGE-BASED ROBOT NAVIGATION"

	@pyqtProperty(bool, notify=imageChanged)
	def isBarnMap(self) -> bool:
		return self._barn_map is not None

	@pyqtProperty(str, notify=imageChanged)
	def datasetSource(self) -> str:
		return "BARN" if self.isBarnMap else "local_image"

	@pyqtProperty(str, notify=imageChanged)
	def mapIdentifier(self) -> str:
		if self._barn_map is not None:
			return self._barn_map.identifier
		return self._image_path.stem if self._image_path else "unknown-map"

	@pyqtProperty(str, notify=datasetChanged)
	def barnDirectory(self) -> str:
		return str(self._barn_directory)

	@pyqtProperty("QVariantList", notify=datasetChanged)
	def barnMaps(self) -> list[dict[str, str]]:
		return [{"label": entry.label, "path": str(entry.path), "identifier": entry.identifier} for entry in self._barn_maps]

	@pyqtSlot(str)
	def scanBarnDirectory(self, source: str) -> None:
		url = QUrl(source)
		path = Path(url.toLocalFile() if url.isLocalFile() else source).expanduser()
		try:
			entries = discover_maps(path)
		except BarnImportError as error:
			self._set_error(str(error))
			return
		self._barn_directory = path.resolve()
		self._barn_maps = entries
		self.datasetChanged.emit()
		self._error_message = "" if entries else "No compatible grid_i.npy or cspace_i.npy maps found in this folder."
		self._status_message = f"Found {len(entries)} BARN occupancy maps. Select a map to import."
		self.errorChanged.emit()
		self.statusChanged.emit()

	@pyqtSlot(str)
	def importBarnMap(self, source: str) -> None:
		url = QUrl(source)
		path = Path(url.toLocalFile() if url.isLocalFile() else source).expanduser()
		try:
			entry = describe_map(path)
			grid = import_barn_map(path)
			self._write_grid_preview(grid)
		except (BarnImportError, OSError, cv2.error) as error:
			self._set_error(str(error))
			return
		self._barn_map = entry
		self._image = None
		self._processed_image = None
		self._image_path = None
		self._occupancy_grid = grid
		self._reset_selection_state(default_start=True)
		self._error_message = ""
		self._status_message = f"Imported {entry.identifier}: {grid.rows} x {grid.columns} cells. Select free endpoints; no image preprocessing is applied."
		self.imageChanged.emit()
		self.gridChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtProperty(str, notify=statusChanged)
	def statusMessage(self) -> str:
		return self._status_message

	@pyqtProperty(str, notify=errorChanged)
	def errorMessage(self) -> str:
		return self._error_message

	@pyqtProperty(bool, notify=imageChanged)
	def hasImage(self) -> bool:
		return self._image is not None

	@pyqtProperty(str, notify=imageChanged)
	def imageName(self) -> str:
		if self._barn_map is not None:
			return self._barn_map.identifier
		return self._image_path.name if self._image_path else "No image selected"

	@pyqtProperty(str, notify=imageChanged)
	def imageDimensions(self) -> str:
		if self.isBarnMap:
			return f"{self.gridColumns} x {self.gridRows} cells"
		if self._image is None:
			return "--"
		height, width = self._image.shape[:2]
		return f"{width} x {height} px"

	@pyqtProperty(int, notify=imageChanged)
	def sourceImageWidth(self) -> int:
		if self.isBarnMap:
			return self.gridColumns
		return int(self._image.shape[1]) if self._image is not None else 0

	@pyqtProperty(int, notify=imageChanged)
	def sourceImageHeight(self) -> int:
		if self.isBarnMap:
			return self.gridRows
		return int(self._image.shape[0]) if self._image is not None else 0

	@pyqtProperty(str, notify=imageChanged)
	def originalPreviewUrl(self) -> str:
		if self.isBarnMap:
			return self.occupancyGridPreviewUrl
		if self._image_path is None:
			return ""
		return QUrl.fromLocalFile(str(self._image_path)).toString()

	@pyqtProperty(str, notify=imageChanged)
	def processedPreviewUrl(self) -> str:
		if self._image is None:
			return ""
		return QUrl.fromLocalFile(str(self._processed_preview_path)).toString()

	@pyqtProperty(int, notify=processingChanged)
	def threshold(self) -> int:
		return self._options.threshold

	@threshold.setter
	def threshold(self, value: int) -> None:
		self._update_options(threshold=int(value))

	@pyqtProperty(bool, notify=processingChanged)
	def adaptiveThreshold(self) -> bool:
		return self._options.adaptive

	@adaptiveThreshold.setter
	def adaptiveThreshold(self, value: bool) -> None:
		self._update_options(adaptive=bool(value), otsu=False)

	@pyqtProperty(bool, notify=processingChanged)
	def otsuThreshold(self) -> bool:
		return self._options.otsu

	@otsuThreshold.setter
	def otsuThreshold(self, value: bool) -> None:
		self._update_options(otsu=bool(value), adaptive=False if value else self._options.adaptive)

	@pyqtProperty(int, notify=processingChanged)
	def adaptiveBlockSize(self) -> int:
		return self._options.block_size

	@adaptiveBlockSize.setter
	def adaptiveBlockSize(self, value: int) -> None:
		self._update_options(block_size=int(value))

	@pyqtProperty(int, notify=processingChanged)
	def adaptiveC(self) -> int:
		return self._options.adaptive_c

	@adaptiveC.setter
	def adaptiveC(self, value: int) -> None:
		self._update_options(adaptive_c=int(value))

	@pyqtProperty(str, notify=processingChanged)
	def morphologyMode(self) -> str:
		return self._options.morphology

	@morphologyMode.setter
	def morphologyMode(self, value: str) -> None:
		self._update_options(morphology=value)

	@pyqtProperty(int, notify=processingChanged)
	def morphologyKernelSize(self) -> int:
		return self._options.kernel_size

	@morphologyKernelSize.setter
	def morphologyKernelSize(self, value: int) -> None:
		self._update_options(kernel_size=int(value))

	@pyqtProperty(bool, notify=processingChanged)
	def lightPixelsAreObstacles(self) -> bool:
		return self._options.light_pixels_are_obstacles

	@lightPixelsAreObstacles.setter
	def lightPixelsAreObstacles(self, value: bool) -> None:
		self._update_options(light_pixels_are_obstacles=bool(value))

	@pyqtProperty(bool, notify=gridChanged)
	def gridReady(self) -> bool:
		return self._occupancy_grid is not None

	@pyqtProperty(int, notify=gridChanged)
	def gridCellSizePx(self) -> int:
		return 1 if self.isBarnMap else self._grid_cell_size_px

	@gridCellSizePx.setter
	def gridCellSizePx(self, value: int) -> None:
		self._update_grid_options(cell_size_px=int(value))

	@pyqtProperty(int, notify=gridChanged)
	def obstacleThresholdPercent(self) -> int:
		return self._obstacle_threshold_percent

	@obstacleThresholdPercent.setter
	def obstacleThresholdPercent(self, value: int) -> None:
		self._update_grid_options(obstacle_threshold_percent=int(value))

	@pyqtProperty(int, notify=gridChanged)
	def gridRows(self) -> int:
		return self._occupancy_grid.rows if self._occupancy_grid else 0

	@pyqtProperty(int, notify=gridChanged)
	def gridColumns(self) -> int:
		return self._occupancy_grid.columns if self._occupancy_grid else 0

	@pyqtProperty(int, notify=gridChanged)
	def gridOccupiedCount(self) -> int:
		return self._occupancy_grid.occupied_count if self._occupancy_grid else 0

	@pyqtProperty(int, notify=gridChanged)
	def gridFreeCount(self) -> int:
		return self._occupancy_grid.free_count if self._occupancy_grid else 0

	@pyqtProperty(str, notify=gridChanged)
	def gridDimensions(self) -> str:
		if self._occupancy_grid is None:
			return "--"
		return f"{self._occupancy_grid.rows} rows x {self._occupancy_grid.columns} columns"

	@pyqtProperty(str, notify=gridChanged)
	def occupancyGridPreviewUrl(self) -> str:
		if self._occupancy_grid is None:
			return ""
		return QUrl.fromLocalFile(str(self._grid_preview_path)).toString()

	@pyqtProperty(str, notify=selectionChanged)
	def selectionMode(self) -> str:
		return self._selection_mode

	@pyqtProperty(bool, notify=selectionChanged)
	def hasStart(self) -> bool:
		return self._start_cell is not None

	@pyqtProperty(bool, notify=selectionChanged)
	def hasGoal(self) -> bool:
		return self._goal_cell is not None

	@pyqtProperty(int, notify=selectionChanged)
	def startRow(self) -> int:
		return self._start_cell[0] if self._start_cell else -1

	@pyqtProperty(int, notify=selectionChanged)
	def startColumn(self) -> int:
		return self._start_cell[1] if self._start_cell else -1

	@pyqtProperty(int, notify=selectionChanged)
	def goalRow(self) -> int:
		return self._goal_cell[0] if self._goal_cell else -1

	@pyqtProperty(int, notify=selectionChanged)
	def goalColumn(self) -> int:
		return self._goal_cell[1] if self._goal_cell else -1

	@pyqtProperty(str, notify=selectionChanged)
	def startCoordinate(self) -> str:
		if self._start_cell is None:
			return "Not set"
		return f"row {self._start_cell[0]}, col {self._start_cell[1]}"

	@pyqtProperty(str, notify=selectionChanged)
	def goalCoordinate(self) -> str:
		if self._goal_cell is None:
			return "Not set"
		return f"row {self._goal_cell[0]}, col {self._goal_cell[1]}"

	@pyqtProperty(bool, notify=searchChanged)
	def canRunBfs(self) -> bool:
		return (
			self._occupancy_grid is not None
			and self._start_cell is not None
			and self._goal_cell is not None
			and not self.searchBusy
		)

	@pyqtProperty(bool, notify=searchChanged)
	def canRunSearch(self) -> bool:
		return self.canRunBfs and not self._comparison_busy

	@pyqtProperty(str, notify=searchChanged)
	def selectedAlgorithm(self) -> str:
		return self._selected_algorithm

	@selectedAlgorithm.setter
	def selectedAlgorithm(self, value: str) -> None:
		if value not in ALGORITHMS:
			self._set_error(f"Unknown search algorithm: {value}.")
			return
		if value == self._selected_algorithm:
			return
		self._selected_algorithm = value
		self._search_changed()

	@pyqtProperty("QVariantList", constant=True)
	def availableAlgorithms(self) -> list[str]:
		return list(ALGORITHMS)

	@pyqtProperty(int, notify=searchChanged)
	def depthLimit(self) -> int:
		return self._depth_limit

	@depthLimit.setter
	def depthLimit(self, value: int) -> None:
		depth = int(value)
		if not 0 <= depth <= 512:
			self._set_error("Depth limit must be between 0 and 512.")
			return
		if depth != self._depth_limit:
			self._depth_limit = depth
			self._search_changed()

	@pyqtProperty(bool, notify=searchChanged)
	def showExploredCells(self) -> bool:
		return self._show_explored_cells

	@showExploredCells.setter
	def showExploredCells(self, value: bool) -> None:
		self._show_explored_cells = bool(value)
		self._search_changed()

	@pyqtProperty(bool, notify=searchChanged)
	def searchBusy(self) -> bool:
		return self._search_busy or self._comparison_busy

	@pyqtProperty(bool, notify=comparisonChanged)
	def comparisonBusy(self) -> bool:
		return self._comparison_busy

	@pyqtProperty(bool, notify=comparisonChanged)
	def hasComparisonResults(self) -> bool:
		return bool(self._comparison_records)

	@pyqtProperty("QVariantList", notify=comparisonChanged)
	def comparisonRows(self) -> list[dict[str, object]]:
		return [record.to_dict() for record in self._comparison_records]

	@pyqtProperty(str, notify=comparisonChanged)
	def comparisonSummary(self) -> str:
		if self._comparison_busy:
			return "Comparing selected algorithms..."
		if not self._comparison_records:
			return "Choose algorithms and run a comparison."
		successes = sum(record.result.found for record in self._comparison_records)
		return f"{successes}/{len(self._comparison_records)} searches found a route. Four-directional movement; each move costs one."

	@pyqtSlot(str)
	def inspectComparisonPath(self, record_id: str) -> None:
		if self.searchBusy:
			return
		for record in self._comparison_records:
			if record.record_id == record_id:
				self._search_result = record.result
				self._visible_path = record.result.path
				self._search_depth_limit = record.parameters.get("max_depth", self._depth_limit)
				self._selected_algorithm = record.algorithm
				self._status_message = self.searchSummary
				self._search_changed()
				self.statusChanged.emit()
				return
		self._set_error("This comparison result is no longer available. Run a new comparison.")

	@pyqtProperty("QVariantList", notify=searchChanged)
	def exploredCells(self) -> list[list[int]]:
		if self._search_result is None:
			return []
		return [list(cell) for cell in self._search_result.explored]

	@pyqtProperty(bool, notify=searchChanged)
	def hasSearchResult(self) -> bool:
		return self._search_result is not None

	@pyqtProperty(bool, notify=searchChanged)
	def searchSucceeded(self) -> bool:
		return self._search_result.found if self._search_result else False

	@pyqtProperty(str, notify=searchChanged)
	def searchSummary(self) -> str:
		if self._search_busy and self._search_result is None:
			return f"{self._selected_algorithm} running..."
		if self._search_result is None:
			return f"No {self._selected_algorithm} result"
		if self._search_result.found:
			return f"{self._search_result.algorithm} route found · {self._search_result.path_length} moves"
		if self._search_result.termination_reason == "depth_limit":
			return f"{self._search_result.algorithm} depth limit reached · no route within {self._search_depth_limit}"
		return "No route between these cells"

	@pyqtProperty(int, notify=searchChanged)
	def pathLength(self) -> int:
		return self._search_result.path_length if self._search_result and self._search_result.found else -1

	@pyqtProperty(int, notify=searchChanged)
	def pathCost(self) -> int:
		return self._search_result.path_cost if self._search_result and self._search_result.path_cost is not None else -1

	@pyqtProperty(float, notify=searchChanged)
	def searchElapsedMs(self) -> float:
		return self._search_result.elapsed_ms if self._search_result else 0.0

	@pyqtProperty(int, notify=searchChanged)
	def nodesExpanded(self) -> int:
		return self._search_result.expanded_nodes if self._search_result else 0

	@pyqtProperty(int, notify=searchChanged)
	def peakFrontierSize(self) -> int:
		return self._search_result.peak_frontier_size if self._search_result else 0

	@pyqtProperty("QVariantList", notify=searchChanged)
	def pathCells(self) -> list[list[int]]:
		return [list(cell) for cell in self._visible_path]

	@pyqtProperty(str, notify=activeSectionChanged)
	def activeSection(self) -> str:
		return self._active_section

	@pyqtSlot(str)
	def selectSection(self, section: str) -> None:
		if section not in ("workspace", "barn") or self._active_section == section:
			return

		self._active_section = section
		self.activeSectionChanged.emit()

	@pyqtSlot(str)
	def loadImage(self, source: str) -> None:
		url = QUrl(source)
		image_path = Path(url.toLocalFile() if url.isLocalFile() else source).expanduser()
		try:
			image = load_image(image_path)
			processed = preprocess_image(image, self._options)
			self._write_processed_preview(processed)
		except (ImageProcessingError, OSError, cv2.error) as error:
			self._set_error(str(error))
			return

		self._image = image
		self._barn_map = None
		self._processed_image = processed
		self._image_path = image_path.resolve()
		self._occupancy_grid = None
		self._reset_selection_state()
		self._error_message = ""
		self._status_message = f"Loaded {self._image_path.name} · {self.imageDimensions}"
		self.imageChanged.emit()
		self.gridChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot()
	def generateOccupancyGrid(self) -> None:
		if self._processed_image is None:
			self._set_error("Load an image before generating an occupancy grid.")
			return
		try:
			grid = binary_image_to_grid(
				self._processed_image,
				cell_size_px=self._grid_cell_size_px,
				obstacle_threshold_percent=self._obstacle_threshold_percent,
			)
			self._write_grid_preview(grid)
		except (OccupancyGridError, OSError, cv2.error) as error:
			self._set_error(str(error))
			return

		self._occupancy_grid = grid
		self._reset_selection_state(default_start=True)
		self._error_message = ""
		if self._start_cell is None:
			self._status_message = "Grid generated, but it contains no free cell for the robot start."
		else:
			self._status_message = (
				f"Grid generated: {grid.rows} x {grid.columns} cells · "
				f"{grid.occupied_count} occupied · {grid.free_count} free. "
				f"Robot start: row {self._start_cell[0]}, column {self._start_cell[1]}."
			)
		self.gridChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot(str)
	def setSelectionMode(self, mode: str) -> None:
		if mode == "none":
			self._selection_mode = "none"
			self._error_message = ""
			self._status_message = "Grid selection mode cancelled."
			self.selectionChanged.emit()
			self.statusChanged.emit()
			self.errorChanged.emit()
			return
		if mode not in ("start", "goal"):
			self._set_error("Choose either Start or Goal selection mode.")
			return
		if self._occupancy_grid is None:
			self._set_error("Generate an occupancy grid before selecting endpoints.")
			return

		self._selection_mode = mode
		self._error_message = ""
		self._status_message = f"Click a free grid cell to set the {mode} position."
		self.selectionChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot(int, int)
	def selectGridCell(self, row: int, column: int) -> None:
		grid = self._occupancy_grid
		if grid is None:
			self._set_error("Generate an occupancy grid before selecting endpoints.")
			return
		if self._selection_mode not in ("start", "goal"):
			self._set_error("Choose Set Start or Set Goal before clicking a grid cell.")
			return
		if any(isinstance(value, bool) or not isinstance(value, int) for value in (row, column)):
			self._set_error("Grid row and column must be integers.")
			return
		if not 0 <= row < grid.rows or not 0 <= column < grid.columns:
			self._set_error("The selected coordinate is outside the occupancy grid.")
			return
		if grid.is_occupied(row, column):
			self._set_error("That cell is occupied. Choose a free cell.")
			return

		cell = (row, column)
		other_cell = self._goal_cell if self._selection_mode == "start" else self._start_cell
		if cell == other_cell:
			self._set_error("Start and goal must be different cells.")
			return

		selected_mode = self._selection_mode
		if selected_mode == "start":
			self._start_cell = cell
		else:
			self._goal_cell = cell
		self._selection_mode = "none"
		self._clear_search_state()
		self._error_message = ""
		self._status_message = f"{selected_mode.title()} set at row {row}, column {column}."
		self.selectionChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot(float, float)
	def selectGridPosition(self, x_fraction: float, y_fraction: float) -> None:
		grid = self._occupancy_grid
		if grid is None:
			self._set_error("Generate an occupancy grid before selecting endpoints.")
			return
		if (
			not math.isfinite(x_fraction)
			or not math.isfinite(y_fraction)
			or not 0 <= x_fraction <= 1
			or not 0 <= y_fraction <= 1
		):
			self._set_error("The selected point is outside the occupancy grid preview.")
			return

		column = min(int(x_fraction * grid.columns), grid.columns - 1)
		row = min(int(y_fraction * grid.rows), grid.rows - 1)
		self.selectGridCell(row, column)

	@pyqtSlot()
	def clearSelection(self) -> None:
		self._reset_selection_state()
		self._error_message = ""
		self._status_message = "Start and goal selections cleared."
		self.selectionChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot()
	def runSearch(self) -> None:
		if self.searchBusy or self._closed:
			return
		if self._occupancy_grid is None or self._start_cell is None or self._goal_cell is None:
			self._set_error("Generate a grid and set both start and goal before running a search.")
			return

		self._search_generation += 1
		generation = self._search_generation
		self._search_depth_limit = self._depth_limit
		self._search_result = None
		self._visible_path = ()
		self._search_busy = True
		self._search_changed()
		self._status_message = f"{self._selected_algorithm} is searching the occupancy grid..."
		self.statusChanged.emit()

		worker = SearchWorker(
			generation,
			self._occupancy_grid,
			self._start_cell,
			self._goal_cell,
			algorithm=self._selected_algorithm,
			max_depth=self._depth_limit if self._selected_algorithm in ("DLS", "IDS") else None,
		)
		self._search_worker = worker
		self._search_thread = self._launch_worker(
			worker, self._receive_search_result,
			self._receive_search_error, self._search_thread_finished,
		)

	@pyqtSlot()
	def runComparison(self) -> None:
		self.runSelectedComparison(list(ALGORITHMS))

	@pyqtSlot("QVariantList")
	def runSelectedComparison(self, algorithms: list[str]) -> None:
		if self.searchBusy or self._closed:
			return
		if self._occupancy_grid is None or self._start_cell is None or self._goal_cell is None:
			self._set_error("Generate a grid and set both start and goal before comparison.")
			return
		if not algorithms or any(algorithm not in ALGORITHMS for algorithm in algorithms) or len(set(algorithms)) != len(algorithms):
			self._set_error("Select at least one distinct, supported algorithm.")
			return

		self._comparison_generation += 1
		generation = self._comparison_generation
		self._comparison_records = ()
		self._comparison_busy = True
		self.comparisonChanged.emit()
		self._search_changed()
		self._status_message = "Comparing selected algorithms on the same grid and endpoints..."
		self.statusChanged.emit()

		worker = ComparisonWorker(
			generation,
			self._occupancy_grid,
			self._start_cell,
			self._goal_cell,
			tuple(algorithms),
			self._depth_limit,
			self.mapIdentifier,
			dataset_source=self.datasetSource,
		)
		self._comparison_worker = worker
		self._comparison_thread = self._launch_worker(
			worker, self._receive_comparison,
			self._receive_comparison_error, self._comparison_thread_finished,
		)

	@pyqtSlot(str, str)
	def exportComparison(self, destination: str, export_format: str) -> None:
		if not self._comparison_records:
			self._set_error("Run an algorithm comparison before exporting results.")
			return
		url = QUrl(destination)
		path = Path(url.toLocalFile() if url.isLocalFile() else destination).expanduser()
		try:
			export_experiments(self._comparison_records, path, export_format)
		except (OSError, ValueError) as error:
			self._set_error(f"Unable to export comparison: {error}")
			return
		self._error_message = ""
		self._status_message = f"Comparison exported to {path.name}."
		self.statusChanged.emit()
		self.errorChanged.emit()

	def _receive_comparison(self, generation: int, records: tuple[ExperimentRecord, ...]) -> None:
		if generation != self._comparison_generation:
			return
		self._comparison_records = records
		try:
			append_experiments(records)
		except (OSError, ValueError) as error:
			self._error_message = f"Comparison completed but could not be logged: {error}"
		else:
			self._error_message = ""
		self._status_message = f"Comparison complete · {len(records)} algorithms · same grid and endpoints."
		self.comparisonChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	def _receive_comparison_error(self, generation: int, message: str) -> None:
		if generation != self._comparison_generation:
			return
		self._error_message = message
		self._status_message = "Algorithm comparison could not complete."
		self.errorChanged.emit()
		self.statusChanged.emit()

	def _comparison_thread_finished(self) -> None:
		self._comparison_thread = None
		self._comparison_worker = None
		self._comparison_busy = False
		self.comparisonChanged.emit()
		self._search_changed()

	@pyqtSlot()
	def cancelComparison(self) -> None:
		if self._comparison_thread is not None:
			self._comparison_generation += 1
			self._comparison_thread.requestInterruption()
			self._status_message = "Comparison cancelled; no partial results were logged."
			self.statusChanged.emit()

	@pyqtSlot()
	def cancelSearch(self) -> None:
		if self._search_thread is not None:
			self._search_generation += 1
			self._search_thread.requestInterruption()
			self._status_message = "Search cancelled; no result was logged."
			self._error_message = ""
			self.statusChanged.emit()
			self.errorChanged.emit()

	@pyqtSlot()
	def runBfs(self) -> None:
		if self.searchBusy:
			return
		self._selected_algorithm = "BFS"
		self.runSearch()

	@pyqtSlot()
	def resetSearchVisualization(self) -> None:
		if self.searchBusy:
			return
		self._search_generation += 1
		self._search_result = None
		self._visible_path = ()
		self._status_message = "Search visualization reset."
		self._search_changed()
		self.statusChanged.emit()

	def _receive_search_result(self, generation: int, result: SearchResult) -> None:
		if generation != self._search_generation:
			return
		self._search_result = result
		self._visible_path = result.path
		try:
			record = ExperimentRecord.create(
				grid=self._occupancy_grid,
				start=self._start_cell,
				goal=self._goal_cell,
				algorithm=result.algorithm,
				parameters={"max_depth": self._search_depth_limit} if result.algorithm in ("DLS", "IDS") else {},
				result=result,
				map_identifier=self.mapIdentifier,
				dataset_source=self.datasetSource,
			)
			append_experiments((record,))
		except (OSError, ValueError) as error:
			self._error_message = f"Search completed but could not be logged: {error}"
		else:
			self._error_message = ""
		self._status_message = self.searchSummary
		self._search_changed()
		self.statusChanged.emit()
		self.errorChanged.emit()

	def _receive_search_error(self, generation: int, message: str) -> None:
		if generation != self._search_generation:
			return
		self._error_message = message
		self._status_message = "Search could not complete."
		self.errorChanged.emit()
		self.statusChanged.emit()

	def _search_thread_finished(self) -> None:
		self._search_thread = None
		self._search_worker = None
		self._search_busy = False
		self._search_changed()

	def _search_changed(self) -> None:
		self.searchChanged.emit()

	def _clear_search_state(self) -> None:
		self._search_generation += 1
		self._comparison_generation += 1
		for thread in (self._search_thread, self._comparison_thread):
			if thread is not None:
				thread.requestInterruption()
		self._comparison_records = ()
		self.comparisonChanged.emit()
		self._search_result = None
		self._visible_path = ()
		self._search_changed()

	@pyqtSlot()
	def resetProcessing(self) -> None:
		self._replace_options(ProcessingOptions())

	@pyqtSlot()
	def cleanup(self) -> None:
		if self._closed:
			return
		self._closed = True
		self._search_generation += 1
		self._comparison_generation += 1
		for thread in (self._search_thread, self._comparison_thread):
			if thread is not None:
				thread.requestInterruption()
				thread.quit()
				thread.wait()
		self._preview_directory.cleanup()

	def _update_options(self, **changes: object) -> None:
		try:
			options = replace(self._options, **changes)
		except (ImageProcessingError, TypeError) as error:
			self._set_error(str(error))
			return
		self._replace_options(options)

	def _replace_options(self, options: ProcessingOptions) -> None:
		if self.isBarnMap:
			self._set_error("BARN grids bypass image preprocessing. Load a custom image to use these controls.")
			return
		if options == self._options:
			self.processingChanged.emit()
			return
		if self._image is not None:
			try:
				processed = preprocess_image(self._image, options)
				self._write_processed_preview(processed)
				grid = None
				if self._occupancy_grid is not None:
					grid = binary_image_to_grid(
						processed,
						cell_size_px=self._grid_cell_size_px,
						obstacle_threshold_percent=self._obstacle_threshold_percent,
					)
					self._write_grid_preview(grid)
			except (ImageProcessingError, OccupancyGridError, OSError, cv2.error) as error:
				self._set_error(str(error))
				return

		self._options = options
		if self._image is not None:
			self._processed_image = processed
			if self._occupancy_grid is not None:
				self._occupancy_grid = grid
				self._reset_selection_state(default_start=True)
		self._error_message = ""
		if self._image is not None:
			self._status_message = "Preview updated. Black = obstacle; white = free space."
			self.imageChanged.emit()
			if self._occupancy_grid is not None:
				self.gridChanged.emit()
		self.processingChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	def _update_grid_options(self, **changes: int) -> None:
		if self.isBarnMap:
			self._set_error("Imported BARN grids retain their original resolution and occupancy cells.")
			return
		cell_size_px = changes.get("cell_size_px", self._grid_cell_size_px)
		obstacle_threshold_percent = changes.get(
			"obstacle_threshold_percent",
			self._obstacle_threshold_percent,
		)
		if not 1 <= cell_size_px <= 512:
			self._set_error("Grid cell size must be between 1 and 512 pixels.")
			return
		if not 1 <= obstacle_threshold_percent <= 100:
			self._set_error("Obstacle threshold must be between 1 and 100 percent.")
			return

		grid = self._occupancy_grid
		if self._processed_image is not None and grid is not None:
			try:
				grid = binary_image_to_grid(
					self._processed_image,
					cell_size_px=cell_size_px,
					obstacle_threshold_percent=obstacle_threshold_percent,
				)
				self._write_grid_preview(grid)
			except (OccupancyGridError, OSError, cv2.error) as error:
				self._set_error(str(error))
				return

		self._grid_cell_size_px = cell_size_px
		self._obstacle_threshold_percent = obstacle_threshold_percent
		if grid is not self._occupancy_grid:
			self._occupancy_grid = grid
			self._reset_selection_state(default_start=True)
			self._status_message = f"Grid updated: {grid.rows} x {grid.columns} cells."
			self.statusChanged.emit()
		self.gridChanged.emit()

	def _launch_worker(
		self,
		worker: SearchWorker | ComparisonWorker,
		completed: Callable[..., None],
		failed: Callable[..., None],
		finished: Callable[[], None],
	) -> QThread:
		"""Share the same ownership, signal delivery, and teardown for both workers."""
		thread = QThread(self)
		worker.moveToThread(thread)
		thread.started.connect(worker.run)
		worker.completed.connect(completed)
		worker.completed.connect(thread.quit)
		worker.failed.connect(failed)
		worker.failed.connect(thread.quit)
		thread.finished.connect(worker.deleteLater)
		thread.finished.connect(finished)
		thread.finished.connect(thread.deleteLater)
		thread.start()
		return thread

	def _write_grid_preview(self, grid: OccupancyGrid) -> None:
		image = np.where(grid.cells, 42, 242).astype(np.uint8)
		try:
			path = self._write_preview(image, "occupancy-grid", self._grid_preview_revision + 1, self._grid_preview_path)
		except ImageProcessingError as error:
			raise OccupancyGridError(str(error)) from error
		self._grid_preview_path = path
		self._grid_preview_revision += 1

	def _write_processed_preview(self, image: np.ndarray) -> None:
		self._processed_preview_path = self._write_preview(
			image, "processed", self._preview_revision + 1, self._processed_preview_path,
		)
		self._preview_revision += 1

	def _write_preview(self, image: np.ndarray, stem: str, revision: int, previous_path: Path) -> Path:
		encoded, buffer = cv2.imencode(".png", image)
		if not encoded:
			raise ImageProcessingError(f"Unable to encode the {stem} preview.")
		next_path = Path(self._preview_directory.name) / f"{stem}-{revision}.png"
		temporary_path = next_path.with_suffix(".tmp")
		try:
			temporary_path.write_bytes(buffer.tobytes())
			temporary_path.replace(next_path)
		except OSError:
			temporary_path.unlink(missing_ok=True)
			raise
		try:
			previous_path.unlink(missing_ok=True)
		except OSError:
			pass  # A displayed preview may still be open on Windows.
		return next_path

	def _set_error(self, message: str) -> None:
		self._error_message = message
		self._status_message = "Action needs attention."
		self.errorChanged.emit()
		self.statusChanged.emit()

	def _reset_selection_state(self, default_start: bool = False) -> None:
		self._selection_mode = "none"
		self._start_cell = None
		self._goal_cell = None
		if default_start and self._occupancy_grid is not None:
			for row in range(self._occupancy_grid.rows):
				free_columns = np.flatnonzero(~self._occupancy_grid.cells[row])
				if free_columns.size:
					self._start_cell = (row, int(free_columns[0]))
					break
		self.selectionChanged.emit()
		self._clear_search_state()
