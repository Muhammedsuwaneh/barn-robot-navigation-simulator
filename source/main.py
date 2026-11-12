import sys
from pathlib import Path

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine


def main() -> int:
	app = QGuiApplication(sys.argv)
	engine = QQmlApplicationEngine()
	qml_file = Path(__file__).resolve().parent / "views" / "main.qml"

	engine.load(qml_file.as_uri())
	if not engine.rootObjects():
		return 1

	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
