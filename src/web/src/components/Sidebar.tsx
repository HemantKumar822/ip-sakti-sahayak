import React, { useState, useEffect } from 'react';
import { 
  FilePlus2, 
  ShieldCheck, 
  BookOpenCheck,
  History,
  MessageSquare,
  Clock
} from 'lucide-react';
import { fetchSessions } from '../api/client';
import type { SessionSummary } from '../api/client';
import './Sidebar.css';

interface SidebarProps {
  onNewNote: () => void;
  activeSessionId?: string;
  onSelectSession?: (sessionId: string) => void;
  refreshTrigger?: number | string;
  disabled?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onNewNote,
  activeSessionId,
  onSelectSession,
  refreshTrigger,
  disabled = false,
}) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  useEffect(() => {
    let isCancelled = false;
    async function load() {
      try {
        const data = await fetchSessions(50);
        if (!isCancelled) {
          setSessions(data);
        }
      } catch {
        // Session store offline or empty
      }
    }
    load();
    return () => {
      isCancelled = true;
    };
  }, [refreshTrigger]);


  // Global Alt+N keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'n' || e.key === 'N')) {
        e.preventDefault();
        if (!disabled) {
          onNewNote();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onNewNote, disabled]);

  const formatRelativeTime = (dateStr?: string): string => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
      if (diffSec < 60) return 'Just now';
      const diffMin = Math.floor(diffSec / 60);
      if (diffMin < 60) return `${diffMin}m ago`;
      const diffHours = Math.floor(diffMin / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  };

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
          title="Start fresh legal research memorandum (Alt+N)"
          type="button"
        >
          <FilePlus2 size={16} />
          <span>New Research Note</span>
          <span className="btn-shortcut">Alt+N</span>
        </button>
      </div>

      {/* Active Session Archive Section */}
      <div className="sidebar-archive-section">
        <div className="sidebar-section-header">
          <div className="section-header-left">
            <History size={13} className="section-header-icon" />
            <span className="section-header-title">Research Archive</span>
          </div>
          <span className="session-count-badge">
            {sessions.length}
          </span>
        </div>

        <div className="session-list-scrollable" role="list" aria-label="Stored Sessions">
          {sessions.length === 0 ? (
            <div className="session-empty-state">
              <MessageSquare size={16} className="empty-icon" />
              <span>No prior research notes</span>
              <span className="empty-sub">Queries persist automatically</span>
            </div>
          ) : (
            sessions.map((sess) => {
              const isActive = sess.session_id === activeSessionId;
              const formattedTime = formatRelativeTime(sess.updated_at || sess.created_at);
              const previewText = sess.preview || 'Untitled Inquiry';

              return (
                <div
                  key={sess.session_id}
                  role="listitem"
                  className={`session-card ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectSession?.(sess.session_id)}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectSession?.(sess.session_id);
                    }
                  }}
                  title={previewText}
                >
                  <div className="session-card-header">
                    <span className="session-turn-pill">
                      {sess.total_turns} {sess.total_turns === 1 ? 'turn' : 'turns'}
                    </span>
                    {formattedTime && (
                      <span className="session-time-text">
                        <Clock size={10} />
                        {formattedTime}
                      </span>
                    )}
                  </div>
                  <div className="session-preview-snippet">
                    {previewText}
                  </div>
                </div>
              );
            })
          )}
        </div>
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

