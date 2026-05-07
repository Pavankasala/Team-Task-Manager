import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import TaskCard from '../components/TaskCard';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [memberEmail, setMemberEmail] = useState('');

  // Task form state
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskPriority, setTaskPriority] = useState('Medium');
  const [taskDue, setTaskDue] = useState('');
  const [taskAssignee, setTaskAssignee] = useState('');

  const fetchAll = async () => {
    try {
      const [projRes, tasksRes] = await Promise.all([
        api.get(`/projects/${id}`),
        api.get(`/projects/${id}/tasks`),
      ]);
      setProject(projRes.data);
      setTasks(tasksRes.data);
      setMembers(projRes.data.members || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, [id]);

  const handleAddTask = async (e) => {
    e.preventDefault();
    try {
      await api.post('/tasks', {
        title: taskTitle, description: taskDesc, priority: taskPriority,
        project_id: id, assigned_to: taskAssignee || null,
        due_date: taskDue ? new Date(taskDue).toISOString() : null,
      });
      setTaskTitle(''); setTaskDesc(''); setTaskPriority('Medium'); setTaskDue(''); setTaskAssignee('');
      setShowTaskForm(false);
      fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try { await api.put(`/tasks/${taskId}`, { status: newStatus }); fetchAll(); }
    catch (err) { alert('Failed to update status'); }
  };

  const handleDeleteTask = async (taskId) => {
    try { await api.delete(`/tasks/${taskId}`); fetchAll(); }
    catch (err) { alert('Failed to delete task'); }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    try { await api.post(`/projects/${id}/members`, { email: memberEmail }); setMemberEmail(''); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Failed to add member'); }
  };

  const handleRemoveMember = async (userId) => {
    try { await api.delete(`/projects/${id}/members/${userId}`); fetchAll(); }
    catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  if (loading) return <div className="page-loader"><div className="spinner"></div></div>;
  if (!project) return <p className="text-center">Project not found.</p>;

  const todoTasks = tasks.filter(t => t.status === 'To Do');
  const inProgressTasks = tasks.filter(t => t.status === 'In Progress');
  const doneTasks = tasks.filter(t => t.status === 'Done');

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/projects" className="back-link">← Back to Projects</Link>
          <h1>{project.title}</h1>
          {project.description && <p className="project-description">{project.description}</p>}
        </div>
        <button className="btn-primary" onClick={() => setShowTaskForm(!showTaskForm)}>
          {showTaskForm ? 'Cancel' : '+ Add Task'}
        </button>
      </div>

      {showTaskForm && (
        <form onSubmit={handleAddTask} className="card form-card">
          <h3>New Task</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Title</label>
              <input value={taskTitle} onChange={e => setTaskTitle(e.target.value)} placeholder="Task title" required />
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select value={taskPriority} onChange={e => setTaskPriority(e.target.value)}>
                <option>Low</option><option>Medium</option><option>High</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={taskDesc} onChange={e => setTaskDesc(e.target.value)} placeholder="Details..." rows={2} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Due Date</label>
              <input type="date" value={taskDue} onChange={e => setTaskDue(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Assign To</label>
              <select value={taskAssignee} onChange={e => setTaskAssignee(e.target.value)}>
                <option value="">Unassigned</option>
                {members.map(m => <option key={m.user_id} value={m.user_id}>{m.username}</option>)}
              </select>
            </div>
          </div>
          <button type="submit" className="btn-primary">Create Task</button>
        </form>
      )}

      {/* Kanban Columns */}
      <div className="kanban-board">
        <div className="kanban-col">
          <div className="kanban-col-header todo">📝 To Do <span className="count">{todoTasks.length}</span></div>
          {todoTasks.map(t => <TaskCard key={t.id} task={t} onStatusChange={handleStatusChange} onDelete={handleDeleteTask} />)}
        </div>
        <div className="kanban-col">
          <div className="kanban-col-header progress">⚡ In Progress <span className="count">{inProgressTasks.length}</span></div>
          {inProgressTasks.map(t => <TaskCard key={t.id} task={t} onStatusChange={handleStatusChange} onDelete={handleDeleteTask} />)}
        </div>
        <div className="kanban-col">
          <div className="kanban-col-header done">✅ Done <span className="count">{doneTasks.length}</span></div>
          {doneTasks.map(t => <TaskCard key={t.id} task={t} onStatusChange={handleStatusChange} onDelete={handleDeleteTask} />)}
        </div>
      </div>

      {/* Team Members */}
      <div className="section">
        <h2>Team Members</h2>
        <form onSubmit={handleAddMember} className="inline-form">
          <input value={memberEmail} onChange={e => setMemberEmail(e.target.value)} placeholder="Add member by email..." required />
          <button type="submit" className="btn-primary btn-sm">Add</button>
        </form>
        <div className="members-list">
          {members.map(m => (
            <div key={m.id} className="member-chip">
              <span>{m.role === 'owner' ? '👑' : '👤'} {m.username}</span>
              <span className="member-email">{m.email}</span>
              {m.role !== 'owner' && (
                <button className="btn-icon btn-xs" onClick={() => handleRemoveMember(m.user_id)} title="Remove">✕</button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
