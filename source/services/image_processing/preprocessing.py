from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np


MorphologyMode = Literal["none", "open", "close"]
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg"}


class ImageProcessingError(ValueError):
	"""Raised when an image cannot be loaded or processed safely."""


@dataclass(frozen=True)
class ProcessingOptions:
	threshold: int = 128
	adaptive: bool = False
	block_size: int = 11
	adaptive_c: int = 2
	morphology: MorphologyMode = "none"
	kernel_size: int = 3
	light_pixels_are_obstacles: bool = False

	def __post_init__(self) -> None:
		if not 0 <= self.threshold <= 255:
			raise ImageProcessingError("Threshold must be between 0 and 255.")
		if self.block_size < 3 or self.block_size % 2 == 0:
			raise ImageProcessingError("Adaptive block size must be an odd number of at least 3.")
		if not -50 <= self.adaptive_c <= 50:
			raise ImageProcessingError("Adaptive C must be between -50 and 50.")
		if self.morphology not in ("none", "open", "close"):
			raise ImageProcessingError("Morphology must be none, open, or close.")
		if self.kernel_size < 1 or self.kernel_size % 2 == 0:
			raise ImageProcessingError("Morphology kernel size must be a positive odd number.")


def load_image(path: str | Path) -> np.ndarray:
	"""Load a supported local image as an 8-bit BGR array, including Unicode paths."""
	image_path = Path(path).expanduser()
	if image_path.suffix.lower() not in SUPPORTED_SUFFIXES:
		raise ImageProcessingError("Choose a PNG, JPG, or JPEG image.")

	try:
		encoded_file = np.frombuffer(image_path.read_bytes(), dtype=np.uint8)
	except OSError as error:
		raise ImageProcessingError(f"Unable to read image: {error}") from error

	if encoded_file.size == 0:
		raise ImageProcessingError("The selected image file is empty.")

	image = cv2.imdecode(encoded_file, cv2.IMREAD_COLOR)
	if image is None or image.size == 0:
		raise ImageProcessingError("The selected file is not a readable image.")
	return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
	"""Convert a uint8 grayscale, BGR, or BGRA image into an 8-bit grayscale image."""
	if not isinstance(image, np.ndarray) or image.size == 0:
		raise ImageProcessingError("Image data is empty.")
	if image.dtype != np.uint8:
		raise ImageProcessingError("Image data must use 8-bit pixels.")
	if image.ndim == 2:
		return image
	if image.ndim != 3:
		raise ImageProcessingError("Image must be grayscale, BGR, or BGRA.")
	if image.shape[2] == 3:
		return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	if image.shape[2] == 4:
		return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
	raise ImageProcessingError("Color images must have 3 (BGR) or 4 (BGRA) channels.")


def preprocess_image(image: np.ndarray, options: ProcessingOptions | None = None) -> np.ndarray:
	"""Return a binary uint8 image where obstacles are black and free space is white."""
	settings = options or ProcessingOptions()
	grayscale = to_grayscale(image)

	if settings.adaptive:
		binary = cv2.adaptiveThreshold(
			grayscale,
			255,
			cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
			cv2.THRESH_BINARY,
			settings.block_size,
			settings.adaptive_c,
		)
	else:
		_, binary = cv2.threshold(
			grayscale,
			settings.threshold,
			255,
			cv2.THRESH_BINARY,
		)

	if settings.light_pixels_are_obstacles:
		binary = cv2.bitwise_not(binary)

	if settings.morphology != "none":
		kernel = np.ones((settings.kernel_size, settings.kernel_size), dtype=np.uint8)
		obstacle_mask = cv2.bitwise_not(binary)
		operation = cv2.MORPH_OPEN if settings.morphology == "open" else cv2.MORPH_CLOSE
		obstacle_mask = cv2.morphologyEx(obstacle_mask, operation, kernel)
		binary = cv2.bitwise_not(obstacle_mask)

	return binary