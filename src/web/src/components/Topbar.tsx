import React from 'react';
import { 
  PanelLeft, 
  PanelRight, 
  RotateCcw, 
  ShieldCheck, 
  ChevronRight 
} from 'lucide-react';
import './Topbar.css';

interface TopbarProps {
  onReset: () => void;
  hasMessages: boolean;
  onToggleSidebar?: () => void;
  onToggleInspector?: () => void;
  isInspectorOpen?: boolean;
  activeCategory?: string | null;
}

export const Topbar: React.FC<TopbarProps> = ({ 
  onReset, 
  hasMessages,
  onToggleSidebar,
  onToggleInspector,
  isInspectorOpen = true,
  activeCategory
}) => {
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

        {/* Notion-Style Document Breadcrumbs */}
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
      </div>

      <div className="topbar-right-section">
        {/* Live Corpus Online Status */}
        <div className="corpus-live-indicator" title="Hybrid Dense + BM25 Legal Retrieval Engine Ready">
          <span className="indicator-dot"></span>
          <span className="indicator-label">11 Gazettes Indexed</span>
        </div>

        {hasMessages && (
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
        {onToggleInspector && (
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
