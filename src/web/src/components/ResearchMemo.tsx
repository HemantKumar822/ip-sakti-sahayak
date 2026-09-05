import React, { useMemo } from 'react';
import { ShieldCheck, Scale, Clock, ExternalLink, Copy, Printer, Download } from 'lucide-react';
import type { QueryResponse, Citation } from '../api/client';
import { toast } from '../utils/toast';

interface ResearchMemoProps {
  response: QueryResponse;
  onCitationClick?: (citation: Citation) => void;
  queryLabel?: string;
}

function verdictFor(r: QueryResponse): { title: string; body: string; tone: 'warn' | 'info' | '' } {
  if (r.tkdl_flag && r.abs_flag)
    return {
      title: 'Patent-barred — and NBA clearance would still be required',
      body: 'This reads as traditional knowledge under Section 3(p), so a patent cannot cover it as claimed. Separately, any use of the underlying biological resource needs National Biodiversity Authority approval under Section 6 before an IP application.',
      tone: 'warn',
    };
  if (r.tkdl_flag)
    return {
      title: 'Patent-barred under Section 3(p)',
      body: 'The invention matches classical prior art or a mere aggregation of known properties. Under the Patents Act 1970 and the 2025 AYUSH examination guidelines, that is not patentable subject matter.',
      tone: 'warn',
    };
  if (r.abs_flag)
    return {
      title: 'Potentially patentable — NBA approval mandatory',
      body: 'A novel, efficacious proprietary invention can be patent-eligible under Section 3(d), but because it uses Indian biological resources, prior NBA approval under Section 6 of the Biological Diversity Act is required before grant.',
      tone: 'info',
    };
  return {
    title: 'No statutory bar detected',
    body: 'No prior-art bar or biodiversity clearance requirement surfaced in the retrieved authorities. Novelty, inventive step and efficacy evidence still decide patentability at examination.',
    tone: '',
  };
}

export const ResearchMemo: React.FC<ResearchMemoProps> = ({ response, onCitationClick, queryLabel }) => {
  const verdict = useMemo(() => verdictFor(response), [response]);

  const bodyHtml = useMemo(() => {
    if (!response.answer) return '';
    const linked = response.answer.replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, (_m, nums: string) =>
      nums
        .split(',')
        .map((n) => n.trim())
        .filter((n) => /^\d+$/.test(n))
        .map((n) => `<a href="#citation-${n}" class="sk-cite-marker" data-index="${n}">[${n}]</a>`)
        .join('')
    );
    return linked
      .split('\n\n')
      .filter((p) => p.trim())
      .map((p) => `<p style="margin:0 0 1rem;">${p.replace(/\n/g, '<br/>')}</p>`)
      .join('');
  }, [response.answer]);

  function activateCitation(el: HTMLElement | null) {
    if (!el) return;
    const idx = parseInt(el.getAttribute('data-index') || '1', 10) - 1;
    const c = response.citations?.[idx];
    if (c && onCitationClick) onCitationClick(c);
  }

  function copyMemo() {
    const cites = (response.citations || [])
      .map((c, i) => `[${i + 1}] ${c.title || c.doc_id} (${c.section || 'general'})\n${c.source_url || ''}`)
      .join('\n\n');
    const md = `# Clearance memorandum\n\n**Verdict:** ${verdict.title}\n\n${verdict.body}\n\n---\n\n## Analysis\n\n${response.answer || ''}\n\n---\n\n## Authorities\n\n${cites}\n\n*IP-SAKTI Sahayak — general awareness only, not legal advice.*`;
    navigator.clipboard
      .writeText(md)
      .then(() => toast.success('Copied', 'Memorandum copied as Markdown.'))
      .catch(() => toast.error('Copy failed', 'Your browser blocked clipboard access.'));
  }

  return (
    <article className="sk-card sk-memo animate-fade-in" aria-label="Clearance memorandum">
      <header className="sk-memo-head">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-sm)', flexWrap: 'wrap' }}>
          <p className="sk-eyebrow">Clearance memorandum</p>
          <div className="sk-memo-actions">
            <button type="button" className="sk-btn sk-btn-sm sk-btn-quiet" onClick={copyMemo} title="Copy as Markdown">
              <Copy size={13} aria-hidden="true" />
              <span>Copy</span>
            </button>
            <button type="button" className="sk-btn sk-btn-sm sk-btn-quiet" onClick={() => window.print()} title="Print or save PDF">
              <Printer size={13} aria-hidden="true" />
              <span>Print</span>
            </button>
          </div>
        </div>
        {queryLabel && <h3 className="sk-h3">{queryLabel}</h3>}
        <div className="sk-memo-tags">
          <span className="sk-tag">{response.category || 'Ayurvedic IP advisory'}</span>
          <span className="sk-tag sk-tag-ok">
            <ShieldCheck size={11} aria-hidden="true" />
            <span>{(response.confidence_score * 100).toFixed(1)}% grounded</span>
          </span>
          <span className="sk-tag">
            <Clock size={11} aria-hidden="true" />
            <span>{response.response_time_ms} ms</span>
          </span>
        </div>
      </header>

      <section className={`sk-alert ${verdict.tone === 'warn' ? 'sk-alert-warn' : verdict.tone === 'info' ? 'sk-alert-info' : ''}`} aria-label="Verdict">
        <p className="sk-eyebrow">Verdict</p>
        <p className="sk-verdict">{verdict.title}</p>
        <p className="sk-alert-body">{verdict.body}</p>
      </section>

      {(response.abs_flag || response.tkdl_flag) && (
        <section aria-label="Compliance flags" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          {response.abs_flag && (
            <div className="sk-flag sk-flag-warn">
              <Scale size={15} aria-hidden="true" style={{ color: 'var(--accent-sunset)', flexShrink: 0, marginTop: '2px' }} />
              <div>
                <p className="sk-small" style={{ margin: 0, color: 'var(--ink)' }}>
                  Section 6 · Biological Diversity Act — NBA approval required
                </p>
                <p className="sk-small" style={{ margin: '2px 0 0' }}>
                  {response.abs_detail || 'Commercial use of this biological resource needs prior National Biodiversity Authority approval.'}
                </p>
              </div>
            </div>
          )}
          {response.tkdl_flag && (
            <div className="sk-flag sk-flag-info">
              <ShieldCheck size={15} aria-hidden="true" style={{ color: 'var(--accent-breeze)', flexShrink: 0, marginTop: '2px' }} />
              <div>
                <p className="sk-small" style={{ margin: 0, color: 'var(--ink)' }}>
                  Section 3(p) · Patents Act — prior-art bar
                </p>
                <p className="sk-small" style={{ margin: '2px 0 0' }}>
                  {response.tkdl_detail || 'This matches traditional-knowledge prior art recorded in the TKDL corpus.'}
                </p>
              </div>
            </div>
          )}
        </section>
      )}

      <section aria-label="Analysis">
        <p className="sk-eyebrow" style={{ marginBottom: 'var(--space-sm)' }}>
          Analysis
        </p>
        <div
          className="sk-body"
          dangerouslySetInnerHTML={{ __html: bodyHtml }}
          onClick={(e) => {
            const t = e.target as HTMLElement;
            if (t.closest?.('.sk-cite-marker')) {
              e.preventDefault();
              activateCitation(t.closest('.sk-cite-marker') as HTMLElement);
            }
          }}
          onKeyDown={(e) => {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            const t = e.target as HTMLElement;
            const m = t.closest?.('.sk-cite-marker') as HTMLElement | null;
            if (m) {
              e.preventDefault();
              activateCitation(m);
            }
          }}
        />
      </section>

      {response.citations?.length > 0 && (
        <section aria-label={`Authorities, ${response.citations.length}`} style={{ borderTop: '1px solid var(--hairline)', paddingTop: 'var(--space-lg)' }}>
          <p className="sk-eyebrow" style={{ marginBottom: 'var(--space-md)' }}>
            Authorities · {response.citations.length}
          </p>
          <div className="sk-cites">
            {response.citations.map((c, i) => (
              <div key={i} className="sk-card sk-card-soft sk-cite" id={`citation-${i + 1}`}>
                <span className="sk-mini">[{i + 1}] · {c.doc_type || 'Authority'}</span>
                <p className="sk-small" style={{ margin: 0, color: 'var(--ink)' }}>
                  {c.title || c.doc_id}
                </p>
                {c.section && <p className="sk-mini" style={{ margin: 0 }}>Section: {c.section}</p>}
                {c.source_url && (
                  <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="sk-small" style={{ display: 'inline-flex', gap: 'var(--space-xs)', alignItems: 'center', color: 'var(--accent-breeze)' }}>
                    <span>Official source</span>
                    <ExternalLink size={12} aria-hidden="true" />
                  </a>
                )}
              </div>
            ))}
          </div>
          <p className="sk-mini" style={{ marginTop: 'var(--space-md)', display: 'flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
            <Download size={12} aria-hidden="true" />
            <span>Full research-brief export lives in the evidence rail.</span>
          </p>
        </section>
      )}
    </article>
  );
};
