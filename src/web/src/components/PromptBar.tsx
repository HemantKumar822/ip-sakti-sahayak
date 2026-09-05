import React, { useState } from 'react';
import { ArrowUp } from 'lucide-react';

interface PromptBarProps {
  onSubmitQuery: (queryText: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export const PromptBar: React.FC<PromptBarProps> = ({ onSubmitQuery, loading, disabled = false }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading || disabled) return;
    onSubmitQuery(query.trim());
    setQuery('');
  };

  return (
    <form onSubmit={handleSubmit} className="sk-inquiry-bar" aria-label="New inquiry">
      <label htmlFor="sk-inquiry-input" className="sk-visually-hidden">
        Describe your formulation or legal question
      </label>
      <input
        id="sk-inquiry-input"
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. Can a novel curcumin extraction process be patented, and what NBA approvals apply?"
        disabled={loading || disabled}
        autoComplete="off"
      />
      <button type="submit" className="sk-btn sk-btn-primary sk-btn-sm" disabled={!query.trim() || loading || disabled} aria-label="Submit inquiry">
        <ArrowUp size={15} aria-hidden="true" />
      </button>
    </form>
  );
};
