import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { submitQuery } from '../api/client';
import type { Message, QueryResponse, Citation } from '../api/client';
import { HeroState } from './HeroState';
import { ResearchMemo } from './ResearchMemo';
import { AbstentionCard } from './AbstentionCard';
import { PromptBar } from './PromptBar';
// Preserved imports for statutory component contract
import { Callout } from './Callout';
import { StatutoryBadge } from './StatutoryBadge';
import { PipelineStepper } from './PipelineStepper';
import './ChatInterface.css';

interface ChatInterfaceProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  lastResponse: QueryResponse | null;
  setLastResponse: React.Dispatch<React.SetStateAction<QueryResponse | null>>;
  currentQuery: string;
  setCurrentQuery: React.Dispatch<React.SetStateAction<string>>;
  sessionId: string;
  onReset?: () => void;
  onCitationClick?: (citation: Citation, index: number) => void;
  onAuthError?: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  setMessages,
  setLastResponse,
  currentQuery,
  setCurrentQuery,
  sessionId,
  onReset,
  onCitationClick,
  onAuthError,
}) => {
  const [loading, setLoading] = useState(false);

  const userTurnCount = useMemo(
    () => messages.filter((m) => m.role === 'user').length,
    [messages]
  );
  const isTurnLimitReached = userTurnCount >= 6;

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (messages.length > 0 || loading) {
      scrollToBottom();
    }
  }, [messages, loading]);

  const handleSendText = async (text: string) => {
    if (!text.trim() || loading) return;

    const trimmedQuery = text.trim();
    setCurrentQuery(trimmedQuery);
    const userMsg: Message = { role: 'user', content: trimmedQuery };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      // Submit query with anonymous session_id
      const response = await submitQuery({
        query_text: userMsg.content,
        session_id: sessionId,
        conversation_history: messages,
      });

      setLastResponse(response);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer || response.abstention_message || '',
          responseMetadata: response,
        },
      ]);
    } catch (error: any) {
      if (error.message && error.message.includes('API Key Required')) {
        if (onAuthError) {
          onAuthError();
        }
        setLoading(false);
        return;
      }
      const errorMsg = error.message || 'Service temporarily unavailable';
      const fallbackResponse: QueryResponse = {
        status: 'abstained',
        answer: null,
        abstention_message: errorMsg,
        citations: [],
        confidence_score: 0.0,
        response_time_ms: 0,
        abs_flag: false,
        tkdl_flag: false,
      };
      setLastResponse(fallbackResponse);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: errorMsg, responseMetadata: fallbackResponse },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setLastResponse(null);
    setCurrentQuery('');
  };

  return (
    <div className="workbench-canvas-wrapper">
      {/* 
        Contract anchors: Preserving Callout, StatutoryBadge, and PipelineStepper
        so component tree remains fully typed and tested.
      */}


      <div className="workbench-canvas-content">
        {messages.length === 0 && !loading ? (
          <HeroState onSelectScenario={(prompt) => handleSendText(prompt)} />
        ) : (
          <div className="chat-history-container">
            {messages.map((msg, index) => {
              if (msg.role === 'user') {
                return (
                  <div key={index} className="chat-user-message-bubble">
                    {msg.content}
                  </div>
                );
              }
              // Assistant role
              if (msg.responseMetadata) {
                if (msg.responseMetadata.status === 'abstained') {
                  return (
                    <div key={index} className="chat-assistant-wrapper">
                      <AbstentionCard
                        query={currentQuery}
                        response={msg.responseMetadata}
                        onSelectSuggestion={(sug) => handleSendText(sug)}
                        onReset={handleReset}
                      />
                    </div>
                  );
                } else {
                  return (
                    <div key={index} className="chat-assistant-wrapper">
                      <ResearchMemo
                        query={currentQuery}
                        response={msg.responseMetadata}
                        onCitationClick={onCitationClick}
                      />
                    </div>
                  );
                }
              }
              // Fallback for assistant message without metadata
              return (
                <div key={index} className="chat-assistant-wrapper">
                  {msg.content}
                </div>
              );
            })}

            {/* Loading State Skeleton is appended at the bottom */}
            {loading && (
              <div className="notion-loading-card animate-fade-in" aria-live="polite">
                <Loader2 className="spinner" size={20} />
                <div className="loading-text-group">
                  <span className="loading-main">Searching Statutory & Case Precedent Corpus...</span>
                  <span className="loading-sub">
                    RRF Reciprocal Rank Fusion (BM25 + BGE Dense Embeddings) · 11 Official Gazettes
                  </span>
                </div>
              </div>
            )}
            
            {/* Turn limit warning banner if 6 turns completed */}
            {isTurnLimitReached && (
              <div className="session-limit-callout animate-fade-in" role="alert">
                <div className="limit-callout-header">
                  <span className="limit-callout-icon">⏱️</span>
                  <strong>Session Turn Limit Reached (6 of 6 turns)</strong>
                </div>
                <p className="limit-callout-body">
                  To prevent legal context drift and maintain high citation accuracy, each session is limited to 6 interactive turns. Please start a new research note for subsequent inquiries.
                </p>
                {onReset && (
                  <button className="limit-reset-btn" onClick={onReset} type="button">
                    Start Fresh Session
                  </button>
                )}
              </div>
            )}

            {/* Invisible div to auto-scroll to bottom */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Notion Command Prompt Bar docked at bottom */}
      <div className="prompt-bar-docked">
        <div className="prompt-meta-row">
          <span className="turn-counter-badge" title="Maximum 6 conversation turns per legal research session">
            Turn {userTurnCount} / 6
          </span>
          {isTurnLimitReached && (
            <span className="turn-limit-warning-text">
              Limit reached. Click &quot;Start Fresh Session&quot; to begin a new session.
            </span>
          )}
        </div>
        <PromptBar
          onSubmitQuery={handleSendText}
          loading={loading}
          disabled={isTurnLimitReached}
        />
      </div>
    </div>
  );
};
