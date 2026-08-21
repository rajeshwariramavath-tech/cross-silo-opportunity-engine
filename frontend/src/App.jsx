import { useState } from "react";
import "./index.css";
import { api } from "./api";
import StageCard from "./components/StageCard";
import DataTable from "./components/DataTable";
import OutcomeBadge from "./components/OutcomeBadge";

const ROLES = ["admin", "broker", "financing", "valuation", "property_management"];
const BATCH_SIZE = 10;

const TABS = [
  { number: 1, label: "Ingestion" },
  { number: 2, label: "Entity Resolution" },
  { number: 3, label: "Opportunity Detection" },
  { number: 4, label: "Access Data" },
];

const initialStage = { status: "idle", error: null };

export default function App() {
  const [activeTab, setActiveTab] = useState(1);

  const [stage1, setStage1] = useState({
    ...initialStage,
    rawCounts: null,
    counts: null,
    canonicalRecords: [],
    batchOffset: 0,
  });
  const [cursor, setCursor] = useState(0);
  const [stage2, setStage2] = useState({ ...initialStage, pairCount: 0, matches: [] });
  const [stage3, setStage3] = useState({ ...initialStage, opportunities: [] });
  const [stage4, setStage4] = useState({ ...initialStage, role: "financing", opportunities: [] });

  const stage1Done = stage1.status === "success";
  const stage2Done = stage2.status === "success";
  const stage3Done = stage3.status === "success";

  const stageStatus = { 1: stage1.status, 2: stage2.status, 3: stage3.status, 4: stage4.status };
  const stageUnlocked = { 1: true, 2: stage1Done, 3: stage2Done, 4: stage3Done };

  async function runIngest() {
    setStage1((s) => ({ ...s, status: "loading", error: null }));
    try {
      let offset = cursor;
      let [sales, debt] = await Promise.all([
        api.salesRecords(BATCH_SIZE, offset),
        api.debtRecords(BATCH_SIZE, offset),
      ]);

      // Ran past the end of both sources - circle back to the start of the dataset.
      if (offset > 0 && sales.length === 0 && debt.length === 0) {
        offset = 0;
        [sales, debt] = await Promise.all([api.salesRecords(BATCH_SIZE, offset), api.debtRecords(BATCH_SIZE, offset)]);
      }

      const result = await api.ingest(BATCH_SIZE, offset);
      setStage1({
        status: "success",
        error: null,
        rawCounts: { sales: sales.length, debt: debt.length },
        counts: { canonical: result.canonical_record_count, rejected: result.rejected_count },
        canonicalRecords: result.canonical_records,
        batchOffset: offset,
      });
      setCursor(offset + BATCH_SIZE);
    } catch (err) {
      setStage1((s) => ({ ...s, status: "error", error: err.message }));
    }
  }

  async function runResolveEntities() {
    setStage2((s) => ({ ...s, status: "loading", error: null }));
    try {
      const result = await api.resolveEntities();
      setStage2({ status: "success", error: null, pairCount: result.pair_count, matches: result.matches });
    } catch (err) {
      setStage2((s) => ({ ...s, status: "error", error: err.message }));
    }
  }

  async function runDetectOpportunities() {
    setStage3((s) => ({ ...s, status: "loading", error: null }));
    try {
      const result = await api.detectOpportunities();
      setStage3({ status: "success", error: null, opportunities: result.opportunities });
    } catch (err) {
      setStage3((s) => ({ ...s, status: "error", error: err.message }));
    }
  }

  async function runGovernance() {
    setStage4((s) => ({ ...s, status: "loading", error: null }));
    try {
      const result = await api.opportunitiesForRole(stage4.role);
      setStage4((s) => ({ ...s, status: "success", error: null, opportunities: result.opportunities }));
    } catch (err) {
      setStage4((s) => ({ ...s, status: "error", error: err.message }));
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Cross-Silo Opportunity Engine</h1>
        <p>
          Connecting sales and debt records across siloed commercial real estate lines of
          business - one pipeline, three stages plus governed access, walked step by step.
        </p>
        <div className="rule" />
      </header>

      <nav className="tab-bar">
        {TABS.map((tab) => {
          const unlocked = stageUnlocked[tab.number];
          return (
            <button
              key={tab.number}
              type="button"
              className={`tab ${activeTab === tab.number ? "active" : ""} ${unlocked ? "" : "locked"}`}
              disabled={!unlocked}
              onClick={() => setActiveTab(tab.number)}
            >
              <span className="tab-number">{tab.number}</span>
              <span className="tab-label">{tab.label}</span>
              {stageStatus[tab.number] === "success" && <span className="tab-check">✓</span>}
            </button>
          );
        })}
      </nav>

      <div className="tab-panel">
        {activeTab === 1 && (
          <StageCard
            title="Ingestion & Normalization"
            description="Reads a batch of raw rows from each source system and normalizes them into one canonical schema. Each click advances to the next batch, and cycles back to the start once the dataset is exhausted."
            status={stage1.status}
            error={stage1.error}
          >
            <div className="controls-row">
              <button className="btn" onClick={runIngest} disabled={stage1.status === "loading"}>
                {stage1.status === "loading" ? "Ingesting…" : "Run Next Batch"}
              </button>
              <span className="hint-text">
                Next click processes rows {cursor + 1}–{cursor + BATCH_SIZE} from each source.
              </span>
            </div>

            {stage1.rawCounts && (
              <div className="summary-row">
                <span className="summary-stat">
                  <strong>{stage1.rawCounts.sales}</strong> raw sales rows (from row{" "}
                  {stage1.batchOffset + 1})
                </span>
                <span className="summary-stat">
                  <strong>{stage1.rawCounts.debt}</strong> raw debt rows (from row{" "}
                  {stage1.batchOffset + 1})
                </span>
                <span className="summary-stat">
                  <strong>{stage1.counts.canonical}</strong> canonical records
                </span>
                <span className="summary-stat">
                  <strong>{stage1.counts.rejected}</strong> rejected
                </span>
              </div>
            )}

            {stage1.canonicalRecords.length > 0 && (
              <DataTable
                rows={stage1.canonicalRecords}
                columns={[
                  "source_system",
                  "source_record_id",
                  "entity_type",
                  "entity_name",
                  "address_line1",
                  "city",
                  "state",
                  "postal_code",
                ]}
              />
            )}
          </StageCard>
        )}

        {activeTab === 2 && (
          <StageCard
            title="Entity Resolution"
            description="Scores every zip-blocked Sales/Debt candidate pair and routes each to auto-match, review queue, or auto-reject."
            status={stage2.status}
            error={stage2.error}
          >
            <div className="controls-row">
              <button
                className="btn"
                onClick={runResolveEntities}
                disabled={!stage1Done || stage2.status === "loading"}
              >
                {stage2.status === "loading" ? "Resolving…" : "Run entity resolution"}
              </button>
            </div>

            {stage2.matches.length > 0 && (
              <>
                <div className="summary-row">
                  <span className="summary-stat">
                    <strong>{stage2.pairCount}</strong> pairs scored
                  </span>
                </div>
                <DataTable
                  rows={stage2.matches}
                  columns={[
                    { key: "entity_name_a", label: "Sales Entity" },
                    { key: "entity_name_b", label: "Debt Entity" },
                    { key: "address_similarity", render: (r) => r.address_similarity.toFixed(2) },
                    { key: "name_similarity", render: (r) => r.name_similarity.toFixed(2) },
                    { key: "confidence", render: (r) => r.confidence.toFixed(2) },
                    { key: "outcome", render: (r) => <OutcomeBadge outcome={r.outcome} /> },
                  ]}
                />
              </>
            )}
          </StageCard>
        )}

        {activeTab === 3 && (
          <StageCard
            title="Opportunity Detection"
            description="Runs the auto-matched pairs through deterministic business rules and ranks the qualifying opportunities."
            status={stage3.status}
            error={stage3.error}
          >
            <div className="controls-row">
              <button
                className="btn"
                onClick={runDetectOpportunities}
                disabled={!stage2Done || stage3.status === "loading"}
              >
                {stage3.status === "loading" ? "Detecting…" : "Run opportunity detection"}
              </button>
            </div>

            {stage3.opportunities.length > 0 && (
              <>
                <div className="summary-row">
                  <span className="summary-stat">
                    <strong>{stage3.opportunities.length}</strong> qualifying opportunities
                  </span>
                </div>
                <DataTable
                  rows={stage3.opportunities}
                  columns={[
                    "entity_name",
                    "property_type",
                    { key: "sale_price", render: (r) => r.sale_price || "—" },
                    { key: "loan_amount", render: (r) => r.loan_amount || "—" },
                    { key: "fired_rules", render: (r) => r.fired_rules.join(", ") },
                    "composite_score",
                  ]}
                />
              </>
            )}
          </StageCard>
        )}

        {activeTab === 4 && (
          <StageCard
            title="Access Data"
            description="Runs the full pipeline end to end and scopes the opportunity list to the role you pick - the same data, rendered differently."
            status={stage4.status}
            error={stage4.error}
          >
            <div className="controls-row">
              <select
                className="role-select"
                value={stage4.role}
                onChange={(e) => setStage4((s) => ({ ...s, role: e.target.value }))}
                disabled={!stage3Done}
              >
                {ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <button
                className="btn"
                onClick={runGovernance}
                disabled={!stage3Done || stage4.status === "loading"}
              >
                {stage4.status === "loading" ? "Loading…" : `View as ${stage4.role}`}
              </button>
            </div>

            {stage4.opportunities.length > 0 && (
              <>
                <div className="summary-row">
                  <span className="summary-stat">
                    <strong>{stage4.opportunities.length}</strong> opportunities scoped to{" "}
                    <strong>{stage4.role}</strong>
                  </span>
                </div>
                <DataTable rows={stage4.opportunities} />
              </>
            )}
          </StageCard>
        )}
      </div>
    </div>
  );
}
