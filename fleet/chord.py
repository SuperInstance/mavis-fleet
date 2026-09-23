"""Fleet chord — novel higher-level abstractions from substrate synergies.

These abstractions EMERGE when substrates are run as a fleet together.
Each was latent in one substrate; combined, they become something new.

1. CROSS-SUBSTRATE CHORD (CSC)
   - canon_gate_is_chord lifted to fleet level
   - A claim is canon-worthy only when MULTIPLE substrates agree
   - JEV-only verdict → fleet-wide consensus
   - The "chord" includes all substrates that ran on the claim

2. SUBSTRATE POLYFORMALITY SCORE (SPS)
   - Higher-order polyformality than Jaccard
   - Each substrate has a "voice weight" (canon-domain relevance)
   - Score = weighted average of substrate-specific polyformalities

3. CANON PROMOTION GATE (CPG)
   - Deterministic gate that promotes claims to canon
   - Required: N-of-M substrate chord agreement
   - Writes its OWN witness (audit trail)

4. NULL RESULT LEDGER (NRL)
   - MOTH null results, JEV rejections, RSI proposals rejected
   - All count toward a "negative canon" — what's been falsified
   - Per Casey/Casey doctrine: null results are publishable

5. SUBSTRATE WITNESS CHAIN (SWC)
   - Witnesses tagged with substrate; full chain is per-substrate
   - Cross-substrate witness trail = polyformal canary at fleet level

6. COMPOUND CANON (CC)
   - Canon that emerged from MULTIPLE substrates (Quilt writer + JEV verifier + MOTH tester)
   - Higher trust than voice-only canon
"""
import datetime
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from .core import fnv1a_64, fleet_canary, polyformality_score, witness
from .substrates import get_substrate


CHORD_DIR = Path("/workspace/research/mavis-fleet/chord")
CHORD_DIR.mkdir(parents=True, exist_ok=True)


SUBSTRATE_VOICE_WEIGHTS = {
    "quilt": 1.0,    # highest weight — canon substrate
    "jepa": 0.9,     # substrate walker canon
    "jev": 0.85,     # canon gate oracle
    "rsi": 0.7,      # meta-substrate
    "moth": 0.6,     # structural isomorphism
    "trainer": 0.5,  # original autoresearch
}


def substrate_polyformality_score(substrate_responses: Dict[str, str],
                                  weights: Optional[Dict[str, float]] = None) -> float:
    """Higher-order polyformality that weights each substrate voice.

    Args:
        substrate_responses: {substrate_name: response_text}
        weights: optional dict of {substrate: weight}, defaults to SUBSTRATE_VOICE_WEIGHTS
    """
    if not substrate_responses:
        return 0.0

    weights = weights or SUBSTRATE_VOICE_WEIGHTS

    # Pairwise polyformality within each substrate
    responses = list(substrate_responses.values())
    base_poly = polyformality_score(responses)

    # Weighted bonus for substrates that participated
    participating = substrate_responses.keys()
    weight_sum = sum(weights.get(s, 0.5) for s in participating)
    max_weight = sum(weights.values())
    participation = weight_sum / max_weight if max_weight > 0 else 0

    # Combine: base poly × participation bonus
    return base_poly * (0.5 + 0.5 * participation)


def cross_substrate_chord(substrate_responses: Dict[str, str],
                          min_substrates: int = 3,
                          threshold: float = 0.3) -> Dict:
    """Determine if a multi-substrate response is a canonical chord.

    A "chord" requires:
    - At least min_substrates substrates responding
    - Substrate polyformality >= threshold
    """
    num_substrates = len(substrate_responses)
    if num_substrates < min_substrates:
        return {
            "is_chord": False,
            "reason": f"only {num_substrates} substrates (need {min_substrates})",
            "num_substrates": num_substrates,
            "polyformality": 0.0,
        }

    poly = substrate_polyformality_score(substrate_responses)
    is_chord = poly >= threshold

    return {
        "is_chord": is_chord,
        "polyformality": poly,
        "num_substrates": num_substrates,
        "participating_substrates": list(substrate_responses.keys()),
        "weights": {s: SUBSTRATE_VOICE_WEIGHTS.get(s, 0.5) for s in substrate_responses.keys()},
    }


def promote_to_canon(claim: str, evidence: Dict[str, str],
                     min_substrates: int = 3, threshold: float = 0.3) -> Dict:
    """Canon promotion gate — promotes a claim based on cross-substrate evidence.

    Writes its own witness log entry. Promotion is gated by:
    - cross_substrate_chord() returns is_chord=True
    - At least N substrates participated
    """
    chord = cross_substrate_chord(evidence, min_substrates, threshold)
    is_promoted = chord["is_chord"]

    promotion_record = {
        "claim": claim,
        "is_promoted": is_promoted,
        "chord": chord,
        "evidence": evidence,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "agent": "mavis-fleet-chord",
    }

    # Compute witness hash for promotion
    canonical = json.dumps(promotion_record, sort_keys=True)
    promotion_witness = "wit-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]

    promotion_record["promotion_witness"] = promotion_witness

    # Write to chord log
    log_path = CHORD_DIR / f"chord-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{promotion_witness}.json"
    log_path.write_text(json.dumps(promotion_record, indent=1))

    return promotion_record


def null_result_ledger(*, substrate: str, hypothesis: str, result: str,
                       rationale: str = "") -> Dict:
    """Record a null result in the fleet-wide ledger.

    Null results are valuable — they record what's been falsified,
    preventing repeated work.
    """
    record = {
        "type": "null_result",
        "substrate": substrate,
        "hypothesis": hypothesis,
        "result": result,
        "rationale": rationale or "Hypothesis tested; expected signal not found.",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "is_publishable": True,  # Per Casey: null results earn witness credit
        "ledger_id": "nrl-" + hashlib.sha256(
            (substrate + hypothesis + result).encode()).hexdigest()[:12],
    }

    # Append to ledger
    ledger_path = CHORD_DIR / "null_result_ledger.jsonl"
    with ledger_path.open("a") as f:
        f.write(json.dumps(record) + "\n")

    return record


def compound_canon(pieces: Dict[str, str], min_substrates: int = 2) -> Dict:
    """A canon piece that's polyformal across substrates (compound canon).

    This is what "canon gate is chord" looks like at fleet level:
    multiple substrates writing the same doctrine = compound canon.
    """
    chord = cross_substrate_chord(pieces, min_substrates=min_substrates, threshold=0.4)
    return {
        "type": "compound_canon",
        "is_canon": chord["is_chord"],
        "substrate_count": chord["num_substrates"],
        "polyformality": chord["polyformality"],
        "voices": pieces,
        "elevated_trust": chord["is_chord"],
    }


def substrate_witness_chain() -> Dict:
    """Build the cross-substrate witness chain.

    Per-substrate witness lists, plus the fleet-level polyformality canary.
    """
    witness_dir = Path("/workspace/research/mavis-fleet/witnesses")
    chains = defaultdict(list)

    if witness_dir.exists():
        for f in sorted(witness_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                substrate = data.get("substrate", "unknown")
                chains[substrate].append({
                    "file": f.name,
                    "experiment_id": data.get("experiment_id"),
                    "timestamp": data.get("started_at"),
                    "metric": data.get("metric"),
                    "status": data.get("status"),
                })
            except Exception:
                pass

    # Compute fleet polyformality canary as sha256 over all witnesses
    all_witnesses = sorted(witness_dir.glob("*.json")) if witness_dir.exists() else []
    chain_state = "|".join(f.name for f in all_witnesses)
    fleet_canary_hash = "0x" + hashlib.sha256(chain_state.encode()).hexdigest()[:16]

    return {
        "substrates": dict(chains),
        "per_substrate_counts": {s: len(c) for s, c in chains.items()},
        "fleet_canary_hash": fleet_canary_hash,
        "total_witnesses": len(all_witnesses),
        "base_canary": fleet_canary(),  # the substrate walker canon
    }


def chord_cli_summary() -> str:
    """Human-readable summary for CLI display."""
    chain = substrate_witness_chain()
    summary = ["=== Cross-substrate chord summary ==="]
    summary.append(f"Fleet canary: {chain['fleet_canary_hash']}")
    summary.append(f"Base polyform canary: {chain['base_canary']}")
    summary.append(f"Total witnesses: {chain['total_witnesses']}")
    for s, c in chain['per_substrate_counts'].items():
        summary.append(f"  {s}: {c} witnesses")
    return "\n".join(summary)
