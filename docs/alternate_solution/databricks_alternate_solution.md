## Alternate implementation: Databricks lakehouse architecture

The same design can also be implemented natively on Databricks. Three processing stages handle ingestion, entity resolution, and opportunity detection, and governance operates as a continuous boundary around them. The responsibilities and the governance-first principle stay the same — what changes is where each stage runs and how the boundary is enforced.

![Databricks lakehouse architecture](databricks_flowdiagram.png)

## Ingestion & normalization

Each source lands as a bronze Delta table via Auto Loader, and the normalization and validation logic becomes a Delta Live Tables transformation into a silver canonical table — the same field-mapping and address/entity-name normalization, with DLT's built-in data quality expectations handling invalid records natively instead of a separate reject file.

## Entity resolution

 Both canonical tables are partitioned by a blocking key (postal code, for example) so that only records already likely to be the same entity get compared, and the similarity scoring runs as a Spark join within each partition. The same three-outcome model — auto-match, review queue, auto-reject — carries over unchanged.

## Opportunity detection

The same rules (maturity window, minimum value, relationship strength) translate directly into Spark SQL over the resolved-match table, writing ranked opportunities to a gold table. The optional LLM rationale step runs as batch inference over just the records that passed the rule stage.

## Governance as a boundary

 Role-based field scoping becomes a Unity Catalog dynamic view sitting over the bronze, silver, and gold tables alike, masking columns based on the querying user's group membership. Enforcement is continuous, applied by the catalog itself on every query against any of the three stages' tables, regardless of what tool or user issues it. Lineage is native to Unity Catalog for the same reason: tracked automatically from bronze onward.

## Orchestration & output

The three processing stages run as a Databricks Workflow, one task per stage with its own retry policy and failure alerting. Unity Catalog enforces governance on every read, whether that read comes from the workflow, an analyst's ad hoc query, or the dashboard. The final output is an AI/BI dashboard querying the governed views directly — the dashboard itself never needs its own access-control logic, since it inherits whatever the querying user is entitled to see.

The point of laying this out: the same design — canonical schema, confidence-scored matching, rule-based detection, and governance as a continuous boundary around the pipeline — holds up cleanly whether it's running as a lightweight standalone pipeline or a production lakehouse. On Databricks, that boundary is enforced by the platform itself, on every stage's data, for every consumer.