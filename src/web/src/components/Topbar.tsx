import React, { useEffect, useState } from 'react';
import { Scale, LayoutGrid, FlaskConical, Database, PanelLeft, PanelRight } from 'lucide-react';
import { fetchCorpusStats } from '../api/client';
import type { CorpusStats } from '../api/client';

export type AppView = 'landing' | 'workbench' | 'admin';

interface TopbarProps {
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  onHome: () => void;
  leftSidebarOpen?: boolean;
  onToggleLeftSidebar?: () => void;
  rightSidebarOpen?: boolean;
  onToggleRightSidebar?: () => void;
}

const TABS: { id: AppView; label: string; icon: React.ReactNode }[] = [
  { id: 'landing', label: 'Overview', icon: <LayoutGrid size={13} aria-hidden="true" /> },
  { id: 'workbench', label: 'Clearance Desk', icon: <FlaskConical size={13} aria-hidden="true" /> },
  { id: 'admin', label: 'Corpus', icon: <Database size={13} aria-hidden="true" /> },
];

export const Topbar: React.FC<TopbarProps> = ({ 
  activeView, 
  onViewChange, 
  onHome,
  leftSidebarOpen,
  onToggleLeftSidebar,
  rightSidebarOpen,
  onToggleRightSidebar
}) => {
  const [stats, setStats] = useState<CorpusStats | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchCorpusStats();
        if (!cancelled) setStats(data);
      } catch {
        /* offline — indicator degrades silently */
      }
    }
    load();
    const t = setInterval(load, 60000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  return (
    <header className="sk-topbar" aria-label="Primary">
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        {activeView === 'workbench' && onToggleLeftSidebar && (
          <button
            type="button"
            className="sk-btn sk-btn-icon sk-btn-ghost sk-only-desktop"
            onClick={onToggleLeftSidebar}
            title={leftSidebarOpen ? "Close history" : "Open history"}
          >
            <PanelLeft size={16} className={leftSidebarOpen ? 'sk-icon-active' : 'sk-icon-inactive'} />
          </button>
        )}
        <button type="button" className="sk-brand" onClick={onHome} aria-label="IP-SAKTI Sahayak home">
          <span className="sk-brand-mark" aria-hidden="true">
            <Scale size={15} />
          </span>
          <span>IP-SAKTI Sahayak</span>
          <span className="sk-brand-sub">Ayurveda IP clearance</span>
        </button>
      </div>

      <nav className="sk-viewtabs" aria-label="Views">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className="sk-viewtab"
            aria-current={activeView === t.id ? 'page' : undefined}
            aria-label={t.label}
            title={t.label}
            onClick={() => onViewChange(t.id)}
          >
            {t.icon}
            <span>{t.label}</span>
          </button>
        ))}
      </nav>

      <div className="sk-topbar-right">
        <span className="sk-live" title="Indexed statutory corpus">
          <span className={`sk-dot${stats ? '' : ' sk-dot-bad'}`} aria-hidden="true" />
          <span>{stats ? `${stats.total_documents} gazettes` : 'Corpus offline'}</span>
        </span>
        {activeView === 'workbench' && onToggleRightSidebar && (
          <button
            type="button"
            className="sk-btn sk-btn-icon sk-btn-ghost sk-only-desktop"
            onClick={onToggleRightSidebar}
            title={rightSidebarOpen ? "Close evidence" : "Open evidence"}
            style={{ marginLeft: 'var(--space-xs)' }}
          >
            <PanelRight size={16} className={rightSidebarOpen ? 'sk-icon-active' : 'sk-icon-inactive'} />
          </button>
        )}
      </div>
    </header>
  );
};
