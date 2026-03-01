import { useState, useEffect } from 'react';
import { Settings, Activity, Server, Database, Brain, Globe, CheckCircle, XCircle } from 'lucide-react';
import { getHealth, getConfig } from '../lib/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [config, setConfig] = useState(null);

  useEffect(() => {
    getHealth().catch(() => null).then(setHealth);
    getConfig().catch(() => null).then(setConfig);
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Settings className="w-7 h-7 text-nerve-400" />
          Settings
        </h1>
        <p className="text-sm text-gray-400 mt-1">System health, configuration, and service status</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Health */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            <Activity className="w-4 h-4 inline mr-2" />
            System Health
          </h3>
          {health ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">API Status</span>
                <span className="flex items-center gap-1.5 text-emerald-400 text-sm">
                  <CheckCircle className="w-4 h-4" /> {health.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">Version</span>
                <span className="text-sm text-gray-400">{health.version}</span>
              </div>
              <hr className="border-gray-800" />
              <h4 className="text-xs font-semibold text-gray-400">Services</h4>
              {health.services && Object.entries(health.services).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300 flex items-center gap-2">
                    {key === 'searxng' ? <Globe className="w-3.5 h-3.5" /> :
                     key === 'ollama' ? <Brain className="w-3.5 h-3.5" /> :
                     <Database className="w-3.5 h-3.5" />}
                    {key}
                  </span>
                  <span className="text-sm">
                    {typeof val === 'boolean' ? (
                      val ? <CheckCircle className="w-4 h-4 text-emerald-400" /> :
                            <XCircle className="w-4 h-4 text-red-400" />
                    ) : (
                      <span className="text-gray-400 text-xs font-mono">{val}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Loading health data...</p>
          )}
        </div>

        {/* Configuration */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            <Server className="w-4 h-4 inline mr-2" />
            Configuration
          </h3>
          {config ? (
            <div className="space-y-3">
              {Object.entries(config).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">{key.replace(/_/g, ' ')}</span>
                  <span className="text-sm text-gray-400 font-mono">
                    {typeof val === 'boolean' ? (val ? 'true' : 'false') : String(val)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Loading config...</p>
          )}
        </div>
      </div>

      {/* Architecture Info */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
          Architecture
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <h4 className="text-sm font-semibold text-nerve-400">Market Intel Agent</h4>
            <p className="text-xs text-gray-400 mt-1">
              Google Trends, RSS feeds, SearXNG, yfinance. Tracks competitors, keywords, and market signals.
            </p>
          </div>
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <h4 className="text-sm font-semibold text-nerve-400">Email Agent</h4>
            <p className="text-xs text-gray-400 mt-1">
              IMAP/SMTP integration, AI classification, draft replies, follow-up reminders, CRM tracking.
            </p>
          </div>
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <h4 className="text-sm font-semibold text-nerve-400">Executive Cockpit</h4>
            <p className="text-xs text-gray-400 mt-1">
              KPI dashboard, anomaly detection, NL business queries, metric tracking and alerts.
            </p>
          </div>
        </div>
        <div className="mt-4 p-4 bg-gray-800/50 rounded-lg">
          <h4 className="text-sm font-semibold text-amber-400">Guardrails & Policy Engine</h4>
          <p className="text-xs text-gray-400 mt-1">
            Human-in-the-loop approval for all actions. Policy rules engine. Complete audit trail.
            Self-hostable with Docker. Privacy-first with local LLM (Ollama) and private search (SearXNG).
          </p>
        </div>
      </div>

      {/* Open Source */}
      <div className="card border-nerve-800/50">
        <h3 className="text-sm font-semibold text-nerve-400 uppercase tracking-wider mb-3">
          Open Source Stack
        </h3>
        <div className="flex flex-wrap gap-2">
          {[
            'FastAPI', 'React', 'SQLite/PostgreSQL', 'Ollama (LLM)',
            'SearXNG (Search)', 'pytrends', 'yfinance', 'feedparser',
            'TailwindCSS', 'Docker', 'Vite'
          ].map((tech) => (
            <span key={tech} className="text-xs px-3 py-1.5 bg-gray-800 rounded-full text-gray-300">
              {tech}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
