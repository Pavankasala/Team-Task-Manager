import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchProjects = () => {
    api.get('/projects').then(res => setProjects(res.data)).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post('/projects', { title, description: desc });
      setTitle(''); setDesc(''); setShowForm(false);
      fetchProjects();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this project and all its tasks?')) return;
    try { await api.delete(`/projects/${id}`); fetchProjects(); } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  if (loading) return <div className="page-loader"><div className="spinner"></div></div>;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Projects</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card form-card">
          <div className="form-group">
            <label>Project Title</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="My Awesome Project" required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} placeholder="What's this project about?" rows={3} />
          </div>
          <button type="submit" className="btn-primary" disabled={creating}>{creating ? 'Creating...' : 'Create Project'}</button>
        </form>
      )}

      {projects.length === 0 ? (
        <div className="empty-state">
          <h3>No projects yet</h3>
          <p>Create your first project to start managing tasks!</p>
        </div>
      ) : (
        <div className="project-grid">
          {projects.map(p => (
            <div key={p.id} className="project-card">
              <div className="project-card-header">
                <Link to={`/projects/${p.id}`} className="project-title">{p.title}</Link>
                <button className="btn-icon btn-danger" onClick={() => handleDelete(p.id)} title="Delete">🗑</button>
              </div>
              <p className="project-desc">{p.description || 'No description'}</p>
              <div className="project-meta">
                <span>📋 {p.task_count} tasks</span>
                <span>👥 {p.member_count} members</span>
              </div>
              <Link to={`/projects/${p.id}`} className="btn-secondary btn-sm">View Project →</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
