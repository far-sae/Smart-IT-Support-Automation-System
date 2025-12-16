import React, { useState, useEffect } from 'react';
import { ticketsAPI } from '../api';
import './Tickets.css';

function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTicket, setNewTicket] = useState({
    subject: '',
    description: '',
    requester_email: '',
    requester_name: '',
    priority: 'medium'
  });

  const loadTickets = async () => {
    try {
      setLoading(true);
      const response = await ticketsAPI.list();
      setTickets(response.data);
    } catch (err) {
      console.error('Failed to load tickets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    try {
      await ticketsAPI.create(newTicket);
      setShowCreateModal(false);
      setNewTicket({
        subject: '',
        description: '',
        requester_email: '',
        requester_name: '',
        priority: 'medium'
      });
      loadTickets();
    } catch (err) {
      let errorMessage = 'Failed to create ticket';
      
      if (err.response?.data) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map(e => e.msg).join(', ');
        } else if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        }
      }
      
      alert(errorMessage);
    }
  };

  const handleCloseTicket = async (ticketId) => {
    if (window.confirm('Are you sure you want to close this ticket?')) {
      try {
        await ticketsAPI.close(ticketId);
        loadTickets();
      } catch (err) {
        alert('Failed to close ticket');
      }
    }
  };

  return (
    <div className="tickets-container">
      <div className="tickets-header">
        <h1>Support Tickets</h1>
        <button onClick={() => setShowCreateModal(true)} className="create-btn">
          ➕ Create Ticket
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading tickets...</div>
      ) : (
        <div className="tickets-list">
          <table>
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Subject</th>
                <th>Category</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Requester</th>
                <th>Auto-Resolved</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr key={ticket.id}>
                  <td>{ticket.ticket_number}</td>
                  <td className="ticket-subject">{ticket.subject}</td>
                  <td><span className="badge category">{ticket.category}</span></td>
                  <td><span className={`badge status-${ticket.status}`}>{ticket.status}</span></td>
                  <td><span className={`badge priority-${ticket.priority}`}>{ticket.priority}</span></td>
                  <td>{ticket.requester_email}</td>
                  <td>{ticket.auto_resolved ? '✅ Yes' : '➖ No'}</td>
                  <td>{new Date(ticket.created_at).toLocaleString()}</td>
                  <td>
                    {ticket.status !== 'closed' && (
                      <button
                        onClick={() => handleCloseTicket(ticket.id)}
                        className="close-ticket-btn"
                      >
                        Close
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Ticket</h2>
            <form onSubmit={handleCreateTicket}>
              <div className="form-group">
                <label>Subject *</label>
                <input
                  type="text"
                  value={newTicket.subject}
                  onChange={(e) => setNewTicket({...newTicket, subject: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({...newTicket, description: e.target.value})}
                  rows="4"
                  required
                />
              </div>

              <div className="form-group">
                <label>Requester Email *</label>
                <input
                  type="email"
                  value={newTicket.requester_email}
                  onChange={(e) => setNewTicket({...newTicket, requester_email: e.target.value})}
                  required
                />
              </div>

              <div className="form-group">
                <label>Requester Name</label>
                <input
                  type="text"
                  value={newTicket.requester_name}
                  onChange={(e) => setNewTicket({...newTicket, requester_name: e.target.value})}
                />
              </div>

              <div className="form-group">
                <label>Priority</label>
                <select
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({...newTicket, priority: e.target.value})}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)} className="cancel-btn">
                  Cancel
                </button>
                <button type="submit" className="submit-btn">
                  Create Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Tickets;
