import csv
import json
import io
from pathlib import Path
from typing import Literal

from services.evaluation.records import ExperimentRecord


ExportFormat = Literal["csv", "json"]
CSV_FIELDS = (
	"record_id",
	"timestamp_utc",
	"map_identifier",
	"dataset_source",
	"grid_rows",
	"grid_columns",
	"start_row",
	"start_column",
	"goal_row",
	"goal_column",
	"algorithm",
	"parameters",
	"success",
	"success_rate",
	"path_length",
	"path_cost",
	"execution_time_ms",
	"nodes_expanded",
	"peak_frontier_size",
)
DEFAULT_EXPERIMENT_LOG = Path(__file__).resolve().parents[2] / "data" / "experiments.csv"


def _csv_text(records: tuple[ExperimentRecord, ...], *, include_header: bool) -> str:
	"""Serialize before opening a destination so invalid metadata cannot corrupt it."""
	output = io.StringIO(newline="")
	writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
	if include_header:
		writer.writeheader()
	for record in records:
		row = record.to_dict()
		row["parameters"] = json.dumps(row["parameters"], sort_keys=True, allow_nan=False)
		writer.writerow(row)
	return output.getvalue()


def append_experiments(
	records: tuple[ExperimentRecord, ...],
	log_path: str | Path | None = None,
) -> Path:
	"""Append records to the local CSV log without replacing previous runs."""
	path = Path(log_path) if log_path is not None else DEFAULT_EXPERIMENT_LOG
	path.parent.mkdir(parents=True, exist_ok=True)
	needs_header = not path.exists() or path.stat().st_size == 0
	if not needs_header:
		with path.open("r", newline="", encoding="utf-8") as existing_file:
			existing_header = tuple(next(csv.reader(existing_file), ()))
		if existing_header != CSV_FIELDS:
			raise ValueError(f"Experiment log has an incompatible header: {path}")

	serialized = _csv_text(records, include_header=needs_header)
	with path.open("a", newline="", encoding="utf-8") as output_file:
		output_file.write(serialized)
	return path


def export_experiments(
	records: tuple[ExperimentRecord, ...],
	path: str | Path,
	export_format: ExportFormat,
) -> Path:
	"""Export selected results exclusively; an existing file is never overwritten."""
	output_path = Path(path)
	if export_format not in ("csv", "json"):
		raise ValueError("Export format must be csv or json.")
	if export_format == "json":
		serialized = json.dumps([record.to_dict() for record in records], indent=2, allow_nan=False) + "\n"
	else:
		serialized = _csv_text(records, include_header=True)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("x", newline="", encoding="utf-8") as output_file:
		output_file.write(serialized)
	return output_path
