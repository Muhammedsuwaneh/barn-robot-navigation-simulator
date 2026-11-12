import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QObject

from app.application import create_application


class ApplicationSmokeTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.application, cls.engine, cls.view_model = create_application([])
		cls.window = cls.engine.rootObjects()[0]

	@classmethod
	def tearDownClass(cls) -> None:
		cls.window.close()
		cls.engine.deleteLater()
		cls.application.processEvents()
		super().tearDownClass()

	def test_qml_window_loads_with_backend_context(self) -> None:
		self.assertEqual(self.window.property("title"), "AI Robot Navigation Simulator")
		self.assertEqual(self.view_model.property("activeSection"), "workspace")

	def test_image_loading_is_enabled_but_pathfinding_is_disabled(self) -> None:
		load_button = self.window.findChild(QObject, "loadImageButton")
		self.assertIsNotNone(load_button)
		self.assertTrue(load_button.property("enabled"))

		for object_name in ("algorithmSelector", "runNavigationButton"):
			with self.subTest(control=object_name):
				control = self.window.findChild(QObject, object_name)
				self.assertIsNotNone(control)
				self.assertFalse(control.property("enabled"))


if __name__ == "__main__":
	unittest.main()