import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Download, 
  ExternalLink, 
  ChevronDown, 
  ChevronRight, 
  CheckCircle2, 
  XCircle, 
  Gauge, 
  Scale, 
  Sparkles,
  Layers
} from 'lucide-react';
import type { QueryResponse, Citation } from '../api/client';
import './TrustInspector.css';

interface TrustInspectorProps {
  query?: string;
  response: QueryResponse | null;
  onClose?: () => void;
}

export const TrustInspector: React.FC<TrustInspectorProps> = ({
  query,
  response,
  onClose
}) => {
  const [openChunkIdx, setOpenChunkIdx] = useState<number | null>(0);

  if (!response) {
    return (
      <div className="trust-inspector-empty" aria-label="Trust Inspector Standby">
        <div className="inspector-empty-icon">🛡️</div>
        <h3 className="empty-title">Trust & Verification Inspector</h3>
        <p className="empty-desc">
          Submit a legal inquiry or select a scenario from Judge Mode to inspect empirical confidence meters and evidentiary provenance.
        </p>
        <div className="inspector-standby-pill">
          <span>Standby · Awaiting Inquiry</span>
        </div>
      </div>
    );
  }

  const confidenceScore = response.confidence_score || 0;
  const confidencePercent = (confidenceScore * 100).toFixed(1);
  const isAboveThreshold = confidenceScore >= 0.65;
  const isAbstained = response.status === 'abstained';
  const groundingScore = response.grounding_score ?? (isAbstained ? 0.0 : 1.0);
  const citations = response.citations || [];

  // Function to generate and trigger Markdown download of the structured Legal Research Brief
  const handleExportBrief = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    const safeTitle = (query || 'legal_research').replace(/[^a-zA-Z0-9]/g, '_').slice(0, 40);
    const fileName = `IP_SAKTI_Research_Brief_${safeTitle}_${timestamp}.md`;

    const markdownContent = `# IP-SAKTI Sahayak: Statutory Legal Research Memorandum
**Generated On:** ${new Date().toUTCString()}  
**Platform Version:** IP-SAKTI Sahayak v2.0 (SIH 2026)  
**Jurisdiction:** ${response.jurisdiction || 'India (CGPDTM / NBA)'}  
**Classification:** ${response.category || 'Ayurvedic IP Advisory'}  
**Status:** ${response.status.toUpperCase()}  

---

## 1. Inquiry
> "${query || 'N/A'}"

---

## 2. Preliminary Assessment & Compliance Status
* **Status:** ${isAbstained ? 'ABSTAINED (Insufficient Evidence or Out-of-Scope)' : 'ANSWERED & VERIFIED'}
* **Patents Act Section 3(p) TKDL Bar:** ${response.tkdl_flag ? 'FLAGGED (Prior Art Bar Anticipated)' : 'NO BAR DETECTED'}
* **Biological Diversity Act (ABS) Section 6 Clearance:** ${response.abs_flag ? 'MANDATORY NBA APPROVAL REQUIRED' : 'NOT REQUIRED'}
* **Empirical Confidence Score:** ${confidencePercent}% (Benchmark Threshold: 65.0%)
* **Citation Grounding Score:** ${(groundingScore * 100).toFixed(1)}% Verified

---

## 3. Detailed Statutory Analysis
${response.answer || response.abstention_message || 'N/A'}

---

## 4. Evidentiary Citations & Primary Authorities (${citations.length})
${citations.length > 0 ? citations.map((c: Citation, idx: number) => `
### [${idx + 1}] ${c.title || c.doc_id}
* **Document ID:** \`${c.doc_id}\`
* **Statutory Section:** ${c.section || 'General'}
* **Source Gazette URL:** ${c.source_url || 'N/A'}
${c.snippet ? `* **Excerpt:** *"${c.snippet.replace(/\n/g, ' ')}"*` : ''}
`).join('\n') : '*No statutory citations recorded.*'}

---

## 5. Compliance & Statutory Disclaimer
${response.disclaimer || 'This information is provided for general awareness and does not constitute legal advice. Consult a qualified IP attorney for decisions specific to your situation.'}
`;

    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <aside className="trust-inspector-container animate-fade-in" aria-label="Trust & Explainability Inspector">
      {/* Inspector Header */}
      <div className="inspector-header">
        <div className="inspector-title-group">
          <ShieldCheck size={16} className="inspector-title-icon" />
          <span className="inspector-title-text">Why This Answer?</span>
        </div>
        {onClose && (
          <button className="inspector-close-btn" onClick={onClose} title="Close Inspector">
            ✕
          </button>
        )}
      </div>

      <div className="inspector-scroll-body">
        {/* Empirical Metrics Cockpit */}
        <section className="inspector-section">
          <div className="section-label-row">
            <Gauge size={13} />
            <span>Empirical Trust Telemetry</span>
          </div>

          <div className="trust-metrics-grid">
            {/* Confidence Meter with Cutoff Marker */}
            <div className="metric-box confidence-box">
              <div className="metric-header-row">
                <span className="metric-name">Confidence Gate</span>
                <span className={`metric-value ${isAboveThreshold ? 'pass' : 'fail'}`}>
                  {confidencePercent}%
                </span>
              </div>
              <div className="meter-track">
                <div 
                  className={`meter-bar ${isAboveThreshold ? 'pass' : 'fail'}`}
                  style={{ width: `${Math.min(100, Math.max(8, Number(confidencePercent)))}%` }}
                />
                <div className="meter-cutoff-marker" style={{ left: '65%' }} title="0.65 Confidence Threshold">
                  <span className="marker-tooltip">0.65 Gate</span>
                </div>
              </div>
              <div className="meter-caption-row">
                <span>Min: 0%</span>
                <span className="cutoff-tag">Threshold: 65%</span>
                <span>Max: 100%</span>
              </div>
            </div>

            {/* Grounding & Latency Row */}
            <div className="metric-two-col-row">
              <div className="metric-sub-box">
                <span className="sub-label">Grounding Verifier</span>
                <span className="sub-value">
                  <CheckCircle2 size={13} className="grounding-icon" />
                  <span>{(groundingScore * 100).toFixed(0)}% Provenance</span>
                </span>
              </div>

              <div className="metric-sub-box">
                <span className="sub-label">Pipeline Latency</span>
                <span className="sub-value font-mono">
                  <span>⚡ {response.response_time_ms} ms</span>
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Dual-Flag Audit State */}
        <section className="inspector-section">
          <div className="section-label-row">
            <Scale size={13} />
            <span>Statutory Compliance Checks</span>
          </div>
          <div className="dual-flags-list">
            <div className={`flag-status-item ${response.tkdl_flag ? 'triggered' : 'clear'}`}>
              {response.tkdl_flag ? <XCircle size={14} /> : <CheckCircle2 size={14} />}
              <div className="flag-item-text">
                <span className="flag-title">Section 3(p) TKDL Prior Art</span>
                <span className="flag-status">
                  {response.tkdl_flag ? 'Bar Triggered (Traditional Knowledge)' : 'Clear (No Prior Art Bar)'}
                </span>
              </div>
            </div>

            <div className={`flag-status-item ${response.abs_flag ? 'warning' : 'clear'}`}>
              {response.abs_flag ? <Sparkles size={14} /> : <CheckCircle2 size={14} />}
              <div className="flag-item-text">
                <span className="flag-title">Biological Diversity Act (ABS)</span>
                <span className="flag-status">
                  {response.abs_flag ? 'Mandatory Section 6 NBA Clearance' : 'Clear (Non-Biological Resource)'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Evidentiary Provenance Excerpts */}
        <section className="inspector-section">
          <div className="section-label-row">
            <Layers size={13} />
            <span>Retrieved Statutory Evidence ({citations.length})</span>
          </div>

          {citations.length === 0 ? (
            <p className="no-chunks-note">No external chunks retrieved for this session.</p>
          ) : (
            <div className="provenance-chunks-list">
              {citations.map((c: Citation, idx: number) => {
                const isOpen = openChunkIdx === idx;
                return (
                  <div key={idx} className="provenance-chunk-card">
                    <button 
                      className="chunk-card-header"
                      onClick={() => setOpenChunkIdx(isOpen ? null : idx)}
                    >
                      <span className="chunk-num">[{idx + 1}]</span>
                      <span className="chunk-doc-title">{c.title || c.doc_id}</span>
                      {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>

                    {isOpen && (
                      <div className="chunk-card-body animate-fade-in">
                        {c.section && (
                          <div className="chunk-section-badge">
                            <strong>Provision:</strong> {c.section}
                          </div>
                        )}
                        {c.snippet && (
                          <blockquote className="chunk-quote">
                            "{c.snippet}"
                          </blockquote>
                        )}
                        {c.source_url && (
                          <a 
                            href={c.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="chunk-source-link"
                          >
                            <span>Official Gazette Source</span>
                            <ExternalLink size={11} />
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Export Action */}
        <div className="inspector-export-section">
          <button 
            className="export-brief-btn"
            onClick={handleExportBrief}
            title="Download structured legal research memorandum as Markdown"
          >
            <Download size={14} />
            <span>Export Research Brief (.md)</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
