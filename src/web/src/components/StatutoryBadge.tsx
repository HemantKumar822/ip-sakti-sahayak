import { ExternalLink } from 'lucide-react';
import './StatutoryBadge.css';
import type { Citation } from '../api/client';

export const StatutoryBadge = ({ citation }: { citation: Citation }) => {
  const cTitle = citation.title || citation.doc_id || "Statute";
  const cSec = citation.section;
  const label = cSec ? `${cTitle} (S. ${cSec})` : cTitle;

  if (!citation.source_url) return null;

  return (
    <a 
      href={citation.source_url} 
      target="_blank" 
      rel="noopener noreferrer" 
      className="statutory-badge animate-fade-in"
    >
      <span className="statutory-badge-icon">📜</span>
      <span className="statutory-badge-label">{label}</span>
      <ExternalLink size={14} className="statutory-badge-link-icon" />
    </a>
  );
};
