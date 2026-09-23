"""JEV substrate — Joint Embedding Validator oracle."""
import datetime
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult


JEV_BASE = "https://api.typesafe.ai/v1"
WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)


class JEVSubstrate(Substrate):
    """The JEV substrate: oracle gate for canon-vs-speculation."""

    name = "jev"

    def __init__(self):
        self.api_key = (
            os.environ.get("TYPESAFEAI_KEY")
            or os.environ.get("TYPESAFE_AI_KEY")
            or ""
        )

    def availability(self) -> Dict:
        return {
            "available": bool(self.api_key),
            "api_key_present": bool(self.api_key),
            "endpoint": JEV_BASE,
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a JEV probe.

        Experiment shape:
        {
            "type": "probe",
            "question_id": "qN",
            "claim_a": "...",
            "claim_b": "...",
        }
        """
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_id = experiment.get("id", f"jev-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            verdict = self._probe(experiment)
            output = verdict
            metric = verdict.get("p_value", 0)
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
            "substrate": "jev",
            "experiment_id": exp_id,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = hashlib.sha256(json.dumps(witness_record, sort_keys=True).encode()).hexdigest()[:16]
        witness_path = WITNESS_DIR / f"{exp_id}_jev.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="jev",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def _probe(self, experiment: Dict) -> Dict:
        """Call JEV API for a probe verdict."""
        if not self.api_key:
            # No API key — return a local heuristic verdict
            return {
                "verdict": "LOCAL_HEURISTIC",
                "p_value": 0.5,
                "rationale": "TYPESAFEAI_KEY not set; using local heuristic",
                "promoted": False,
            }

        url = f"{JEV_BASE}/probe"
        body = json.dumps({
            "question_id": experiment.get("question_id", "q01"),
            "claim_a": experiment.get("claim_a", ""),
            "claim_b": experiment.get("claim_b", ""),
        }).encode()

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data
        except Exception as e:
            return {
                "verdict": "ERROR",
                "p_value": 0.0,
                "error": str(e),
                "promoted": False,
            }

    def list_experiments(self, limit: int = 10) -> List[str]:
        return sorted([p.stem for p in WITNESS_DIR.glob("*_jev.json")])[-limit:]
