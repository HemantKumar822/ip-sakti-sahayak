import React from 'react';
import { 
  FilePlus2, 
  ShieldCheck, 
  BookOpenCheck
} from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  onNewNote: () => void;
  disabled?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onNewNote,
  disabled = false,
}) => {
  return (
    <aside className="sidebar-container" aria-label="Workbench Navigation">
      {/* Workspace Branding Header */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-logo-seal">⚖️</div>
          <div className="brand-text-group">
            <span className="brand-title">IP-SAKTI Sahayak</span>
            <span className="brand-subtitle">Legal Research Workbench</span>
          </div>
        </div>
      </div>

      {/* Primary Workspace Action: New Research Note */}
      <div className="sidebar-actions-section">
        <button 
          className="new-note-btn" 
          onClick={onNewNote}
          disabled={disabled}
          title="Start fresh legal research memorandum"
        >
          <FilePlus2 size={16} />
          <span>New Research Note</span>
          <span className="btn-shortcut">Alt+N</span>
        </button>
      </div>

      {/* Empty space filler to push footer to bottom */}
      <div style={{ flex: 1 }} />

      {/* Privacy & Compliance Verification Footer */}
      <div className="sidebar-footer">
        <div className="privacy-badge">
          <ShieldCheck size={14} className="privacy-shield-icon" />
          <div className="privacy-text-group">
            <span className="privacy-title">DPDP Act 2023 Compliant</span>
            <span className="privacy-sub">Client-Side PII Scrubbing • Zero PII Stored</span>
          </div>
        </div>
        <div className="corpus-meta-row">
          <BookOpenCheck size={13} />
          <span>Supreme Court, CGPDTM & NBA Rules</span>
        </div>
      </div>
    </aside>
  );
};
