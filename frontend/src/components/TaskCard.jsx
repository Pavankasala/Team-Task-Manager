export default function TaskCard({ task, onStatusChange, onDelete }) {
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'Done';
  const statusColors = { 'To Do': '#6366f1', 'In Progress': '#f59e0b', 'Done': '#10b981' };
  const priorityColors = { Low: '#6b7280', Medium: '#3b82f6', High: '#ef4444' };

  return (
    <div className={`task-card ${isOverdue ? 'overdue' : ''}`}>
      <div className="task-header">
        <h4 className="task-title">{task.title}</h4>
        {onDelete && <button className="btn-icon" onClick={() => onDelete(task.id)} title="Delete">✕</button>}
      </div>
      {task.description && <p className="task-desc">{task.description}</p>}
      <div className="task-meta">
        <span className="badge" style={{ background: statusColors[task.status] || '#6366f1' }}>
          {task.status}
        </span>
        <span className="badge" style={{ background: priorityColors[task.priority] || '#3b82f6' }}>
          {task.priority}
        </span>
      </div>
      <div className="task-footer">
        {task.assignee_name && <span className="task-assignee">👤 {task.assignee_name}</span>}
        {task.due_date && (
          <span className={`task-due ${isOverdue ? 'text-red' : ''}`}>
            📅 {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
      </div>
      {onStatusChange && (
        <select className="status-select" value={task.status} onChange={(e) => onStatusChange(task.id, e.target.value)}>
          <option>To Do</option>
          <option>In Progress</option>
          <option>Done</option>
        </select>
      )}
    </div>
  );
}