import React from 'react';
import { ArrowRight } from 'lucide-react';

interface Scenario {
  title: string;
  prompt: string;
  tag: string;
}

const SCENARIOS: Scenario[] = [
  {
    title: 'Classical S. 3(p) Bar',
    prompt: 'Can classical Triphala formulation be patented in India?',
    tag: 'S. 3(p) · TKDL',
  },
  {
    title: 'Proprietary Extract + ABS',
    prompt:
      'Is an innovative synergistic formulation of Ashwagandha and Giloy patentable and what ABS approvals are required?',
    tag: 'BDA S. 6 · NBA',
  },
  {
    title: 'Devanagari Query Processing',
    prompt: 'क्या त्रिफला चूर्ण पर भारतीय कानून के तहत पेटेंट मिल सकता है?',
    tag: 'Bilingual Bridge',
  },
  {
    title: 'Domain Abstention Gate',
    prompt: 'How do I train a transformer neural network using backpropagation?',
    tag: 'Out-of-Scope Circuit-Breaker',
  },
];

export const HeroState: React.FC<{ onSelectScenario: (prompt: string) => void }> = ({
  onSelectScenario,
}) => {
  return (
    <div className="animate-fade-in" aria-label="Getting started">
      <div className="sk-empty">
        <p className="sk-eyebrow sk-eyebrow-accent">Clearance Desk</p>
        <h1 className="sk-h2">Describe the invention. Get a cited verdict.</h1>
        <p className="sk-lead" style={{ maxWidth: '640px' }}>
          Ask in plain words — or break a formulation down below. Every answer is checked against
          11 official gazettes (296 chunks), and refused when evidence falls below the 0.65 gate.
        </p>
      </div>

      <p className="sk-eyebrow" style={{ marginTop: 'var(--space-lg)' }}>
        Start from a verified scenario
      </p>
      <div className="sk-scenarios" style={{ marginTop: 'var(--space-md)' }}>
        {SCENARIOS.map((sc) => (
          <button
            key={sc.title}
            type="button"
            className="sk-card sk-card-interactive"
            onClick={() => onSelectScenario(sc.prompt)}
            aria-label={`Run scenario: ${sc.title}`}
          >
            <span className="sk-tag" style={{ marginBottom: 'var(--space-sm)' }}>
              {sc.tag}
            </span>
            <span className="sk-h3" style={{ display: 'block', marginBottom: 'var(--space-xs)' }}>
              {sc.title}
            </span>
            <span className="sk-small" style={{ display: 'block', marginBottom: 'var(--space-md)' }}>
              &ldquo;{sc.prompt}&rdquo;
            </span>
            <span className="sk-small" style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-xs)', color: 'var(--mute)' }}>
              Run this check <ArrowRight size={13} aria-hidden="true" />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
