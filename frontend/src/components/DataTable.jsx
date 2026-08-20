function prettifyLabel(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "number") return String(value);
  return String(value);
}

/**
 * Generic table: pass `columns` as an array of strings (plain field keys) or
 * { key, label?, render? } objects for custom formatting. Omit `columns` to derive them
 * from the keys of the first row - used by the governance stage, where the field set
 * genuinely differs by role and shouldn't be hardcoded here.
 */
export default function DataTable({ rows, columns }) {
  if (!rows || rows.length === 0) {
    return <p className="row-count-note">No rows returned.</p>;
  }

  const cols = (columns || Object.keys(rows[0])).map((c) => (typeof c === "string" ? { key: c } : c));

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c.key}>{c.label || prettifyLabel(c.key)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c.key}>{c.render ? c.render(row) : formatValue(row[c.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
