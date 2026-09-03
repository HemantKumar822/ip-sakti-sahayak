import { useState, useMemo, useRef, useEffect } from 'react';
import type { FormEvent } from 'react';
import { Send, Loader2, Sparkles, User, ShieldCheck } from 'lucide-react';
import { submitQuery } from '../api/client';
import type { Message, QueryResponse } from '../api/client';
import { Callout } from './Callout';
import { StatutoryBadge } from './StatutoryBadge';
import { PipelineStepper } from './PipelineStepper';
import { CitationsDrawer } from './CitationsDrawer';
import { HeroState } from './HeroState';
import './ChatInterface.css';

const QUICK_SUGGESTIONS = [
  "Do I need SBB approval for Indian entities?",
  "Explain Section 3(p) Traditional Knowledge rule",
  "Novartis standard for Section 3(d) efficacy",
  "Commercial bio-resource royalty under ABS"
];

interface ChatInterfaceProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

export const ChatInterface = ({ messages, setMessages }: ChatInterfaceProps) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const sessionId = useMemo(() => crypto.randomUUID(), []);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, loading]);

  const handleSendText = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);
    setLastResponse(null);

    try {
      const response = await submitQuery({
        query_text: userMsg.content,
        session_id: sessionId,
        conversation_history: messages
      });

      setLastResponse(response);
      setMessages(prev => [...prev, { role: 'assistant', content: response.answer }]);
    } catch (error: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: error.message || 'Service temporarily unavailable' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSendText(query);
  };

  return (
    <div className="chat-container">
      {/* If no messages yet, show rich Hero/Onboarding state */}
      {messages.length === 0 ? (
        <div className="chat-empty-state">
          <HeroState onSelectScenario={(prompt) => handleSendText(prompt)} />
        </div>
      ) : (
        <div className="chat-history">
          {messages.map((msg, i) => (
            <div key={i} className={`message-wrapper ${msg.role} animate-fade-in`}>
              <div className={`message-bubble ${msg.role}`}>
                {msg.role === 'user' ? (
                  <div className="user-message-container">
                    <div className="user-avatar-tag">
                      <User size={14} />
                      <span>Legal Query</span>
                    </div>
                    <div className="user-query-text">{msg.content}</div>
                  </div>
                ) : (
                  <div className="assistant-card">
                    {lastResponse && i === messages.length - 1 && (
                      <>
                        {/* Technical Cockpit & Grounding Badges */}
                        <div className="response-cockpit-bar">
                          <span className="cockpit-tag category">
                            🏷️ {lastResponse.category || "Legal Advisory"}
                          </span>
                          <span className="cockpit-separator">•</span>
                          <span className="cockpit-tag jurisdiction">
                            ⚖️ {lastResponse.jurisdiction || "India"}
                          </span>
                          <span className="cockpit-separator">•</span>
                          <span className="cockpit-tag confidence">
                            <ShieldCheck size={13} className="confidence-icon" />
                            <span>{(lastResponse.confidence_score * 100).toFixed(1)}% Grounded</span>
                          </span>
                          <span className="cockpit-separator">•</span>
                          <span className="cockpit-tag latency">
                            ⚡ {lastResponse.response_time_ms} ms
                          </span>
                        </div>

                        {/* Real-Time Pipeline Lifecycle Stepper */}
                        <PipelineStepper 
                          category={lastResponse.category} 
                          jurisdiction={lastResponse.jurisdiction} 
                        />

                        {/* Statutory Compliance Alerts */}
                        {lastResponse.abs_flag && (
                          <Callout type="abs" title="Biological Diversity Act — Mandatory ABS Clearance Required">
                            {lastResponse.abs_detail}
                          </Callout>
                        )}

                        {lastResponse.tkdl_flag && (
                          <Callout type="tkdl" title="Patents Act 1970 — Section 3(p) Traditional Knowledge Prior Art Bar">
                            {lastResponse.tkdl_detail}
                          </Callout>
                        )}
                      </>
                    )}

                    {/* Main Legal Answer Prose */}
                    <div 
                      className="message-content" 
                      dangerouslySetInnerHTML={{ __html: msg.content }} 
                    />

                    {/* Primary Government Citation Pills */}
                    {lastResponse && lastResponse.citations && lastResponse.citations.length > 0 && i === messages.length - 1 && (
                      <>
                        <div className="statutory-badges-section">
                          <div className="section-label">📜 Primary Statutory Authorities:</div>
                          <div className="statutory-badges-grid">
                            {lastResponse.citations.map((cit, idx) => (
                              <StatutoryBadge key={idx} citation={cit} />
                            ))}
                          </div>
                        </div>

                        {/* Full Detailed Citations & Snippets Accordion */}
                        <CitationsDrawer citations={lastResponse.citations} />
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper assistant animate-fade-in">
              <div className="message-bubble assistant loading">
                <Loader2 className="spinner" size={18} />
                <div className="loading-text-group">
                  <span className="loading-main">Searching Statutory & Precedent Corpus...</span>
                  <span className="loading-sub">RRF Reciprocal Rank Fusion (BM25 + BGE Embeddings)</span>
                </div>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      )}

      {/* Floating Prompt Bar with Suggestion Chips */}
      <div className="chat-footer-wrapper">
        {messages.length > 0 && (
          <div className="quick-suggestions-bar">
            <Sparkles size={13} className="suggestion-sparkle" />
            <span className="suggestion-title">Suggested:</span>
            {QUICK_SUGGESTIONS.map((sug, sIdx) => (
              <button 
                key={sIdx} 
                className="suggestion-chip"
                onClick={() => handleSendText(sug)}
                disabled={loading}
              >
                {sug}
              </button>
            ))}
          </div>
        )}

        <div className="chat-input-container glass">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask your Ayurveda IP question (e.g. patentability under Section 3(p), NBA ABS approval)..."
              disabled={loading}
              className="chat-input"
            />
            <button 
              type="submit" 
              disabled={!query.trim() || loading} 
              className="chat-submit"
              title="Submit legal inquiry"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
