import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import QUrl

from services.image_processing.preprocessing import (
	ImageProcessingError,
	ProcessingOptions,
	load_image,
	preprocess_image,
	to_grayscale,
)
from viewmodels.navigation_view_model import NavigationViewModel


class ImagePreprocessingTests(unittest.TestCase):
	def setUp(self) -> None:
		self.image = np.full((9, 9), 255, dtype=np.uint8)
		self.image[:, :4] = 0

	def test_grayscale_conversion_accepts_color_and_grayscale(self) -> None:
		color = np.dstack((self.image, self.image, self.image))
		self.assertTrue(np.array_equal(to_grayscale(self.image), self.image))
		self.assertTrue(np.array_equal(to_grayscale(color), self.image))

	def test_fixed_threshold_marks_dark_pixels_as_obstacles(self) -> None:
		processed = preprocess_image(self.image, ProcessingOptions(threshold=120))
		self.assertEqual(processed[4, 1], 0)
		self.assertEqual(processed[4, 7], 255)
		self.assertEqual(set(np.unique(processed)), {0, 255})

	def test_light_obstacle_interpretation_inverts_output(self) -> None:
		processed = preprocess_image(
			self.image,
			ProcessingOptions(threshold=120, light_pixels_are_obstacles=True),
		)
		self.assertEqual(processed[4, 1], 255)
		self.assertEqual(processed[4, 7], 0)

	def test_adaptive_threshold_produces_binary_output(self) -> None:
		gradient = np.tile(np.arange(9, dtype=np.uint8) * 28, (9, 1))
		processed = preprocess_image(
			gradient,
			ProcessingOptions(adaptive=True, block_size=5),
		)
		self.assertEqual(processed.shape, gradient.shape)
		self.assertEqual(set(np.unique(processed)), {0, 255})

	def test_opening_removes_an_isolated_obstacle(self) -> None:
		image = np.full((9, 9), 255, dtype=np.uint8)
		image[4, 4] = 0
		processed = preprocess_image(
			image,
			ProcessingOptions(morphology="open", kernel_size=3),
		)
		self.assertEqual(processed[4, 4], 255)

	def test_invalid_processing_options_are_rejected(self) -> None:
		with self.assertRaises(ImageProcessingError):
			ProcessingOptions(block_size=4)
		with self.assertRaises(ImageProcessingError):
			ProcessingOptions(threshold=256)

	def test_loader_accepts_unicode_path_and_rejects_bad_files(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "café_map.png"
			encoded, buffer = cv2.imencode(".png", self.image)
			self.assertTrue(encoded)
			image_path.write_bytes(buffer.tobytes())
			loaded = load_image(image_path)
			self.assertEqual(loaded.shape, (9, 9, 3))

			bad_path = Path(directory) / "broken.jpg"
			bad_path.write_bytes(b"not an image")
			with self.assertRaises(ImageProcessingError):
				load_image(bad_path)

			unsupported_path = Path(directory) / "map.gif"
			with self.assertRaises(ImageProcessingError):
				load_image(unsupported_path)

	def test_view_model_updates_preview_and_preserves_image_on_load_error(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			image_path = Path(directory) / "sample.png"
			encoded, buffer = cv2.imencode(".png", self.image)
			self.assertTrue(encoded)
			image_path.write_bytes(buffer.tobytes())

			view_model = NavigationViewModel()
			self.addCleanup(view_model.cleanup)
			view_model.loadImage(str(image_path))
			self.assertTrue(view_model.hasImage)
			self.assertEqual(view_model.imageDimensions, "9 x 9 px")
			preview_path = Path(QUrl(view_model.processedPreviewUrl).toLocalFile())
			self.assertTrue(preview_path.is_file())
			view_model.threshold = 200
			self.assertEqual(view_model.threshold, 200)
			view_model.loadImage(str(Path(directory) / "missing.png"))
			self.assertTrue(view_model.hasImage)
			self.assertIn("Unable to read image", view_model.errorMessage)


if __name__ == "__main__":
	unittest.main()