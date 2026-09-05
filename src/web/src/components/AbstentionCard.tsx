import React from 'react';
import { ShieldAlert, ArrowRight, RotateCcw, Globe2, GaugeCircle } from 'lucide-react';
import type { QueryResponse } from '../api/client';

interface AbstentionCardProps {
  response: QueryResponse;
  onSelectSuggestion: (suggestion: string) => void;
  onReset: () => void;
}

const IN_SCOPE = [
  {
    title: 'What does Section 3(p) exclude?',
    query: 'What formulations are excluded under Section 3(p) of the Patents Act?',
  },
  {
    title: 'When is NBA approval needed?',
    query: 'Does an Indian startup need NBA approval before filing a patent using biological resources?',
  },
  {
    title: 'Proving enhanced efficacy',
    query: 'What evidence is needed to prove enhanced efficacy under Section 3(d) for Ayurvedic extracts?',
  },
  {
    title: 'Generic names as trademarks',
    query: 'Can a generic Ayurvedic drug name like Chyawanprash be registered as an exclusive trademark?',
  },
];

export const AbstentionCard: React.FC<AbstentionCardProps> = ({ response, onSelectSuggestion, onReset }) => {
  const foreign = !!response.jurisdiction && response.jurisdiction !== 'India';
  const pct = Math.round((response.confidence_score || 0) * 100);
  const groundingFailed =
    response.verification_status === 'failed' ||
    (response.grounding_score !== undefined && response.grounding_score < 0.8);

  return (
    <div className="sk-card animate-fade-in" role="alert" aria-label="No confident answer">
      <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
        <span style={{ color: 'var(--status-error)', display: 'inline-flex', flexShrink: 0 }}>
          <ShieldAlert size={22} aria-hidden="true" />
        </span>
        <div>
          <p className="sk-eyebrow" style={{ color: 'var(--status-error)' }}>
            No confident answer
          </p>
          <h3 className="sk-h3" style={{ marginTop: 'var(--space-xs)' }}>
            The evidence is not strong enough to advise
          </h3>
        </div>
      </div>

      <p className="sk-body" style={{ marginTop: 'var(--space-md)' }}>
        {response.abstention_message ||
          'Nothing in the indexed gazettes supports this inquiry at the required confidence level. Refusing is deliberate — a guessed legal answer is worse than none.'}
      </p>

      {foreign ? (
        <div className="sk-flag sk-flag-bad" style={{ marginTop: 'var(--space-md)' }}>
          <Globe2 size={15} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />
          <p className="sk-small" style={{ margin: 0 }}>
            <strong style={{ color: 'var(--ink)' }}>Outside Indian jurisdiction.</strong> IP rights are
            territorial; this desk is calibrated for the Patents Act 1970, the Biological Diversity
            Act, and TKDL authorities only.
          </p>
        </div>
      ) : groundingFailed ? (
        <div className="sk-flag sk-flag-bad" style={{ marginTop: 'var(--space-md)' }}>
          <ShieldAlert size={15} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />
          <p className="sk-small" style={{ margin: 0 }}>
            <strong style={{ color: 'var(--ink)' }}>A draft answer failed verification.</strong> It could
            not be pinned to retrieved authorities, so it was withheld rather than shown unverified.
          </p>
        </div>
      ) : (
        pct < 65 && (
          <div style={{ marginTop: 'var(--space-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-xs)' }}>
              <span className="sk-mini">Retrieved confidence</span>
              <span className="sk-mini">
                {pct}% · gate 65%
              </span>
            </div>
            <div className="sk-meter" role="img" aria-label={`Confidence ${pct} percent, below the 65 percent gate`}>
              <div className="sk-meter-fill sk-meter-fill-bad" style={{ width: `${Math.min(100, Math.max(5, pct))}%` }} />
              <div className="sk-meter-gate" style={{ left: '65%' }} />
            </div>
          </div>
        )
      )}

      <div style={{ marginTop: 'var(--space-lg)' }}>
        <p className="sk-eyebrow" style={{ marginBottom: 'var(--space-sm)', display: 'flex', gap: 'var(--space-xs)', alignItems: 'center' }}>
          <GaugeCircle size={12} aria-hidden="true" />
          <span>How to get an answerable inquiry</span>
        </p>
        <ul className="sk-small" style={{ margin: 0, paddingLeft: 'var(--space-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
          <li>Name an Indian statute or guideline — Patents Act, BDA, AYUSH 2025.</li>
          <li>Name the botanical or formulation — Ashwagandha, Curcuma longa, Triphala.</li>
          <li>Say whether it is classical or a novel proprietary process.</li>
        </ul>
      </div>

      <div style={{ marginTop: 'var(--space-lg)' }}>
        <p className="sk-eyebrow" style={{ marginBottom: 'var(--space-sm)' }}>
          Verified in-scope topics
        </p>
        <div className="sk-suggest-grid">
          {IN_SCOPE.map((t) => (
            <button key={t.title} type="button" className="sk-btn sk-btn-sm" onClick={() => onSelectSuggestion(t.query)} style={{ justifyContent: 'space-between' }}>
              <span>{t.title}</span>
              <ArrowRight size={13} aria-hidden="true" />
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 'var(--space-md)' }}>
        <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={onReset}>
          <RotateCcw size={13} aria-hidden="true" />
          <span>Start a new inquiry</span>
        </button>
      </div>
    </div>
  );
};
