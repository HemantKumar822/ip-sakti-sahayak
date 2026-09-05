import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Loader2, RotateCcw, ShieldCheck } from 'lucide-react';
import { submitQuery } from '../api/client';
import type { Message, QueryResponse, Citation } from '../api/client';
import { HeroState } from './HeroState';
import { ResearchMemo } from './ResearchMemo';
import { AbstentionCard } from './AbstentionCard';
import { PromptBar } from './PromptBar';
import { FormulationDeconstructor } from './FormulationDeconstructor';

const PHASES = [
  { text: "Parsing formulation claims...", detail: "Extracting botanical names and preparation methods" },
  { text: "Querying ChromaDB legal index...", detail: "Dense + lexical retrieval against 11 gazettes" },
  { text: "Evaluating Section 3(p) prior art...", detail: "Applying 0.65 confidence gate for TKDL matches" },
  { text: "Synthesizing legal memorandum...", detail: "Drafting compliance verdict and formatting citations" }
];

const PhasedLoading: React.FC = () => {
  const [phaseIdx, setPhaseIdx] = useState(0);

  useEffect(() => {
    const intervals = [1500, 2500, 3000]; // milliseconds for each phase transition
    let timeoutId: ReturnType<typeof setTimeout>;

    const advancePhase = (currentIdx: number) => {
      if (currentIdx < PHASES.length - 1) {
        timeoutId = setTimeout(() => {
          setPhaseIdx(currentIdx + 1);
          advancePhase(currentIdx + 1);
        }, intervals[currentIdx] || 2000);
      }
    };

    advancePhase(0);
    return () => clearTimeout(timeoutId);
  }, []);

  return (
    <div className="sk-glass-card animate-fade-in" role="status" aria-label="Checking">
      <div className="sk-loading" style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'center' }}>
        <Loader2 size={24} className="animate-spin" aria-hidden="true" style={{ color: 'var(--accent-sunset)', flexShrink: 0 }} />
        <div style={{ flex: 1, minHeight: '42px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <p className="sk-eyebrow" style={{ color: 'var(--ink)' }}>
            {PHASES[phaseIdx].text}
          </p>
          <p className="sk-mini animate-fade-in" style={{ margin: '4px 0 0', color: 'var(--mute)' }} key={phaseIdx}>
            {PHASES[phaseIdx].detail}
          </p>
        </div>
      </div>
    </div>
  );
};

interface ChatInterfaceProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  lastResponse: QueryResponse | null;
  setLastResponse: React.Dispatch<React.SetStateAction<QueryResponse | null>>;
  sessionId: string;
  onReset?: () => void;
  onCitationClick?: (citation: Citation) => void;
  onAuthError?: () => void;
  onOpenEvidence?: () => void;
  pendingQuery?: string | null;
  onConsumePending?: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  setMessages,
  setLastResponse,
  sessionId,
  onCitationClick,
  onAuthError,
  onOpenEvidence,
  pendingQuery,
  onConsumePending,
}) => {
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const userTurns = useMemo(() => messages.filter((m) => m.role === 'user').length, [messages]);
  const limitReached = userTurns >= 6;
  const isEmpty = messages.length === 0 && !loading;

  useEffect(() => {
    if (messages.length > 0 || loading) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, loading]);

  // Portal persona CTAs arrive as a pending query: send exactly once.
  const pendingRef = useRef<string | null>(null);
  useEffect(() => {
    if (pendingQuery && pendingRef.current !== pendingQuery) {
      pendingRef.current = pendingQuery;
      onConsumePending?.();
      void send(pendingQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingQuery]);

  async function send(text: string) {
    const query = text.trim();
    if (!query || loading) return;
    setLoading(true);
    try {
      setMessages((prev) => [...prev, { role: 'user', content: query }]);
      const history: Message[] = [...messages, { role: 'user', content: query }];
      const response = await submitQuery({ query_text: query, session_id: sessionId, conversation_history: history });
      setLastResponse(response);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.answer || response.abstention_message || '', responseMetadata: response },
      ]);
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : 'Service temporarily unavailable';
      if (msg.includes('API Key Required')) {
        onAuthError?.();
        return;
      }
      const fallback: QueryResponse = {
        status: 'error' as any,
        answer: null,
        abstention_message: msg,
        citations: [],
        confidence_score: 0,
        response_time_ms: 0,
        abs_flag: false,
        tkdl_flag: false,
      };
      setLastResponse(fallback);
      setMessages((prev) => [...prev, { role: 'assistant', content: msg, responseMetadata: fallback }]);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setMessages([]);
    setLastResponse(null);
  }

  return (
    <div className="sk-dock-chat">
      <div className="sk-dock-scroll">
        <div className="sk-dock-narrow">
          {messages.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <p className="sk-eyebrow">Clearance record · {userTurns} of 6 inquiries</p>
              <div style={{ display: 'flex', gap: 'var(--space-xs)' }}>
                {onOpenEvidence && (
                  <button type="button" className="sk-btn sk-btn-sm sk-only-mobile" onClick={onOpenEvidence}>
                    <ShieldCheck size={13} aria-hidden="true" />
                    <span>Evidence</span>
                  </button>
                )}
                <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={reset} title="Start over">
                  <RotateCcw size={13} aria-hidden="true" />
                  <span>Start over</span>
                </button>
              </div>
            </div>
          )}

          {isEmpty && <HeroState onSelectScenario={(p) => void send(p)} />}

          {messages.map((msg, i) => {
            if (msg.role === 'user') {
              return (
                <section key={i} className="animate-fade-in" aria-label={`Inquiry ${Math.ceil((i + 1) / 2)}`}>
                  <p className="sk-eyebrow" style={{ marginBottom: 'var(--space-xs)' }}>
                    Your inquiry
                  </p>
                  <h2 className="sk-h2">{msg.content}</h2>
                </section>
              );
            }
            const r = msg.responseMetadata;
            if (!r) return null;
            if (r.status === 'error' as any) {
              return (
                <div key={i} className="sk-glass-card animate-fade-in" role="alert" style={{ borderColor: 'var(--status-error)' }}>
                  <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'flex-start' }}>
                    <span style={{ color: 'var(--status-error)' }}>
                      <RotateCcw size={22} aria-hidden="true" />
                    </span>
                    <div>
                      <p className="sk-eyebrow" style={{ color: 'var(--status-error)' }}>System Error</p>
                      <h3 className="sk-h3" style={{ marginTop: 'var(--space-xs)' }}>{r.abstention_message}</h3>
                      <div style={{ marginTop: 'var(--space-md)' }}>
                        <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={reset}>
                          <RotateCcw size={13} aria-hidden="true" />
                          <span>Start over</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            }
            return r.status === 'abstained' ? (
              <AbstentionCard key={i} response={r} onSelectSuggestion={(s) => void send(s)} onReset={reset} />
            ) : (
              <ResearchMemo key={i} response={r} onCitationClick={onCitationClick} />
            );
          })}

          {loading && <PhasedLoading />}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="sk-dock-inquiry">
        <div className="sk-dock-inquiry-inner">
          {limitReached ? (
            <div className="sk-glass-card sk-card-soft" style={{ padding: 'var(--space-md)' }}>
              <p className="sk-small" style={{ margin: 0 }}>
                Six inquiries used — session memory is full. Start over for a fresh record.
              </p>
            </div>
          ) : (
            <>
              <PromptBar onSubmitQuery={(t) => void send(t)} loading={loading} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
