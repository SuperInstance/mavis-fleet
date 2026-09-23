"""Quilt substrate — canon, witness log, multi-oracle, tile pipeline."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult


# Path to the Quilt canon
CANON_DIR = Path("/workspace/research/canon_writings")
WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)

# Path to multi-oracle client
QUILT_REPO = Path("/workspace/repos/quilt-multi-oracle")


class QuiltSubstrate(Substrate):
    """The Quilt substrate: canon + witness + multi-oracle."""

    name = "quilt"

    def __init__(self):
        self.canon_dir = CANON_DIR
        self.witness_dir = WITNESS_DIR

    def availability(self) -> Dict:
        return {
            "available": self.canon_dir.exists(),
            "canon_pieces": len(list(self.canon_dir.glob("*.md"))) if self.canon_dir.exists() else 0,
            "witness_dir": str(self.witness_dir),
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a Quilt experiment.

        Experiment types:
        - "load_canon": Load N canon pieces into context
        - "probe": Probe a candidate canon piece via JEV-style multi-oracle
        - "iterate": Iterate a canon piece with LLM (if available)
        """
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_type = experiment.get("type", "load_canon")
        exp_id = experiment.get("id", f"quilt-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            if exp_type == "load_canon":
                output = self._load_canon(experiment.get("limit", 5))
                metric = float(len(output.get("pieces", [])))
            elif exp_type == "probe":
                output = self._probe(experiment.get("text", ""))
                metric = output.get("polyformality", 0)
            elif exp_type == "iterate":
                output = self._iterate(experiment.get("topic", ""))
                metric = output.get("composite", 0.0)
            else:
                output = {"error": f"unknown experiment type: {exp_type}"}
                metric = 0.0

            status = "success"
            error = None
        except Exception as e:
            status = "failed"
            error = str(e)
            output = {}
            metric = 0.0

        finished = datetime.datetime.utcnow().isoformat() + "Z"

        # Witness
        witness_record = {
            "substrate": "quilt",
            "experiment_id": exp_id,
            "type": exp_type,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = hashlib.sha256(json.dumps(witness_record, sort_keys=True).encode()).hexdigest()[:16]
        witness_path = self.witness_dir / f"{exp_id}_quilt.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="quilt",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def _load_canon(self, limit: int) -> Dict:
        """Load canon pieces."""
        pieces = []
        if not self.canon_dir.exists():
            return {"pieces": pieces, "error": "canon dir not found"}
        for f in sorted(self.canon_dir.glob("*.md"))[:limit]:
            content = f.read_text(errors="replace")
            pieces.append({
                "id": f.stem,
                "preview": content[:300],
                "size": len(content),
            })
        return {"pieces": pieces}

    def _probe(self, text: str) -> Dict:
        """Probe a candidate canon piece."""
        # Simple polyformality heuristic: compare against existing canon
        if not self.canon_dir.exists():
            return {"polyformality": 0.0, "matched_doctrines": []}

        matches = 0
        matched_doctrines = []
        for f in self.canon_dir.glob("*.md"):
            content = f.read_text(errors="replace").lower()
            for doctrine in ["cells_are_scars", "witness_log_is_prediction",
                            "canon_gate_is_chord", "oracle_is_heard",
                            "substrate_quantum"]:
                if doctrine in text.lower() and doctrine in content:
                    matches += 1
                    if doctrine not in matched_doctrines:
                        matched_doctrines.append(doctrine)

        canon_count = len(list(self.canon_dir.glob("*.md")))
        polyformality = matches / (canon_count * 5) if canon_count > 0 else 0
        return {
            "polyformality": min(1.0, polyformality),
            "matched_doctrines": matched_doctrines,
        }

    def _iterate(self, topic: str) -> Dict:
        """Iterate on a topic using canon context (mock)."""
        # Real implementation would call LLM with canon context
        return {
            "topic": topic,
            "composite": 0.0,  # Mock — real LLM call would produce a score
            "note": "iterate requires DEEPINFRA_TOKEN or ZAI_TOKEN",
        }

    def list_experiments(self, limit: int = 10) -> List[str]:
        """List recent experiments."""
        return sorted([p.stem for p in self.witness_dir.glob("*.json")])[-limit:]
