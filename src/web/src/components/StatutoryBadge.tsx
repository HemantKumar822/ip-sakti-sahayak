import { ExternalLink, ScrollText } from 'lucide-react';
import type { Citation } from '../api/client';

export const StatutoryBadge = ({ citation }: { citation: Citation }) => {
  if (!citation.source_url) return null;
  const label = citation.section
    ? `${citation.title || citation.doc_id} · ${citation.section}`
    : citation.title || citation.doc_id || 'Statute';
  return (
    <a href={citation.source_url} target="_blank" rel="noopener noreferrer" className="sk-tag sk-tag-info" title={label}>
      <ScrollText size={11} aria-hidden="true" />
      <span style={{ maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>
      <ExternalLink size={11} aria-hidden="true" />
    </a>
  );
};
