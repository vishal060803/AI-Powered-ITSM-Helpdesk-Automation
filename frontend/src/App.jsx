import { useEffect, useState } from 'react'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

function isResolvedStatus(status) {
  return ['resolved', 'auto-resolved', 'closed'].includes(String(status || '').toLowerCase())
}

function isEscalatedStatus(status) {
  return ['escalated', 'escalated-to-human'].includes(String(status || '').toLowerCase())
}

async function requestJson(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.detail || 'The request could not be completed.')
  }
  return payload
}

const navItems = [
  { id: 'chat', label: 'Chat' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'knowledge', label: 'Knowledge Base' },
  { id: 'requests', label: 'Requests' },
]

const fallbackCatalogItems = [
  {
    software_id: 'SW-VSCODE',
    name: 'Visual Studio Code',
    category: 'Developer Tools',
    approval_required: false,
    estimated_fulfillment_hours: 2,
  },
  {
    software_id: 'SW-TEAMS',
    name: 'Microsoft Teams',
    category: 'Collaboration',
    approval_required: false,
    estimated_fulfillment_hours: 4,
  },
  {
    software_id: 'SW-ADOBE-READER',
    name: 'Adobe Reader',
    category: 'Productivity',
    approval_required: false,
    estimated_fulfillment_hours: 6,
  },
  {
    software_id: 'SW-VPN-CLIENT',
    name: 'Corporate VPN Client',
    category: 'Network Security',
    approval_required: true,
    estimated_fulfillment_hours: 8,
  },
]

const fallbackStatusLifecycle = ['requested', 'queued', 'approved', 'provisioning', 'completed', 'failed', 'rejected']

const mockRequestRecords = [
  {
    request_id: 'REQ-001245',
    software_name: 'Visual Studio Code',
    status: 'requested',
    service_now_ref: 'RITM1001245',
    created_at: '2026-10-07T09:10:00Z',
    updated_at: '2026-10-07T09:10:00Z',
  },
  {
    request_id: 'REQ-001290',
    software_name: 'Microsoft Teams',
    status: 'provisioning',
    service_now_ref: 'RITM1001290',
    created_at: '2026-10-07T07:00:00Z',
    updated_at: '2026-10-07T08:30:00Z',
  },
  {
    request_id: 'REQ-001310',
    software_name: 'Adobe Reader',
    status: 'completed',
    service_now_ref: 'RITM1001310',
    created_at: '2026-10-06T11:00:00Z',
    updated_at: '2026-10-06T12:20:00Z',
  },
]

const provisioningProgression = ['requested', 'provisioning', 'completed']

function toReadableTime(value) {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'N/A'
  return date.toLocaleString()
}

const knowledgeArticles = [
  { title: 'VPN connection troubleshooting', category: 'Network', subCategory: 'VPN', source: 'corporate_wifi_troubleshooting.md' },
  { title: 'Password reset and unlock', category: 'Identity', subCategory: 'Password', source: 'password_reset_and_account_unlock.md' },
  { title: 'Outlook sync troubleshooting', category: 'Email', subCategory: 'Outlook', source: 'outlook_sync_troubleshooting.md' },
  { title: 'Slow laptop basic checks', category: 'Endpoint', subCategory: 'Performance', source: 'slow_laptop_basic_checks.md' },
  { title: 'Business application access', category: 'Applications', subCategory: 'Access', source: 'business_application_access.md' },
  { title: 'Approved software installation', category: 'Software', subCategory: 'Provisioning', source: 'approved_software_installation.md' },
]

const DEFAULT_KNOWLEDGE_QUERY = 'How do I fix VPN?'
const DEFAULT_CHAT_QUERY = 'I cannot connect to VPN since this morning. Authentication keeps failing.'

async function fetchKnowledgeData(question, category, onSuccess, onError, setLoading) {
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
        category: category === 'All' ? null : category,
        top_k: 3,
      }),
    })

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || 'Knowledge search failed.')
    }

    const payload = await response.json()
    onSuccess(
      payload.results || [],
      payload.sources || [],
      payload.answer || '',
      Number(payload.confidence || 0),
      payload.is_supported !== false,
    )
  } catch (error) {
    onError(error.message || 'Unable to retrieve knowledge results.')
    onSuccess([], [], '', 0, false)
  } finally {
    setLoading(false)
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [recentTickets, setRecentTickets] = useState([])
  const [ticketLoading, setTicketLoading] = useState(false)
  const [ticketSaving, setTicketSaving] = useState(false)
  const [ticketError, setTicketError] = useState('')
  const [ticketFilter, setTicketFilter] = useState('all')
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [ticketDetailLoading, setTicketDetailLoading] = useState(false)
  const [dashboardSoftwareRequests, setDashboardSoftwareRequests] = useState([])
  const [knowledgeQuery, setKnowledgeQuery] = useState(DEFAULT_KNOWLEDGE_QUERY)
  const [knowledgeCategory, setKnowledgeCategory] = useState('All')
  const [knowledgeResults, setKnowledgeResults] = useState([])
  const [knowledgeSources, setKnowledgeSources] = useState([])
  const [knowledgeAnswer, setKnowledgeAnswer] = useState('')
  const [knowledgeConfidence, setKnowledgeConfidence] = useState(0)
  const [knowledgeSupported, setKnowledgeSupported] = useState(true)
  const [knowledgeLoading, setKnowledgeLoading] = useState(false)
  const [knowledgeError, setKnowledgeError] = useState('')
  const [chatQuestion, setChatQuestion] = useState(DEFAULT_CHAT_QUERY)
  const [ticketQuestion, setTicketQuestion] = useState('')
  const [chatResults, setChatResults] = useState([])
  const [chatSources, setChatSources] = useState([])
  const [chatAnalysis, setChatAnalysis] = useState(null)
  const [chatNextAction, setChatNextAction] = useState('')
  const [lastChatRequest, setLastChatRequest] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [isTicketFlow, setIsTicketFlow] = useState(false)
  const [catalogItems, setCatalogItems] = useState(fallbackCatalogItems)
  const [catalogLifecycle, setCatalogLifecycle] = useState(fallbackStatusLifecycle)
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [catalogError, setCatalogError] = useState('')
  const [softwareRequests, setSoftwareRequests] = useState(mockRequestRecords)
  const [selectedSoftwareRequest, setSelectedSoftwareRequest] = useState(mockRequestRecords[0] || null)
  const [softwareRequestLoading, setSoftwareRequestLoading] = useState(false)
  const [showRequestForm, setShowRequestForm] = useState(false)
  const [requestEmployeeId, setRequestEmployeeId] = useState('demo-user')
  const [requestSoftwareName, setRequestSoftwareName] = useState('')
  const [requestJustification, setRequestJustification] = useState('')
  const [requestFormError, setRequestFormError] = useState('')
  const [requestSuccessMessage, setRequestSuccessMessage] = useState('')
  const [requestSubmitting, setRequestSubmitting] = useState(false)
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I can help with password resets, VPN issues, Outlook problems, and support workflows. Tell me what you need help with.',
    },
  ])

  const normalizedKnowledgeKeyword = knowledgeQuery.trim().toLowerCase()
  const filteredKnowledgeArticles = knowledgeArticles.filter((article) => {
    const categoryMatch = knowledgeCategory === 'All' || article.category === knowledgeCategory
    const keywordMatch = !normalizedKnowledgeKeyword || [
      article.title,
      article.subCategory,
      article.source,
    ].join(' ').toLowerCase().includes(normalizedKnowledgeKeyword)
    return categoryMatch && keywordMatch
  })

  useEffect(() => {
    if (activeTab !== 'dashboard') return undefined

    let cancelled = false
    const loadTickets = async () => {
      setTicketLoading(true)
      setTicketError('')
      try {
        const [tickets, requests] = await Promise.all([
          requestJson('/knowledge/incidents'),
          requestJson('/software/requests').catch(() => []),
        ])
        if (!cancelled) {
          setRecentTickets(tickets)
          setDashboardSoftwareRequests(requests)
          setSelectedTicket((current) => current || tickets[0] || null)
        }
      } catch (error) {
        if (!cancelled) setTicketError(error.message || 'Unable to load ticket records.')
      } finally {
        if (!cancelled) setTicketLoading(false)
      }
    }

    loadTickets()
    return () => {
      cancelled = true
    }
  }, [activeTab])

  useEffect(() => {
    if (activeTab !== 'requests') return undefined

    let cancelled = false
    const loadCatalog = async () => {
      setCatalogLoading(true)
      setCatalogError('')
      setSoftwareRequestLoading(true)
      try {
        const [catalogPayload, requestsPayload] = await Promise.all([
          requestJson('/software/catalog'),
          requestJson('/software/requests'),
        ])
        if (!cancelled) {
          setCatalogItems(catalogPayload.items || fallbackCatalogItems)
          setCatalogLifecycle(catalogPayload.status_lifecycle || fallbackStatusLifecycle)
          if (!requestSoftwareName && (catalogPayload.items || []).length > 0) {
            setRequestSoftwareName(catalogPayload.items[0].name)
          }
          const requestRecords = requestsPayload.length > 0 ? requestsPayload : mockRequestRecords
          setSoftwareRequests(requestRecords)
          setSelectedSoftwareRequest((current) => current || requestRecords[0] || null)
        }
      } catch (error) {
        if (!cancelled) {
          setCatalogError(error.message || 'Unable to load software catalog.')
          setCatalogItems(fallbackCatalogItems)
          setCatalogLifecycle(fallbackStatusLifecycle)
          if (!requestSoftwareName && fallbackCatalogItems.length > 0) {
            setRequestSoftwareName(fallbackCatalogItems[0].name)
          }
          setSoftwareRequests(mockRequestRecords)
          setSelectedSoftwareRequest((current) => current || mockRequestRecords[0] || null)
        }
      } finally {
        if (!cancelled) {
          setCatalogLoading(false)
          setSoftwareRequestLoading(false)
        }
      }
    }

    loadCatalog()
    return () => {
      cancelled = true
    }
  }, [activeTab])

  useEffect(() => {
    if (requestSoftwareName) return
    if (!catalogItems.length) return
    setRequestSoftwareName(catalogItems[0].name)
  }, [catalogItems, requestSoftwareName])

  const handleCreateTicket = () => {
    setIsTicketFlow(true)
    setChatError('')
    setActiveTab('chat')
  }

  const submitTicket = async () => {
    const trimmedQuestion = ticketQuestion.trim()
    if (!trimmedQuestion) {
      setChatError('Please enter a ticket description before creating a request.')
      return
    }

    setTicketSaving(true)
    setChatError('')
    try {
      const chat = await requestJson('/knowledge/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: 'demo-user',
          message: trimmedQuestion,
          context: { channel: 'ticket-intake' },
        }),
      })
      const created = await requestJson('/knowledge/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: 'demo-user',
          description: trimmedQuestion,
          analysis: chat.analysis,
        }),
      })
      const tickets = await requestJson('/knowledge/incidents')
      const ticket = await requestJson(`/knowledge/incidents/${encodeURIComponent(created.ticket_id)}`)
      setRecentTickets(tickets)
      setSelectedTicket(ticket)
      setTicketQuestion('')
      setIsTicketFlow(false)
      setActiveTab('dashboard')
    } catch (error) {
      setChatError(error.message || 'Unable to create the ticket.')
    } finally {
      setTicketSaving(false)
    }
  }

  const handleTicketSelect = async (ticketId) => {
    setTicketDetailLoading(true)
    setTicketError('')
    try {
      const ticket = await requestJson(`/knowledge/incidents/${encodeURIComponent(ticketId)}`)
      setSelectedTicket(ticket)
    } catch (error) {
      setTicketError(error.message || 'Unable to load ticket details.')
    } finally {
      setTicketDetailLoading(false)
    }
  }

  const handleKnowledgeSearch = async (event) => {
    event.preventDefault()
    await fetchKnowledgeData(
      knowledgeQuery,
      knowledgeCategory,
      (results, sources, answer, confidence, isSupported) => {
        setKnowledgeResults(results)
        setKnowledgeSources(sources)
        setKnowledgeAnswer(answer)
        setKnowledgeConfidence(confidence)
        setKnowledgeSupported(isSupported)
      },
      setKnowledgeError,
      setKnowledgeLoading,
    )
  }

  const handleCreateSoftwareRequest = async (event) => {
    event.preventDefault()
    const employeeId = requestEmployeeId.trim()
    const softwareName = requestSoftwareName.trim()
    const businessJustification = requestJustification.trim()

    if (!employeeId) {
      setRequestFormError('Employee ID is required to submit a software request.')
      return
    }
    if (!softwareName) {
      setRequestFormError('Select a software item before submitting the request.')
      return
    }

    setRequestSubmitting(true)
    setRequestFormError('')
    setRequestSuccessMessage('')

    try {
      const created = await requestJson('/software/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_id: employeeId,
          software_name: softwareName,
          metadata: {
            business_justification: businessJustification,
            source: 'employee-portal',
          },
        }),
      })

      const createdRequest = await requestJson(`/software/requests/${encodeURIComponent(created.request_id)}`)
      const requestRecords = await requestJson('/software/requests')
      setSoftwareRequests(requestRecords)
      setSelectedSoftwareRequest(createdRequest)
      setDashboardSoftwareRequests(requestRecords)
      setRequestJustification('')
      setRequestSuccessMessage(`Request ${created.request_id} created successfully.`)
      setShowRequestForm(false)
    } catch (error) {
      setRequestFormError(error.message || 'Unable to create software request.')
    } finally {
      setRequestSubmitting(false)
    }
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
    setLastChatRequest(message)
    setChatMessages((current) => [...current, { role: 'user', content: message }])
    setChatQuestion('')

    try {
      const payload = await requestJson('/knowledge/chat', {
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
      const assistantResponse = payload.response || 'I could not determine the right guidance from the knowledge base.'
      setChatAnalysis(payload.analysis || null)
      setChatNextAction('')
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

  const handleAcceptResolution = () => {
    setChatNextAction('accepted')
    setChatMessages((current) => [
      ...current,
      {
        role: 'assistant',
        content: 'Great — I marked this as accepted guidance. If needed later, you can still create a ticket.',
      },
    ])
  }

  const handleEscalateIssue = () => {
    setChatNextAction('escalated')
    setTicketQuestion(lastChatRequest || chatQuestion)
    setIsTicketFlow(true)
  }

  const handleCreateTicketFromChat = () => {
    setChatNextAction('ticket')
    setTicketQuestion(lastChatRequest || chatQuestion)
    setIsTicketFlow(true)
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        const visibleTickets = recentTickets.filter((ticket) => {
          if (ticketFilter === 'open') return !isResolvedStatus(ticket.status)
          if (ticketFilter === 'resolved') return isResolvedStatus(ticket.status)
          return true
        })
        const openCount = recentTickets.filter((ticket) => !isResolvedStatus(ticket.status) && !isEscalatedStatus(ticket.status)).length
        const resolvedCount = recentTickets.filter((ticket) => isResolvedStatus(ticket.status)).length
        const escalatedCount = recentTickets.filter((ticket) => isEscalatedStatus(ticket.status)).length
        const automatedCount = recentTickets.filter((ticket) => Boolean(ticket.last_automation_action_id)).length
        const automationResolvedCount = recentTickets.filter((ticket) => String(ticket.automation_outcome || '').toLowerCase() === 'resolved').length
        const automationEscalatedCount = recentTickets.filter((ticket) => String(ticket.automation_outcome || '').toLowerCase() === 'escalated').length
        const softwareRequestCount = dashboardSoftwareRequests.length
        const provisioningCount = dashboardSoftwareRequests.filter((request) => String(request.status || '').toLowerCase() === 'provisioning').length
        const softwareCompletedCount = dashboardSoftwareRequests.filter((request) => String(request.status || '').toLowerCase() === 'completed').length
        const dashboardStats = [
          { label: 'Open Tickets', value: openCount },
          { label: 'Resolved Tickets', value: resolvedCount },
          { label: 'Escalated Tickets', value: escalatedCount },
          { label: 'Total Tickets', value: recentTickets.length },
        ]
        return (
          <section className="content-panel">
            <div className="panel-header">
              <h2>ITSM Dashboard</h2>
              <button
                className="secondary-btn"
                type="button"
                onClick={handleCreateTicket}
              >
                Create Ticket
              </button>
            </div>

            <div className="stats-grid">
              {dashboardStats.map((stat) => (
                <div key={stat.label} className="stat-card">
                  <span>{stat.label}</span>
                  <strong>{stat.value}</strong>
                </div>
              ))}
            </div>

            <div className="card-grid two-column dashboard-summary-grid">
              <div className="info-card">
                <h3>Automation Summary</h3>
                <p>Total automated: {automatedCount}</p>
                <p>Auto-resolved: {automationResolvedCount}</p>
                <p>Escalated after automation: {automationEscalatedCount}</p>
              </div>
              <div className="info-card">
                <h3>Software Request Summary</h3>
                <p>Total requests: {softwareRequestCount}</p>
                <p>Provisioning: {provisioningCount}</p>
                <p>Completed: {softwareCompletedCount}</p>
              </div>
            </div>

            {ticketError ? <p className="error-message">{ticketError}</p> : null}
            <div className="dashboard-ticket-layout">
              <div className="table-card">
                <div className="ticket-list-header">
                  <h3>Ticket Records</h3>
                  <div className="ticket-filters" aria-label="Filter tickets">
                    {['all', 'open', 'resolved'].map((filter) => (
                      <button
                        key={filter}
                        className={ticketFilter === filter ? 'filter-btn active' : 'filter-btn'}
                        type="button"
                        onClick={() => setTicketFilter(filter)}
                      >
                        {filter[0].toUpperCase() + filter.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
                {ticketLoading ? <p className="muted-copy">Loading ticket records...</p> : null}
                {!ticketLoading && visibleTickets.length === 0 ? (
                  <div className="empty-state">No {ticketFilter === 'all' ? '' : `${ticketFilter} `}tickets found.</div>
                ) : null}
                {visibleTickets.length > 0 ? (
                  <div className="ticket-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Ticket</th>
                          <th>Issue</th>
                          <th>Status</th>
                          <th>Priority</th>
                          <th>Assignment</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleTickets.map((ticket) => (
                          <tr key={ticket.ticket_id}>
                            <td>
                              <button
                                className="ticket-link"
                                type="button"
                                onClick={() => handleTicketSelect(ticket.ticket_id)}
                              >
                                {ticket.ticket_id}
                              </button>
                            </td>
                            <td>{ticket.title}</td>
                            <td><span className="tag">{ticket.status}</span></td>
                            <td>{ticket.priority}</td>
                            <td>{ticket.assignment_group}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
              </div>

              <aside className="ticket-detail-card">
                <h3>Ticket Details</h3>
                {ticketDetailLoading ? <p className="muted-copy">Loading ticket details...</p> : null}
                {!ticketDetailLoading && selectedTicket ? (
                  <>
                    <div className="ticket-detail-heading">
                      <strong>{selectedTicket.ticket_id}</strong>
                      <span className="tag">{selectedTicket.status}</span>
                    </div>
                    <h4>{selectedTicket.title}</h4>
                    <p className="ticket-description">{selectedTicket.description}</p>
                    <dl className="ticket-detail-list">
                      <div><dt>Category</dt><dd>{selectedTicket.category} / {selectedTicket.sub_category}</dd></div>
                      <div><dt>Priority</dt><dd>{selectedTicket.priority}</dd></div>
                      <div><dt>Impact / Urgency</dt><dd>{selectedTicket.impact} / {selectedTicket.urgency}</dd></div>
                      <div><dt>Assignment group</dt><dd>{selectedTicket.assignment_group}</dd></div>
                      <div><dt>Confidence</dt><dd>{Math.round((selectedTicket.confidence || 0) * 100)}%</dd></div>
                      <div><dt>ServiceNow reference</dt><dd>{selectedTicket.service_now_ref || 'Not assigned'}</dd></div>
                      <div><dt>Automation outcome</dt><dd>{selectedTicket.automation_outcome || 'Not automated'}</dd></div>
                      <div><dt>Automation status</dt><dd>{selectedTicket.last_automation_status || 'Not started'}</dd></div>
                    </dl>

                    {selectedTicket.last_automation_steps?.length > 0 ? (
                      <div className="ticket-ai-analysis">
                        <h4>Automated Action Sequence</h4>
                        <p><strong>Action ID:</strong> {selectedTicket.last_automation_action_id || 'N/A'}</p>
                        <p><strong>Automation:</strong> {selectedTicket.last_automation_name || 'N/A'}</p>
                        <p><strong>Validation:</strong> {selectedTicket.last_automation_validation_result || 'No validation details'}</p>
                        <ol>
                          {selectedTicket.last_automation_steps.map((step, index) => (
                            <li key={`${selectedTicket.last_automation_action_id || 'step'}-${index}`}>{step}</li>
                          ))}
                        </ol>
                      </div>
                    ) : null}

                    <div className="ticket-ai-analysis">
                      <h4>AI Analysis</h4>
                      <p><strong>Intent:</strong> {selectedTicket.ai_analysis?.intent || selectedTicket.intent}</p>
                      <p><strong>Suggested resolution:</strong> {selectedTicket.ai_analysis?.suggested_resolution || 'No suggestion recorded.'}</p>
                      {selectedTicket.ai_analysis?.sources?.length > 0 ? (
                        <div>
                          <strong>Knowledge sources</strong>
                          <ul>
                            {selectedTicket.ai_analysis.sources.map((source) => (
                              <li key={source.article_id}>{source.title}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  </>
                ) : null}
                {!ticketDetailLoading && !selectedTicket ? (
                  <p className="muted-copy">Select a ticket to review its record and AI analysis.</p>
                ) : null}
              </aside>
            </div>
          </section>
        )

      case 'knowledge':
        return (
          <section className="content-panel knowledge-panel">
            <div className="panel-header">
              <h2>Knowledge Base</h2>
            </div>

            <div className="knowledge-search-row">
              <form className="knowledge-search" onSubmit={handleKnowledgeSearch}>
                <input
                  type="text"
                  value={knowledgeQuery}
                  onChange={(event) => setKnowledgeQuery(event.target.value)}
                  placeholder="Search by keyword (VPN, Outlook, password, Wi-Fi...)"
                  aria-label="Knowledge search question"
                />
                <select
                  value={knowledgeCategory}
                  onChange={(event) => setKnowledgeCategory(event.target.value)}
                  aria-label="Knowledge article category filter"
                >
                  <option value="All">All categories</option>
                  <option value="Network">Network</option>
                  <option value="Identity">Identity</option>
                  <option value="Email">Email</option>
                  <option value="Endpoint">Endpoint</option>
                  <option value="Applications">Applications</option>
                  <option value="Software">Software</option>
                </select>
                <button className="primary-btn" type="submit" disabled={knowledgeLoading}>
                  {knowledgeLoading ? 'Searching...' : 'Search Articles'}
                </button>
              </form>
            </div>

            {knowledgeError ? <p className="error-message">{knowledgeError}</p> : null}

            <div className="knowledge-article-grid">
              {filteredKnowledgeArticles.map((article) => (
                <article key={article.title} className="info-card knowledge-article-card">
                  <span className="pill">{article.category}</span>
                  <h3>{article.title}</h3>
                  <p>{article.subCategory}</p>
                  <small>{article.source}</small>
                </article>
              ))}
              {filteredKnowledgeArticles.length === 0 ? (
                <div className="empty-state">
                  <p>No knowledge articles match the selected category/keyword.</p>
                </div>
              ) : null}
            </div>

            {knowledgeAnswer ? (
              <div className={`grounded-answer-card ${knowledgeSupported ? 'supported' : 'unsupported'}`}>
                <div className="grounded-answer-header">
                  <h3>Grounded Answer</h3>
                  <span className="confidence-badge">Confidence: {knowledgeConfidence.toFixed(2)}</span>
                </div>
                <p>{knowledgeAnswer}</p>
                <div className="answer-source-row">
                  <span>{knowledgeSupported ? 'Approved knowledge guidance' : 'Escalation required'}</span>
                </div>
              </div>
            ) : null}

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
                        <span>Distance: {Number(result.distance || 0).toFixed(3)}</span>
                        <span>Article ID: {result.article_id}</span>
                        <span>Chunk ID: {result.chunk_id}</span>
                        <span>Source: {result.source_file}</span>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="source-panel">
                  <h3>Source References</h3>
                  <ul>
                    {knowledgeSources.map((source) => (
                      <li key={source.article_id}>
                        <strong>{source.title}</strong>
                        <span>{source.source_file}</span>
                        <small>{source.category} / {source.sub_category}</small>
                        <small>Article ID: {source.article_id}</small>
                        {source.chunk_id ? <small>Top chunk: {source.chunk_id}</small> : null}
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
              <button
                className="primary-btn"
                type="button"
                onClick={() => {
                  setRequestFormError('')
                  setRequestSuccessMessage('')
                  setShowRequestForm((current) => !current)
                }}
              >
                {showRequestForm ? 'Close Form' : 'New Request'}
              </button>
            </div>

            {catalogError ? <p className="error-message">{catalogError}</p> : null}
            {requestFormError ? <p className="error-message">{requestFormError}</p> : null}
            {requestSuccessMessage ? <p className="success-message">{requestSuccessMessage}</p> : null}
            {catalogLoading ? <p className="muted-copy">Loading software catalog...</p> : null}

            {showRequestForm ? (
              <form className="request-form" onSubmit={handleCreateSoftwareRequest}>
                <div className="request-form-grid">
                  <label>
                    Employee ID
                    <input
                      type="text"
                      value={requestEmployeeId}
                      onChange={(event) => setRequestEmployeeId(event.target.value)}
                      placeholder="EMP-1001"
                      aria-label="Employee ID"
                      disabled={requestSubmitting}
                    />
                  </label>
                  <label>
                    Software
                    <select
                      value={requestSoftwareName}
                      onChange={(event) => setRequestSoftwareName(event.target.value)}
                      aria-label="Software name"
                      disabled={requestSubmitting || catalogItems.length === 0}
                    >
                      {catalogItems.map((item) => (
                        <option key={item.software_id} value={item.name}>{item.name}</option>
                      ))}
                    </select>
                  </label>
                </div>
                <label>
                  Business justification
                  <textarea
                    value={requestJustification}
                    onChange={(event) => setRequestJustification(event.target.value)}
                    placeholder="Reason for this software request"
                    rows={3}
                    disabled={requestSubmitting}
                  />
                </label>
                <div className="request-form-actions">
                  <button className="primary-btn" type="submit" disabled={requestSubmitting}>
                    {requestSubmitting ? 'Submitting...' : 'Submit Request'}
                  </button>
                  <button
                    className="secondary-btn"
                    type="button"
                    disabled={requestSubmitting}
                    onClick={() => {
                      setShowRequestForm(false)
                      setRequestFormError('')
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}

            <div className="card-grid two-column">
              {catalogItems.map((item) => (
                <div key={item.software_id} className="info-card">
                  <span className="pill">{item.category}</span>
                  <h3>{item.name}</h3>
                  <p>{item.software_id}</p>
                  <small>
                    Approval: {item.approval_required ? 'Required' : 'Standard'} · ETA {item.estimated_fulfillment_hours}h
                  </small>
                </div>
              ))}
            </div>

            {softwareRequestLoading ? <p className="muted-copy">Loading request records...</p> : null}

            <div className="source-panel" style={{ marginTop: '1rem' }}>
              <h3>Provisioning Request Records</h3>
              <ul>
              {softwareRequests.map((request) => (
                  <li key={request.request_id}>
                    <strong>{request.request_id}</strong>
                    <span>{request.software_name}</span>
                    <small>Status: {String(request.status || '').toUpperCase()}</small>
                    <small>Created: {toReadableTime(request.created_at)}</small>
                    <small>Updated: {toReadableTime(request.updated_at)}</small>
                    <small>ServiceNow Ref: {request.service_now_ref || 'N/A'}</small>
                    <small>
                      Progress: {provisioningProgression.map((step) => {
                        const isCurrent = String(request.status || '').toLowerCase() === step
                        return isCurrent ? `[${step}]` : step
                      }).join(' → ')}
                    </small>
                    <button
                      className="secondary-btn"
                      type="button"
                      onClick={() => setSelectedSoftwareRequest(request)}
                    >
                      View Analysis
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <div className="source-panel" style={{ marginTop: '1rem' }}>
              <h3>Request Status Lifecycle</h3>
              <ul>
                {catalogLifecycle.map((status) => (
                  <li key={status}>
                    <strong>{status}</strong>
                  </li>
                ))}
              </ul>
            </div>

            <div className="source-panel" style={{ marginTop: '1rem' }}>
              <h3>AI Analysis Panel</h3>
              <ul>
                <li><span>Intent</span><strong>service_request</strong></li>
                <li><span>Category</span><strong>Software / Provisioning</strong></li>
                <li><span>Confidence</span><strong>92%</strong></li>
                <li>
                  <span>Resolution</span>
                  <strong>
                    {selectedSoftwareRequest
                      ? `Track ${selectedSoftwareRequest.software_name} request through the provisioning lifecycle and update delivery status.`
                      : 'Select a request to view recommendations.'}
                  </strong>
                </li>
                <li><span>Sources</span><strong>Approved software catalog</strong></li>
                <li>
                  <span>ServiceNow ref</span>
                  <strong>{selectedSoftwareRequest?.service_now_ref || 'N/A'}</strong>
                </li>
              </ul>
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
                  <button className="primary-btn" type="button" onClick={submitTicket} disabled={ticketSaving}>
                    {ticketSaving ? 'Creating Ticket...' : 'Save Ticket'}
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

                  {chatAnalysis ? (
                    <section className="response-summary-card">
                      <div className="response-summary-header">
                        <h3>AI Summary</h3>
                        <span className="pill">{chatAnalysis.intent || 'analysis'}</span>
                      </div>
                      <p>{chatAnalysis.summary || 'No summary generated.'}</p>
                      <div className="response-summary-meta">
                        <span>Category: {chatAnalysis.category || 'N/A'} / {chatAnalysis.sub_category || 'N/A'}</span>
                        <span>Next action: {chatAnalysis.assignment_group || 'Support Team'}</span>
                      </div>
                      <div className="response-summary-actions">
                        <button className="secondary-btn" type="button" onClick={handleCreateTicketFromChat}>Create Ticket</button>
                        <button className="secondary-btn" type="button" onClick={handleAcceptResolution}>Accept Resolution</button>
                        <button className="primary-btn" type="button" onClick={handleEscalateIssue}>Escalate</button>
                      </div>
                      {chatNextAction ? <small>Action selected: {chatNextAction}</small> : null}
                    </section>
                  ) : null}

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
              {chatAnalysis ? (
                <ul>
                  <li><span>Intent</span><strong>{chatAnalysis.intent || 'N/A'}</strong></li>
                  <li><span>Category</span><strong>{chatAnalysis.category || 'N/A'} / {chatAnalysis.sub_category || 'N/A'}</strong></li>
                  <li><span>Confidence</span><strong>{Math.round((chatAnalysis.confidence || 0) * 100)}%</strong></li>
                  <li><span>Resolution</span><strong>{chatAnalysis.suggested_resolution || 'No recommendation available.'}</strong></li>
                  <li><span>ServiceNow ref</span><strong>{selectedTicket?.service_now_ref || 'Not assigned'}</strong></li>
                  <li>
                    <span>Sources</span>
                    <strong>{chatSources.length > 0 ? `${chatSources.length} source(s)` : 'No sources'}</strong>
                  </li>
                  {chatSources.map((source) => (
                    <li key={source.article_id}>
                      <span>Source</span>
                      <strong>{source.title}</strong>
                      <small>{source.source_file}</small>
                    </li>
                  ))}
                </ul>
              ) : isTicketFlow ? (
                <ul>
                  <li><span>Intent</span><strong>incident</strong></li>
                  <li><span>Category</span><strong>Network / VPN</strong></li>
                  <li><span>Confidence</span><strong>Pending analysis</strong></li>
                  <li><span>Resolution</span><strong>Collect details and create ticket.</strong></li>
                  <li><span>ServiceNow ref</span><strong>Not assigned</strong></li>
                  <li><span>Sources</span><strong>Knowledge lookup after first response</strong></li>
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
