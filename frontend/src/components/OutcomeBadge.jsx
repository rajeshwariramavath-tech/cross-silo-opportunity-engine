export default function OutcomeBadge({ outcome }) {
  return <span className={`outcome-badge ${outcome}`}>{outcome.replace(/_/g, " ")}</span>;
}
