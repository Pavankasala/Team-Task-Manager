import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import StatsCard from '../components/StatsCard';
import TaskCard from '../components/TaskCard';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard')
      .then(res => setStats(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loader"><div className="spinner"></div></div>;
  if (!stats) return <p className="text-center">Failed to load dashboard.</p>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <Link to="/projects" className="btn-primary">+ New Project</Link>
      </div>

      <div className="stats-grid">
        <StatsCard icon="📊" label="Total Tasks" count={stats.total_tasks} color="#6366f1" />
        <StatsCard icon="📝" label="To Do" count={stats.todo_count} color="#8b5cf6" />
        <StatsCard icon="⚡" label="In Progress" count={stats.in_progress_count} color="#f59e0b" />
        <StatsCard icon="✅" label="Done" count={stats.done_count} color="#10b981" />
        <StatsCard icon="🔥" label="Overdue" count={stats.overdue_count} color="#ef4444" />
        <StatsCard icon="📁" label="Projects" count={stats.total_projects} color="#3b82f6" />
      </div>

      <div className="section">
        <h2>Recent Tasks</h2>
        {stats.recent_tasks.length === 0 ? (
          <div className="empty-state">
            <p>No tasks yet. <Link to="/projects">Create a project</Link> to get started!</p>
          </div>
        ) : (
          <div className="task-grid">
            {stats.recent_tasks.map(t => <TaskCard key={t.id} task={t} />)}
          </div>
        )}
      </div>
    </div>
  );
}
