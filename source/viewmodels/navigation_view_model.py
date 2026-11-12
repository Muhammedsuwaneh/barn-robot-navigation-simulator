import tempfile
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtCore import QUrl

from models.occupancy_grid import OccupancyGrid, OccupancyGridError
from services.image_processing.occupancy_grid import binary_image_to_grid
from services.image_processing.preprocessing import (
	ImageProcessingError,
	ProcessingOptions,
	load_image,
	preprocess_image,
)


class NavigationViewModel(QObject):
	activeSectionChanged = pyqtSignal()
	imageChanged = pyqtSignal()
	processingChanged = pyqtSignal()
	gridChanged = pyqtSignal()
	statusChanged = pyqtSignal()
	errorChanged = pyqtSignal()

	def __init__(self) -> None:
		super().__init__()
		self._active_section = "workspace"
		self._options = ProcessingOptions()
		self._image: np.ndarray | None = None
		self._processed_image: np.ndarray | None = None
		self._image_path: Path | None = None
		self._occupancy_grid: OccupancyGrid | None = None
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
		return "PHASE 04 / OCCUPANCY GRID"

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
		return self._image_path.name if self._image_path else "No image selected"

	@pyqtProperty(str, notify=imageChanged)
	def imageDimensions(self) -> str:
		if self._image is None:
			return "--"
		height, width = self._image.shape[:2]
		return f"{width} x {height} px"

	@pyqtProperty(str, notify=imageChanged)
	def originalPreviewUrl(self) -> str:
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
		self._update_options(adaptive=bool(value))

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
		return self._grid_cell_size_px

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

	@pyqtProperty(str, notify=activeSectionChanged)
	def activeSection(self) -> str:
		return self._active_section

	@pyqtSlot(str)
	def selectSection(self, section: str) -> None:
		if section != "workspace" or self._active_section == section:
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
		self._processed_image = processed
		self._image_path = image_path.resolve()
		self._occupancy_grid = None
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
		self._error_message = ""
		self._status_message = (
			f"Grid generated: {grid.rows} x {grid.columns} cells · "
			f"{grid.occupied_count} occupied · {grid.free_count} free."
		)
		self.gridChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

	@pyqtSlot()
	def resetProcessing(self) -> None:
		self._replace_options(ProcessingOptions())

	@pyqtSlot()
	def cleanup(self) -> None:
		self._preview_directory.cleanup()

	def _update_options(self, **changes: object) -> None:
		try:
			options = replace(self._options, **changes)
		except (ImageProcessingError, TypeError) as error:
			self._set_error(str(error))
			return
		self._replace_options(options)

	def _replace_options(self, options: ProcessingOptions) -> None:
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
			self._status_message = f"Grid updated: {grid.rows} x {grid.columns} cells."
			self.statusChanged.emit()
		self.gridChanged.emit()

	def _write_grid_preview(self, grid: OccupancyGrid) -> None:
		image = np.where(grid.cells, 42, 242).astype(np.uint8)
		encoded, buffer = cv2.imencode(".png", image)
		if not encoded:
			raise OccupancyGridError("Unable to encode the occupancy-grid preview.")
		preview_directory = Path(self._preview_directory.name)
		next_revision = self._grid_preview_revision + 1
		next_path = preview_directory / f"occupancy-grid-{next_revision}.png"
		temporary_path = next_path.with_suffix(".tmp")
		try:
			temporary_path.write_bytes(buffer.tobytes())
			temporary_path.replace(next_path)
		except OSError:
			temporary_path.unlink(missing_ok=True)
			raise

		previous_path = self._grid_preview_path
		self._grid_preview_path = next_path
		self._grid_preview_revision = next_revision
		try:
			previous_path.unlink(missing_ok=True)
		except OSError:
			pass

	def _write_processed_preview(self, image: np.ndarray) -> None:
		encoded, buffer = cv2.imencode(".png", image)
		if not encoded:
			raise ImageProcessingError("Unable to encode the processed preview.")
		preview_directory = Path(self._preview_directory.name)
		next_revision = self._preview_revision + 1
		next_path = preview_directory / f"processed-{next_revision}.png"
		temporary_path = next_path.with_suffix(".tmp")
		try:
			temporary_path.write_bytes(buffer.tobytes())
			temporary_path.replace(next_path)
		except OSError:
			temporary_path.unlink(missing_ok=True)
			raise

		previous_path = self._processed_preview_path
		self._processed_preview_path = next_path
		self._preview_revision = next_revision
		try:
			previous_path.unlink(missing_ok=True)
		except OSError:
			pass

	def _set_error(self, message: str) -> None:
		self._error_message = message
		self._status_message = "Image could not be processed."
		self.errorChanged.emit()
		self.statusChanged.emit()