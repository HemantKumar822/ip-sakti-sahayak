import React, { useState } from 'react';
import { Key, RotateCw, X } from 'lucide-react';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (key: string) => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ isOpen, onClose, onSave }) => {
  const [apiKey, setApiKey] = useState('');

  if (!isOpen) return null;

  return (
    <>
      <div className="sk-drawer-backdrop" onClick={onClose} aria-hidden="true" style={{ zIndex: 900 }} />
      <div className="sk-drawer animate-fade-in" style={{ zIndex: 901, width: '400px', margin: 'auto', right: 0, left: 0, top: '20vh', bottom: 'auto', height: 'auto', padding: 'var(--space-2xl)', borderRadius: 'var(--radius-sm)' }} role="dialog" aria-modal="true" aria-labelledby="api-key-title">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-md)' }}>
          <h2 id="api-key-title" className="sk-h3" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            <Key size={18} style={{ color: 'var(--accent-sunset)' }} />
            Authorization Required
          </h2>
          <button type="button" className="sk-btn sk-btn-quiet sk-btn-sm" onClick={onClose} aria-label="Close">
            <X size={14} aria-hidden="true" />
          </button>
        </div>
        <p className="sk-small" style={{ marginBottom: 'var(--space-xl)' }}>
          The backend rejected the provided API key. Enter a valid key to continue using the workspace.
        </p>
        <form onSubmit={(e) => { e.preventDefault(); onSave(apiKey); }}>
          <div className="sk-field" style={{ marginBottom: 'var(--space-lg)' }}>
            <label className="sk-label" htmlFor="apiKeyInput">API Key</label>
            <input
              id="apiKeyInput"
              type="password"
              className="sk-input"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              autoFocus
            />
          </div>
          <button type="submit" className="sk-btn sk-btn-primary sk-btn-block" disabled={!apiKey.trim()}>
            <RotateCw size={14} aria-hidden="true" />
            <span>Save & Retry</span>
          </button>
        </form>
      </div>
    </>
  );
};
