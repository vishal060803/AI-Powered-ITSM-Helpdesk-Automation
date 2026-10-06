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

const defaultTickets = [
  { id: 'INC-1028', title: 'VPN authentication failure', status: 'In progress', owner: 'Network Support' },
  { id: 'INC-1031', title: 'Password expired', status: 'Auto-resolved', owner: 'Self-heal agent' },
  { id: 'INC-1036', title: 'Outlook sync issue', status: 'Awaiting user', owner: 'End User Support' },
]

const requestCards = [
  { id: 'REQ-001245', software: 'Visual Studio Code', status: 'Provisioning' },
  { id: 'REQ-001290', software: 'Microsoft Teams', status: 'Approved' },
  { id: 'REQ-001310', software: 'Adobe Reader', status: 'Queued' },
]

const processingSummary = {
  status: 'Processing',
  message: 'AI knowledge retrieval is active for live user requests.',
  stage: 'Knowledge lookup',
  updated: '2 minutes ago',
}

const DEFAULT_KNOWLEDGE_QUERY = 'How do I fix VPN?'
const DEFAULT_CHAT_QUERY = 'I cannot connect to VPN since this morning. Authentication keeps failing.'

async function fetchKnowledgeData(question, onSuccess, onError, setLoading) {
  const trimmedQuestion = question.trim()
  if (!trimmedQuestion) {
    onError('Please enter a question before searching the knowledge base.')
    return
  }

  setLoading(true)
  onError('')

  try {
    const response = await fetch('http://127.0.0.1:8000/api/v1/knowledge/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: trimmedQuestion,
        top_k: 3,
      }),
    })

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || 'Knowledge search failed.')
    }

    const payload = await response.json()
    onSuccess(payload.results || [], payload.sources || [])
  } catch (error) {
    onError(error.message || 'Unable to retrieve knowledge results.')
    onSuccess([], [])
  } finally {
    setLoading(false)
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [recentTickets, setRecentTickets] = useState(defaultTickets)
  const [knowledgeQuery, setKnowledgeQuery] = useState(DEFAULT_KNOWLEDGE_QUERY)
  const [knowledgeResults, setKnowledgeResults] = useState([])
  const [knowledgeSources, setKnowledgeSources] = useState([])
  const [knowledgeLoading, setKnowledgeLoading] = useState(false)
  const [knowledgeError, setKnowledgeError] = useState('')
  const [chatQuestion, setChatQuestion] = useState(DEFAULT_CHAT_QUERY)
  const [ticketQuestion, setTicketQuestion] = useState('')
  const [chatResults, setChatResults] = useState([])
  const [chatSources, setChatSources] = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [isTicketFlow, setIsTicketFlow] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I can help with password resets, VPN issues, Outlook problems, and support workflows. Tell me what you need help with.',
    },
  ])

  const handleCreateTicket = () => {
    setIsTicketFlow(true)
    setChatError('')
  }

  const submitTicket = () => {
    const trimmedQuestion = ticketQuestion.trim()
    if (!trimmedQuestion) {
      setChatError('Please enter a ticket description before creating a request.')
      return
    }

    const ticketId = `INC-${Math.floor(1000 + Math.random() * 9000)}`
    const newTicket = {
      id: ticketId,
      title: trimmedQuestion.length > 70 ? `${trimmedQuestion.slice(0, 67)}...` : trimmedQuestion,
      status: 'In progress',
      owner: 'AI Request Queue',
    }

    setRecentTickets((currentTickets) => [newTicket, ...currentTickets])
    setTicketQuestion('')
    setChatError('')
    setIsTicketFlow(false)
    setActiveTab('dashboard')
  }

  const handleKnowledgeSearch = async (event) => {
    event.preventDefault()
    await fetchKnowledgeData(
      knowledgeQuery,
      (results, sources) => {
        setKnowledgeResults(results)
        setKnowledgeSources(sources)
      },
      setKnowledgeError,
      setKnowledgeLoading,
    )
  }

  const handleChatSubmit = async (event) => {
    event.preventDefault()
    const message = chatQuestion.trim()

    if (!message) {
      setChatError('Please enter a message before sending it to the assistant.')
      return
    }

    setChatLoading(true)
    setChatError('')
    setChatMessages((current) => [...current, { role: 'user', content: message }])
    setChatQuestion('')

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/knowledge/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employee_id: 'demo-user',
          message,
          context: { channel: 'chat' },
        }),
      })

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Unable to get a chat response.')
      }

      const payload = await response.json()
      const assistantResponse = payload.response || 'I could not determine the right guidance from the knowledge base.'
      setChatResults(payload.analysis?.sources || [])
      setChatSources(payload.analysis?.sources || [])
      setChatMessages((current) => [...current, { role: 'assistant', content: assistantResponse }])
    } catch (error) {
      setChatError(error.message || 'Unable to reach the assistant.')
      setChatMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: 'I could not generate a response right now. Please try again or check the support guidance manually.',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <section className="content-panel">
            <div className="panel-header">
              <h2>ITSM Dashboard</h2>
              <button className="secondary-btn" type="button">Export Report</button>
            </div>

            <div className="stats-grid">
              {stats.map((stat) => (
                <div key={stat.label} className="stat-card">
                  <span>{stat.label}</span>
                  <strong>{stat.value}</strong>
                </div>
              ))}
            </div>

            <div className="processing-card">
              <div className="processing-header">
                <span className="status-dot" aria-hidden="true" />
                <h3>Request Processing</h3>
                <span className="status-badge">{processingSummary.status}</span>
              </div>
              <p>{processingSummary.message}</p>
              <div className="processing-meta">
                <span>{processingSummary.stage}</span>
                <span>{processingSummary.updated}</span>
              </div>
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
          <section className="content-panel knowledge-panel">
            <div className="panel-header">
              <h2>Knowledge Base</h2>
            </div>

            <form className="knowledge-search" onSubmit={handleKnowledgeSearch}>
              <input
                type="text"
                value={knowledgeQuery}
                onChange={(event) => setKnowledgeQuery(event.target.value)}
                placeholder="Ask about VPN, Outlook, passwords, or Wi-Fi issues"
                aria-label="Knowledge search question"
              />
              <button className="primary-btn" type="submit" disabled={knowledgeLoading}>
                {knowledgeLoading ? 'Searching...' : 'Search Articles'}
              </button>
            </form>

            {knowledgeError ? <p className="error-message">{knowledgeError}</p> : null}

            {knowledgeResults.length > 0 ? (
              <>
                <div className="result-list">
                  {knowledgeResults.map((result) => (
                    <article key={result.chunk_id} className="result-card">
                      <div className="result-header">
                        <span className="rank-badge">#{result.rank}</span>
                        <span className="pill">{result.category}</span>
                        <span className="muted-tag">{result.sub_category}</span>
                      </div>
                      <h3>{result.title}</h3>
                      <p className="result-text">{result.text}</p>
                      <div className="result-meta">
                        <span>Score: {result.score.toFixed(3)}</span>
                        <span>Source: {result.source_file}</span>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="source-panel">
                  <h3>Source Articles</h3>
                  <ul>
                    {knowledgeSources.map((source) => (
                      <li key={source.article_id}>
                        <strong>{source.title}</strong>
                        <span>{source.source_file}</span>
                        <small>{source.category} / {source.sub_category}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <p>Search a knowledge question to view ranked IT help articles and source metadata.</p>
              </div>
            )}
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
                <h2>{isTicketFlow ? 'Create Ticket' : 'Employee Self-Service'}</h2>
                {!isTicketFlow ? (
                  <button className="primary-btn" type="button" onClick={handleCreateTicket}>
                    Create Ticket
                  </button>
                ) : (
                  <button className="secondary-btn" type="button" onClick={() => setIsTicketFlow(false)}>
                    Back to Chat
                  </button>
                )}
              </div>

              {isTicketFlow ? (
                <div className="ticket-intake">
                  <p className="ticket-help">
                    Describe the issue and save it as a ticket. This flow is only for issue capture.
                  </p>
                  <textarea
                    value={ticketQuestion}
                    onChange={(event) => setTicketQuestion(event.target.value)}
                    placeholder="Describe the problem you need help with"
                    aria-label="Ticket issue description"
                    rows={6}
                  />
                  <button className="primary-btn" type="button" onClick={submitTicket}>
                    Save Ticket
                  </button>
                </div>
              ) : (
                <>
                  <div className="message-list">
                    {chatMessages.map((message, index) => (
                      <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                        <p style={{ whiteSpace: 'pre-line' }}>{message.content}</p>
                      </div>
                    ))}
                  </div>

                  <form className="composer" onSubmit={handleChatSubmit}>
                    <input
                      type="text"
                      value={chatQuestion}
                      onChange={(event) => setChatQuestion(event.target.value)}
                      placeholder="Describe your issue or question"
                      aria-label="Chat request"
                    />
                    <button className="primary-btn" type="submit" disabled={chatLoading}>
                      {chatLoading ? 'Searching...' : 'Send'}
                    </button>
                  </form>

                  {chatError ? <p className="error-message">{chatError}</p> : null}

                  {chatResults.length > 0 ? (
                    <div className="result-list chat-results">
                      {chatResults.map((result) => (
                        <article key={result.chunk_id || result.article_id} className="result-card">
                          <div className="result-header">
                            <span className="rank-badge">#{result.rank || 1}</span>
                            <span className="pill">{result.category}</span>
                            <span className="muted-tag">{result.sub_category}</span>
                          </div>
                          <h3>{result.title}</h3>
                          <p className="result-text">{result.text}</p>
                          <div className="result-meta">
                            <span>Source: {result.source_file}</span>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : null}
                </>
              )}

              {chatError && isTicketFlow ? <p className="error-message">{chatError}</p> : null}
            </div>

            <aside className="analysis-panel">
              <h3>AI Analysis</h3>
              {isTicketFlow ? (
                <ul>
                  <li><span>Flow</span><strong>Ticket intake</strong></li>
                  <li><span>Status</span><strong>Waiting for issue details</strong></li>
                  <li><span>Save</span><strong>Dashboard record</strong></li>
                </ul>
              ) : chatSources.length > 0 ? (
                <ul>
                  {chatSources.map((source) => (
                    <li key={source.article_id}>
                      <span>Source</span>
                      <strong>{source.title}</strong>
                      <small>{source.source_file}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <ul>
                  <li><span>Intent</span><strong>Incident</strong></li>
                  <li><span>Category</span><strong>Network / VPN</strong></li>
                  <li><span>Priority</span><strong>P2</strong></li>
                  <li><span>Confidence</span><strong>91%</strong></li>
                  <li><span>Assignment</span><strong>Network Support</strong></li>
                </ul>
              )}
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
