export default function StatsCard({ icon, label, count, color }) {
  return (
    <div className="stats-card" style={{ '--accent': color }}>
      <div className="stats-icon">{icon}</div>
      <div className="stats-info">
        <span className="stats-count">{count}</span>
        <span className="stats-label">{label}</span>
      </div>
    </div>
  );
}
