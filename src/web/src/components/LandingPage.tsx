import React from 'react';
import {
  ArrowRight,
  Database,
  ShieldCheck,
  Scale,
  Briefcase,
  Landmark,
  Leaf
} from 'lucide-react';

interface LandingPageProps {
  onEnterWorkbench: (initialQuery?: string) => void;
  onEnterAdmin: () => void;
}

const PERSONAS = [
  {
    icon: <Leaf size={24} aria-hidden="true" />,
    tag: 'AYUSH formulator',
    title: 'Survive Section 3(p)',
    body: 'Describe your botanicals. We check classical prior art and tell you whether filing is worth the cost.',
    cta: 'Check a formulation',
    query: 'Novelty assessment for an Ashwagandha withanolide supercritical CO2 extract for neuroprotection against traditional knowledge prior art.',
  },
  {
    icon: <Briefcase size={24} aria-hidden="true" />,
    tag: 'Patent attorney',
    title: 'Build the 3(e) record',
    body: 'Frame the enhanced-efficacy argument with the exact statutory provisions it must satisfy.',
    cta: 'Draft a 3(e) position',
    query: 'Draft Section 3(e) synergy defense demonstrating bioavailability enhancement between Piperine and Curcumin beyond mere admixture.',
  },
  {
    icon: <Landmark size={24} aria-hidden="true" />,
    tag: 'NBA / SBB officer',
    title: 'Audit ABS approvals',
    body: 'Verify whether an application using Indian biological resources carries the mandatory Section 6 approval.',
    cta: 'Audit compliance',
    query: 'Assess Biological Diversity Act 2002 Section 6 approval and Form I requirements for a patent application using Commiphora mukul sourced in India.',
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterWorkbench, onEnterAdmin }) => {
  return (
    <div className="sk-portal" aria-label="Premium Product Overview">
      
      {/* Background Glow Effect */}
      <div className="sk-hero-glow"></div>

      <section className="sk-hero">
        <p className="sk-eyebrow sk-eyebrow-accent" style={{ letterSpacing: '2px', display: 'inline-block', padding: 'var(--space-xs) var(--space-md)', background: 'rgba(255, 122, 23, 0.1)', borderRadius: 'var(--radius-pill)', border: '1px solid rgba(255, 122, 23, 0.2)' }}>
          SMART INDIA HACKATHON 2026 · PS-26045
        </p>
        <h1 className="sk-hero-title">
          Know before you file.
        </h1>
        <p className="sk-lead">
          IP-SAKTI Sahayak evaluates Ayurvedic, Siddha, and Unani formulations against Indian patent bars and Biodiversity Law. 
          Grounded in official gazettes. No hallucinations. Just evidence.
        </p>
        <div className="sk-hero-ctas">
          <button type="button" className="sk-btn sk-btn-primary" onClick={() => onEnterWorkbench()} style={{ padding: 'var(--space-md) var(--space-xl)', fontSize: '16px', borderRadius: 'var(--radius-pill)', boxShadow: 'var(--shadow-glow)' }}>
            <span>Start a clearance check</span>
            <ArrowRight size={18} aria-hidden="true" />
          </button>
          <button type="button" className="sk-btn" onClick={onEnterAdmin} style={{ padding: 'var(--space-md) var(--space-xl)', fontSize: '16px', borderRadius: 'var(--radius-pill)', background: 'var(--canvas-soft)', border: '1px solid var(--hairline-strong)' }}>
            <Database size={18} aria-hidden="true" />
            <span>Inspect the corpus</span>
          </button>
        </div>
      </section>

      {/* Feature Band: The Output Anatomy */}
      <div className="sk-feature-band">
        <div className="sk-feature-content">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
            <p className="sk-eyebrow" style={{ color: 'var(--accent-sunset)' }}>Precision Output</p>
            <h2 className="sk-h2">A cited memorandum, not a chat reply.</h2>
            <p className="sk-body" style={{ fontSize: '18px', color: 'var(--mute)', maxWidth: '480px' }}>
              We rebuilt legal retrieval from the ground up to ensure you never get a hallucinated precedent.
              Every claim is pinned to a verified gazette chunk.
            </p>
            <ul style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', listStyle: 'none', padding: 0, marginTop: 'var(--space-md)' }}>
              <li style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
                <Scale size={20} style={{ color: 'var(--accent-breeze)', marginTop: '2px' }} />
                <div>
                  <strong style={{ display: 'block', color: 'var(--ink)' }}>Clear Verdicts</strong>
                  <span style={{ color: 'var(--mute)' }}>Patent-barred, patentable, or subject to NBA clearance stated upfront.</span>
                </div>
              </li>
              <li style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
                <ShieldCheck size={20} style={{ color: 'var(--status-success)', marginTop: '2px' }} />
                <div>
                  <strong style={{ display: 'block', color: 'var(--ink)' }}>Honest Refusals</strong>
                  <span style={{ color: 'var(--mute)' }}>The system refuses foreign law or ungrounded queries instead of guessing.</span>
                </div>
              </li>
            </ul>
          </div>
          
          <div className="sk-glass-card" style={{ padding: 'var(--space-xl)', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, right: 0, width: '150px', height: '150px', background: 'radial-gradient(circle, rgba(160, 195, 236, 0.1) 0%, transparent 70%)', transform: 'translate(50%, -50%)' }}></div>
            <p className="sk-eyebrow" style={{ color: 'var(--mute)', marginBottom: 'var(--space-sm)' }}>Example Output</p>
            <p className="sk-h3" style={{ marginBottom: 'var(--space-xs)' }}>Can a novel curcumin extraction process be patented?</p>
            <p className="sk-small" style={{ color: 'var(--mute)', marginBottom: 'var(--space-xl)' }}>…with quantified bioavailability gain, using turmeric sourced in Maharashtra.</p>
            
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: 'var(--space-md)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--hairline)' }}>
              <p className="sk-eyebrow sk-eyebrow-accent" style={{ marginBottom: 'var(--space-xs)' }}>Verdict</p>
              <p style={{ color: 'var(--status-success)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-xs)' }}>Potentially patentable — NBA approval mandatory</p>
              <p className="sk-small" style={{ color: 'var(--mute)', marginBottom: 'var(--space-md)' }}>Pinned to Patents Act § 3(d) and BDA § 6.</p>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                <span className="sk-tag" style={{ border: '1px solid rgba(160,195,236,0.3)', color: 'var(--accent-breeze)' }}>§ 3(d) · Gazette</span>
                <span className="sk-tag" style={{ border: '1px solid rgba(255,122,23,0.3)', color: 'var(--accent-sunset)' }}>§ 6 · NBA clearance</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginBottom: 'var(--space-2xl)' }}>
        <h2 className="sk-h2">Three desks, one clearance pipeline.</h2>
        <p className="sk-body" style={{ color: 'var(--mute)', marginTop: 'var(--space-sm)' }}>Built for the complete IP lifecycle.</p>
      </div>

      <div className="sk-premium-grid">
        {PERSONAS.map((p) => (
          <article key={p.tag} className="sk-glass-card" style={{ alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '48px', height: '48px', background: 'rgba(255, 122, 23, 0.1)', borderRadius: '12px', color: 'var(--accent-sunset)', marginBottom: 'var(--space-md)' }}>
              {p.icon}
            </div>
            <span className="sk-tag" style={{ marginBottom: 'var(--space-md)', background: 'var(--canvas-mid)', border: 'none' }}>{p.tag}</span>
            <h3 className="sk-h3" style={{ marginBottom: 'var(--space-xs)' }}>
              {p.title}
            </h3>
            <p className="sk-small" style={{ color: 'var(--mute)', lineHeight: 1.6, flexGrow: 1 }}>
              {p.body}
            </p>
            <button type="button" className="sk-btn sk-btn-sm" onClick={() => onEnterWorkbench(p.query)} style={{ marginTop: 'var(--space-lg)', width: '100%', justifyContent: 'center' }}>
              <span>{p.cta}</span>
              <ArrowRight size={14} aria-hidden="true" />
            </button>
          </article>
        ))}
      </div>
      
      <div style={{ textAlign: 'center', padding: 'var(--space-3xl) 0', color: 'var(--mute)', fontSize: '13px', maxWidth: '600px', margin: '0 auto', borderTop: '1px solid var(--hairline)', marginTop: 'var(--space-4xl)' }}>
        IP-SAKTI Sahayak covers Indian IP and biodiversity law. It is not a lawyer, it does not cover foreign jurisdictions, and its output is general awareness — not legal advice.
      </div>
    </div>
  );
};
