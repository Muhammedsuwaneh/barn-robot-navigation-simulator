import os
import sys
from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from viewmodels.navigation_view_model import NavigationViewModel


def create_application(argv: Sequence[str] | None = None,
) -> tuple[QGuiApplication, QQmlApplicationEngine, NavigationViewModel]:
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

	return application, engine, view_model
