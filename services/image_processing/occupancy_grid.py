import math

import numpy as np

from models.occupancy_grid import MAX_GRID_CELLS, OccupancyGrid, OccupancyGridError


def binary_image_to_grid(
	image: np.ndarray,
	cell_size_px: int = 8,
	obstacle_threshold_percent: int = 50,
) -> OccupancyGrid:
	"""Convert a binary preview into a grid; black pixels are obstacle pixels.

	A cell is occupied when at least the configured percentage of its source pixels
	are obstacles. Partial cells along the bottom and right edges use only the
	image pixels actually present in that cell.
	"""
	if not isinstance(image, np.ndarray) or image.ndim != 2 or image.size == 0:
		raise OccupancyGridError("Processed image must be a non-empty 2D binary image.")
	if image.dtype == np.bool_:
		obstacle_pixels = image
	else:
		if image.dtype != np.uint8 or not np.isin(image, (0, 255)).all():
			raise OccupancyGridError("Processed image values must be binary 0/255 (black obstacle, white free).")
		obstacle_pixels = image == 0
	if isinstance(cell_size_px, bool) or not isinstance(cell_size_px, int):
		raise OccupancyGridError("Cell size must be an integer number of pixels.")
	if not 1 <= cell_size_px <= 512:
		raise OccupancyGridError("Cell size must be between 1 and 512 pixels.")
	if isinstance(obstacle_threshold_percent, bool) or not isinstance(obstacle_threshold_percent, int):
		raise OccupancyGridError("Obstacle threshold must be an integer percentage.")
	if not 1 <= obstacle_threshold_percent <= 100:
		raise OccupancyGridError("Obstacle threshold must be between 1 and 100 percent.")

	image_height, image_width = image.shape
	grid_rows = math.ceil(image_height / cell_size_px)
	grid_columns = math.ceil(image_width / cell_size_px)
	if grid_rows * grid_columns > MAX_GRID_CELLS:
		raise OccupancyGridError(
			f"Requested grid has {grid_rows * grid_columns:,} cells; "
			f"increase cell size to stay within the {MAX_GRID_CELLS:,}-cell limit."
		)

	padded_height = grid_rows * cell_size_px
	padded_width = grid_columns * cell_size_px
	padded = np.pad(
		obstacle_pixels,
		((0, padded_height - image_height), (0, padded_width - image_width)),
		mode="constant",
		constant_values=False,
	)
	obstacle_counts = padded.reshape(
		grid_rows,
		cell_size_px,
		grid_columns,
		cell_size_px,
	).sum(axis=(1, 3), dtype=np.int64)

	valid_row_pixels = np.minimum(
		cell_size_px,
		image_height - np.arange(grid_rows) * cell_size_px,
	)
	valid_column_pixels = np.minimum(
		cell_size_px,
		image_width - np.arange(grid_columns) * cell_size_px,
	)
	valid_pixel_counts = valid_row_pixels[:, None] * valid_column_pixels[None, :]
	occupied_cells = obstacle_counts * 100 >= valid_pixel_counts * obstacle_threshold_percent

	return OccupancyGrid(
		cells=occupied_cells,
		cell_size_px=cell_size_px,
		obstacle_threshold_percent=obstacle_threshold_percent,
		source_width_px=image_width,
		source_height_px=image_height,
	)