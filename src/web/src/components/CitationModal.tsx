import React, { useEffect } from 'react';
import { X, ExternalLink, ScrollText } from 'lucide-react';
import type { Citation } from '../api/client';

interface CitationModalProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, isOpen, onClose }) => {
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !citation) return null;

  return (
    <div
      className="sk-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sk-citation-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="sk-modal animate-fade-in">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p className="sk-eyebrow" style={{ display: 'inline-flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
            <ScrollText size={14} aria-hidden="true" />
            <span>Gazette source</span>
          </p>
          <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={onClose} aria-label="Close citation">
            <X size={15} aria-hidden="true" />
          </button>
        </div>
        <h2 id="sk-citation-title" className="sk-h3">
          {citation.title || citation.doc_id}
        </h2>
        <p className="sk-mini" style={{ margin: 0 }}>
          {citation.doc_id}
          {citation.section ? ` · ${citation.section}` : ''}
          {citation.doc_type ? ` · ${citation.doc_type}` : ''}
        </p>
        <blockquote className="sk-body" style={{ margin: 0, borderLeft: '2px solid var(--hairline-strong)', paddingLeft: 'var(--space-md)' }}>
          {citation.snippet || 'No extract recorded for this citation.'}
        </blockquote>
        {citation.source_url ? (
          <a href={citation.source_url} target="_blank" rel="noopener noreferrer" className="sk-btn sk-btn-primary sk-btn-sm" style={{ alignSelf: 'flex-start' }}>
            <span>Open official source</span>
            <ExternalLink size={13} aria-hidden="true" />
          </a>
        ) : (
          <p className="sk-mini" style={{ margin: 0 }}>No official URL recorded.</p>
        )}
      </div>
    </div>
  );
};
