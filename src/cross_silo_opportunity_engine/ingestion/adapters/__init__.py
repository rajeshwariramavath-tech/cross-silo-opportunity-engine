"""Per-source-system adapter implementations - one CSV adapter and one API adapter per source,
both producing identical CanonicalRecords so the rest of the pipeline can't tell them apart.

Only the CSV adapters are imported here. The API adapters (api_adapters.py) depend on
`requests`, which is an optional extra (`pip install -e ".[api]"`) - import them directly from
cross_silo_opportunity_engine.ingestion.adapters.api_adapters so a core install never needs it.
"""

from .csv_adapters import DebtCSVAdapter, SalesCSVAdapter

__all__ = ["SalesCSVAdapter", "DebtCSVAdapter"]
