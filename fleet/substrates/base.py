"""Base substrate — common interface for all substrates."""
import abc
import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SubstrateResult:
    """Result of a substrate experiment."""
    substrate: str
    experiment_id: str
    status: str  # "success", "failed", "pending"
    started_at: str
    finished_at: Optional[str] = None
    output: Dict = field(default_factory=dict)
    metric: Optional[float] = None
    witness: Optional[str] = None
    error: Optional[str] = None


class Substrate(abc.ABC):
    """Abstract base for all substrates."""

    name: str = "base"

    @abc.abstractmethod
    def availability(self) -> Dict:
        """Return availability info (resources, keys, etc.)."""
        ...

    @abc.abstractmethod
    def run(self, experiment: Dict) -> SubstrateResult:
        """Run an experiment in this substrate."""
        ...

    @abc.abstractmethod
    def list_experiments(self, limit: int = 10) -> List[str]:
        """List recent experiments."""
        ...
