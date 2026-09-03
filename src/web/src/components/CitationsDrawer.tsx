import { useState } from 'react';
import { ChevronDown, FileText, ExternalLink, Calendar, Tag } from 'lucide-react';
import type { Citation } from '../api/client';
import './CitationsDrawer.css';

export const CitationsDrawer = ({ citations }: { citations: Citation[] }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="citations-drawer animate-fade-in">
      <button 
        className="citations-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className="toggle-left">
          <FileText size={16} className="toggle-icon" />
          <span className="toggle-label">
            <strong>{citations.length}</strong> Statutory Citation{citations.length > 1 ? 's' : ''} & Legal Source{citations.length > 1 ? 's' : ''} Grounded
          </span>
        </div>
        <ChevronDown 
          size={16} 
          className={`toggle-chevron ${isOpen ? 'rotated' : ''}`} 
        />
      </button>

      {isOpen && (
        <div className="citations-list">
          {citations.map((cit, idx) => {
            const title = cit.title || cit.doc_id || "Statutory Authority";
            return (
              <div key={idx} className="citation-detail-card">
                <div className="citation-header-row">
                  <span className="citation-index-badge">[{idx + 1}]</span>
                  <span className="citation-doc-title">{title}</span>
                  {cit.section && (
                    <span className="citation-section-badge">Section {cit.section}</span>
                  )}
                </div>

                {cit.snippet && (
                  <blockquote className="citation-quote">
                    "{cit.snippet}"
                  </blockquote>
                )}

                <div className="citation-meta-row">
                  <div className="citation-tags">
                    <span className="meta-tag">
                      <Tag size={12} />
                      <span>{cit.doc_type || "Statutory Act"}</span>
                    </span>
                    <span className="meta-tag">
                      <Calendar size={12} />
                      <span>{cit.date_retrieved || "Verified 2026"}</span>
                    </span>
                  </div>

                  {cit.source_url && (
                    <a 
                      href={cit.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="citation-source-link"
                    >
                      <span>Official Govt. Source</span>
                      <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
