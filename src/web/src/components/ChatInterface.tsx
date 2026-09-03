import { useState, useMemo } from 'react';
import type { FormEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { submitQuery } from '../api/client';
import type { Message, QueryResponse } from '../api/client';
import { Callout } from './Callout';
import { StatutoryBadge } from './StatutoryBadge';
import { PipelineStepper } from './PipelineStepper';
import './ChatInterface.css';

export const ChatInterface = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<QueryResponse | null>(null);

  const sessionId = useMemo(() => crypto.randomUUID(), []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: query };
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
      setMessages(prev => [...prev, { role: 'assistant', content: error.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`message-wrapper ${msg.role} animate-fade-in`}>
            <div className={`message-bubble ${msg.role}`}>
              {msg.role === 'assistant' && lastResponse && i === messages.length - 1 ? (
                <>
                  <PipelineStepper category={lastResponse.category} jurisdiction={lastResponse.jurisdiction} />
                  
                  {lastResponse.abs_flag && (
                    <Callout type="abs" title="ABS Compliance Note">
                      {lastResponse.abs_detail}
                    </Callout>
                  )}
                  
                  {lastResponse.tkdl_flag && (
                    <Callout type="tkdl" title="Traditional Knowledge & TKDL Prior Art Notice">
                      {lastResponse.tkdl_detail}
                    </Callout>
                  )}

                  <div className="message-content" dangerouslySetInnerHTML={{ __html: msg.content }} />

                  {lastResponse.citations && lastResponse.citations.length > 0 && (
                    <div className="citations-container">
                      <div className="citations-title">Sources & Citations:</div>
                      {lastResponse.citations.map((cit, idx) => (
                        <StatutoryBadge key={idx} citation={cit} />
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="message-content">{msg.content}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message-wrapper assistant animate-fade-in">
            <div className="message-bubble assistant loading">
              <Loader2 className="spinner" size={20} />
              <span>Analyzing legal corpus...</span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-container glass">
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask your Ayurveda IP question..."
            disabled={loading}
            className="chat-input"
          />
          <button type="submit" disabled={!query.trim() || loading} className="chat-submit">
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};
