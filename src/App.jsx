import { useEffect, useMemo, useState } from 'react';
import { BrowserRouter, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import { fetchJSON, postJSON, requestJSON } from './services/api';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: '▣' },
  { to: '/agents', label: 'AI Agents', icon: '◌' },
  { to: '/transactions', label: 'Transactions', icon: '◎' },
  { to: '/mandates', label: 'Mandates', icon: '◍' },
  { to: '/analytics', label: 'Analytics', icon: '◔' },
  { to: '/settings', label: 'Settings', icon: '⚙' }
];

const pageMeta = {
  '/dashboard': { title: 'Dashboard', eyebrow: 'Command centre' },
  '/agents': { title: 'AI Agents', eyebrow: 'Agent fleet' },
  '/transactions': { title: 'Transactions', eyebrow: 'Payment intelligence' },
  '/mandates': { title: 'Mandates', eyebrow: 'Spending rules' },
  '/analytics': { title: 'Analytics', eyebrow: 'Performance insights' },
  '/settings': { title: 'Settings', eyebrow: 'Profile & controls' }
};

const statusColors = {
  online: '#66845C',
  idle: '#C9A66B',
  error: '#B94B45',
  processing: '#6F4E37',
  approved: '#66845C',
  pending: '#C9A66B',
  rejected: '#B94B45',
  failed: '#B94B45'
};

const formatCurrency = (value) => {
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  }

  if (typeof value === 'string' && value.startsWith('$')) {
    return value;
  }

  return '$0';
};

const formatDate = (dateValue) => {
  if (!dateValue) return '—';
  const d = new Date(dateValue);
  return Number.isNaN(d.getTime()) ? dateValue : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

function AppShell() {
  const location = useLocation();
  const meta = pageMeta[location.pathname] || pageMeta['/dashboard'];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">Z</div>
          <div className="brand-text">
            <span className="brand-name">Zentro</span>
            <small>Private AI</small>
          </div>
        </div>

        <nav className="nav-menu" aria-label="Sidebar navigation">
          <div className="nav-group">
            <span className="nav-label">Overview</span>
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
            <a className="nav-item" href="/mandate-pay.html">
              <span className="nav-icon" aria-hidden="true">◈</span>
              <span>Mandate Pay</span>
            </a>
          </div>
        </nav>

        <div className="upgrade-card">
          <div className="upgrade-badge">Elite</div>
          <h3>Private Treasury</h3>
          <p>Unlock deeper risk coverage and faster mandate reviews.</p>
          <button type="button" className="premium-btn">Upgrade</button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">{meta.eyebrow}</p>
            <h1>{meta.title}</h1>
          </div>
          <div className="topbar-actions">
            <label className="search-box" aria-label="Search">
              <span className="search-icon">⌕</span>
              <input type="text" placeholder="Search Zentro" />
            </label>
            <button type="button" className="icon-button" aria-label="Notifications">
              <span>◔</span>
              <em className="notification-dot" />
            </button>
            <div className="profile-pill">
              <div className="avatar">MC</div>
              <div>
                <strong>Maia Chen</strong>
                <small>Advisor</small>
              </div>
            </div>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/mandates" element={<MandatesPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AnimatePresence>
      </main>

      <FloatingChatbot />
    </div>
  );
}

function PageShell({ children }) {
  return (
    <motion.div
      className="page-shell"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

function LoadingState({ message = 'Loading Zentro data...' }) {
  return (
    <div className="loading-state">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="loader" aria-hidden="true" />
        <span>{message}</span>
      </div>
    </div>
  );
}

function ErrorState({ message }) {
  return <div className="error-state">{message || 'Something went wrong while loading this page.'}</div>;
}

function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const data = await fetchJSON('/api/dashboard');
        if (active) {
          setDashboard(data);
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load dashboard data.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  return (
    <PageShell>
      <section className="overview-strip">
        {dashboard.summaryCards.map((card) => (
          <div key={card.label} className={`metric-card ${card.accent ? 'accent' : ''}`}>
            <span className="metric-label">{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.note}</small>
          </div>
        ))}
      </section>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Overview</p>
              <h3>Spending overview</h3>
            </div>
            <span className={`status-badge ${dashboard.dataSource === 'demo' ? 'demo' : 'live'}`}>
              {dashboard.dataSource === 'demo' ? 'Demo data' : 'Verified data'}
            </span>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dashboard.spendingTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(111,78,55,0.15)" />
                <XAxis dataKey="name" stroke="#817467" />
                <YAxis stroke="#817467" />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Legend />
                <Line type="monotone" dataKey="amount" stroke="#6F4E37" strokeWidth={3} name="Spending" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Budget</p>
              <h3>Remaining budget</h3>
            </div>
          </div>
          <div className="status-list">
            {dashboard.mandates.slice(0, 3).map((mandate) => (
              <div key={mandate.id} className="status-row">
                <div>
                  <strong>{mandate.name}</strong>
                  <div className="meta-label">{mandate.status}</div>
                </div>
                <span className="pill-positive">{formatCurrency(mandate.remainingBudget)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="lower-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Movement</p>
              <h3>Recent transactions</h3>
            </div>
            <button type="button" className="secondary-btn">View all</button>
          </div>
          <div className="transactions-list">
            {dashboard.recentTransactions.map((transaction) => (
              <div key={transaction.id} className="transaction-row">
                <div className="transaction-main">
                  <strong>{transaction.merchant}</strong>
                  <span className="meta-label">{transaction.category} • {formatDate(transaction.date)}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="badge badge--approve">{transaction.status}</span>
                  <strong>{formatCurrency(transaction.amount)}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Policy</p>
              <h3>Active mandates</h3>
            </div>
          </div>
          <div className="mandates-list">
            {dashboard.mandates.map((mandate) => (
              <div key={mandate.id} className="mandate-row">
                <div className="mandate-main">
                  <strong>{mandate.name}</strong>
                  <span className="meta-label">{mandate.status} • {mandate.allowedCategories.join(', ')}</span>
                </div>
                <span className="badge pending">{formatCurrency(mandate.remainingBudget)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Activity</p>
              <h3>AI agent activity</h3>
            </div>
          </div>
          <div className="activity-list">
            {dashboard.agentActivity.map((agent) => (
              <div key={agent.name} className="activity-row">
                <div className="activity-main">
                  <strong>{agent.name}</strong>
                  <span className="meta-label">{agent.currentActivity}</span>
                </div>
                <span className="status-pill" style={{ color: statusColors[agent.status], background: `${statusColors[agent.status]}1a` }}>
                  <span className="status-dot" />{agent.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Insights</p>
              <h3>Category mix</h3>
            </div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dashboard.categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(111,78,55,0.15)" />
                <XAxis dataKey="name" stroke="#817467" />
                <YAxis stroke="#817467" />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Bar dataKey="value" fill="#6F4E37" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </PageShell>
  );
}

function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadAgents() {
      try {
        const data = await fetchJSON('/api/agents');
        if (active) {
          setAgents(data.agents || []);
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load AI agents.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAgents();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  return (
    <PageShell>
      <div className="agent-card-grid">
        {agents.map((agent) => (
          <div key={agent.name} className={`agent-card ${agent.status === 'online' ? 'is-active' : ''}`}>
            <div className="agent-header-row">
              <div className={`agent-icon ${agent.iconClass || 'soft-sage'}`}>
                {agent.shortLabel || 'AI'}
              </div>
              <span className="status-pill" style={{ color: statusColors[agent.status] || '#6F4E37', background: `${statusColors[agent.status] || '#6F4E37'}1a` }}>
                <span className="status-dot" />{agent.status}
              </span>
            </div>
            <h3>{agent.name}</h3>
            <p>{agent.description}</p>
            <div className="agent-meta">
              <span>{agent.currentActivity}</span>
              <span>{agent.confidence}% confidence</span>
            </div>
          </div>
        ))}
      </div>

      <div className="lower-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Execution log</p>
              <h3>Live history</h3>
            </div>
          </div>
          <div className="timeline">
            {agents[0]?.history?.map((entry, index) => (
              <div key={`${entry.label}-${index}`} className={`timeline-item ${entry.state}`}>
                <div className="dot" />
                <div className="event-copy">
                  <h4>{entry.label}</h4>
                  <p>{entry.summary}</p>
                  <time>{entry.time}</time>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Decision engine</p>
              <h3>Current evaluation</h3>
            </div>
          </div>
          <div className="field-group">
            <label>Selected agent</label>
            <input type="text" value={agents[0]?.name || 'Mandate Creator'} readOnly />
          </div>
          <div className="field-group">
            <label>Last decision</label>
            <input type="text" value={agents[0]?.decision || 'APPROVE'} readOnly />
          </div>
          <div className="field-group">
            <label>Risk score</label>
            <input type="text" value={agents[0]?.riskScore ?? 12} readOnly />
          </div>
          <button type="button" className="primary-btn">View details</button>
        </div>
      </div>
    </PageShell>
  );
}

function TransactionsPage() {
  const [transactions, setTransactions] = useState([]);
  const [search, setSearch] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [amountFilter, setAmountFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedTxId, setSelectedTxId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadTransactions() {
      try {
        const data = await fetchJSON('/api/transactions');
        if (active) {
          setTransactions(data.transactions || []);
          if ((data.transactions || []).length > 0) {
            setSelectedTxId(data.transactions[0].id);
          }
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load transactions.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadTransactions();
    return () => {
      active = false;
    };
  }, []);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((transaction) => {
      const matchesSearch = !search || [transaction.merchant, transaction.category, transaction.paymentReference, transaction.id]
        .join(' ')
        .toLowerCase()
        .includes(search.toLowerCase());

      const matchesDate = !dateFilter || transaction.date === dateFilter;

      const matchesAmount = (() => {
        if (amountFilter === 'all') return true;
        if (amountFilter === 'lt500') return Number(transaction.amount) < 500;
        if (amountFilter === '500-1500') return Number(transaction.amount) >= 500 && Number(transaction.amount) <= 1500;
        if (amountFilter === 'gt1500') return Number(transaction.amount) > 1500;
        return true;
      })();

      const matchesStatus = statusFilter === 'all' || transaction.status === statusFilter;
      return matchesSearch && matchesDate && matchesAmount && matchesStatus;
    });
  }, [transactions, search, dateFilter, amountFilter, statusFilter]);

  const selectedTransaction = filteredTransactions.find((item) => item.id === selectedTxId) || filteredTransactions[0] || null;

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  return (
    <PageShell>
      <div className="page-tools">
        <button type="button" className="primary-btn">Export report</button>
        <button type="button" className="ghost-btn">Refresh data</button>
      </div>

      <div className="panel">
        <div className="filter-controls">
          <div>
            <label>Search</label>
            <input type="text" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Merchant or ref" />
          </div>
          <div>
            <label>Date</label>
            <input type="date" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} />
          </div>
          <div>
            <label>Amount</label>
            <select value={amountFilter} onChange={(event) => setAmountFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="lt500">Under $500</option>
              <option value="500-1500">$500 to $1,500</option>
              <option value="gt1500">Over $1,500</option>
            </select>
          </div>
          <div>
            <label>Status</label>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="approved">Approved</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Ledger</p>
              <h3>Transaction history</h3>
            </div>
          </div>
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Merchant</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Reference</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan="5"><div className="empty-state">No transactions match the selected filters.</div></td>
                  </tr>
                ) : (
                  filteredTransactions.map((transaction) => (
                    <tr key={transaction.id} onClick={() => setSelectedTxId(transaction.id)} style={{ cursor: 'pointer' }}>
                      <td>{transaction.merchant}</td>
                      <td>{formatDate(transaction.date)}</td>
                      <td>{formatCurrency(transaction.amount)}</td>
                      <td><span className={`badge ${transaction.status}`}>{transaction.status}</span></td>
                      <td>{transaction.paymentReference}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="details-panel">
          {selectedTransaction ? (
            <>
              <h3>{selectedTransaction.merchant}</h3>
              <div className="details-grid">
                <div className="detail-box">
                  <strong>Amount</strong>
                  {formatCurrency(selectedTransaction.amount)}
                </div>
                <div className="detail-box">
                  <strong>Status</strong>
                  <span className={`badge ${selectedTransaction.status}`}>{selectedTransaction.status}</span>
                </div>
                <div className="detail-box">
                  <strong>Payment reference</strong>
                  {selectedTransaction.paymentReference}
                </div>
                <div className="detail-box">
                  <strong>Category</strong>
                  {selectedTransaction.category}
                </div>
                <div className="detail-box">
                  <strong>AI evaluation</strong>
                  {selectedTransaction.aiEvaluation?.result || 'Not available'}
                </div>
                <div className="detail-box">
                  <strong>Agent</strong>
                  {selectedTransaction.aiEvaluation?.agent || 'Pending'}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">Select a transaction to view details.</div>
          )}
        </div>
      </div>
    </PageShell>
  );
}

function MandatesPage() {
  const [mandates, setMandates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState({ type: '', message: '' });
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    name: 'Travel and Lifestyle',
    monthlyLimit: 6000,
    perPurchaseLimit: 1800,
    approvalThreshold: 85,
    allowedCategories: 'Travel,Dining,Technology,Wellness',
    prohibitedCategories: 'Crypto,Gambling',
    sellerRestrictions: 'No marketplace sellers',
    status: 'active'
  });

  useEffect(() => {
    let active = true;

    async function loadMandates() {
      try {
        const data = await fetchJSON('/api/mandates');
        if (active) {
          setMandates(data.mandates || []);
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load mandates.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadMandates();
    return () => {
      active = false;
    };
  }, []);

  const handleFieldChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setNotice({ type: '', message: '' });

    try {
      const payload = {
        ...form,
        action: editingId ? 'update' : 'create',
        id: editingId || undefined,
        allowedCategories: form.allowedCategories.split(',').map((item) => item.trim()).filter(Boolean),
        prohibitedCategories: form.prohibitedCategories.split(',').map((item) => item.trim()).filter(Boolean),
        sellerRestrictions: form.sellerRestrictions.split(',').map((item) => item.trim()).filter(Boolean)
      };

      const response = await postJSON('/api/mandates', payload);
      setMandates(response.mandates || []);
      setNotice({ type: 'success', message: response.message || 'Mandate saved and validated.' });
      setEditingId(null);
      setForm({
        name: 'Travel and Lifestyle',
        monthlyLimit: 6000,
        perPurchaseLimit: 1800,
        approvalThreshold: 85,
        allowedCategories: 'Travel,Dining,Technology,Wellness',
        prohibitedCategories: 'Crypto,Gambling',
        sellerRestrictions: 'No marketplace sellers',
        status: 'active'
      });
    } catch (err) {
      setNotice({ type: 'error', message: err.message || 'Backend validation blocked this change.' });
    }
  };

  const handleEdit = (mandate) => {
    setEditingId(mandate.id);
    setForm({
      name: mandate.name,
      monthlyLimit: mandate.monthlyLimit,
      perPurchaseLimit: mandate.perPurchaseLimit,
      approvalThreshold: mandate.approvalThreshold,
      allowedCategories: (mandate.allowedCategories || []).join(', '),
      prohibitedCategories: (mandate.prohibitedCategories || []).join(', '),
      sellerRestrictions: (mandate.sellerRestrictions || []).join(', '),
      status: mandate.status
    });
  };

  const handleToggleStatus = async (mandate) => {
    try {
      const updated = await requestJSON(`/api/mandates/${mandate.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ active: !mandate.active })
      });
      setMandates(updated.mandates || []);
      setNotice({ type: 'success', message: `Mandate ${mandate.name} updated.` });
    } catch (err) {
      setNotice({ type: 'error', message: err.message || 'Unable to change mandate status.' });
    }
  };

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  return (
    <PageShell>
      {notice.message ? <div className={`notice-box ${notice.type}`}>{notice.message}</div> : null}

      <div className="form-card">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Mandate controls</p>
            <h3>{editingId ? 'Edit mandate' : 'Create new mandate'}</h3>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="field-group">
              <label>Mandate name</label>
              <input type="text" name="name" value={form.name} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Status</label>
              <select name="status" value={form.status} onChange={handleFieldChange}>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="draft">Draft</option>
              </select>
            </div>
            <div className="field-group">
              <label>Monthly spend limit</label>
              <input type="number" name="monthlyLimit" value={form.monthlyLimit} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Per purchase limit</label>
              <input type="number" name="perPurchaseLimit" value={form.perPurchaseLimit} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Approval threshold (%)</label>
              <input type="number" name="approvalThreshold" value={form.approvalThreshold} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Allowed categories</label>
              <input type="text" name="allowedCategories" value={form.allowedCategories} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Prohibited categories</label>
              <input type="text" name="prohibitedCategories" value={form.prohibitedCategories} onChange={handleFieldChange} />
            </div>
            <div className="field-group">
              <label>Seller restrictions</label>
              <input type="text" name="sellerRestrictions" value={form.sellerRestrictions} onChange={handleFieldChange} />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="primary-btn">{editingId ? 'Save mandate' : 'Create mandate'}</button>
            <button type="button" className="secondary-btn" onClick={() => setEditingId(null)}>Clear</button>
          </div>
        </form>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Policy engine</p>
            <h3>Decision preview</h3>
          </div>
        </div>
        <div className="overview-strip" style={{ marginTop: '12px' }}>
          <div className="metric-card accent">
            <span className="metric-label">Current spend cap</span>
            <strong>₹5,000</strong>
            <small>Max transaction threshold</small>
          </div>
          <div className="metric-card">
            <span className="metric-label">Active mandates</span>
            <strong>{mandates.filter((item) => item.active).length}</strong>
            <small>Live policy runs</small>
          </div>
          <div className="metric-card">
            <span className="metric-label">Approval gates</span>
            <strong>3</strong>
            <small>Pending user confirmation</small>
          </div>
        </div>
        <div className="transactions-list" style={{ marginTop: '14px' }}>
          {[
            { label: 'APPROVED', detail: 'Laptop refresh below spending cap', badge: 'badge--approve' },
            { label: 'BLOCKED', detail: 'Luxury jewelry outside allowed categories', badge: 'badge rejected' },
            { label: 'ESCALATED', detail: 'High-value electronics requiring approval', badge: 'badge pending' }
          ].map((status) => (
            <div key={status.label} className="transaction-row">
              <div className="transaction-main">
                <strong>{status.label}</strong>
                <span className="meta-label">{status.detail}</span>
              </div>
              <span className={status.badge}>{status.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Rules</p>
            <h3>Mandate library</h3>
          </div>
        </div>
        <div className="mandates-list">
          {mandates.map((mandate) => (
            <div key={mandate.id} className="mandate-row">
              <div className="mandate-main">
                <strong>{mandate.name}</strong>
                <span className="meta-label">Monthly {formatCurrency(mandate.monthlyLimit)} • Per purchase {formatCurrency(mandate.perPurchaseLimit)} • Remaining {formatCurrency(mandate.remainingBudget)}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button type="button" className="secondary-btn" onClick={() => handleEdit(mandate)}>Edit</button>
                <button type="button" className="action-btn" onClick={() => handleToggleStatus(mandate)}>{mandate.active ? 'Deactivate' : 'Activate'}</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageShell>
  );
}

function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function loadAnalytics() {
      try {
        const data = await fetchJSON('/api/analytics');
        if (active) {
          setAnalytics(data);
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load analytics.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAnalytics();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  const pieData = analytics.approvalBreakdown || [];
  const pieColors = ['#6F4E37', '#A8BFA0', '#C9A66B'];

  return (
    <PageShell>
      <div className="overview-strip">
        {analytics.summaryCards.map((card) => (
          <div key={card.label} className="metric-card">
            <span className="metric-label">{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.note}</small>
          </div>
        ))}
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Trend</p>
              <h3>Monthly spending</h3>
            </div>
            <span className={`status-badge ${analytics.dataSource === 'demo' ? 'demo' : 'live'}`}>
              {analytics.dataSource === 'demo' ? 'Demo data' : 'Verified data'}
            </span>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.spendingTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(111,78,55,0.15)" />
                <XAxis dataKey="month" stroke="#817467" />
                <YAxis stroke="#817467" />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Line type="monotone" dataKey="amount" stroke="#A8BFA0" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Breakdown</p>
              <h3>Approved vs rejected</h3>
            </div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={45} outerRadius={70} dataKey="value" nameKey="name" paddingAngle={4}>
                  {pieData.map((entry, index) => (
                    <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Categories</p>
              <h3>Category-wise spending</h3>
            </div>
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.categoryBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(111,78,55,0.15)" />
                <XAxis dataKey="category" stroke="#817467" />
                <YAxis stroke="#817467" />
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                <Bar dataKey="amount" fill="#6F4E37" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">Performance</p>
              <h3>Agent performance</h3>
            </div>
          </div>
          <div className="status-list">
            {analytics.agentStats.map((item) => (
              <div key={item.name} className="status-row">
                <div>
                  <strong>{item.name}</strong>
                  <div className="meta-label">{item.activity}</div>
                </div>
                <span className="pill-positive">{item.score}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}

function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      try {
        const data = await fetchJSON('/api/settings');
        if (active) {
          setSettings(data.settings || {});
          setError('');
        }
      } catch (err) {
        if (active) {
          setError(err.message || 'Unable to load settings.');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadSettings();
    return () => {
      active = false;
    };
  }, []);

  const handleChange = (event) => {
    const { name, value, checked, type } = event.target;
    setSettings((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = async (event) => {
    event.preventDefault();
    try {
      const result = await postJSON('/api/settings', settings);
      setMessage(result.message || 'Settings updated successfully.');
    } catch (err) {
      setMessage(err.message || 'Unable to save settings.');
    }
  };

  if (loading) return <PageShell><LoadingState /></PageShell>;
  if (error) return <PageShell><ErrorState message={error} /></PageShell>;

  return (
    <PageShell>
      {message ? <div className="notice-box success">{message}</div> : null}

      <form onSubmit={handleSave}>
        <div className="settings-grid">
          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Profile</p>
                <h3>User profile</h3>
              </div>
            </div>
            <div className="field-group">
              <label>Full name</label>
              <input type="text" name="fullName" value={settings.fullName || ''} onChange={handleChange} />
            </div>
            <div className="field-group">
              <label>Email</label>
              <input type="email" name="email" value={settings.email || ''} onChange={handleChange} />
            </div>
            <div className="field-group">
              <label>Timezone</label>
              <input type="text" name="timezone" value={settings.timezone || ''} onChange={handleChange} />
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Preferences</p>
                <h3>AI assistant</h3>
              </div>
            </div>
            <div className="field-group">
              <label>Default assistant mode</label>
              <select name="assistantMode" value={settings.assistantMode || 'guided'} onChange={handleChange}>
                <option value="guided">Guided</option>
                <option value="autonomous">Autonomous</option>
                <option value="minimal">Minimal</option>
              </select>
            </div>
            <div className="field-group">
              <label>Theme</label>
              <select name="theme" value={settings.theme || 'luxury'} onChange={handleChange}>
                <option value="luxury">Luxury</option>
                <option value="dark">Dark</option>
                <option value="ivory">Ivory</option>
              </select>
            </div>
            <div className="inline-toggle">
              <input className="checkbox" type="checkbox" name="notificationsEnabled" checked={settings.notificationsEnabled || false} onChange={handleChange} />
              <label>Email notifications enabled</label>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Security</p>
                <h3>Account status</h3>
              </div>
            </div>
            <div className="status-list">
              <div className="status-row">
                <span>Two-factor</span>
                <span className="status-badge live">{settings.mfaStatus || 'Enabled'}</span>
              </div>
              <div className="status-row">
                <span>Session timeout</span>
                <span>{settings.sessionTimeout || '30 mins'}</span>
              </div>
              <div className="status-row">
                <span>API connectivity</span>
                <span className="status-badge live">{settings.apiStatus || 'Healthy'}</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">Sync</p>
                <h3>API connections</h3>
              </div>
            </div>
            <div className="status-list">
              <div className="status-row">
                <span>Gemini</span>
                <span className="status-badge live">{settings.geminiStatus || 'Connected'}</span>
              </div>
              <div className="status-row">
                <span>PayPal</span>
                <span className="status-badge demo">{settings.paypalStatus || 'Ready'}</span>
              </div>
              <div className="status-row">
                <span>Last sync</span>
                <span>{settings.lastSync || 'Just now'}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="primary-btn">Save settings</button>
        </div>
      </form>
    </PageShell>
  );
}

function FloatingChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: 'Hi, I’m Zentro AI. Ask about spending, mandates, or the latest AI agent activity.',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('');

  const pushMessage = (role, text) => {
    setMessages((current) => [
      ...current,
      {
        role,
        text,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  const answerQuickAction = async (action) => {
    setLoading(true);

    try {
      let data;
      if (action === 'Check My Spending') {
        data = await fetchJSON('/api/dashboard');
        const summary = data.summaryCards?.find((card) => card.label === 'Total spend') || data.summaryCards?.[0];
        pushMessage('ai', `Your current spend snapshot is ${summary?.value || 'unavailable'}. Remaining policy headroom is shown in the dashboard and will refresh with backend data.`);
      } else if (action === 'Explain My Mandate') {
        data = await fetchJSON('/api/mandates');
        const activeMandates = (data.mandates || []).filter((item) => item.active).map((item) => item.name).join(', ');
        pushMessage('ai', `Your active mandates are ${activeMandates || 'currently unavailable'}. I can help review limits, categories, and approval thresholds.`);
      } else if (action === 'Analyse Transactions') {
        data = await fetchJSON('/api/analytics');
        pushMessage('ai', `I reviewed the transaction trends. Total spending is ${data.summaryCards?.[0]?.value || 'unavailable'} with ${data.summaryCards?.[2]?.value || 'unavailable'} in the current month.`);
      } else if (action === 'Evaluate a Purchase') {
        data = await fetchJSON('/api/transactions');
        const latest = data.transactions?.[0];
        pushMessage('ai', `Latest purchase review: ${latest?.merchant || 'No merchant available'} is marked ${latest?.status || 'unknown'} with AI evaluation ${latest?.aiEvaluation?.result || 'pending'}.`);
      } else {
        data = await fetchJSON('/api/agents');
        const summary = data.agents?.map((agent) => `${agent.name}: ${agent.status}`).join(' • ') || 'No agent data available';
        pushMessage('ai', `AI agent status: ${summary}`);
      }

      setLastUpdated(data?.lastUpdated || new Date().toISOString());
    } catch (err) {
      pushMessage('ai', 'I could not reach the live Zentro backend right now. Please check connectivity or retry later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!input.trim()) return;

    const currentInput = input.trim();
    setInput('');
    pushMessage('user', currentInput);
    setLoading(true);

    try {
      const response = await postJSON('/chat/message', { message: currentInput });
      setLastUpdated(response.lastUpdated || new Date().toISOString());
      pushMessage('ai', response.answer || 'I could not answer that question with the current data.');
    } catch (err) {
      pushMessage('ai', err.message || 'The backend is currently unavailable, so I cannot fetch live data for this request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="floating-chatbot">
      {isOpen && (
        <motion.div
          className="chat-panel"
          initial={{ opacity: 0, y: 12, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 12, scale: 0.96 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
        >
          <div className="chat-header">
            <div className="chat-brand">
              <span className="chat-brand-mark">Z</span>
              <span>Zentro AI</span>
            </div>
            <button type="button" className="chat-close" onClick={() => setIsOpen(false)} aria-label="Close chat">×</button>
          </div>

          <div className="chat-body">
            <div className="quick-actions">
              {['Check My Spending', 'Explain My Mandate', 'Analyse Transactions', 'Evaluate a Purchase', 'View AI Agent Activity'].map((action) => (
                <button key={action} type="button" className="quick-action" onClick={() => answerQuickAction(action)}>{action}</button>
              ))}
            </div>

            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`chat-entry ${message.role}`}>
                <div className={`chat-bubble ${message.role}`}>{message.text}</div>
                <span className="chat-timestamp">{message.time}</span>
              </div>
            ))}

            {loading ? (
              <div className="loader-row">
                <span className="loader" aria-hidden="true" style={{ width: 18, height: 18 }} />
                Zentro is thinking...
              </div>
            ) : null}
          </div>

          <div className="chat-input-wrap">
            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about your spending or mandates"
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSubmit(event);
                }
              }}
            />
            <button type="button" className="chat-send" onClick={handleSubmit} aria-label="Send message">➤</button>
          </div>

          {lastUpdated ? <div style={{ padding: '0 14px 12px', fontSize: '0.72rem', color: '#817467' }}>Last updated: {new Date(lastUpdated).toLocaleString()}</div> : null}
        </motion.div>
      )}

      <button type="button" className="chat-toggle" onClick={() => setIsOpen((current) => !current)} aria-label="Open AI assistant">
        {isOpen ? '×' : 'AI'}
        <span className="chat-notification" aria-hidden="true" />
      </button>
    </div>
  );
}
