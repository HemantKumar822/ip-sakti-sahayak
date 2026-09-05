import type { ReactNode } from 'react';
import { AlertTriangle, Info, XCircle } from 'lucide-react';

interface CalloutProps {
  type: 'abs' | 'tkdl' | 'abstain' | 'error';
  title: string;
  children: ReactNode;
}

const META = {
  abs: { icon: <AlertTriangle size={16} aria-hidden="true" />, cls: 'sk-alert-warn' },
  tkdl: { icon: <Info size={16} aria-hidden="true" />, cls: 'sk-alert-info' },
  abstain: { icon: <XCircle size={16} aria-hidden="true" />, cls: 'sk-alert-bad' },
  error: { icon: <XCircle size={16} aria-hidden="true" />, cls: 'sk-alert-bad' },
} as const;

export const Callout = ({ type, title, children }: CalloutProps) => {
  const m = META[type];
  return (
    <div className={`sk-alert ${m.cls} animate-fade-in`} role="note">
      <p className="sk-alert-title">
        {m.icon}
        <span>{title}</span>
      </p>
      <div className="sk-alert-body">{children}</div>
    </div>
  );
};
