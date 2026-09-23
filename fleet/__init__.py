"""mavis-fleet — multi-substrate autonomous research & RSI system."""

__version__ = "0.1.0"

from .core import (
    fleet_canary, fleet_health, SUBSTRATES,
    polyformality_score, chord_verdict, witness,
    RSILoop, ResourceLimits, DEFAULT_LIMITS,
    check_substrate_available,
)
from .substrates import (
    Substrate, SubstrateResult,
    QuiltSubstrate, MOTHSubstrate, JEVSubstrate,
    JEPASubstrate, TrainerSubstrate, RSISubstrate,
    get_substrate, list_substrates, SUBSTRATE_CLASSES,
)
from .agents import (
    Agent, AGENT_ROLES, AGENT_CLASSES,
    get_agent, list_agents,
)
from .bus import MessageBus
from .scheduler import Scheduler
from .chord import (
    substrate_polyformality_score, cross_substrate_chord,
    promote_to_canon, null_result_ledger, compound_canon,
    substrate_witness_chain, chord_cli_summary,
    SUBSTRATE_VOICE_WEIGHTS,
)


__all__ = [
    "__version__", "fleet_canary", "fleet_health", "SUBSTRATES",
    "polyformality_score", "chord_verdict", "witness", "RSILoop",
    "Substrate", "SubstrateResult", "get_substrate", "list_substrates",
    "Agent", "AGENT_ROLES", "get_agent", "list_agents",
    "MessageBus", "Scheduler",
    "substrate_polyformality_score", "cross_substrate_chord",
    "promote_to_canon", "null_result_ledger", "compound_canon",
    "substrate_witness_chain", "chord_cli_summary",
]
