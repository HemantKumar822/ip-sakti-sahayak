import React, { useState } from 'react';
import {
  ShieldCheck,
  Download,
  ExternalLink,
  ChevronDown,
  CheckCircle2,
  XCircle,
  X,
  Gauge,
  Scale,
  Layers,
  Sparkles,
} from 'lucide-react';
import type { QueryResponse, Citation } from '../api/client';

interface TrustInspectorProps {
  response: QueryResponse | null;
  onClose?: () => void;
}

const STAGES = ['PII scrubbed', 'Classified', 'Jurisdiction routed', 'Hybrid retrieval', 'Gate checked'];

function downloadBrief(query: string, r: QueryResponse) {
  const pct = ((r.confidence_score || 0) * 100).toFixed(1);
  const cites = (r.citations || [])
    .map(
      (c: Citation, i: number) =>
        `### [${i + 1}] ${c.title || c.doc_id}\n- Document: \`${c.doc_id}\`\n- Section: ${c.section || 'general'}\n- Source: ${c.source_url || 'n/a'}${c.snippet ? `\n- Extract: "${c.snippet.replace(/\n/g, ' ')}"` : ''}`
    )
    .join('\n\n');
  const md = `# IP-SAKTI clearance memorandum\n\n**Jurisdiction:** ${r.jurisdiction || 'India'} · **Category:** ${r.category || 'Advisory'} · **Status:** ${r.status.toUpperCase()}\n\n## Inquiry\n\n> "${query || 'n/a'}"\n\n## Compliance\n\n- Section 3(p) prior-art bar: ${r.tkdl_flag ? 'TRIGGERED' : 'clear'}\n- BDA Section 6 NBA clearance: ${r.abs_flag ? 'REQUIRED' : 'not required'}\n- Confidence: ${pct}% (gate 65%)\n\n## Analysis\n\n${r.answer || r.abstention_message || 'n/a'}\n\n## Authorities\n\n${cites || 'None recorded.'}\n\n*General awareness only — not legal advice.*`;
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `IP_SAKTI_brief_${new Date().toISOString().split('T')[0]}.md`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const TrustInspector: React.FC<TrustInspectorProps> = ({ response, onClose }) => {
  const [openIdx, setOpenIdx] = useState<number | null>(0);

  if (!response) {
    return (
      <div aria-label="Evidence standby">
        <p className="sk-eyebrow">Evidence & verification</p>
        <div className="sk-card" style={{ marginTop: 'var(--space-md)' }}>
          <p className="sk-small" style={{ margin: 0, display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
            <ShieldCheck size={15} aria-hidden="true" style={{ color: 'var(--mute)' }} />
            <span>Run an inquiry and this rail shows the verdict basis: confidence, flags, and every cited gazette.</span>
          </p>
        </div>
        <div className="sk-ev-block" style={{ marginTop: 'var(--space-lg)' }}>
          <p className="sk-eyebrow">Pipeline stages</p>
          <ul className="sk-stage-list">
            {STAGES.map((s) => (
              <li key={s} className="sk-stage">
                <span className="sk-stage-dot" style={{ background: 'var(--hairline-strong)' }} aria-hidden="true" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  const pct = (response.confidence_score || 0) * 100;
  const pass = response.confidence_score >= 0.65 && response.status === 'answered';
  const grounding = (response.grounding_score ?? (response.status === 'abstained' ? 0 : 1)) * 100;
  const cites = response.citations || [];

  return (
    <div className="animate-fade-in" aria-label="Evidence and verification">
      <div className="sk-ev-row">
        <p className="sk-eyebrow">Why this answer?</p>
        {onClose && (
          <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={onClose} aria-label="Close evidence panel">
            <X size={14} aria-hidden="true" />
          </button>
        )}
      </div>

      <div className="sk-ev-block" style={{ marginTop: 'var(--space-md)' }}>
        <p className="sk-eyebrow">
          <Gauge size={12} aria-hidden="true" />
          <span>Confidence</span>
        </p>
        <div className="sk-card" style={{ padding: 'var(--space-md)' }}>
          <div className="sk-ev-row" style={{ marginBottom: 'var(--space-sm)' }}>
            <span className="sk-small">Retrieved confidence</span>
            <span className="sk-tag" style={{ border: 'none', background: 'transparent', padding: 0 }}>
              {pass ? <CheckCircle2 size={13} aria-hidden="true" style={{ color: 'var(--status-success)' }} /> : <XCircle size={13} aria-hidden="true" style={{ color: 'var(--status-error)' }} />}
              <span>{pct.toFixed(1)}%</span>
            </span>
          </div>
          <div className="sk-meter" role="img" aria-label={`Confidence ${pct.toFixed(0)} percent, gate 65 percent`}>
            <div className={`sk-meter-fill ${pass ? '' : 'sk-meter-fill-bad'}`} style={{ width: `${Math.min(100, Math.max(8, pct))}%` }} />
            <div className="sk-meter-gate" style={{ left: '65%' }} />
          </div>
          <div className="sk-ev-row" style={{ marginTop: 'var(--space-xs)' }}>
            <span className="sk-mini">Gate 65%</span>
            <span className="sk-mini">Grounding {grounding.toFixed(0)}% · {response.response_time_ms} ms</span>
          </div>
        </div>
      </div>

      <div className="sk-ev-block" style={{ marginTop: 'var(--space-lg)' }}>
        <p className="sk-eyebrow">
          <Scale size={12} aria-hidden="true" />
          <span>Compliance</span>
        </p>
        <div className={`sk-flag ${response.tkdl_flag ? 'sk-flag-bad' : ''}`}>
          {response.tkdl_flag ? <XCircle size={14} aria-hidden="true" style={{ color: 'var(--status-error)', flexShrink: 0 }} /> : <CheckCircle2 size={14} aria-hidden="true" style={{ color: 'var(--status-success)', flexShrink: 0 }} />}
          <p className="sk-small" style={{ margin: 0 }}>
            <strong style={{ color: 'var(--ink)' }}>3(p) prior art:</strong> {response.tkdl_flag ? 'bar triggered' : 'clear'}
          </p>
        </div>
        <div className={`sk-flag ${response.abs_flag ? 'sk-flag-warn' : ''}`}>
          {response.abs_flag ? <Sparkles size={14} aria-hidden="true" style={{ color: 'var(--accent-sunset)', flexShrink: 0 }} /> : <CheckCircle2 size={14} aria-hidden="true" style={{ color: 'var(--status-success)', flexShrink: 0 }} />}
          <p className="sk-small" style={{ margin: 0 }}>
            <strong style={{ color: 'var(--ink)' }}>BDA Section 6:</strong> {response.abs_flag ? 'NBA clearance required' : 'clear'}
          </p>
        </div>
      </div>

      <div className="sk-ev-block" style={{ marginTop: 'var(--space-lg)' }}>
        <p className="sk-eyebrow">
          <Layers size={12} aria-hidden="true" />
          <span>Authorities ({cites.length})</span>
        </p>
        {cites.length === 0 ? (
          <p className="sk-mini" style={{ margin: 0 }}>No gazettes cited for this response.</p>
        ) : (
          cites.map((c, i) => {
            const open = openIdx === i;
            return (
              <div key={i} className="sk-card" style={{ padding: 0, overflow: 'hidden' }}>
                <button
                  type="button"
                  onClick={() => setOpenIdx(open ? null : i)}
                  aria-expanded={open}
                  style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', padding: 'var(--space-sm) var(--space-md)', background: 'var(--canvas-soft)', color: 'var(--ink)', fontSize: '13px' }}
                >
                  <span className="sk-mini">[{i + 1}]</span>
                  <span style={{ flex: 1, textAlign: 'left', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {c.title || c.doc_id}
                  </span>
                  <ChevronDown size={14} aria-hidden="true" style={{ transform: open ? 'rotate(180deg)' : undefined, color: 'var(--mute)' }} />
                </button>
                {open && (
                  <div style={{ padding: 'var(--space-md)', display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
                    {c.section && <p className="sk-mini" style={{ margin: 0 }}>Provision: {c.section}</p>}
                    {c.snippet && <blockquote className="sk-small" style={{ margin: 0, borderLeft: '2px solid var(--hairline-strong)', paddingLeft: 'var(--space-sm)' }}>&ldquo;{c.snippet}&rdquo;</blockquote>}
                    {c.source_url && (
                      <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="sk-small" style={{ display: 'inline-flex', gap: 'var(--space-xs)', alignItems: 'center', color: 'var(--accent-breeze)' }}>
                        <span>Official gazette</span>
                        <ExternalLink size={11} aria-hidden="true" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div style={{ marginTop: 'var(--space-lg)' }}>
        <button type="button" className="sk-btn sk-btn-block sk-btn-sm" onClick={() => downloadBrief('', response)} title="Download memorandum as Markdown">
          <Download size={14} aria-hidden="true" />
          <span>Export Research Brief (.md)</span>
        </button>
      </div>
    </div>
  );
};
