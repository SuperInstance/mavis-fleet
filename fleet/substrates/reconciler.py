"""Reconciler — the K8s Operator pattern, for mavis-fleet.

Inspired by the Kubernetes controller-runtime Reconcile() loop:
- Read desired state (the workbook / canon spec)
- Read actual state (the live canon substrate / fleet witnesses)
- Compare (diff)
- Take action to converge (patch via substrates)
- Update status

The Reconciler is the substrate that makes mavis-fleet SELF-HEALING.

For a canon substrate reconciler:
- desired: what canon SHOULD be (a workbook of cells with expected values)
- actual: what canon IS (current witness log entries)
- diff: missing/extra/different cells
- action: submit missing cells to quilt substrate; flag extras
- status: write a witness
"""
import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .base import Substrate, SubstrateResult


@dataclass
class ReconcileState:
    """The current state of a reconciler — what it last saw."""
    desired: Dict[str, Any] = field(default_factory=dict)
    actual: Dict[str, Any] = field(default_factory=dict)
    diff: Dict[str, List[str]] = field(default_factory=lambda: {"missing": [], "extra": [], "changed": []})
    last_reconciled_at: str = ""
    reconcile_count: int = 0
    success_count: int = 0
    failure_count: int = 0


@dataclass
class ReconcileResult:
    """Result of one reconcile iteration."""
    success: bool
    diff: Dict[str, List[str]]
    actions_taken: List[str]
    duration_ms: int
    timestamp: str
    error: Optional[str] = None


class Reconciler(Substrate):
    """A substrate that reconciles desired vs actual state.

    Models the K8s controller loop:
    1. Read desired state (from the spec)
    2. Read actual state (from the world)
    3. Diff
    4. Take action to converge
    5. Update status
    6. Requeue if not converged
    """

    def __init__(self, name: str = "reconciler", max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self.states: Dict[str, ReconcileState] = {}
        self.results: List[ReconcileResult] = []

    def read(self, topic: str) -> "ReconcileResult":
        """Reconcile a topic. Returns the diff and actions."""
        # topic is a "spec name" — its desired state is stored separately
        state = self.states.get(topic, ReconcileState())
        if not state.desired:
            return ReconcileResult(
                success=False,
                diff={"missing": [], "extra": [], "changed": []},
                actions_taken=["error:no_desired_state"],
                duration_ms=0,
                timestamp="",
                error="no desired state for topic",
            )
        # Compute diff
        diff = self._compute_diff(state.desired, state.actual)
        state.diff = diff
        state.reconcile_count += 1

        # Take action
        actions = []
        if diff["missing"] or diff["changed"]:
            # In a real system: emit substrate calls to create/patch
            # Here: just record what we'd do
            for missing_id in diff["missing"]:
                actions.append(f"create:{missing_id}")
            for changed_id in diff["changed"]:
                actions.append(f"patch:{changed_id}")
        for extra_id in diff["extra"]:
            actions.append(f"prune:{extra_id}")

        success = not bool(diff["missing"] and not actions)
        if success:
            state.success_count += 1
        else:
            state.failure_count += 1

        result = ReconcileResult(
            success=success,
            diff=diff,
            actions_taken=actions,
            duration_ms=0,
            timestamp=state.last_reconciled_at,
        )
        self.results.append(result)
        self.states[topic] = state

        return result

    def write(self, topic: str, data: Any) -> "ReconcileResult":
        """Set the desired state for a topic."""
        if topic not in self.states:
            self.states[topic] = ReconcileState()
        self.states[topic].desired = data if isinstance(data, dict) else {"value": data}
        return ReconcileResult(
            success=True,
            diff={"missing": [], "extra": [], "changed": []},
            actions_taken=[f"set_desired:{topic}"],
            duration_ms=0,
            timestamp="",
        )

    def observe(self, topic: str, data: Any) -> "ReconcileResult":
        """Update the actual state for a topic (what the world reports)."""
        if topic not in self.states:
            self.states[topic] = ReconcileState()
        self.states[topic].actual = data if isinstance(data, dict) else {"value": data}
        return ReconcileResult(
            success=True,
            diff={"missing": [], "extra": [], "changed": []},
            actions_taken=[f"set_actual:{topic}"],
            duration_ms=0,
            timestamp="",
        )

    def _compute_diff(self, desired: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, List[str]]:
        """Compute missing / extra / changed between desired and actual."""
        diff = {"missing": [], "extra": [], "changed": []}
        d_keys = set(desired.keys())
        a_keys = set(actual.keys())
        for k in d_keys - a_keys:
            diff["missing"].append(k)
        for k in a_keys - d_keys:
            diff["extra"].append(k)
        for k in d_keys & a_keys:
            if desired[k] != actual[k]:
                diff["changed"].append(k)
        return diff

    def reconcile_all(self) -> List["ReconcileResult"]:
        """Reconcile all known topics."""
        results = []
        for topic in self.states:
            results.append(self.read(topic))
        return results

    def health(self) -> Dict:
        """Health check for the reconciler substrate."""
        total = sum(s.reconcile_count for s in self.states.values())
        succ = sum(s.success_count for s in self.states.values())
        return {
            "name": self.name,
            "topics": list(self.states.keys()),
            "total_reconciles": total,
            "success_rate": succ / total if total > 0 else 0.0,
        }

    # ─── Substrate interface (required) ───────────────────────

    def availability(self) -> Dict:
        """Return availability info."""
        return {
            "substrate": self.name,
            "topics": len(self.states),
            "results": len(self.results),
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a reconcile experiment.

        Experiment format:
        {
            "spec": {...},     # desired state
            "actual": {...},   # actual state
            "experiment_id": "..."
        }
        """
        spec = experiment.get("spec", {})
        actual = experiment.get("actual", {})
        topic = experiment.get("topic", "default")
        exp_id = experiment.get("experiment_id", str(uuid.uuid4()))

        # Set desired + actual
        if spec:
            self.write(topic, spec)
        if actual:
            self.observe(topic, actual)

        # Reconcile
        result = self.read(topic)

        now = datetime.datetime.utcnow().isoformat() + "Z"
        # Convert our substrate-internal SubstrateResult to the public one
        return SubstrateResult(
            substrate=self.name,
            experiment_id=exp_id,
            status="success" if result.success else "failed",
            started_at=now,
            finished_at=now,
            output=result.data,
        )

    def list_experiments(self, limit: int = 10) -> List[str]:
        """List recent reconcile results."""
        return [
            f"reconcile:{i}" for i, _ in enumerate(self.results[-limit:])
        ]
