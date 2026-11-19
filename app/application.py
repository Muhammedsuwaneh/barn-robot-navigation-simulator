import os
import sys
from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import QSize, QUrlsay
from PyQt6.QtQml import QQmlApplicationEngine

from viewmodels.navigation_view_model import NavigationViewModel


def _fill_available_desktop(window: QWindow) -> None:
	"""Fill the current monitor's work area, leaving its taskbar accessible."""
	current_screen = None

	def fit_to_work_area() -> None:
		if current_screen is None:
			return
		geometry = current_screen.availableGeometry()
		window.setMinimumSize(QSize(min(1080, geometry.width()), min(720, geometry.height())))
		window.setGeometry(geometry)

	def follow_screen(screen) -> None:
		nonlocal current_screen
		if current_screen is not None:
			current_screen.availableGeometryChanged.disconnect(fit_to_work_area)
		current_screen = screen
		if current_screen is not None:
			current_screen.availableGeometryChanged.connect(fit_to_work_area)
		fit_to_work_area()

	window.screenChanged.connect(follow_screen)
	follow_screen(window.screen())


def create_application(argv: Sequence[str] | None = None,) -> tuple[QGuiApplication, QQmlApplicationEngine, NavigationViewModel]:
	
	os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
	application = QGuiApplication(list(argv) if argv is not None else sys.argv)
	application.setApplicationName("AI Robot Navigation Simulator")
	application.setOrganizationName("AI Robot Navigation Simulator")

	engine = QQmlApplicationEngine()
	view_model = NavigationViewModel()
	view_model.setParent(engine)
	barn_view_model = NavigationViewModel()
	barn_view_model.setParent(engine)
	engine.setInitialProperties({"navigationViewModel": view_model, "barnViewModel": barn_view_model})
	application.aboutToQuit.connect(view_model.cleanup)
	application.aboutToQuit.connect(barn_view_model.cleanup)

	qml_file = Path(__file__).resolve().parent.parent / "views" / "main.qml"
	if not qml_file.is_file():
		raise FileNotFoundError(f"QML interface not found: {qml_file}")

	engine.load(QUrl.fromLocalFile(str(qml_file)))
	if not engine.rootObjects():
		raise RuntimeError(f"Failed to load QML interface: {qml_file}")
	_fill_available_desktop(engine.rootObjects()[0])

	return application, engine, view_model
