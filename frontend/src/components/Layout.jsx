import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, Radar, Mail, ShieldCheck, Settings, Zap, Brain
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/market', icon: Radar, label: 'Market Intel' },
  { to: '/email', icon: Mail, label: 'Email Agent' },
  { to: '/actions', icon: ShieldCheck, label: 'Actions' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-nerve-600 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">NerveOS</h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">AI Business OS</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-nerve-600/15 text-nerve-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
              }
            >
              <Icon className="w-4.5 h-4.5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Zap className="w-3.5 h-3.5 text-nerve-500" />
            <span>Agents: <span className="text-emerald-400">Active</span></span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
