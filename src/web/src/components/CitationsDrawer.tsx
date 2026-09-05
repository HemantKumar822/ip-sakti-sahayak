import { useState } from 'react';
import { ChevronDown, FileText, ExternalLink } from 'lucide-react';
import type { Citation } from '../api/client';

export const CitationsDrawer = ({ citations }: { citations: Citation[] }) => {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;

  return (
    <div className="sk-card animate-fade-in" style={{ padding: 0, overflow: 'hidden' }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-md) var(--space-lg)', color: 'var(--ink)', fontSize: '13px' }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <FileText size={15} aria-hidden="true" />
          <span>
            <strong>{citations.length}</strong> cited {citations.length === 1 ? 'authority' : 'authorities'}
          </span>
        </span>
        <ChevronDown size={15} aria-hidden="true" style={{ transform: open ? 'rotate(180deg)' : undefined, color: 'var(--mute)' }} />
      </button>
      {open && (
        <div style={{ borderTop: '1px solid var(--hairline)', padding: 'var(--space-md)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {citations.map((c, i) => (
            <div key={i}>
              <p className="sk-mini" style={{ margin: '0 0 2px' }}>
                [{i + 1}] · {c.doc_type || 'Authority'}{c.section ? ` · ${c.section}` : ''}
              </p>
              <p className="sk-small" style={{ margin: 0, color: 'var(--ink)' }}>
                {c.title || c.doc_id}
              </p>
              {c.snippet && (
                <blockquote className="sk-small" style={{ margin: 'var(--space-xs) 0 0', borderLeft: '2px solid var(--hairline-strong)', paddingLeft: 'var(--space-sm)' }}>
                  &ldquo;{c.snippet}&rdquo;
                </blockquote>
              )}
              {c.source_url && (
                <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="sk-small" style={{ display: 'inline-flex', gap: 'var(--space-xs)', alignItems: 'center', color: 'var(--accent-breeze)' }}>
                  <span>Official source</span>
                  <ExternalLink size={11} aria-hidden="true" />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
