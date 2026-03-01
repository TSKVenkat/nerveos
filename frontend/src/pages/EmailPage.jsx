import { useState, useEffect } from 'react';
import {
  Mail, Inbox, Send, AlertCircle, Clock, Users, Plus, RefreshCw,
  Star, Filter, ChevronRight, FileText, X
} from 'lucide-react';
import {
  getInbox, getInboxSummary, getEmailDetail, generateDrafts,
  getDrafts, approveDraft, rejectDraft, syncEmails,
  getFollowUps, getContacts, addContact
} from '../lib/api';

const categoryColors = {
  lead: 'badge-success',
  renewal_risk: 'badge-warning',
  complaint: 'badge-critical',
  partnership: 'badge-info',
  spam: 'bg-gray-700/50 text-gray-500',
  general: 'bg-gray-800 text-gray-400',
};

const priorityColors = {
  urgent: 'text-red-400',
  high: 'text-amber-400',
  medium: 'text-gray-300',
  low: 'text-gray-500',
};

function EmailRow({ email, selected, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
        selected ? 'bg-nerve-600/10 border border-nerve-800' : 'hover:bg-gray-800/50'
      } ${!email.is_read ? 'border-l-2 border-l-nerve-500' : ''}`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${!email.is_read ? 'text-white' : 'text-gray-300'}`}>
            {email.from?.split('<')[0]?.trim() || email.from}
          </span>
          <span className={`badge text-[10px] ${categoryColors[email.category] || categoryColors.general}`}>
            {email.category}
          </span>
        </div>
        <p className={`text-sm truncate mt-0.5 ${!email.is_read ? 'text-gray-200' : 'text-gray-400'}`}>
          {email.subject}
        </p>
        {email.summary && (
          <p className="text-xs text-gray-500 truncate mt-0.5">{email.summary}</p>
        )}
      </div>
      <div className="text-right shrink-0">
        <p className={`text-xs ${priorityColors[email.priority] || 'text-gray-400'}`}>
          {email.priority}
        </p>
        <p className="text-[10px] text-gray-600 mt-1">
          {email.received_at ? new Date(email.received_at).toLocaleDateString() : ''}
        </p>
      </div>
    </div>
  );
}

export default function EmailPage() {
  const [inbox, setInbox] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [emailDetail, setEmailDetail] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [generatingDrafts, setGeneratingDrafts] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [followUps, setFollowUps] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState('all');
  const [showContacts, setShowContacts] = useState(false);
  const [showAddContact, setShowAddContact] = useState(false);
  const [newContact, setNewContact] = useState({ name: '', email: '', company: '', deal_value: 0, deal_stage: 'new' });

  const fetchData = async () => {
    const [inb, sum, cont, fu] = await Promise.all([
      getInbox(50, filter === 'all' ? null : filter).catch(() => []),
      getInboxSummary().catch(() => null),
      getContacts().catch(() => []),
      getFollowUps().catch(() => []),
    ]);
    setInbox(inb);
    setSummary(sum);
    setContacts(cont);
    setFollowUps(fu);
  };

  useEffect(() => { fetchData(); }, [filter]);

  const handleSelectEmail = async (email) => {
    setSelectedEmail(email.id);
    setDrafts([]);
    const detail = await getEmailDetail(email.id).catch(() => null);
    setEmailDetail(detail);
  };

  const handleGenerateDrafts = async () => {
    if (!selectedEmail) return;
    setGeneratingDrafts(true);
    try {
      const result = await generateDrafts(selectedEmail);
      setDrafts(result.drafts || []);
    } catch { setDrafts([]); }
    finally { setGeneratingDrafts(false); }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncEmails();
      await fetchData();
    } finally { setSyncing(false); }
  };

  const handleAddContact = async () => {
    await addContact(newContact);
    setShowAddContact(false);
    setNewContact({ name: '', email: '', company: '', deal_value: 0, deal_stage: 'new' });
    const cont = await getContacts().catch(() => []);
    setContacts(cont);
  };

  const categories = ['all', 'lead', 'renewal_risk', 'complaint', 'partnership', 'general'];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Mail className="w-7 h-7 text-nerve-400" />
            Email Agent
          </h1>
          <p className="text-sm text-gray-400 mt-1">AI-powered inbox triage, classification, and reply drafting</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowContacts(!showContacts)} className="btn btn-secondary">
            <Users className="w-4 h-4" /> CRM
          </button>
          <button onClick={handleSync} disabled={syncing} className="btn btn-primary">
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            Sync
          </button>
        </div>
      </div>

      {/* Summary Badges */}
      {summary && (
        <div className="flex items-center gap-4 flex-wrap">
          <div className="badge badge-info"><Inbox className="w-3 h-3 mr-1" />{summary.total_unread} unread</div>
          {Object.entries(summary.by_category || {}).map(([cat, count]) => (
            <div key={cat} className={`badge ${categoryColors[cat] || 'badge-info'}`}>
              {cat}: {count}
            </div>
          ))}
          {summary.needs_reply > 0 && (
            <div className="badge badge-warning"><Clock className="w-3 h-3 mr-1" />{summary.needs_reply} need reply</div>
          )}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-1">
        {categories.map((cat) => (
          <button key={cat} onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === cat ? 'bg-nerve-600/15 text-nerve-400' : 'text-gray-400 hover:bg-gray-800'
            }`}>
            {cat === 'all' ? 'All' : cat.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inbox list */}
        <div className="space-y-1 max-h-[600px] overflow-auto">
          {inbox.length === 0 ? (
            <div className="card text-center text-gray-500 py-12">
              <Mail className="w-8 h-8 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No emails. Connect an account or sync.</p>
            </div>
          ) : (
            inbox.map((em) => (
              <EmailRow key={em.id} email={em} selected={selectedEmail === em.id}
                onClick={() => handleSelectEmail(em)} />
            ))
          )}
        </div>

        {/* Email detail */}
        <div className="lg:col-span-2">
          {emailDetail ? (
            <div className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">{emailDetail.subject}</h3>
                  <p className="text-sm text-gray-400 mt-1">From: {emailDetail.from}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`badge ${categoryColors[emailDetail.category]}`}>{emailDetail.category}</span>
                    <span className={`text-xs ${priorityColors[emailDetail.priority]}`}>{emailDetail.priority} priority</span>
                  </div>
                </div>
                <button onClick={() => { setSelectedEmail(null); setEmailDetail(null); }}
                  className="text-gray-500 hover:text-gray-300">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {emailDetail.summary && (
                <div className="p-3 bg-nerve-600/5 border border-nerve-800 rounded-lg mb-4">
                  <p className="text-xs font-semibold text-nerve-400 uppercase mb-1">AI Summary</p>
                  <p className="text-sm text-gray-300">{emailDetail.summary}</p>
                </div>
              )}

              <div className="p-4 bg-gray-800/30 rounded-lg mb-4 max-h-48 overflow-auto">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans">
                  {emailDetail.body || 'No body content'}
                </pre>
              </div>

              <div className="flex gap-2 mb-4">
                <button onClick={handleGenerateDrafts} disabled={generatingDrafts} className="btn btn-primary">
                  <FileText className="w-4 h-4" />
                  {generatingDrafts ? 'Drafting...' : 'Generate Reply Drafts'}
                </button>
              </div>

              {drafts.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-gray-400 uppercase">Draft Replies</h4>
                  {drafts.map((d, i) => (
                    <div key={i} className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="badge badge-info">{d.tone}</span>
                        <div className="flex gap-2">
                          <button className="btn btn-success text-xs py-1 px-2">
                            <Send className="w-3 h-3" /> Approve & Send
                          </button>
                          <button className="btn btn-danger text-xs py-1 px-2">Reject</button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-300 whitespace-pre-wrap">{d.body}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center text-gray-500 py-20">
              <Mail className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select an email to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Follow-ups */}
      {followUps.length > 0 && (
        <div className="card border-amber-800">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-3">
            <Clock className="w-4 h-4 inline mr-2" />
            Follow-ups Needed ({followUps.length})
          </h3>
          <div className="space-y-2">
            {followUps.map((fu, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-amber-500/5">
                <div>
                  <p className="text-sm text-gray-200">{fu.subject}</p>
                  <p className="text-xs text-gray-500">{fu.from} · {fu.days_old} days old</p>
                </div>
                <button className="btn btn-secondary text-xs py-1">Reply</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CRM / Contacts Panel */}
      {showContacts && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              Contacts & Pipeline
            </h3>
            <button onClick={() => setShowAddContact(true)} className="p-1.5 rounded hover:bg-gray-800 text-gray-400">
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {showAddContact && (
            <div className="mb-4 p-3 bg-gray-800/50 rounded-lg space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <input placeholder="Name" value={newContact.name}
                  onChange={(e) => setNewContact({ ...newContact, name: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
                <input placeholder="Email" value={newContact.email}
                  onChange={(e) => setNewContact({ ...newContact, email: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
                <input placeholder="Company" value={newContact.company}
                  onChange={(e) => setNewContact({ ...newContact, company: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
                <input placeholder="Deal value" type="number" value={newContact.deal_value}
                  onChange={(e) => setNewContact({ ...newContact, deal_value: Number(e.target.value) })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddContact} className="btn btn-primary text-xs">Add</button>
                <button onClick={() => setShowAddContact(false)} className="btn btn-secondary text-xs">Cancel</button>
              </div>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 text-gray-400 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-400 font-medium">Company</th>
                  <th className="text-left py-2 text-gray-400 font-medium">Stage</th>
                  <th className="text-right py-2 text-gray-400 font-medium">Value</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((c) => (
                  <tr key={c.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-2 text-gray-200">{c.name}</td>
                    <td className="py-2 text-gray-400">{c.company}</td>
                    <td className="py-2">
                      <span className={`badge ${
                        c.deal_stage === 'won' ? 'badge-success' :
                        c.deal_stage === 'proposal' ? 'badge-info' :
                        c.deal_stage === 'lost' ? 'badge-critical' : 'bg-gray-800 text-gray-400'
                      }`}>
                        {c.deal_stage}
                      </span>
                    </td>
                    <td className="py-2 text-right text-gray-200">${c.deal_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
