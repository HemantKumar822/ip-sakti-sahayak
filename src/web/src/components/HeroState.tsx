import { Sparkles, ShieldCheck, Scale, BookOpen, AlertCircle, ArrowRight } from 'lucide-react';
import './HeroState.css';

interface Scenario {
  icon: string;
  category: string;
  title: string;
  prompt: string;
  badges: string[];
}

const SCENARIOS: Scenario[] = [
  {
    icon: "🌿",
    category: "Non-Patentability Exclusion",
    title: "Classical Polyherbal Formulation",
    prompt: "Can I patent an Ayurvedic formulation combining Ashwagandha, Brahmi, and Shankhpushpi for memory enhancement?",
    badges: ["Patents Act § 3(p)", "TKDL Prior Art", "Classical Texts"]
  },
  {
    icon: "🧪",
    category: "Mandatory Regulatory Clearance",
    title: "Biological Resource ABS Clearance",
    prompt: "What are the mandatory NBA approvals under Section 6 of Biological Diversity Act for commercializing a proprietary Withania somnifera extract?",
    badges: ["Bio Diversity Act § 6", "Form I-III Filing", "ABS Royalty"]
  },
  {
    icon: "⚗️",
    category: "Enhanced Efficacy Standard",
    title: "Isolated Curcuminoid Derivative",
    prompt: "How does the Supreme Court's Novartis standard apply to proving enhanced therapeutic efficacy for a novel curcumin formulation under Section 3(d)?",
    badges: ["Section 3(d)", "Novartis Precedent", "Therapeutic Efficacy"]
  },
  {
    icon: "🏷️",
    category: "Trademark & Distinctiveness",
    title: "Classical Formulation Brand Names",
    prompt: "Can an ASU manufacturer claim exclusive trademark protection over generic Ayurvedic formulation names like Chyawanprash or Triphala?",
    badges: ["Trade Marks Act § 9", "Dabur v. Emami", "Generic Names"]
  }
];

export const HeroState = ({ onSelectScenario }: { onSelectScenario: (prompt: string) => void }) => {
  return (
    <div className="hero-container animate-fade-in">
      {/* Top Banner Badge */}
      <div className="hero-badge">
        <Sparkles size={14} className="hero-badge-icon" />
        <span>Smart India Hackathon 2026 · Problem Statement PS-26045</span>
      </div>

      {/* Main Headline */}
      <h1 className="hero-title">
        Citation-Grounded Legal Intelligence for <span className="gradient-text">Ayurveda & Bio-Resources</span>
      </h1>
      <p className="hero-subtitle">
        Statutory compliance verification across Patents Act 1970 § 3(p), National Biodiversity Authority (NBA) Access and Benefit Sharing (ABS) clearances, and TKDL prior art archives.
      </p>

      {/* Trust & Capability Pillars */}
      <div className="hero-pillars">
        <div className="pillar-item">
          <ShieldCheck size={16} className="pillar-icon success" />
          <span>Zero Hallucinations (0.65 Confidence Gate)</span>
        </div>
        <div className="pillar-item">
          <BookOpen size={16} className="pillar-icon primary" />
          <span>11 Authentic Government Gazettes</span>
        </div>
        <div className="pillar-item">
          <Scale size={16} className="pillar-icon warning" />
          <span>Dual Statutory NBA & Patent Checks</span>
        </div>
        <div className="pillar-item">
          <AlertCircle size={16} className="pillar-icon info" />
          <span>Client-Side DPDP Privacy Scrubbing</span>
        </div>
      </div>

      {/* Quick-Launch Scenarios Header */}
      <div className="scenarios-header">
        <span className="scenarios-label">⚡ Explore Verified Legal Scenarios:</span>
        <span className="scenarios-hint">Click any brief to inspect full statutory analysis</span>
      </div>

      {/* 2x2 Grid of Scenario Cards */}
      <div className="scenarios-grid">
        {SCENARIOS.map((sc, idx) => (
          <div 
            key={idx} 
            className="scenario-card"
            onClick={() => onSelectScenario(sc.prompt)}
          >
            <div className="scenario-card-header">
              <span className="scenario-card-icon">{sc.icon}</span>
              <span className="scenario-card-category">{sc.category}</span>
            </div>
            <h3 className="scenario-card-title">{sc.title}</h3>
            <p className="scenario-card-prompt">"{sc.prompt}"</p>
            <div className="scenario-card-footer">
              <div className="scenario-badges">
                {sc.badges.map((b, bIdx) => (
                  <span key={bIdx} className="scenario-tag">{b}</span>
                ))}
              </div>
              <div className="scenario-action-btn">
                <span>Run Check</span>
                <ArrowRight size={14} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
