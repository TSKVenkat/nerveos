import { useState, useEffect } from 'react';
import {
  Radar, Search, Plus, RefreshCw, TrendingUp, Newspaper,
  DollarSign, Brain, X, Globe, Trash2
} from 'lucide-react';
import {
  getCompetitors, addCompetitor, deleteCompetitor,
  getTopics, addTopic, getReports, runMarketScan,
  quickSearch, getDigest, getTrending, getStockInfo
} from '../lib/api';

function CompetitorCard({ comp, onScan, onDelete }) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-white">{comp.name}</h4>
          <p className="text-xs text-gray-500 mt-0.5">{comp.domain}</p>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => onDelete(comp.id)} className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-red-400">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <div className="flex items-center gap-2 mt-3">
        {comp.track_news && <span className="badge badge-info"><Newspaper className="w-3 h-3 mr-1" />News</span>}
        {comp.track_trends && <span className="badge badge-info"><TrendingUp className="w-3 h-3 mr-1" />Trends</span>}
        {comp.track_finance && <span className="badge badge-success"><DollarSign className="w-3 h-3 mr-1" />{comp.ticker_symbol}</span>}
      </div>
      {comp.keywords?.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {comp.keywords.map((k, i) => (
            <span key={i} className="text-[10px] px-2 py-0.5 bg-gray-800 rounded text-gray-400">{k}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function ReportCard({ report }) {
  const [expanded, setExpanded] = useState(false);
  const typeIcons = {
    news: Newspaper, trends: TrendingUp, finance: DollarSign,
    ai_analysis: Brain, trending: Globe, topic_news: Newspaper, topic_trends: TrendingUp,
  };
  const Icon = typeIcons[report.type] || Newspaper;
  const severityColors = {
    info: 'border-l-blue-500', warning: 'border-l-amber-500', critical: 'border-l-red-500',
  };

  return (
    <div className={`card border-l-2 ${severityColors[report.severity] || severityColors.info} cursor-pointer`}
         onClick={() => setExpanded(!expanded)}>
      <div className="flex items-start gap-3">
        <Icon className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-200 truncate">{report.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{report.summary?.slice(0, 120)}</p>
          <p className="text-[10px] text-gray-600 mt-1">
            {report.type} · {new Date(report.created_at).toLocaleString()}
          </p>
        </div>
        {!report.is_read && <div className="w-2 h-2 bg-nerve-500 rounded-full shrink-0 mt-1.5" />}
      </div>
      {expanded && report.data && (
        <div className="mt-3 p-3 bg-gray-800/50 rounded-lg text-xs text-gray-400 max-h-60 overflow-auto">
          <pre className="whitespace-pre-wrap">{JSON.stringify(report.data, null, 2).slice(0, 2000)}</pre>
        </div>
      )}
    </div>
  );
}

export default function MarketIntelPage() {
  const [competitors, setCompetitors] = useState([]);
  const [topics, setTopics] = useState([]);
  const [reports, setReports] = useState([]);
  const [trending, setTrending] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [digest, setDigest] = useState('');
  const [scanning, setScanning] = useState(false);
  const [showAddComp, setShowAddComp] = useState(false);
  const [showAddTopic, setShowAddTopic] = useState(false);
  const [newComp, setNewComp] = useState({ name: '', domain: '', keywords: '', ticker_symbol: '' });
  const [newTopic, setNewTopic] = useState({ topic: '', topic_type: 'keyword' });

  const fetchAll = async () => {
    const [c, t, r, tr] = await Promise.all([
      getCompetitors().catch(() => []),
      getTopics().catch(() => []),
      getReports(30).catch(() => []),
      getTrending().catch(() => ({ trending: [] })),
    ]);
    setCompetitors(c);
    setTopics(t);
    setReports(r);
    setTrending(tr.trending || []);
  };

  useEffect(() => { fetchAll(); }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await runMarketScan();
      await fetchAll();
    } finally { setScanning(false); }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    const results = await quickSearch(searchQuery);
    setSearchResults(results);
  };

  const handleAddCompetitor = async () => {
    await addCompetitor({
      ...newComp,
      keywords: newComp.keywords.split(',').map(k => k.trim()).filter(Boolean),
    });
    setShowAddComp(false);
    setNewComp({ name: '', domain: '', keywords: '', ticker_symbol: '' });
    fetchAll();
  };

  const handleAddTopic = async () => {
    await addTopic(newTopic);
    setShowAddTopic(false);
    setNewTopic({ topic: '', topic_type: 'keyword' });
    fetchAll();
  };

  const handleDeleteComp = async (id) => {
    await deleteCompetitor(id);
    fetchAll();
  };

  const handleDigest = async () => {
    const result = await getDigest(1);
    setDigest(result.digest);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Radar className="w-7 h-7 text-nerve-400" />
            Market Intelligence
          </h1>
          <p className="text-sm text-gray-400 mt-1">Track competitors, trends, and market signals</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDigest} className="btn btn-secondary">
            <Brain className="w-4 h-4" /> AI Digest
          </button>
          <button onClick={handleScan} disabled={scanning} className="btn btn-primary">
            <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning...' : 'Run Scan'}
          </button>
        </div>
      </div>

      {/* Quick Search */}
      <div className="card">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search across news, web, and market data..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm
                       text-gray-200 placeholder-gray-500 focus:outline-none focus:border-nerve-500"
          />
          <button onClick={handleSearch} className="btn btn-primary">
            <Search className="w-4 h-4" />
          </button>
        </div>
        {searchResults && (
          <div className="mt-4 space-y-3 max-h-60 overflow-auto">
            {[...(searchResults.news || []), ...(searchResults.web || [])].slice(0, 10).map((r, i) => (
              <div key={i} className="flex items-start gap-2">
                <Globe className="w-3.5 h-3.5 text-gray-500 mt-0.5 shrink-0" />
                <div>
                  <a href={r.url || r.link} target="_blank" rel="noopener" className="text-sm text-nerve-400 hover:underline">
                    {r.title}
                  </a>
                  <p className="text-xs text-gray-500">{(r.content || r.summary || '').slice(0, 150)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Digest */}
      {digest && (
        <div className="card border-nerve-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-nerve-400 uppercase tracking-wider">AI Digest</h3>
            <button onClick={() => setDigest('')} className="text-gray-500 hover:text-gray-300">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-sm text-gray-200 whitespace-pre-wrap">{digest}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Competitors */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Competitors ({competitors.length})
            </h3>
            <button onClick={() => setShowAddComp(true)} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {showAddComp && (
            <div className="card mb-3 border-nerve-800 space-y-2">
              <input placeholder="Company name" value={newComp.name}
                onChange={(e) => setNewComp({ ...newComp, name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <input placeholder="Domain (e.g. company.com)" value={newComp.domain}
                onChange={(e) => setNewComp({ ...newComp, domain: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <input placeholder="Keywords (comma-separated)" value={newComp.keywords}
                onChange={(e) => setNewComp({ ...newComp, keywords: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <input placeholder="Ticker symbol (optional)" value={newComp.ticker_symbol}
                onChange={(e) => setNewComp({ ...newComp, ticker_symbol: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <div className="flex gap-2">
                <button onClick={handleAddCompetitor} className="btn btn-primary text-xs">Add</button>
                <button onClick={() => setShowAddComp(false)} className="btn btn-secondary text-xs">Cancel</button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {competitors.map((c) => (
              <CompetitorCard key={c.id} comp={c} onDelete={handleDeleteComp} />
            ))}
          </div>
        </div>

        {/* Reports */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Intelligence Reports ({reports.length})
            </h3>
          </div>
          <div className="space-y-3 max-h-[600px] overflow-auto">
            {reports.length === 0 ? (
              <div className="card text-center text-gray-500 py-8">
                <Radar className="w-8 h-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No reports yet. Run a scan to get started.</p>
              </div>
            ) : (
              reports.map((r) => <ReportCard key={r.id} report={r} />)
            )}
          </div>
        </div>
      </div>

      {/* Watched Topics + Trending */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Watched Topics */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Watched Topics
            </h3>
            <button onClick={() => setShowAddTopic(true)} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {showAddTopic && (
            <div className="mb-3 space-y-2">
              <input placeholder="Topic or keyword" value={newTopic.topic}
                onChange={(e) => setNewTopic({ ...newTopic, topic: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <select value={newTopic.topic_type}
                onChange={(e) => setNewTopic({ ...newTopic, topic_type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200">
                <option value="keyword">Keyword</option>
                <option value="industry">Industry</option>
                <option value="technology">Technology</option>
                <option value="ticker">Ticker</option>
              </select>
              <div className="flex gap-2">
                <button onClick={handleAddTopic} className="btn btn-primary text-xs">Add</button>
                <button onClick={() => setShowAddTopic(false)} className="btn btn-secondary text-xs">Cancel</button>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {topics.map((t) => (
              <span key={t.id} className="badge badge-info">
                {t.topic}
                <span className="text-[10px] text-gray-500 ml-1">({t.topic_type})</span>
              </span>
            ))}
          </div>
        </div>

        {/* Trending */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            Trending Now (India)
          </h3>
          <div className="flex flex-wrap gap-2">
            {trending.length === 0 ? (
              <p className="text-sm text-gray-500">No trending data available</p>
            ) : (
              trending.slice(0, 15).map((t, i) => (
                <span key={i} className="text-xs px-2.5 py-1 bg-gray-800 rounded-full text-gray-300 hover:bg-gray-700 cursor-pointer"
                  onClick={() => { setSearchQuery(t); handleSearch(); }}>
                  {t}
                </span>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
