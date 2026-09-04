import React, { useEffect, useState } from 'react';
import { 
  PanelLeft, 
  PanelRight, 
  RotateCcw, 
  ShieldCheck, 
  ChevronRight,
  Database,
  Terminal
} from 'lucide-react';
import { fetchCorpusStats } from '../api/client';
import type { CorpusStats } from '../api/client';
import './Topbar.css';

interface TopbarProps {
  onReset: () => void;
  hasMessages: boolean;
  onToggleSidebar?: () => void;
  onToggleInspector?: () => void;
  isInspectorOpen?: boolean;
  activeCategory?: string | null;
  activeView: 'workbench' | 'admin';
  onViewChange: (view: 'workbench' | 'admin') => void;
}

export const Topbar: React.FC<TopbarProps> = ({ 
  onReset, 
  hasMessages,
  onToggleSidebar,
  onToggleInspector,
  isInspectorOpen = true,
  activeCategory,
  activeView,
  onViewChange
}) => {
  const [stats, setStats] = useState<CorpusStats | null>(null);

  useEffect(() => {
    let isCancelled = false;
    async function loadStats() {
      try {
        const data = await fetchCorpusStats();
        if (!isCancelled) setStats(data);
      } catch (err) {
        console.error("Failed to load corpus stats", err);
      }
    }
    loadStats();
    // Refresh stats periodically
    const interval = setInterval(loadStats, 30000);
    return () => {
      isCancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="topbar-workbench" aria-label="Workbench Topbar">
      <div className="topbar-left-section">
        {onToggleSidebar && (
          <button 
            className="sidebar-toggle-btn"
            onClick={onToggleSidebar}
            title="Toggle Navigation Sidebar"
            aria-label="Toggle Sidebar"
          >
            <PanelLeft size={16} />
          </button>
        )}

        {/* View Toggles */}
        <div className="view-toggles" aria-label="View Toggles">
          <button 
            className={`view-toggle-btn ${activeView === 'workbench' ? 'active' : ''}`}
            onClick={() => onViewChange('workbench')}
            title="Intelligence Workbench"
          >
            <Terminal size={14} />
            <span>Workbench</span>
          </button>
          <button 
            className={`view-toggle-btn ${activeView === 'admin' ? 'active' : ''}`}
            onClick={() => onViewChange('admin')}
            title="Corpus Admin Console"
          >
            <Database size={14} />
            <span>Admin Console</span>
          </button>
        </div>

        {/* Breadcrumbs for Workbench */}
        {activeView === 'workbench' && (
          <nav className="notion-breadcrumbs" aria-label="Breadcrumb">
            <span className="breadcrumb-item brand-link" onClick={onReset}>
              <span className="brand-icon">🏛️</span>
              <span className="brand-text">IP-SAKTI Sahayak</span>
            </span>
            <ChevronRight size={13} className="breadcrumb-arrow" />
            <span className="breadcrumb-item jurisdiction-link">
              <span className="flag-icon-inline">🇮🇳</span>
              <span>India</span>
            </span>
            {activeCategory && (
              <>
                <ChevronRight size={13} className="breadcrumb-arrow" />
                <span className="breadcrumb-item category-current">
                  {activeCategory}
                </span>
              </>
            )}
          </nav>
        )}
      </div>

      <div className="topbar-right-section">
        {/* Live Corpus Online Status */}
        <div className="corpus-live-indicator" title="Hybrid Dense + BM25 Legal Retrieval Engine Ready">
          <span className="indicator-dot"></span>
          <span className="indicator-label">
            {stats ? `${stats.total_documents} Gazettes (${stats.total_chunks} chunks)` : 'Loading Stats...'}
          </span>
        </div>

        {activeView === 'workbench' && hasMessages && (
          <button 
            className="topbar-reset-btn" 
            onClick={onReset}
            title="Reset to New Legal Research Memorandum"
          >
            <RotateCcw size={13} />
            <span>Reset Canvas</span>
          </button>
        )}

        {/* Trust Inspector Toggle Button */}
        {activeView === 'workbench' && onToggleInspector && (
          <button 
            className={`inspector-toggle-btn ${isInspectorOpen ? 'active' : ''}`}
            onClick={onToggleInspector}
            title="Toggle Trust & Telemetry Inspector"
          >
            <ShieldCheck size={15} />
            <span>Trust Inspector</span>
            <PanelRight size={14} className="panel-right-icon" />
          </button>
        )}
      </div>
    </header>
  );
};
