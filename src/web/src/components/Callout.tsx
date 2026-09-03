import type { ReactNode } from 'react';
import { AlertTriangle, Info, XCircle } from 'lucide-react';
import './Callout.css';

interface CalloutProps {
  type: 'abs' | 'tkdl' | 'abstain' | 'error';
  title: string;
  children: ReactNode;
}

export const Callout = ({ type, title, children }: CalloutProps) => {
  const icons = {
    abs: <AlertTriangle size={20} color="var(--color-warning)" />,
    tkdl: <Info size={20} color="var(--color-info)" />,
    abstain: <XCircle size={20} color="var(--color-error)" />,
    error: <XCircle size={20} color="var(--color-error)" />
  };

  return (
    <div className={`callout callout-${type} animate-fade-in`}>
      <div className="callout-header">
        <span className="callout-icon">{icons[type]}</span>
        <span className="callout-title">{title}</span>
      </div>
      <div className="callout-body">
        {children}
      </div>
    </div>
  );
};
