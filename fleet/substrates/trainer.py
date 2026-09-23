"""Trainer substrate — original autoresearch 5-minute experiment pattern."""
import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult


WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)


class TrainerSubstrate(Substrate):
    """The Trainer substrate: 5-minute budget experiments on train.py.

    Original autoresearch pattern: agent modifies train.py, runs for
    exactly 5 minutes, evaluates val_bpb (lower = better), keeps improvement.

    Generalized: any time-budgeted experiment loop.
    """

    name = "trainer"

    def availability(self) -> Dict:
        return {
            "available": True,
            "default_time_budget_seconds": 300,  # 5 minutes
            "metric_target": "val_bpb (lower is better)",
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a training experiment with time budget."""
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_id = experiment.get("id", f"trainer-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            budget = experiment.get("budget_seconds", 300)
            output = self._simulate_training(experiment, budget)
            metric = output.get("val_bpb", 1.0)
            status = "success"
            error = None
        except Exception as e:
            status = "failed"
            error = str(e)
            output = {}
            metric = 1.0

        finished = datetime.datetime.utcnow().isoformat() + "Z"

        witness_record = {
            "substrate": "trainer",
            "experiment_id": exp_id,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = hashlib.sha256(json.dumps(witness_record, sort_keys=True).encode()).hexdigest()[:16]
        witness_path = WITNESS_DIR / f"{exp_id}_trainer.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="trainer",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def _simulate_training(self, experiment: Dict, budget_seconds: int) -> Dict:
        """Simulate a training run with deterministic metric."""
        seed = experiment.get("seed", "default")
        lr = experiment.get("learning_rate", 1e-3)
        arch = experiment.get("architecture", "transformer")

        # Deterministic mock val_bpb based on hyperparameters
        # Lower lr = better, deeper arch = better (somewhat)
        base_bpb = 1.0
        if lr <= 1e-4:
            base_bpb -= 0.05  # Too low: undertrains
        elif lr <= 1e-3:
            base_bpb -= 0.10  # Sweet spot
        else:
            base_bpb -= 0.02  # Too high: unstable

        if "deep" in arch:
            base_bpb -= 0.03
        elif "wide" in arch:
            base_bpb -= 0.02

        return {
            "val_bpb": round(base_bpb, 6),
            "training_seconds": budget_seconds,
            "architecture": arch,
            "learning_rate": lr,
            "peak_vram_mb": 32768 + (2000 if "deep" in arch else 0),
        }

    def list_experiments(self, limit: int = 10) -> List[str]:
        return sorted([p.stem for p in WITNESS_DIR.glob("*_trainer.json")])[-limit:]
