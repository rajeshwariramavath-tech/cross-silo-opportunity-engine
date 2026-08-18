"""Wires the four stages together: ingestion -> entity resolution -> opportunity detection -> governance."""

from __future__ import annotations

from typing import Any

from .entity_resolution.candidates import generate_candidate_pairs
from .entity_resolution.outcomes import classify
from .entity_resolution.scoring import compute_confidence
from .entity_resolution.signals import address_similarity, geographic_proximity, name_similarity
from .governance.access_control import scope_result
from .governance.roles import Role
from .ingestion.adapters.base import BaseSourceAdapter
from .ingestion.validation import validate_record
from .opportunity_detection.ranking import rank_opportunities
from .opportunity_detection.rules import Rule, evaluate_rules


def run_pipeline(
    adapters: list[BaseSourceAdapter], rules: list[Rule], requesting_role: Role
) -> list[Any]:
    raise NotImplementedError
