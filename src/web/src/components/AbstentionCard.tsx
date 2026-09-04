import React from 'react';
import { 
  ShieldAlert, 
  HelpCircle, 
  ArrowRight, 
  Sparkles, 
  Scale, 
  RotateCcw 
} from 'lucide-react';
import type { QueryResponse } from '../api/client';
import './AbstentionCard.css';

interface AbstentionCardProps {
  query: string;
  response: QueryResponse;
  onSelectSuggestion: (suggestion: string) => void;
  onReset: () => void;
}

const IN_SCOPE_TOPICS = [
  {
    title: 'Section 3(p) Traditional Knowledge Bar',
    query: 'What formulations are excluded under Section 3(p) of the Patents Act?'
  },
  {
    title: 'Biological Diversity Act ABS Approvals',
    query: 'Does an Indian startup need NBA approval before filing a patent using biological resources?'
  },
  {
    title: 'Section 3(d) Enhanced Therapeutic Efficacy',
    query: 'What evidence is needed to prove enhanced efficacy under Section 3(d) for Ayurvedic extracts?'
  },
  {
    title: 'ASU Medicine Trademark Registration',
    query: 'Can a generic Ayurvedic drug name like Chyawanprash be registered as an exclusive trademark?'
  }
];

export const AbstentionCard: React.FC<AbstentionCardProps> = ({
  query,
  response,
  onSelectSuggestion,
  onReset
}) => {
  const isOutOfJurisdiction = response.jurisdiction && response.jurisdiction !== 'India';
  const confidenceScore = response.confidence_score || 0;
  const confidencePercentage = Math.round(confidenceScore * 100);

  return (
    <div className="abstention-card-container animate-fade-in" aria-label="Transparent Abstention Advisory">
      {/* Abstention Banner Header */}
      <div className="abstention-header">
        <div className="abstention-icon-box" style={{ color: '#dc143c', backgroundColor: 'rgba(220, 20, 60, 0.1)' }}>
          <ShieldAlert size={22} />
        </div>
        <div className="abstention-header-text">
          <span className="abstention-badge" style={{ color: '#dc143c' }}>SAFETY CIRCUIT-BREAKER</span>
          <h2 className="abstention-title">Authoritative Statutory Evidence Not Established</h2>
          <p className="abstention-query-ref">Query: "{query}"</p>
        </div>
      </div>

      {/* Primary Reason Explanation */}
      <div className="abstention-reason-box">
        <p className="abstention-reason-main">
          {response.abstention_message || 
            "The system abstained from generating an ungrounded response to prevent regulatory hallucination. Under our strict safety protocol, answers are only provided when supported by authentic legal gazettes."}
        </p>

        {isOutOfJurisdiction ? (
          <div className="abstention-detail-row">
            <Scale size={14} className="detail-icon" />
            <span>
              <strong>Territorial Jurisdiction Restriction:</strong> IP rights are strictly territorial. 
              This engine is currently calibrated specifically for <strong>Indian Law</strong> (Patents Act 1970, BDA 2002/2023, and CSIR TKDL).
            </span>
          </div>
        ) : response.verification_status === 'failed' || (response.grounding_score !== undefined && response.grounding_score < 0.8) ? (
          <div className="abstention-detail-row warning">
            <ShieldAlert size={14} className="detail-icon" style={{ color: 'var(--color-error)' }} />
            <span>
              <strong>Grounding Verification Failed:</strong> The generated answer could not be explicitly verified against the retrieved statutory documents. To strictly prevent legal hallucination, the response has been suppressed.
            </span>
          </div>
        ) : response.tkdl_flag ? (
          <div className="abstention-detail-row warning">
            <ShieldAlert size={14} className="detail-icon" style={{ color: 'var(--color-error)' }} />
            <span>
              <strong>Traditional Knowledge Bar (Section 3(p)):</strong> This query directly triggers statutory bars under the Patents Act. Traditional knowledge cannot be patented in India.
            </span>
          </div>
        ) : confidencePercentage < 65 ? (
          <div className="confidence-deficit-gauge">
            <div className="gauge-meta-row">
              <span className="gauge-label">Empirical Confidence Gate</span>
              <span className="gauge-score-text">
                Current: <strong>{confidencePercentage}%</strong> / Cutoff: <strong>65.0%</strong>
              </span>
            </div>
            <div className="gauge-track">
              <div 
                className="gauge-fill" 
                style={{ width: `${Math.min(100, Math.max(5, confidencePercentage))}%` }}
              />
              <div className="gauge-threshold-marker" style={{ left: '65%' }}>
                <span className="marker-label">Gate 0.65</span>
              </div>
            </div>
            <p className="gauge-note">
              Confidence score did not meet the calibrated 0.65 threshold. Rather than risk speculative advice, the pipeline safely abstained.
            </p>
          </div>
        ) : (
          <div className="abstention-detail-row">
            <ShieldAlert size={14} className="detail-icon" />
            <span>
              <strong>Pipeline Abstention:</strong> The system safely abstained from answering this query based on its internal safety protocols and lack of authoritative statutory evidence.
            </span>
          </div>
        )}
      </div>

      {/* Actionable Guidance & Rephrasing Advice */}
      <div className="abstention-guidance-section">
        <div className="guidance-heading">
          <HelpCircle size={15} />
          <h3>How to Refine Your Legal Inquiry</h3>
        </div>
        <ul className="guidance-list">
          <li>
            <strong>Anchor in Indian Jurisdiction:</strong> Frame questions around Indian statutes (e.g. <em>Patents Act 1970</em>, <em>Biological Diversity Act 2002</em>, or <em>AYUSH Guidelines 2025</em>).
          </li>
          <li>
            <strong>Specify the Botanical or Formulation:</strong> Mention specific Ayurvedic plants (e.g. <em>Ashwagandha</em>, <em>Curcuma longa</em>, <em>Triphala</em>) or formulation processes.
          </li>
          <li>
            <strong>Distinguish Formulations:</strong> Clarify whether the formulation is a classical ancient recipe or a novel, standardized synergistic proprietary extract.
          </li>
        </ul>
      </div>

      {/* Clickable In-Scope Topic Suggestions */}
      <div className="in-scope-suggestions-section">
        <div className="suggestions-header">
          <Sparkles size={14} className="sparkle-icon" />
          <span>Explore Verified In-Scope Topics:</span>
        </div>
        <div className="suggestions-grid">
          {IN_SCOPE_TOPICS.map((topic, idx) => (
            <button
              key={idx}
              className="in-scope-topic-chip"
              onClick={() => onSelectSuggestion(topic.query)}
            >
              <span className="topic-title">{topic.title}</span>
              <ArrowRight size={13} className="topic-arrow" />
            </button>
          ))}
        </div>
      </div>

      {/* Reset Action */}
      <div className="abstention-footer-actions">
        <button className="abstention-reset-btn" onClick={onReset}>
          <RotateCcw size={14} />
          <span>Start a New Legal Research Note</span>
        </button>
      </div>
    </div>
  );
};
