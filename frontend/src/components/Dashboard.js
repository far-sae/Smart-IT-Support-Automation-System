import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './Dashboard.css';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await dashboardAPI.getStats();
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard statistics');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  if (loading && !stats) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  // Prepare chart data
  const categoryData = stats?.tickets_by_category ? Object.entries(stats.tickets_by_category).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  })) : [];

  const statusData = stats?.tickets_by_status ? Object.entries(stats.tickets_by_status).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    count: value
  })) : [];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>IT Support Dashboard</h1>
        <button onClick={handleRefresh} disabled={refreshing} className="refresh-btn">
          {refreshing ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <h3>Total Tickets</h3>
            <p className="metric-value">{stats?.total_tickets || 0}</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⏳</div>
          <div className="metric-content">
            <h3>Open Tickets</h3>
            <p className="metric-value">{stats?.open_tickets || 0}</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <h3>Resolved</h3>
            <p className="metric-value">{stats?.resolved_tickets || 0}</p>
          </div>
        </div>

        <div className="metric-card highlight">
          <div className="metric-icon">🤖</div>
          <div className="metric-content">
            <h3>Auto-Resolved</h3>
            <p className="metric-value">{stats?.auto_resolved_tickets || 0}</p>
          </div>
        </div>

        <div className="metric-card success">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <h3>Auto-Resolution Rate</h3>
            <p className="metric-value">{stats?.auto_resolution_rate || 0}%</p>
          </div>
        </div>

        <div className="metric-card warning">
          <div className="metric-icon">⚠️</div>
          <div className="metric-content">
            <h3>Pending Approvals</h3>
            <p className="metric-value">{stats?.pending_approvals || 0}</p>
          </div>
        </div>

        <div className="metric-card error">
          <div className="metric-icon">❌</div>
          <div className="metric-content">
            <h3>Failed Automations</h3>
            <p className="metric-value">{stats?.failed_automations || 0}</p>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Tickets by Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={statusData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Tickets by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Tickets */}
      <div className="recent-tickets">
        <h3>Recent Tickets</h3>
        <div className="tickets-table">
          <table>
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Subject</th>
                <th>Category</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Auto-Resolved</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {stats?.recent_tickets?.map((ticket) => (
                <tr key={ticket.id}>
                  <td>{ticket.ticket_number}</td>
                  <td className="ticket-subject">{ticket.subject}</td>
                  <td>
                    <span className="badge category">{ticket.category}</span>
                  </td>
                  <td>
                    <span className={`badge status-${ticket.status}`}>{ticket.status}</span>
                  </td>
                  <td>
                    <span className={`badge priority-${ticket.priority}`}>{ticket.priority}</span>
                  </td>
                  <td>{ticket.auto_resolved ? '✅' : '➖'}</td>
                  <td>{new Date(ticket.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
