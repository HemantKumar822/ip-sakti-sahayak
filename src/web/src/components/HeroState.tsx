import React from 'react';
import { 
  Sparkles, 
  ShieldCheck, 
  Scale, 
  BookOpen, 
  ArrowRight, 
  FileCode2 
} from 'lucide-react';
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
    category: "S. 3(p) TKDL Bar",
    title: "Classical S. 3(p) Bar",
    prompt: "Can classical Triphala formulation be patented in India?",
    badges: ["Patents Act § 3(p)", "Traditional Knowledge"]
  },
  {
    icon: "🧪",
    category: "BDA S. 6 ABS",
    title: "Proprietary Extract + ABS",
    prompt: "Is an innovative synergistic formulation of Ashwagandha and Giloy patentable and what ABS approvals are required?",
    badges: ["Bio Diversity Act § 6", "NBA Clearance"]
  },
  {
    icon: "🌍",
    category: "Bilingual Bridge",
    title: "Devanagari Query Processing",
    prompt: "क्या त्रिफला चूर्ण पर भारतीय कानून के तहत पेटेंट मिल सकता है?",
    badges: ["Hindi Translation", "Cross-lingual Retrieval"]
  },
  {
    icon: "🛡️",
    category: "Out-of-Scope Circuit-Breaker",
    title: "Domain Abstention Gate",
    prompt: "How do I train a transformer neural network using backpropagation?",
    badges: ["Score < 0.65", "Honest Refusal"]
  }
];

export const HeroState: React.FC<{ onSelectScenario: (prompt: string) => void }> = ({ onSelectScenario }) => {
  return (
    <div className="notion-hero-sheet animate-fade-in" aria-label="Legal Research Onboarding Canvas">
      {/* Notion Document Icon & Title Block */}
      <div className="hero-document-header">
        <div className="hero-doc-icon">📜</div>
        <div className="hero-event-pill">
          <Sparkles size={13} className="sparkle-icon" />
          <span>Smart India Hackathon 2026 · Problem Statement SIH26045</span>
        </div>
        <h1 className="hero-main-title">
          Ayurvedic IP & Regulatory Intelligence Workbench
        </h1>
        <p className="hero-main-subtitle">
          Authoritative, citation-grounded statutory analysis across the <strong>Patents Act 1970</strong> (Section 3(p) Traditional Knowledge prior art), the <strong>Biological Diversity Act 2002/2023</strong> (NBA / SBB Access and Benefit Sharing), and Supreme Court precedents.
        </p>
      </div>

      {/* Trust & Provenance Feature Strip */}
      <div className="hero-provenance-strip">
        <div className="provenance-chip">
          <ShieldCheck size={14} className="provenance-icon success" />
          <span>Calibrated Confidence Gate (0.65 Cutoff)</span>
        </div>
        <div className="provenance-chip">
          <BookOpen size={14} className="provenance-icon primary" />
          <span>11 Official Government Publications (296 Chunks)</span>
        </div>
        <div className="provenance-chip">
          <Scale size={14} className="provenance-icon warning" />
          <span>Dual-Flag Patents & Biodiversity Engine</span>
        </div>
        <div className="provenance-chip">
          <FileCode2 size={14} className="provenance-icon info" />
          <span>DPDP Act 2023 Privacy-by-Design</span>
        </div>
      </div>

      {/* Notion Scenarios Block */}
      <div className="hero-scenarios-section">
        <div className="scenarios-section-header">
          <span className="section-bullet">▶</span>
          <span className="section-title-text">Select a Verified Legal Research Scenario:</span>
        </div>

        <div className="hero-scenarios-grid">
          {SCENARIOS.map((sc, idx) => (
            <button 
              key={idx} 
              className="notion-scenario-card"
              onClick={() => onSelectScenario(sc.prompt)}
            >
              <div className="card-top-meta">
                <span className="card-icon">{sc.icon}</span>
                <span className="card-category">{sc.category}</span>
              </div>
              <h3 className="card-title">{sc.title}</h3>
              <p className="card-prompt">"{sc.prompt}"</p>
              <div className="card-footer-row">
                <div className="card-tags-group">
                  {sc.badges.map((b, bIdx) => (
                    <span key={bIdx} className="card-tag">{b}</span>
                  ))}
                </div>
                <div className="card-run-action">
                  <span>Run Analysis</span>
                  <ArrowRight size={13} />
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
