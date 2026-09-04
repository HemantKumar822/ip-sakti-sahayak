import React, { useEffect, useRef } from 'react';
import { X, ExternalLink, ScrollText } from 'lucide-react';
import type { Citation } from '../api/client';
import './CitationModal.css';

interface CitationModalProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, isOpen, onClose }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scrolling
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onClose();
    }
  };

  if (!isOpen || !citation) return null;

  return (
    <div 
      className="citation-modal-backdrop" 
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="citation-modal-title"
    >
      <div className="citation-modal-content animate-slide-up" ref={modalRef}>
        <header className="citation-modal-header">
          <div className="citation-modal-title-group">
            <ScrollText size={16} className="title-icon" />
            <h2 id="citation-modal-title">Authentic Gazette Source</h2>
          </div>
          <button className="citation-modal-close" onClick={onClose} aria-label="Close modal">
            <X size={16} />
          </button>
        </header>

        <div className="citation-modal-body">
          <div className="citation-meta-grid">
            <div className="meta-cell">
              <span className="meta-label">Document ID</span>
              <span className="meta-value doc-id">{citation.doc_id}</span>
            </div>
            {citation.section && (
              <div className="meta-cell">
                <span className="meta-label">Section</span>
                <span className="meta-value">{citation.section}</span>
              </div>
            )}
          </div>

          {citation.title && (
            <div className="citation-full-title">
              {citation.title}
            </div>
          )}

          <div className="citation-snippet-container">
            <span className="snippet-label">Verbatim Extract:</span>
            <pre className="citation-snippet">
              {citation.snippet || 'No extract available.'}
            </pre>
          </div>
        </div>

        <footer className="citation-modal-footer">
          {citation.source_url ? (
            <a 
              href={citation.source_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="citation-official-link"
            >
              <span>View Official Government Source</span>
              <ExternalLink size={14} />
            </a>
          ) : (
            <span className="citation-no-link">No official URL available</span>
          )}
        </footer>
      </div>
    </div>
  );
};
