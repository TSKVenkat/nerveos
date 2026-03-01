import { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Users, AlertTriangle, BarChart3,
  FileText, MessageSquare, Zap, RefreshCw, Send
} from 'lucide-react';
import { getDashboard, getPendingActions, askQuestion, getMorningBriefing } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

function MetricCard({ name, value, unit, change, icon: Icon }) {
  const isPositive = change > 0;
  const isNegative = change < 0;
  const changeColor = name === 'churn_rate'
    ? (isPositive ? 'text-red-400' : 'text-emerald-400')
    : (isPositive ? 'text-emerald-400' : 'text-red-400');

  const formatValue = (val) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
    return val?.toFixed?.(1) ?? val;
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          {name.replace(/_/g, ' ')}
        </span>
        {Icon && <Icon className="w-4 h-4 text-gray-600" />}
      </div>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-white">{formatValue(value)}</span>
        <span className="text-sm text-gray-500">{unit}</span>
      </div>
      {change !== null && change !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs ${changeColor}`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {isPositive ? '+' : ''}{change}%
          <span className="text-gray-500 ml-1">vs prev</span>
        </div>
      )}
    </div>
  );
}

function AlertCard({ alert }) {
  const severityColors = {
    info: 'border-blue-800 bg-blue-500/5',
    warning: 'border-amber-800 bg-amber-500/5',
    critical: 'border-red-800 bg-red-500/5',
  };

  return (
    <div className={`p-3 rounded-lg border ${severityColors[alert.severity] || severityColors.info}`}>
      <div className="flex items-start gap-2">
        <AlertTriangle className={`w-4 h-4 mt-0.5 ${
          alert.severity === 'critical' ? 'text-red-400' :
          alert.severity === 'warning' ? 'text-amber-400' : 'text-blue-400'
        }`} />
        <div>
          <p className="text-sm font-medium text-gray-200">{alert.title}</p>
          <p className="text-xs text-gray-400 mt-1">{alert.message}</p>
          <p className="text-[10px] text-gray-600 mt-1">{alert.source} · {new Date(alert.created_at).toLocaleDateString()}</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [asking, setAsking] = useState(false);
  const [briefing, setBriefing] = useState(null);
  const [briefingLoading, setBriefingLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dash, actions] = await Promise.all([
        getDashboard().catch(() => null),
        getPendingActions().catch(() => []),
      ]);
      setDashboard(dash);
      setPending(actions);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const result = await askQuestion(question);
      setAnswer(result.answer);
    } catch { setAnswer('Failed to get answer. Is Ollama running?'); }
    finally { setAsking(false); }
  };

  const handleBriefing = async () => {
    setBriefingLoading(true);
    try {
      const result = await getMorningBriefing();
      setBriefing(result);
    } catch { setBriefing({ error: 'Failed to generate briefing' }); }
    finally { setBriefingLoading(false); }
  };

  const metrics = dashboard?.metrics || {};
  const pipeline = dashboard?.pipeline || {};
  const alerts = dashboard?.alerts || [];
  const intel = dashboard?.intel_summary || {};

  const metricIcons = {
    mrr: BarChart3,
    new_leads: Users,
    churn_rate: TrendingDown,
    nps_score: TrendingUp,
    support_tickets: MessageSquare,
  };

  // Build chart data from metrics
  const metricEntries = Object.entries(metrics);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-sm text-gray-400 mt-1">Your AI-powered business at a glance</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleBriefing} disabled={briefingLoading}
            className="btn btn-primary">
            <Zap className="w-4 h-4" />
            {briefingLoading ? 'Generating...' : 'Morning Briefing'}
          </button>
          <button onClick={fetchData} disabled={loading} className="btn btn-secondary">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {metricEntries.map(([name, data]) => (
          <MetricCard
            key={name}
            name={name}
            value={data.value}
            unit={data.unit}
            change={data.change_pct}
            icon={metricIcons[name]}
          />
        ))}
      </div>

      {/* Mid Row — Pipeline + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales Pipeline */}
        <div className="card lg:col-span-1">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            Sales Pipeline
          </h3>
          <div className="text-3xl font-bold text-white mb-1">
            ${(pipeline.total_pipeline_value || 0).toLocaleString()}
          </div>
          <p className="text-xs text-gray-400 mb-4">{pipeline.total_contacts || 0} contacts</p>
          <div className="space-y-2">
            {Object.entries(pipeline.by_stage || {}).map(([stage, data]) => (
              <div key={stage} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    stage === 'won' ? 'bg-emerald-400' :
                    stage === 'proposal' ? 'bg-nerve-400' :
                    stage === 'qualified' ? 'bg-amber-400' :
                    stage === 'lost' ? 'bg-red-400' : 'bg-gray-500'
                  }`} />
                  <span className="text-sm text-gray-300 capitalize">{stage}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium text-gray-200">{data.count}</span>
                  <span className="text-xs text-gray-500 ml-2">${data.value.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Active Alerts
            </h3>
            <span className="badge badge-warning">{alerts.length} active</span>
          </div>
          <div className="space-y-3 max-h-64 overflow-auto">
            {alerts.length === 0 ? (
              <p className="text-sm text-gray-500">No active alerts</p>
            ) : (
              alerts.map((alert) => <AlertCard key={alert.id} alert={alert} />)
            )}
          </div>
        </div>
      </div>

      {/* Bottom Row — NL Query + Intel + Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Natural Language Query */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            Ask Your Business
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
              placeholder="How did this month's sales compare to last quarter?"
              className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm
                         text-gray-200 placeholder-gray-500 focus:outline-none focus:border-nerve-500"
            />
            <button onClick={handleAsk} disabled={asking} className="btn btn-primary">
              <Send className="w-4 h-4" />
            </button>
          </div>
          {answer && (
            <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
              <p className="text-sm text-gray-200 whitespace-pre-wrap">{answer}</p>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            Quick Stats
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Intel reports this week</span>
              <span className="text-lg font-bold text-nerve-400">{intel.reports_this_week || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Unread reports</span>
              <span className="text-lg font-bold text-amber-400">{intel.unread_reports || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Pending actions</span>
              <span className="text-lg font-bold text-red-400">{pending.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Morning Briefing */}
      {briefing && (
        <div className="card border-nerve-800">
          <h3 className="text-sm font-semibold text-nerve-400 uppercase tracking-wider mb-4">
            <Zap className="w-4 h-4 inline mr-2" />
            Morning Briefing
          </h3>
          {briefing.error ? (
            <p className="text-sm text-red-400">{briefing.error}</p>
          ) : (
            <div className="space-y-4">
              {briefing.market_intel && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase">Market Intel</h4>
                  <p className="text-sm text-gray-300 mt-1">
                    Status: {briefing.market_intel.status} — {briefing.market_intel.reports || 0} reports
                  </p>
                </div>
              )}
              {briefing.email && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase">Email</h4>
                  <p className="text-sm text-gray-300 mt-1">
                    {briefing.email.new_emails || 0} new emails · {briefing.email.follow_ups_needed || 0} follow-ups needed
                  </p>
                </div>
              )}
              {briefing.dashboard?.anomalies?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase">Anomalies Detected</h4>
                  {briefing.dashboard.anomalies.map((a, i) => (
                    <p key={i} className="text-sm text-amber-300 mt-1">
                      {a.metric}: {a.change_pct > 0 ? '+' : ''}{a.change_pct}% (current: {a.current})
                    </p>
                  ))}
                </div>
              )}
              <p className="text-xs text-gray-500">
                Generated at {briefing.generated_at ? new Date(briefing.generated_at).toLocaleString() : 'now'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
