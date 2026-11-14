import sys

from app.application import create_application


def main() -> int:
	try:
		application, engine, view_model = create_application()
	except (OSError, RuntimeError) as error:
		print(f"Unable to start the application: {error}", file=sys.stderr)
		return 1

	return application.exec()


if __name__ == "__main__":
	sys.exit(main())
