import { useState, useEffect } from 'react';
import {
  ShieldCheck, CheckCircle, XCircle, Clock, Search, FileText, AlertTriangle
} from 'lucide-react';
import {
  getPendingActions, approveAction, rejectAction,
  getAuditTrail, getPolicies, addPolicy, deletePolicy
} from '../lib/api';

export default function ActionsPage() {
  const [pending, setPending] = useState([]);
  const [audit, setAudit] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [tab, setTab] = useState('pending');
  const [showAddPolicy, setShowAddPolicy] = useState(false);
  const [newPolicy, setNewPolicy] = useState({
    name: '', description: '', rule_type: 'require_approval',
    conditions: '{}', priority: 0,
  });

  const fetchData = async () => {
    const [p, a, pol] = await Promise.all([
      getPendingActions().catch(() => []),
      getAuditTrail().catch(() => []),
      getPolicies().catch(() => []),
    ]);
    setPending(p);
    setAudit(a);
    setPolicies(pol);
  };

  useEffect(() => { fetchData(); }, []);

  const handleApprove = async (id) => {
    await approveAction(id);
    fetchData();
  };

  const handleReject = async (id) => {
    await rejectAction(id);
    fetchData();
  };

  const handleAddPolicy = async () => {
    try {
      await addPolicy({
        ...newPolicy,
        conditions: JSON.parse(newPolicy.conditions),
        priority: Number(newPolicy.priority),
      });
      setShowAddPolicy(false);
      setNewPolicy({ name: '', description: '', rule_type: 'require_approval', conditions: '{}', priority: 0 });
      fetchData();
    } catch (e) {
      alert('Invalid JSON in conditions');
    }
  };

  const handleDeletePolicy = async (id) => {
    await deletePolicy(id);
    fetchData();
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <ShieldCheck className="w-7 h-7 text-nerve-400" />
          Actions & Guardrails
        </h1>
        <p className="text-sm text-gray-400 mt-1">Review, approve, and audit autonomous agent actions</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-800 pb-0">
        {['pending', 'audit', 'policies'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-nerve-500 text-nerve-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}>
            {t === 'pending' && <Clock className="w-4 h-4 inline mr-1.5" />}
            {t === 'audit' && <FileText className="w-4 h-4 inline mr-1.5" />}
            {t === 'policies' && <ShieldCheck className="w-4 h-4 inline mr-1.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {t === 'pending' && pending.length > 0 && (
              <span className="ml-2 bg-red-500/20 text-red-400 text-xs px-1.5 py-0.5 rounded-full">
                {pending.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Pending Actions */}
      {tab === 'pending' && (
        <div className="space-y-3">
          {pending.length === 0 ? (
            <div className="card text-center text-gray-500 py-12">
              <CheckCircle className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">All clear! No pending actions.</p>
            </div>
          ) : (
            pending.map((action) => (
              <div key={action.id} className="card border-l-2 border-l-amber-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="badge badge-warning">{action.action_type}</span>
                      <span className="text-[10px] text-gray-500">
                        {new Date(action.created_at).toLocaleString()}
                      </span>
                    </div>
                    <h4 className="text-sm font-medium text-white mt-2">{action.title}</h4>
                    <p className="text-xs text-gray-400 mt-1">{action.description}</p>
                  </div>
                  <div className="flex gap-2 shrink-0 ml-4">
                    <button onClick={() => handleApprove(action.id)} className="btn btn-success text-xs py-1.5">
                      <CheckCircle className="w-3.5 h-3.5" /> Approve
                    </button>
                    <button onClick={() => handleReject(action.id)} className="btn btn-danger text-xs py-1.5">
                      <XCircle className="w-3.5 h-3.5" /> Reject
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Audit Trail */}
      {tab === 'audit' && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left py-2 text-gray-400 font-medium">Agent</th>
                <th className="text-left py-2 text-gray-400 font-medium">Action</th>
                <th className="text-left py-2 text-gray-400 font-medium">Entity</th>
                <th className="text-left py-2 text-gray-400 font-medium">Approved</th>
                <th className="text-left py-2 text-gray-400 font-medium">Status</th>
                <th className="text-right py-2 text-gray-400 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {audit.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-500">No audit logs yet</td></tr>
              ) : (
                audit.map((log) => (
                  <tr key={log.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-2 text-gray-300">{log.agent}</td>
                    <td className="py-2 text-gray-300">{log.action}</td>
                    <td className="py-2 text-gray-400">{log.entity_type} #{log.entity_id}</td>
                    <td className="py-2">
                      {log.user_approved ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                    </td>
                    <td className="py-2">
                      <span className={`badge ${
                        log.status === 'completed' ? 'badge-success' : 'badge-warning'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="py-2 text-right text-xs text-gray-500">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Policies */}
      {tab === 'policies' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => setShowAddPolicy(true)} className="btn btn-primary text-sm">
              + Add Policy
            </button>
          </div>

          {showAddPolicy && (
            <div className="card border-nerve-800 space-y-3">
              <h4 className="text-sm font-semibold text-nerve-400">New Policy Rule</h4>
              <input placeholder="Policy name" value={newPolicy.name}
                onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <input placeholder="Description" value={newPolicy.description}
                onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              <div className="grid grid-cols-2 gap-2">
                <select value={newPolicy.rule_type}
                  onChange={(e) => setNewPolicy({ ...newPolicy, rule_type: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200">
                  <option value="require_approval">Require Approval</option>
                  <option value="block">Block</option>
                  <option value="auto_approve">Auto Approve</option>
                </select>
                <input placeholder="Priority (0-100)" type="number" value={newPolicy.priority}
                  onChange={(e) => setNewPolicy({ ...newPolicy, priority: e.target.value })}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200" />
              </div>
              <textarea placeholder='Conditions JSON: {"action_type": "send_email"}' value={newPolicy.conditions}
                onChange={(e) => setNewPolicy({ ...newPolicy, conditions: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 font-mono h-20" />
              <div className="flex gap-2">
                <button onClick={handleAddPolicy} className="btn btn-primary text-xs">Create</button>
                <button onClick={() => setShowAddPolicy(false)} className="btn btn-secondary text-xs">Cancel</button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {policies.map((policy) => (
              <div key={policy.id} className="card flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-white">{policy.name}</h4>
                    <span className={`badge ${
                      policy.rule_type === 'block' ? 'badge-critical' :
                      policy.rule_type === 'auto_approve' ? 'badge-success' : 'badge-warning'
                    }`}>
                      {policy.rule_type}
                    </span>
                    <span className="text-[10px] text-gray-500">priority: {policy.priority}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{policy.description}</p>
                  <p className="text-[10px] text-gray-600 mt-1 font-mono">
                    {JSON.stringify(policy.conditions)}
                  </p>
                </div>
                <button onClick={() => handleDeletePolicy(policy.id)}
                  className="text-gray-500 hover:text-red-400 p-1.5">
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
