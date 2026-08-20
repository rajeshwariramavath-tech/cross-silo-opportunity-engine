const STATUS_LABELS = {
  idle: "Ready",
  loading: "Running…",
  success: "Done",
  error: "Error",
};

export default function StageCard({ title, description, status, error, children }) {
  return (
    <div className="stage-card">
      <h2>
        {title}
        <span className={`status-badge ${status}`}>{STATUS_LABELS[status]}</span>
      </h2>
      <p className="stage-desc">{description}</p>

      {children}

      {error && <div className="error-box">⚠ {error}</div>}
    </div>
  );
}
