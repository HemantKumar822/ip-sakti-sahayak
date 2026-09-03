import { RefreshCw } from 'lucide-react';
import './Topbar.css';

interface TopbarProps {
  onReset: () => void;
  hasMessages: boolean;
}

export const Topbar = ({ onReset, hasMessages }: TopbarProps) => {
  return (
    <header className="topbar">
      <div className="brand" onClick={onReset} style={{ cursor: 'pointer' }}>
        <div className="brand-logo">
          <span>🏛️</span>
        </div>
        <div className="brand-info">
          <div className="brand-title">IP-SAKTI Sahayak</div>
          <div className="brand-subtitle">Ayurveda & Bio-Resource IP Workbench</div>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="system-status-indicator">
          <span className="pulse-dot"></span>
          <span className="status-text">Legal Core Online · RRF Hybrid Search</span>
        </div>

        {hasMessages && (
          <button 
            className="new-chat-btn" 
            onClick={onReset}
            title="Start new verification inquiry"
          >
            <RefreshCw size={14} />
            <span>New Inquiry</span>
          </button>
        )}

        <div className="jurisdiction-pill">
          <span className="jurisdiction-flag">🇮🇳</span>
          <span>India Law · Act 1970 & 2002</span>
        </div>
      </div>
    </header>
  );
};
