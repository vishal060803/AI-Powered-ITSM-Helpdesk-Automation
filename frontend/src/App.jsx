import { useState } from 'react'

const navItems = [
  { id: 'chat', label: 'Chat' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'knowledge', label: 'Knowledge Base' },
  { id: 'requests', label: 'Requests' },
]

const stats = [
  { label: 'Open Tickets', value: '128' },
  { label: 'AI Resolved', value: '42' },
  { label: 'Escalations', value: '11' },
  { label: 'Software Requests', value: '19' },
]

const recentTickets = [
  { id: 'INC-1028', title: 'VPN authentication failure', status: 'In progress', owner: 'Network Support' },
  { id: 'INC-1031', title: 'Password expired', status: 'Auto-resolved', owner: 'Self-heal agent' },
  { id: 'INC-1036', title: 'Outlook sync issue', status: 'Awaiting user', owner: 'End User Support' },
]

const knowledgeCards = [
  { title: 'VPN Troubleshooting', category: 'Network', description: 'Authentication and tunnel checks for remote users.' },
  { title: 'Password Reset Guide', category: 'Identity', description: 'Reset flows, MFA validation, and account unlock guidance.' },
  { title: 'Outlook Sync Fix', category: 'Email', description: 'Step-by-step checks for profile and cache-related sync issues.' },
]

const requestCards = [
  { id: 'REQ-001245', software: 'Visual Studio Code', status: 'Provisioning' },
  { id: 'REQ-001290', software: 'Microsoft Teams', status: 'Approved' },
  { id: 'REQ-001310', software: 'Adobe Reader', status: 'Queued' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <section className="content-panel">
            <div className="panel-header">
              <h2>ITSM Dashboard</h2>
              <button className="secondary-btn">Export Report</button>
            </div>

            <div className="stats-grid">
              {stats.map((stat) => (
                <div key={stat.label} className="stat-card">
                  <span>{stat.label}</span>
                  <strong>{stat.value}</strong>
                </div>
              ))}
            </div>

            <div className="table-card">
              <h3>Recent Tickets</h3>
              <table>
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Issue</th>
                    <th>Status</th>
                    <th>Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTickets.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>{ticket.id}</td>
                      <td>{ticket.title}</td>
                      <td><span className="tag">{ticket.status}</span></td>
                      <td>{ticket.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )

      case 'knowledge':
        return (
          <section className="content-panel">
            <div className="panel-header">
              <h2>Knowledge Base</h2>
              <button className="primary-btn">Search Articles</button>
            </div>

            <div className="card-grid two-column">
              {knowledgeCards.map((article) => (
                <div key={article.title} className="info-card">
                  <span className="pill">{article.category}</span>
                  <h3>{article.title}</h3>
                  <p>{article.description}</p>
                </div>
              ))}
            </div>
          </section>
        )

      case 'requests':
        return (
          <section className="content-panel">
            <div className="panel-header">
              <h2>Service Requests</h2>
              <button className="primary-btn">New Request</button>
            </div>

            <div className="card-grid two-column">
              {requestCards.map((request) => (
                <div key={request.id} className="info-card">
                  <span className="pill">{request.status}</span>
                  <h3>{request.software}</h3>
                  <p>{request.id}</p>
                </div>
              ))}
            </div>
          </section>
        )

      case 'chat':
      default:
        return (
          <section className="chat-layout">
            <div className="chat-panel">
              <div className="panel-header">
                <h2>Employee Self-Service</h2>
                <button className="primary-btn">Create Ticket</button>
              </div>

              <div className="message-list">
                <div className="message user">
                  <p>I cannot connect to VPN since this morning. Authentication keeps failing.</p>
                </div>
                <div className="message assistant">
                  <p>AI identified: Incident • Network / VPN • Priority P2. Suggested resolution: VPN troubleshooting steps.</p>
                </div>
              </div>

              <div className="composer">
                <input type="text" value="Type your request..." readOnly />
                <button className="primary-btn">Send</button>
              </div>
            </div>

            <aside className="analysis-panel">
              <h3>AI Analysis</h3>
              <ul>
                <li><span>Intent</span><strong>Incident</strong></li>
                <li><span>Category</span><strong>Network / VPN</strong></li>
                <li><span>Priority</span><strong>P2</strong></li>
                <li><span>Confidence</span><strong>91%</strong></li>
                <li><span>Assignment</span><strong>Network Support</strong></li>
              </ul>
            </aside>
          </section>
        )
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Intelligent Helpdesk</p>
          <h1>AI ITSM Portal</h1>
        </div>
        <div className="topbar-actions">
          <span className="status-pill">System Healthy</span>
          <button className="secondary-btn">Admin View</button>
        </div>
      </header>

      <nav className="nav-bar" aria-label="Main navigation">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={activeTab === item.id ? 'nav-item active' : 'nav-item'}
            onClick={() => setActiveTab(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>

      {renderContent()}
    </main>
  )
}
