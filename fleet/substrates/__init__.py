"""Substrate registry for the fleet."""
from .base import Substrate, SubstrateResult
from .quilt import QuiltSubstrate
from .moth import MOTHSubstrate
from .jev import JEVSubstrate
from .jepa import JEPASubstrate
from .trainer import TrainerSubstrate
from .rsi import RSISubstrate
from .reconciler import Reconciler, ReconcileState, ReconcileResult


SUBSTRATE_CLASSES = {
    "quilt": QuiltSubstrate,
    "moth": MOTHSubstrate,
    "jev": JEVSubstrate,
    "jepa": JEPASubstrate,
    "rsi": RSISubstrate,
    "trainer": TrainerSubstrate,
    "reconciler": Reconciler,
}


def get_substrate(name: str) -> Substrate:
    """Get a substrate instance by name."""
    cls = SUBSTRATE_CLASSES.get(name)
    if not cls:
        raise ValueError(f"unknown substrate: {name}")
    return cls()


def list_substrates() -> list:
    return list(SUBSTRATE_CLASSES.keys())
