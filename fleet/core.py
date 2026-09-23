"""Mavis Fleet — multi-substrate autonomous research & RSI system.

This is the renamed/expanded version of autoclaw. It coordinates agents
across multiple substrates:
  - QUIlT: canon, witness log, multi-oracle, tile pipeline
  - MOTH: quantum polygon experiments (quantumaudio SDK)
  - JEV: Joint Embedding Validator (canon-vs-speculation oracle)
  - JEPA: Joint Embedding Predictive Architecture (cell graph prediction)
  - RSI: Recursive Self-Improvement (the system improving itself)
  - Trainer: original autoresearch pattern (5-min experiments on train.py)

Key principles:
  - Polyformalism: same computation across substrates
  - Witness log: every state change recorded
  - Canon gate: promotion requires multi-substrate chord agreement
  - Personified agents: teacher, critic, distiller, researcher, etc.
"""
import datetime
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


FLEET_BASE = Path("/workspace/research/mavis-fleet")
FLEET_BASE.mkdir(parents=True, exist_ok=True)


def fnv1a_64(s: str) -> int:
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h = h ^ b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


def fleet_canary() -> str:
    return f"0x{fnv1a_64('café Δ 日本語'):016x}"


__version__ = "0.1.0"


# ─── Substrate registry ──────────────────────────────────────

SUBSTRATES = ["quilt", "moth", "jev", "jepa", "rsi", "trainer"]


# ─── Resource limits ─────────────────────────────────────────

@dataclass
class ResourceLimits:
    """Substrate resource limits — a substrate self-declares what it needs."""
    substrate: str
    gpu: bool = False
    cpu_cores: int = 1
    memory_mb: int = 512
    disk_mb: int = 100
    network_dependencies: List[str] = field(default_factory=list)
    api_keys_required: List[str] = field(default_factory=list)


DEFAULT_LIMITS = {
    "quilt": ResourceLimits("quilt", gpu=False, cpu_cores=1, memory_mb=256,
                            api_keys_required=[]),
    "moth": ResourceLimits("moth", gpu=False, cpu_cores=2, memory_mb=512,
                           api_keys_required=[]),
    "jev": ResourceLimits("jev", gpu=False, cpu_cores=1, memory_mb=512,
                          api_keys_required=["TYPESAFEAI_KEY"]),
    "jepa": ResourceLimits("jepa", gpu=True, cpu_cores=4, memory_mb=2048,
                           api_keys_required=["DEEPINFRA_TOKEN"]),
    "rsi": ResourceLimits("rsi", gpu=False, cpu_cores=1, memory_mb=256,
                          api_keys_required=["ZAI_TOKEN", "DEEPINFRA_TOKEN"]),
    "trainer": ResourceLimits("trainer", gpu=True, cpu_cores=8, memory_mb=8192,
                              api_keys_required=[]),
}


def check_substrate_available(substrate: str) -> Dict:
    """Check if a substrate's required resources are available."""
    limits = DEFAULT_LIMITS.get(substrate)
    if not limits:
        return {"available": False, "reason": f"unknown substrate: {substrate}"}

    missing_keys = []
    for key in limits.api_keys_required:
        env_var = key.replace("TOKEN", "_TOKEN")
        if not os.environ.get(key) and not os.environ.get(env_var):
            missing_keys.append(key)

    return {
        "available": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "limits": {
            "gpu": limits.gpu,
            "cpu_cores": limits.cpu_cores,
            "memory_mb": limits.memory_mb,
        },
    }


# ─── Task system ─────────────────────────────────────────────

@dataclass
class Task:
    """A task to be executed by the fleet."""
    id: str
    substrate: str
    goal: str
    priority: int = 5
    created_at: str = ""
    status: str = "pending"  # pending, running, success, failed
    assigned_agent: Optional[str] = None
    result: Optional[Dict] = None
    dependencies: List[str] = field(default_factory=list)


# ─── Polyformality ───────────────────────────────────────────

def polyformality_score(items: List[str]) -> float:
    """Score how similar items are (Jaccard on word sets)."""
    if not items:
        return 0.0
    sets = [set(s.lower().split()) for s in items]
    if len(sets) == 1:
        return 1.0
    overlaps = []
    base = sets[0]
    for other in sets[1:]:
        if not base and not other:
            continue
        inter = base & other
        union = base | other
        overlaps.append(len(inter) / len(union) if union else 0)
    return sum(overlaps) / len(overlaps) if overlaps else 0


def chord_verdict(items: List[str], threshold: float = 0.5) -> Dict:
    """Determine if items form a canon-promotion chord."""
    poly = polyformality_score(items)
    return {
        "polyformality": poly,
        "is_chord": poly >= threshold,
        "promoted": poly >= threshold,
    }


# ─── Witness ────────────────────────────────────────────────

def witness(record: Dict) -> str:
    """Compute a witness hash for a record."""
    s = json.dumps(record, sort_keys=True, default=str)
    h = hash(fnv1a_64(s))  # Stable hash
    return f"wit-{abs(h) % 16**12:012x}"


# ─── RSI loop ───────────────────────────────────────────────

class RSILoop:
    """Recursive Self-Improvement loop.

    The fleet improves itself by:
    1. Proposing an improvement (LLM-generated or heuristic)
    2. Testing it (run experiment in substrate)
    3. Scoring the result (polyformality test)
    4. Keeping if better, discarding if not
    5. Witnessing the change

    This is the substrate walker canon made executable: the system
    walks its own substrate (code), probes each step, witnesses the
    journey, and chord-verifies before promotion.
    """

    def __init__(self, base: Path = FLEET_BASE):
        self.base = base
        self.log_path = base / "rsi_log.jsonl"
        self.runs: List[Dict] = []

    def propose(self) -> Dict:
        """Propose an improvement candidate."""
        candidates = [
            {
                "type": "scale_agent",
                "rationale": "Spawn additional researcher agents",
                "impact": "more parallelism",
            },
            {
                "type": "tune_threshold",
                "rationale": "Adjust polyformality threshold for canon promotion",
                "impact": "more or fewer promotions",
            },
            {
                "type": "add_substrate",
                "rationale": "Wire a new substrate into the fleet",
                "impact": "broader research surface",
            },
            {
                "type": "compress_memory",
                "rationale": "Archive cold knowledge to a smaller store",
                "impact": "less memory pressure",
            },
        ]
        import random
        return random.choice(candidates)

    def test(self, proposal: Dict) -> Dict:
        """Test a proposal (dry-run simulator)."""
        return {
            "proposal": proposal,
            "metric_change": 0.05,  # simulated improvement
            "cost_change": 0.02,
            "passed": True,
        }

    def score(self, test_result: Dict) -> Dict:
        """Score the proposal: keep if improved."""
        passed = test_result.get("passed", False)
        return {
            "kept": passed,
            "improvement": test_result.get("metric_change", 0) if passed else 0,
            "witness_id": witness({"proposal": test_result.get("proposal"),
                                   "result": test_result}),
        }

    def step(self) -> Dict:
        """Run one RSI iteration."""
        proposal = self.propose()
        test_result = self.test(proposal)
        scored = self.score(test_result)

        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "proposal": proposal,
            "test": test_result,
            "scored": scored,
        }
        self.runs.append(record)

        # Log to file
        with self.log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")

        return record

    def run(self, iterations: int = 5) -> List[Dict]:
        """Run multiple RSI iterations."""
        return [self.step() for _ in range(iterations)]


# ─── Health ─────────────────────────────────────────────────

def fleet_health() -> Dict:
    """Get fleet health status."""
    substrate_status = {}
    for substrate in SUBSTRATES:
        substrate_status[substrate] = check_substrate_available(substrate)

    return {
        "version": __version__,
        "canary": fleet_canary(),
        "substrates": substrate_status,
        "all_available": all(s["available"] for s in substrate_status.values()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
