"""Combined test runner: core tests + chord tests."""
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent

print("=" * 60)
print("MAVIS-FLEET — COMPREHENSIVE TESTS")
print("=" * 60)

# Run core tests
print("\n[1/2] Core tests:")
result = subprocess.run(
    [sys.executable, str(THIS_DIR / "run_core_tests.py")],
    capture_output=True, text=True, timeout=60,
)
print(result.stdout)
if result.returncode != 0:
    print(f"Core tests stderr: {result.stderr}")
    print("CORE TESTS FAILED")
    sys.exit(1)

# Run chord tests
print("\n[2/2] Chord tests (higher-level abstractions):")
sys.path.insert(0, str(THIS_DIR))

from fleet import fleet_canary
from fleet.chord import (
    substrate_polyformality_score, cross_substrate_chord,
    promote_to_canon, null_result_ledger, compound_canon,
    substrate_witness_chain, chord_cli_summary, SUBSTRATE_VOICE_WEIGHTS,
)

results = []
failures = []

def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


def t_sps_identical():
    res = {"quilt": "the substrate walker canon: every chord is canon",
           "jepa": "the substrate walker canon: every chord is canon"}
    assert substrate_polyformality_score(res) > 0.5

def t_sps_different():
    res = {"quilt": "the substrate walker canon doctrine",
           "jepa": "completely different vocabulary entirely"}
    assert substrate_polyformality_score(res) < 0.5

def t_sps_weights():
    res_with = {"quilt": "shared words canon", "jepa": "shared words canon"}
    res_without = {"jepa": "shared words canon", "trainer": "shared words canon"}
    s1 = substrate_polyformality_score(res_with)
    s2 = substrate_polyformality_score(res_without)
    assert s1 >= s2

def t_csc_min_substrates():
    res = {"quilt": "shared text"}
    chord = cross_substrate_chord(res, min_substrates=3)
    assert not chord["is_chord"]

def t_csc_meets_threshold():
    res = {"quilt": "the substrate walker is doctrine",
           "jepa": "the substrate walker is doctrine",
           "jev": "the substrate walker is doctrine"}
    chord = cross_substrate_chord(res, min_substrates=3, threshold=0.3)
    assert chord["is_chord"]

def test_promote_to_canon():
    evidence = {"quilt": "the cells are scars",
                "jepa": "every scar is a witness log entry",
                "jev": "refusal is also a witness"}
    result = promote_to_canon("every cell is a scar", evidence, min_substrates=2, threshold=0.2)
    assert "promotion_witness" in result
    assert "is_promoted" in result

def test_promote_rejects():
    result = promote_to_canon("x", {"quilt": "alone"}, min_substrates=3)
    assert not result["is_promoted"]

def test_null_result_ledger():
    record = null_result_ledger(
        substrate="moth",
        hypothesis="quantum polygon experiments canon-promote at N=8",
        result="NULL",
        rationale="Tested 4 polygon configurations.",
    )
    assert record["is_publishable"]

def test_compound_canon():
    pieces = {"quilt": "every chord is canon in disguise — agreement is canonical",
              "jepa": "every chord is canon in disguise — agreement is canonical",
              "jev": "every chord is canon: agreement is canonical"}
    cc = compound_canon(pieces)
    assert cc["substrate_count"] == 3

def test_substrate_witness_chain():
    chain = substrate_witness_chain()
    assert "fleet_canary_hash" in chain
    assert chain["base_canary"] == "0x24a555471370b18d"

def t_chord_cli_summary():
    summary = chord_cli_summary()
    assert "Cross-substrate chord" in summary

def t_voice_weights():
    assert SUBSTRATE_VOICE_WEIGHTS["quilt"] > SUBSTRATE_VOICE_WEIGHTS["trainer"]

test("test_sps_identical", t_sps_identical)
test("test_sps_different", t_sps_different)
test("test_sps_weights", t_sps_weights)
test("test_csc_min_substrates", t_csc_min_substrates)
test("test_csc_meets_threshold", t_csc_meets_threshold)
test("test_promote_to_canon", test_promote_to_canon)
test("test_promote_rejects", test_promote_rejects)
test("test_null_result_ledger", test_null_result_ledger)
test("test_compound_canon", test_compound_canon)
test("test_substrate_witness_chain", test_substrate_witness_chain)
test("test_chord_cli_summary", t_chord_cli_summary)
test("test_voice_weights", t_voice_weights)

print()
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n  {len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSING ✓")
print("=" * 60)
