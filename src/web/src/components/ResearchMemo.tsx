import React, { useMemo } from 'react';
import { 
  ShieldCheck, 
  Scale, 
  Clock, 
  FileText, 
  ExternalLink,
  BookOpen,
  Sparkles
} from 'lucide-react';
import type { QueryResponse, Citation } from '../api/client';
import { Callout } from './Callout';
import { StatutoryBadge } from './StatutoryBadge';
import './ResearchMemo.css';

interface ResearchMemoProps {
  query: string;
  response: QueryResponse;
  onCitationClick?: (citation: Citation, index: number) => void;
}

export const ResearchMemo: React.FC<ResearchMemoProps> = ({
  query,
  response,
  onCitationClick
}) => {
  // Format inline citation markers [1], [2] into interactive link tags
  const formattedAnswerHtml = useMemo(() => {
    if (!response.answer) return '';

    const replaceCitation = (match: string, p1: string) => {
      const rawNums = p1.split(',');
      const links = rawNums.map((n) => {
        const num = n.trim();
        if (/^\d+$/.test(num)) {
          return `<a href="#citation-${num}" class="citation-marker" data-index="${num}">[${num}]</a>`;
        }
        return match;
      });
      return links.join('');
    };

    const processed = response.answer.replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, replaceCitation);
    const paragraphs = processed.split('\n\n').filter((p) => p.trim().length > 0);
    if (paragraphs.length === 0) {
      return `<p>${processed}</p>`;
    }
    return paragraphs.map((p) => `<p>${p.replace(/\n/g, '<br/>')}</p>`).join('');
  }, [response.answer]);

  // Determine preliminary assessment styling and text
  const preliminaryAssessment = useMemo(() => {
    const isAbstained = response.status === 'abstained';
    const isAbs = Boolean(response.abs_flag);
    const isTkdl = Boolean(response.tkdl_flag);

    if (isAbstained) {
      return {
        verdict: 'OUT OF SCOPE / INSUFFICIENT STATUTORY EVIDENCE',
        type: 'abstain',
        summary: response.abstention_message || 'The inquiry falls outside the indexed Indian Ayurvedic & patent corpus or scored below the 0.65 confidence gate.'
      };
    }

    if (isTkdl && isAbs) {
      return {
        verdict: 'NON-PATENTABLE UNDER S. 3(p) + MANDATORY NBA ABS CLEARANCE REQUIRED',
        type: 'critical',
        summary: 'Invention is barred as traditional knowledge prior art under Section 3(p) of the Patents Act, 1970. Furthermore, utilizing biological resources mandates prior Form I/III approval from the National Biodiversity Authority under Section 6 of the Biological Diversity Act, 2002.'
      };
    }

    if (isTkdl) {
      return {
        verdict: 'NON-PATENTABLE UNDER PATENTS ACT 1970 — SECTION 3(p) EXCLUSION',
        type: 'warning',
        summary: 'Invention is barred as traditional knowledge or mere aggregation of known properties under Section 3(p) and Ayush Examination Guidelines 2025.'
      };
    }

    if (isAbs) {
      return {
        verdict: 'PATENTABLE SUBJECT TO MANDATORY BIOLOGICAL DIVERSITY ABS CLEARANCE',
        type: 'info',
        summary: 'Proprietary formulation may be patent-eligible under Section 3(d) provided enhanced therapeutic efficacy is proven. Mandatory approval from National Biodiversity Authority (NBA) is required prior to grant under Section 6 of BDA 2002/2023.'
      };
    }

    return {
      verdict: 'PATENT-ELIGIBLE SUBJECT TO STATUTORY NOVELTY & EFFICACY STANDARDS',
      type: 'success',
      summary: 'Inquiry meets initial patentability thresholds under Indian patent law. Requires non-obviousness and proven therapeutic efficacy (Novartis standard) if modifying an existing substance.'
    };
  }, [response]);

  return (
    <article className="research-memo-container animate-fade-in" aria-label="Legal Research Memorandum">
      {/* Memorandum Title Header */}
      <header className="memo-header">
        <div className="memo-type-badge">
          <FileText size={13} />
          <span>STATUTORY RESEARCH MEMORANDUM</span>
        </div>
        <h1 className="memo-title">{query}</h1>
      </header>

      {/* Notion Property Metadata Table */}
      <section className="memo-properties-grid" aria-label="Memorandum Properties">
        <div className="property-cell">
          <span className="property-label">Category</span>
          <span className="property-tag category-tag">
            🏷️ {response.category || 'Ayurvedic IP Advisory'}
          </span>
        </div>

        <div className="property-cell">
          <span className="property-label">Jurisdiction</span>
          <span className="property-tag jurisdiction-tag">
            <Scale size={12} />
            <span>{response.jurisdiction || 'India (CGPDTM / NBA)'}</span>
          </span>
        </div>

        <div className="property-cell">
          <span className="property-label">Confidence</span>
          <span className="property-tag confidence-tag">
            <ShieldCheck size={12} />
            <span>{(response.confidence_score * 100).toFixed(1)}% Grounded</span>
          </span>
        </div>

        <div className="property-cell">
          <span className="property-label">Latency</span>
          <span className="property-tag latency-tag">
            <Clock size={12} />
            <span>{response.response_time_ms} ms</span>
          </span>
        </div>
      </section>

      {/* Preliminary Executive Assessment Banner */}
      <section className={`preliminary-assessment-callout ${preliminaryAssessment.type}`}>
        <div className="assessment-verdict-row">
          <span className="assessment-indicator"></span>
          <span className="assessment-verdict-title">{preliminaryAssessment.verdict}</span>
        </div>
        <p className="assessment-summary-text">{preliminaryAssessment.summary}</p>
      </section>

      {/* Statutory Compliance Alerts (ABS & TKDL) */}
      {response.abs_flag && (
        <Callout type="abs" title="Biological Diversity Act — Mandatory ABS Clearance Required">
          {response.abs_detail}
        </Callout>
      )}

      {response.tkdl_flag && (
        <Callout type="tkdl" title="Patents Act 1970 — Section 3(p) Traditional Knowledge Prior Art Bar">
          {response.tkdl_detail}
        </Callout>
      )}

      {/* Structured Legal Analysis Content */}
      <section className="memo-body-section">
        <div className="memo-section-heading">
          <BookOpen size={15} />
          <h2>Detailed Statutory Analysis & Reasoning</h2>
        </div>
        <div 
          className="memo-prose-content" 
          dangerouslySetInnerHTML={{ __html: formattedAnswerHtml }}
          onClick={(e) => {
            const target = e.target as HTMLElement;
            if (target.classList.contains('citation-marker')) {
              e.preventDefault();
              const idx = parseInt(target.getAttribute('data-index') || '1', 10) - 1;
              if (response.citations && response.citations[idx] && onCitationClick) {
                onCitationClick(response.citations[idx], idx);
              }
            }
          }}
        />
      </section>

      {/* Primary Statutory Authorities & Official Gazette Citations */}
      {response.citations && response.citations.length > 0 && (
        <section className="memo-authorities-section" id="memo-authorities">
          <div className="memo-section-heading">
            <Sparkles size={15} />
            <h2>Primary Statutory Authorities & Gazette Records ({response.citations.length})</h2>
          </div>
          <p className="authorities-desc">
            All citations are programmatically verified against the 11 official legal publications:
          </p>

          <div className="authorities-grid">
            {response.citations.map((cit, idx) => (
              <div 
                key={idx} 
                className="authority-card" 
                id={`citation-${idx + 1}`}
              >
                <div className="authority-card-header">
                  <span className="authority-index-pill">[{idx + 1}]</span>
                  <StatutoryBadge citation={cit} />
                </div>
                <div className="authority-card-body">
                  <div className="authority-doc-id">{cit.doc_id}</div>
                  {cit.section && (
                    <div className="authority-section-ref">
                      <strong>Section:</strong> {cit.section}
                    </div>
                  )}
                  {cit.source_url && (
                    <a 
                      href={cit.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="authority-external-link"
                    >
                      <span>Official Source Gazette</span>
                      <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </article>
  );
};
