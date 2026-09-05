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
      'Is an innovative synergistic formulation of Ashwagandha and Giloy patentable?',
    tag: 'BDA S. 6',
  }
];

export const HeroState: React.FC<{ onSelectScenario: (prompt: string) => void }> = ({
  onSelectScenario,
}) => {
  return (
    <div className="animate-fade-in" aria-label="Getting started" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', textAlign: 'center' }}>
      <h1 className="sk-h2" style={{ marginBottom: 'var(--space-2xl)', fontSize: '28px', color: 'var(--ink)' }}>
        What IP scenario are we analyzing today?
      </h1>
      
      <div style={{ display: 'flex', gap: 'var(--space-md)', flexWrap: 'wrap', justifyContent: 'center' }}>
        {SCENARIOS.map((sc) => (
          <button
            key={sc.title}
            type="button"
            className="sk-btn sk-btn-quiet"
            style={{ borderRadius: '24px', padding: 'var(--space-sm) var(--space-lg)', border: '1px solid var(--hairline)', background: 'var(--canvas-soft)', color: 'var(--mute)' }}
            onClick={() => onSelectScenario(sc.prompt)}
            title={sc.prompt}
          >
            {sc.prompt}
          </button>
        ))}
      </div>
    </div>
  );
};
