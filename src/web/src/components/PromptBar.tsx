import React, { useState } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';
import './PromptBar.css';

interface PromptBarProps {
  onSubmitQuery: (queryText: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export const PromptBar: React.FC<PromptBarProps> = ({
  onSubmitQuery,
  loading,
  disabled = false
}) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading || disabled) return;
    onSubmitQuery(query.trim());
    setQuery('');
  };

  return (
    <div className="notion-prompt-bar-wrapper">
      {/* Notion-Style Command Input Bar */}
      <form onSubmit={handleSubmit} className="notion-input-box glass">
        <span className="input-prompt-symbol">/</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask your Ayurveda IP question (e.g. patentability under Section 3(p), NBA ABS approval)..."
          disabled={loading || disabled}
          className="notion-text-input"
          aria-label="Ask an IP or regulatory question"
        />
        <div className="input-actions-group">
          <span className="input-key-hint" title="Press Enter to Submit">
            <CornerDownLeft size={11} />
          </span>
          <button
            type="submit"
            disabled={!query.trim() || loading || disabled}
            className="notion-submit-btn"
            title="Submit Legal Inquiry"
            aria-label="Submit"
          >
            <Send size={15} />
          </button>
        </div>
      </form>
    </div>
  );
};
