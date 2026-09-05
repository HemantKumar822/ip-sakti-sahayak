import React from 'react';
import {
  ArrowRight,
  Database,
  Search,
  ShieldCheck,
  Scale,
  FileText,
  Leaf,
  Briefcase,
  Landmark,
  ExternalLink,
} from 'lucide-react';

interface LandingPageProps {
  onEnterWorkbench: (initialQuery?: string) => void;
  onEnterAdmin: () => void;
}

const PERSONAS = [
  {
    icon: <Leaf size={16} aria-hidden="true" />,
    tag: 'AYUSH formulator',
    title: 'Will my formulation survive Section 3(p)?',
    body: 'Describe your botanicals and process. We check classical prior art and tell you whether filing is worth the cost — before you spend it.',
    cta: 'Check a formulation',
    query:
      'Novelty assessment for an Ashwagandha withanolide supercritical CO2 extract for neuroprotection against traditional knowledge prior art.',
  },
  {
    icon: <Briefcase size={16} aria-hidden="true" />,
    tag: 'Patent attorney',
    title: 'Build the Section 3(e) synergy record',
    body: 'Frame the enhanced-efficacy argument with the exact statutory provisions and examination guidelines it must satisfy.',
    cta: 'Draft a 3(e) position',
    query:
      'Draft Section 3(e) synergy defense demonstrating bioavailability enhancement between Piperine and Curcumin beyond mere admixture.',
  },
  {
    icon: <Landmark size={16} aria-hidden="true" />,
    tag: 'NBA / SBB officer',
    title: 'Audit ABS approvals before grant',
    body: 'Verify whether an application using Indian biological resources carries the mandatory Section 6 NBA approval and Form I filing.',
    cta: 'Audit ABS compliance',
    query:
      'Assess Biological Diversity Act 2002 Section 6 approval and Form I requirements for a patent application using Commiphora mukul sourced in India.',
  },
];

const STEPS = [
  {
    n: '01',
    title: 'State the invention',
    body: 'A plain question, or a structured breakdown: botanicals, process, efficacy claim, resource origin.',
  },
  {
    n: '02',
    title: 'Statutory retrieval',
    body: 'Hybrid dense + lexical search over 11 official gazettes — Patents Act, BDA, AYUSH guidelines, precedents.',
  },
  {
    n: '03',
    title: 'Compliance screen',
    body: 'The Section 3(p) prior-art bar and Section 6 ABS clearance are flagged independently — never blended.',
  },
  {
    n: '04',
    title: 'Memo or refusal',
    body: 'A cited memorandum when evidence clears the 0.65 gate. An explicit, actionable refusal when it does not.',
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterWorkbench, onEnterAdmin }) => {
  return (
    <div className="sk-portal" aria-label="Product overview">
      <section className="sk-hero">
        <p className="sk-eyebrow sk-eyebrow-accent">Smart India Hackathon 2026 · PS-26045</p>
        <h1 className="sk-hero-title">Know before you file.</h1>
        <p className="sk-lead">
          IP-SAKTI Sahayak screens Ayurvedic, Siddha and Unani inventions against Indian patent
          bars and biodiversity law — grounded in official gazettes, with citations you can verify.
          When the evidence is not there, it says so instead of inventing an answer.
        </p>
        <div className="sk-hero-ctas">
          <button type="button" className="sk-btn sk-btn-primary" onClick={() => onEnterWorkbench()}>
            <span>Start a clearance check</span>
            <ArrowRight size={15} aria-hidden="true" />
          </button>
          <button type="button" className="sk-btn" onClick={onEnterAdmin}>
            <Database size={15} aria-hidden="true" />
            <span>Inspect the corpus</span>
          </button>
        </div>
        <div className="sk-corpus-strip" aria-label="Corpus facts">
          <span className="sk-tag">11 official gazettes</span>
          <span className="sk-tag">296 indexed chunks</span>
          <span className="sk-tag sk-tag-warn">0.65 confidence gate</span>
          <span className="sk-tag sk-tag-ok">PII scrubbed in-browser</span>
        </div>
      </section>

      <section className="sk-section" aria-label="What an answer looks like">
        <div className="sk-section-head">
          <p className="sk-eyebrow">What an answer looks like</p>
          <h2 className="sk-h2">A memorandum with a verdict — not a chat reply</h2>
        </div>
        <div className="sk-card sk-preview" aria-hidden="true">
          <div className="sk-preview-query">
            <p className="sk-eyebrow">Inquiry</p>
            <p className="sk-h3">Can a novel curcumin extraction process be patented?</p>
            <p className="sk-small">…with quantified bioavailability gain, using turmeric sourced in Maharashtra.</p>
          </div>
          <div className="sk-preview-verdict">
            <p className="sk-eyebrow sk-eyebrow-accent">Verdict</p>
            <p className="sk-small" style={{ margin: 0, color: 'var(--ink)' }}>
              Potentially patentable — NBA approval mandatory
            </p>
            <p className="sk-mini" style={{ margin: 0 }}>
              Pinned to Patents Act § 3(d) and BDA § 6, with gazette links on every claim. Illustrative
              shape — run a check for a real memorandum.
            </p>
            <p style={{ margin: 0, display: 'flex', gap: 'var(--space-xs)', flexWrap: 'wrap' }}>
              <span className="sk-tag sk-tag-info">§ 3(d) · Gazette</span>
              <span className="sk-tag sk-tag-warn">§ 6 · NBA clearance</span>
            </p>
          </div>
        </div>
      </section>

      <hr className="sk-divider" />

      <section className="sk-section" aria-label="Who this is for">
        <div className="sk-section-head">
          <p className="sk-eyebrow">Who this is for</p>
          <h2 className="sk-h2">Three desks, one clearance question</h2>
          <p className="sk-small" style={{ margin: 0 }}>
            Each path opens the desk with a realistic inquiry pre-loaded.
          </p>
        </div>
        <div className="sk-personas">
          {PERSONAS.map((p) => (
            <article key={p.tag} className="sk-card sk-persona">
              <span className="sk-tag">{p.tag}</span>
              <h3 className="sk-h3" style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
                <span style={{ color: 'var(--accent-sunset)', display: 'inline-flex' }}>{p.icon}</span>
                <span>{p.title}</span>
              </h3>
              <p className="sk-small" style={{ margin: 0 }}>
                {p.body}
              </p>
              <div className="sk-persona-foot">
                <button type="button" className="sk-btn sk-btn-sm sk-btn-block" onClick={() => onEnterWorkbench(p.query)}>
                  <span>{p.cta}</span>
                  <ArrowRight size={14} aria-hidden="true" />
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <hr className="sk-divider" />

      <section className="sk-section" aria-label="How a clearance works">
        <div className="sk-section-head">
          <p className="sk-eyebrow">How a clearance works</p>
          <h2 className="sk-h2">A pipeline you can audit, not a black box</h2>
        </div>
        <div className="sk-steps">
          {STEPS.map((s) => (
            <div key={s.n} className="sk-card sk-step">
              <span className="sk-step-num">{s.n}</span>
              <h3 className="sk-h3">{s.title}</h3>
              <p className="sk-small" style={{ margin: 0 }}>
                {s.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      <hr className="sk-divider" />

      <section className="sk-section" aria-label="What you receive">
        <div className="sk-section-head">
          <p className="sk-eyebrow">What you receive</p>
          <h2 className="sk-h2">Everything a filing decision needs</h2>
        </div>
        <div className="sk-anatomy">
          <div className="sk-card" style={{ display: 'flex', gap: 'var(--space-md)' }}>
            <Scale size={18} aria-hidden="true" style={{ color: 'var(--accent-sunset)', flexShrink: 0 }} />
            <div>
              <h3 className="sk-h3">A verdict in plain language</h3>
              <p className="sk-small">Patent-barred, patentable subject to NBA clearance, or out of scope — stated first, reasoned after.</p>
            </div>
          </div>
          <div className="sk-card" style={{ display: 'flex', gap: 'var(--space-md)' }}>
            <FileText size={18} aria-hidden="true" style={{ color: 'var(--accent-breeze)', flexShrink: 0 }} />
            <div>
              <h3 className="sk-h3">Every claim pinned to a gazette</h3>
              <p className="sk-small">Numbered citations open the official source. No gazette, no claim — the gate enforces it at 0.65.</p>
            </div>
          </div>
          <div className="sk-card" style={{ display: 'flex', gap: 'var(--space-md)' }}>
            <ShieldCheck size={18} aria-hidden="true" style={{ color: 'var(--status-success)', flexShrink: 0 }} />
            <div>
              <h3 className="sk-h3">Two independent compliance flags</h3>
              <p className="sk-small">The 3(p) prior-art bar and Section 6 ABS clearance are checked separately, so one never hides the other.</p>
            </div>
          </div>
          <div className="sk-card" style={{ display: 'flex', gap: 'var(--space-md)' }}>
            <Search size={18} aria-hidden="true" style={{ color: 'var(--accent-twilight)', flexShrink: 0 }} />
            <div>
              <h3 className="sk-h3">Honest refusals with a next step</h3>
              <p className="sk-small">Foreign law, non-legal questions, or thin evidence get a refusal plus concrete in-scope topics — never a guess.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="sk-section" aria-label="Limits">
        <div className="sk-section-head">
          <p className="sk-eyebrow">Limits, stated upfront</p>
          <p className="sk-body" style={{ margin: 0 }}>
            This desk covers <strong style={{ color: 'var(--ink)' }}>Indian</strong> IP and biodiversity
            law for traditional-knowledge formulations. It is not a lawyer, it does not cover foreign
            jurisdictions, and its output is general awareness — not legal advice. Inquiries are
            scrubbed of personal identifiers before they leave your browser.
          </p>
        </div>
        <div className="sk-cta-band">
          <h2 className="sk-h2">Bring your formulation. Leave with a verdict.</h2>
          <p className="sk-small" style={{ margin: 0, maxWidth: '520px' }}>
            Type a question or break a formulation down field by field — the desk returns a cited
            memorandum or an honest refusal.
          </p>
          <div className="sk-hero-ctas">
            <button type="button" className="sk-btn sk-btn-primary" onClick={() => onEnterWorkbench()}>
              <span>Start a clearance check</span>
              <ArrowRight size={15} aria-hidden="true" />
            </button>
            <button type="button" className="sk-btn" onClick={onEnterAdmin}>
              <span>Inspect the corpus</span>
              <ExternalLink size={14} aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
