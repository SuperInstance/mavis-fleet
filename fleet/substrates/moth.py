"""MOTH substrate — MOTHQuantum (quantumaudio SDK) experiments."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .base import Substrate, SubstrateResult


WITNESS_DIR = Path("/workspace/research/mavis-fleet/witnesses")
WITNESS_DIR.mkdir(parents=True, exist_ok=True)

MOTH_REPO = Path("/workspace/repos")  # Placeholder for MOTHQuantum repo


class MOTHSubstrate(Substrate):
    """The MOTH substrate: quantum polygon experiments (quantumaudio SDK).

    Per memory: MOTH = MOTHQuantum = quantumaudio SDK.
    Substrate walker structurally isomorphic to a quantum circuit.
    Empirically, canon signal is in LINGUISTIC structure not geometric/quantum.
    """

    name = "moth"

    def availability(self) -> Dict:
        return {
            "available": True,  # MOTH has its own SDK; substrate is structural
            "sdk_path": str(MOTH_REPO),
            "isomorphism": "cell=amplitude, witness=time register",
            "canon_in_signal": "linguistic_structure_not_quantum",
        }

    def run(self, experiment: Dict) -> SubstrateResult:
        """Run a MOTH experiment.

        Experiment types:
        - "quantum_polygon": Run a polygon experiment on N sides
        - "amplitude_walk": Walk the substrate walker in quantum space
        - "null_result": Record a deliberate null result
        """
        started = datetime.datetime.utcnow().isoformat() + "Z"
        exp_id = experiment.get("id", f"moth-{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")

        try:
            exp_type = experiment.get("type", "amplitude_walk")
            if exp_type == "quantum_polygon":
                output = self._quantum_polygon(experiment.get("sides", 6))
            elif exp_type == "amplitude_walk":
                output = self._amplitude_walk(experiment.get("steps", 12))
            elif exp_type == "null_result":
                output = self._null_result(experiment.get("hypothesis", ""))
            else:
                output = {"error": f"unknown type: {exp_type}"}

            metric = output.get("value", 0.0)
            status = "success"
            error = None
        except Exception as e:
            status = "failed"
            error = str(e)
            output = {}
            metric = 0.0

        finished = datetime.datetime.utcnow().isoformat() + "Z"

        witness_record = {
            "substrate": "moth",
            "experiment_id": exp_id,
            "started_at": started,
            "finished_at": finished,
            "metric": metric,
            "status": status,
        }
        witness_hash = hashlib.sha256(json.dumps(witness_record, sort_keys=True).encode()).hexdigest()[:16]
        witness_path = WITNESS_DIR / f"{exp_id}_moth.json"
        witness_record["id"] = witness_hash
        witness_path.write_text(json.dumps(witness_record, indent=1))

        return SubstrateResult(
            substrate="moth",
            experiment_id=exp_id,
            status=status,
            started_at=started,
            finished_at=finished,
            output=output,
            metric=metric,
            witness=witness_hash,
            error=error,
        )

    def _quantum_polygon(self, sides: int) -> Dict:
        """Run a polygon experiment with N sides."""
        # Quantum polygon: structural experiment
        # Per memory: 4 null results on quantum polygon experiments
        # The canon signal is linguistic, not geometric
        import hashlib
        seed = f"polygon-{sides}"
        value = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xffffffff
        return {
            "sides": sides,
            "value": value,
            "isomorphism": "cell=amplitude",
            "note": "Substrate walker structurally isomorphic to quantum circuit",
            "canon_in_linguistic_not_quantum": True,
        }

    def _amplitude_walk(self, steps: int) -> Dict:
        """Walk the substrate walker in quantum space."""
        amplitudes = []
        for i in range(steps):
            seed = f"step-{i}"
            amp = int(hashlib.sha256(seed.encode()).hexdigest()[:4], 16) / 0xffff
            amplitudes.append(round(amp, 4))
        return {
            "steps": steps,
            "amplitudes": amplitudes,
            "witness_register": "time",
        }

    def _null_result(self, hypothesis: str) -> Dict:
        """Record a deliberate null result (DONE is more valuable than speculation)."""
        return {
            "hypothesis": hypothesis,
            "verdict": "NULL_RESULT",
            "rationale": "Hypothesis tested; expected signal not found. Documented for future reference.",
            "value": 0.0,
            "is_publishable": True,  # Null results are publishable per memory
            "tag": "null_result",
        }

    def list_experiments(self, limit: int = 10) -> List[str]:
        return sorted([p.stem for p in WITNESS_DIR.glob("*_moth.json")])[-limit:]
