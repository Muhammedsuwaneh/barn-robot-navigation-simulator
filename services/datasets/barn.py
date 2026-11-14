from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np

from models.occupancy_grid import MAX_GRID_CELLS, OccupancyGrid


DEFAULT_BARN_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "dataset"
MAP_NAME = re.compile(r"(grid|cspace)_(\d+)\.npy")


class BarnImportError(ValueError):
	"""A local BARN map or dataset directory cannot be imported."""


@dataclass(frozen=True)
class BarnMap:
	path: Path
	family: str
	scenario: int

	@property
	def identifier(self) -> str:
		return f"BARN/{self.family}_{self.scenario}"

	@property
	def label(self) -> str:
		return f"{self.family}_{self.scenario} ({'C-space' if self.family == 'cspace' else 'raw grid'})"


def describe_map(path: str | Path) -> BarnMap:
	path = Path(path).expanduser().resolve()
	match = MAP_NAME.fullmatch(path.name)
	if match is None or not 0 <= int(match[2]) < 300:
		raise BarnImportError("Select grid_i.npy or cspace_i.npy with scenario i between 0 and 299.")
	return BarnMap(path, match[1], int(match[2]))


def discover_maps(directory: str | Path) -> tuple[BarnMap, ...]:
	"""List candidate occupancy maps, never metrics, paths, or simulation files."""
	root = Path(directory).expanduser().resolve()
	if not root.is_dir():
		raise BarnImportError(f"BARN dataset directory does not exist: {root}")
	entries: dict[Path, BarnMap] = {}
	try:
		for folder in (root, root / "grid_files", root / "cspace_files"):
			if not folder.is_dir():
				continue
			for path in folder.glob("*.npy"):
				if not path.is_file() or MAP_NAME.fullmatch(path.name) is None:
					continue
				try:
					entry = describe_map(path)
				except BarnImportError:
					continue
				entries[entry.path] = entry
	except OSError as error:
		raise BarnImportError(f"Unable to inspect BARN dataset: {error}") from error
	return tuple(sorted(entries.values(), key=lambda entry: (entry.family != "grid", entry.scenario, str(entry.path))))


def import_barn_map(path: str | Path) -> OccupancyGrid:
	"""Read a binary .npy occupancy map without modifying its contents or orientation."""
	entry = describe_map(path)
	try:
		# Read-only memory mapping bounds memory use before shape/value validation.
		cells = np.load(entry.path, allow_pickle=False, mmap_mode="r")
		if not isinstance(cells, np.ndarray) or cells.ndim != 2 or cells.size == 0:
			raise BarnImportError("BARN occupancy maps must be non-empty two-dimensional arrays.")
		if cells.size > MAX_GRID_CELLS:
			raise BarnImportError(f"BARN map exceeds the {MAX_GRID_CELLS:,}-cell limit.")
		if cells.dtype.kind not in "biuf" or not np.all((cells == 0) | (cells == 1)):
			raise BarnImportError("BARN occupancy cells must contain only numeric 0 (free) and 1 (occupied).")
		return OccupancyGrid(
			cells=np.asarray(cells, dtype=np.bool_),
			cell_size_px=1,
			obstacle_threshold_percent=50,
			source_width_px=int(cells.shape[1]),
			source_height_px=int(cells.shape[0]),
		)
	except BarnImportError:
		raise
	except (OSError, ValueError, TypeError, EOFError) as error:
		raise BarnImportError(f"Unable to import {entry.path.name}: {error}") from error
