import tempfile
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtCore import QUrl

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
	statusChanged = pyqtSignal()
	errorChanged = pyqtSignal()

	def __init__(self) -> None:
		super().__init__()
		self._active_section = "workspace"
		self._options = ProcessingOptions()
		self._image: np.ndarray | None = None
		self._image_path: Path | None = None
		self._preview_directory = tempfile.TemporaryDirectory(prefix="ai-navigation-")
		self._preview_revision = 0
		self._processed_preview_path = Path(self._preview_directory.name) / "processed-0.png"
		self._status_message = "Ready. Load a PNG, JPG, or JPEG environment image."
		self._error_message = ""

	@pyqtProperty(str, constant=True)
	def applicationName(self) -> str:
		return "AI Robot Navigation Simulator"

	@pyqtProperty(str, constant=True)
	def phaseLabel(self) -> str:
		return "PHASE 03 / IMAGE PREPROCESSING"

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
		self._image_path = image_path.resolve()
		self._error_message = ""
		self._status_message = f"Loaded {self._image_path.name} · {self.imageDimensions}"
		self.imageChanged.emit()
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
			except (ImageProcessingError, OSError, cv2.error) as error:
				self._set_error(str(error))
				return

		self._options = options
		self._error_message = ""
		if self._image is not None:
			self._status_message = "Preview updated. Black = obstacle; white = free space."
			self.imageChanged.emit()
		self.processingChanged.emit()
		self.statusChanged.emit()
		self.errorChanged.emit()

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