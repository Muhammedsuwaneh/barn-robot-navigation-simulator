from dataclasses import dataclass
from typing import Literal


CellCoordinate = tuple[int, int]
SearchTermination = Literal["found", "unreachable", "depth_limit"]


@dataclass(frozen=True)
class SearchResult:
	"""Shared search result; path length counts edges, while path includes endpoints."""

	algorithm: str
	found: bool
	path: tuple[CellCoordinate, ...]
	explored: tuple[CellCoordinate, ...]
	path_cost: int | None
	expanded_nodes: int
	elapsed_ms: float
	peak_frontier_size: int
	termination_reason: SearchTermination

	@property
	def path_length(self) -> int | None:
		if not self.found:
			return None
		return max(0, len(self.path) - 1)