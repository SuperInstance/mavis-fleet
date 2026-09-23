"""RSI substrate — the meta-substrate for recursive self-improvement.

The RSI substrate doesn't run experiments on the world; it runs
experiments on the fleet itself. It's the substrate walker for the
fleet's own operation.
"""
import datetime
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult
from ..core import RSILoop, witness as witness_hash_fn


WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)


class RSISubstrate(Substrate):
    """The RSI substrate: experiments on the fleet itself."""

    name = "rsi"

    def __init__(self):
        self.proposals = deque(maxlen=100)
        self.results = []

    def availability(self) -> Dict:
        return {
            "available": True,
            "proposals_in_queue": len(self.proposals),
            "experiments_completed": len(self.results),
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run an RSI iteration."""
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_id = experiment.get("id", f"rsi-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            loop = RSILoop()
            iterations = experiment.get("iterations", 1)
            records = loop.run(iterations=iterations)
            output = {
                "iterations": len(records),
                "kept_count": sum(1 for r in records if r.get("scored", {}).get("kept")),
                "improvement_total": sum(r.get("scored", {}).get("improvement", 0) for r in records),
                "last_proposal": records[-1]["proposal"] if records else None,
            }
            metric = float(output["improvement_total"])
            status = "success"
            error = None
            self.results.extend(records)
        except Exception as e:
            status = "failed"
            error = str(e)
            output = {}
            metric = 0.0

        finished = datetime.datetime.utcnow().isoformat() + "Z"

        witness_record = {
            "substrate": "rsi",
            "experiment_id": exp_id,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = witness_hash_fn(witness_record)
        witness_path = WITNESS_DIR / f"{exp_id}_rsi.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="rsi",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def list_experiments(self, limit: int = 10) -> List[str]:
        return sorted([p.stem for p in WITNESS_DIR.glob("*_rsi.json")])[-limit:]
