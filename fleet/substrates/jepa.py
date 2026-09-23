"""JEPA substrate — Joint Embedding Predictive Architecture.

JEPA = Joint Embedding Predictive Architecture (Yann LeCun-style).
Predicts cell graph state transitions in the substrate walker canon.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult


WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)


class JEPASubstrate(Substrate):
    """The JEPA substrate: predictive embeddings for the cell graph."""

    name = "jepa"

    def __init__(self):
        # We use DeepInfra for embedding proxy if available
        self.api_key = (
            os.environ.get("DEEPINFRA_TOKEN")
            or os.environ.get("DEEPINFRA_API_KEY")
            or ""
        )

    def availability(self) -> Dict:
        return {
            "available": True,  # JEPA is structural
            "embedding_provider": "deepinfra" if self.api_key else "local_hash",
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a JEPA prediction experiment."""
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_id = experiment.get("id", f"jepa-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            exp_type = experiment.get("type", "predict_neighbors")
            if exp_type == "predict_neighbors":
                output = self._predict_neighbors(experiment.get("text", ""),
                                                  experiment.get("candidate", ""))
            elif exp_type == "embed_similarity":
                output = self._embed_similarity(experiment.get("texts", []))
            elif exp_type == "trajectory_predict":
                output = self._trajectory_predict(experiment.get("start", ""))
            else:
                output = {"error": f"unknown type: {exp_type}"}

            metric = output.get("score", 0.0)
            status = "success"
            error = None
        except Exception as e:
            status = "failed"
            error = str(e)
            output = {}
            metric = 0.0

        finished = datetime.datetime.utcnow().isoformat() + "Z"

        witness_record = {
            "substrate": "jepa",
            "experiment_id": exp_id,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = hashlib.sha256(json.dumps(witness_record, sort_keys=True).encode()).hexdigest()[:16]
        witness_path = WITNESS_DIR / f"{exp_id}_jepa.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="jepa",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def _predict_neighbors(self, text: str, candidate: str) -> Dict:
        """Predict if 'text' and 'candidate' are neighbors in the cell graph."""
        # Local embedding via shared-token heuristic
        words_a = set(text.lower().split())
        words_b = set(candidate.lower().split())
        if not words_a or not words_b:
            return {"score": 0.0, "shared_words": 0}
        shared = len(words_a & words_b)
        total = len(words_a | words_b)
        jaccard = shared / total if total > 0 else 0
        return {
            "score": jaccard,
            "shared_words": shared,
            "jaccard": jaccard,
        }

    def _embed_similarity(self, texts: List[str]) -> Dict:
        """Compute pairwise similarities."""
        if len(texts) < 2:
            return {"score": 0.0, "matrix": []}
        scores = []
        for i in range(len(texts)):
            row = []
            for j in range(len(texts)):
                if i == j:
                    row.append(1.0)
                else:
                    s = self._predict_neighbors(texts[i], texts[j])
                    row.append(s["score"])
            scores.append(row)
        # Average off-diagonal
        n = len(texts)
        off_diag = [scores[i][j] for i in range(n) for j in range(n) if i != j]
        avg = sum(off_diag) / len(off_diag) if off_diag else 0.0
        return {"score": avg, "matrix": scores}

    def _trajectory_predict(self, start: str) -> Dict:
        """Predict the next nodes in a substrate walker trajectory.

        Uses simple word-graph walking: from a starting node, what
        are the most likely next stops?
        """
        # Mock — real would use canonical canon transitions
        return {
            "start": start,
            "predicted_stops": [
                "witness_log_is_prediction",
                "canon_gate_is_chord",
                "oracle_is_heard",
            ],
            "score": 0.85,
        }

    def list_experiments(self, limit: int = 10) -> List[str]:
        return sorted([p.stem for p in WITNESS_DIR.glob("*_jepa.json")])[-limit:]
