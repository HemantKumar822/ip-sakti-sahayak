import React, { useEffect, useState } from 'react';
import { FilePlus2, History, ShieldCheck, MessageSquare, Trash2, Loader2 } from 'lucide-react';
import { fetchSessions, deleteSession } from '../api/client';
import type { SessionSummary } from '../api/client';

interface SidebarProps {
  onNewNote: () => void;
  activeSessionId?: string;
  onSelectSession?: (sessionId: string) => void;
  refreshTrigger?: number | string;
  currentTurns?: number;
  disabled?: boolean;
}

function relativeTime(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    const d = Math.floor(diff / 86400);
    if (d < 7) return `${d}d ago`;
    return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export const Sidebar: React.FC<SidebarProps> = ({
  onNewNote,
  activeSessionId,
  onSelectSession,
  refreshTrigger,
  currentTurns,
  disabled = false,
}) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchSessions(50);
        if (!cancelled) setSessions(data);
      } catch {
        /* history unavailable — empty state covers it */
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [refreshTrigger]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'n' || e.key === 'N')) {
        e.preventDefault();
        if (!disabled) onNewNote();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onNewNote, disabled]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    // Instant optimistic deletion
    setSessions(prev => prev.filter(s => s.session_id !== id));
    if (activeSessionId === id) {
      onNewNote();
    }
    try {
      setDeletingId(id);
      await deleteSession(id);
    } catch (err) {
      console.error('Failed to delete session', err);
    } finally {
      setDeletingId(null);
    }
  };

  // Optimistically update or inject the active session so the UI feels instant
  const displaySessions = React.useMemo(() => {
    let list = [...sessions];
    if (activeSessionId && currentTurns && currentTurns > 0) {
      const idx = list.findIndex(s => s.session_id === activeSessionId);
      if (idx >= 0) {
        list[idx] = { ...list[idx], total_turns: Math.floor(currentTurns / 2) || 1 }; // Turn = user + assistant
      } else {
        list = [
          { 
            session_id: activeSessionId, 
            preview: 'New inquiry...', 
            total_turns: Math.floor(currentTurns / 2) || 1, 
            created_at: new Date().toISOString() 
          }, 
          ...list
        ];
      }
    }
    return list;
  }, [sessions, activeSessionId, currentTurns]);

  return (
    <aside aria-label="Inquiry history">
      <button type="button" className="sk-btn sk-btn-block" onClick={onNewNote} disabled={disabled} title="Start a new clearance inquiry (Alt+N)">
        <FilePlus2 size={15} aria-hidden="true" />
        <span>New inquiry</span>
      </button>

      <div>
        <p className="sk-eyebrow">
          <History size={12} aria-hidden="true" />
          <span>History · {sessions.length}</span>
        </p>
        <div className="sk-history-list" role="list" aria-label="Past inquiries" style={{ marginTop: 'var(--space-sm)' }}>
          {displaySessions.length === 0 ? (
            <div className="sk-card sk-card-soft" style={{ padding: 'var(--space-md)' }}>
              <p className="sk-small" style={{ margin: 0, display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
                <MessageSquare size={14} aria-hidden="true" />
                <span>No inquiries yet. They are saved automatically.</span>
              </p>
            </div>
          ) : (
            displaySessions.map((s) => (
              <div key={s.session_id} style={{ display: 'flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
                <button
                  type="button"
                  role="listitem"
                  className="sk-history-item"
                  style={{ flex: 1 }}
                  aria-current={s.session_id === activeSessionId}
                  onClick={() => onSelectSession?.(s.session_id)}
                  title={s.preview || 'Untitled inquiry'}
                >
                  <span className="sk-history-preview">{s.preview || 'Untitled inquiry'}</span>
                  <span className="sk-history-meta">
                    <span>
                      {s.total_turns} {s.total_turns === 1 ? 'turn' : 'turns'}
                    </span>
                    <span>{relativeTime(s.updated_at || s.created_at)}</span>
                  </span>
                </button>
                <button 
                  type="button" 
                  className="sk-btn sk-btn-quiet sk-btn-sm" 
                  style={{ padding: '6px', color: 'var(--status-error)' }}
                  onClick={(e) => handleDelete(e, s.session_id)}
                  disabled={deletingId === s.session_id}
                  title="Delete inquiry"
                >
                  {deletingId === s.session_id ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div style={{ marginTop: 'auto', paddingTop: 'var(--space-md)' }}>
        <p className="sk-mini" style={{ margin: 0, display: 'flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
          <ShieldCheck size={13} aria-hidden="true" />
          <span>PII is scrubbed in your browser before anything is sent.</span>
        </p>
      </div>
    </aside>
  );
};
