import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Loader2, RotateCcw, ShieldCheck } from 'lucide-react';
import { submitQuery } from '../api/client';
import type { Message, QueryResponse, Citation } from '../api/client';
import { HeroState } from './HeroState';
import { ResearchMemo } from './ResearchMemo';
import { AbstentionCard } from './AbstentionCard';
import { PromptBar } from './PromptBar';
import { FormulationDeconstructor } from './FormulationDeconstructor';

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
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
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
      const history = [...messages, { role: 'user', content: query }];
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
        status: 'abstained',
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
            return r.status === 'abstained' ? (
              <AbstentionCard key={i} response={r} onSelectSuggestion={(s) => void send(s)} onReset={reset} />
            ) : (
              <ResearchMemo key={i} response={r} onCitationClick={onCitationClick} />
            );
          })}

          {loading && (
            <div className="sk-card animate-fade-in" role="status" aria-label="Checking">
              <div className="sk-loading">
                <Loader2 size={18} className="animate-spin" aria-hidden="true" style={{ color: 'var(--accent-sunset)' }} />
                <div>
                  <p className="sk-eyebrow" style={{ color: 'var(--ink)' }}>
                    Checking gazettes and compliance flags
                  </p>
                  <p className="sk-mini" style={{ margin: '2px 0 0' }}>
                    Dense + lexical retrieval, Section 3(p) / Section 6 screen, 0.65 gate…
                  </p>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="sk-dock-inquiry">
        <div className="sk-dock-inquiry-inner">
          {limitReached ? (
            <div className="sk-card sk-card-soft" style={{ padding: 'var(--space-md)' }}>
              <p className="sk-small" style={{ margin: 0 }}>
                Six inquiries used — session memory is full. Start over for a fresh record.
              </p>
            </div>
          ) : (
            <>
              <PromptBar onSubmitQuery={(t) => void send(t)} loading={loading} />
              {!loading && messages.length < 3 && (
                <FormulationDeconstructor onSubmitDeconstruction={(q) => void send(q)} isLoading={loading} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
