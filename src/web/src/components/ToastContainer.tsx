// src/components/ToastContainer.tsx
import { useState, useEffect, useCallback } from 'react';
import type { FC } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle2, X } from 'lucide-react';
import { subscribeToasts, toast } from '../utils/toast';
import type { ToastItem } from '../utils/toast';
import './Toast.css';

export const ToastContainer: FC = () => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((incoming: ToastItem) => {
    setToasts((prev) => {
      // Prevent rapid duplicate spamming (same message within 1.5 seconds)
      const existing = prev.find(
        (t) => t.message === incoming.message && Math.abs(t.timestamp - incoming.timestamp) < 1500
      );
      if (existing) {
        return prev;
      }
      return [...prev, incoming];
    });
  }, []);

  // Listen to pubsub notifications and window offline/online events
  useEffect(() => {
    const unsubscribe = subscribeToasts((item) => {
      addToast(item);
    });

    const handleCustomToast = (event: Event) => {
      const customEvent = event as CustomEvent<ToastItem>;
      if (customEvent.detail) {
        addToast(customEvent.detail);
      }
    };

    const handleOffline = () => {
      toast.error(
        'Network Disconnected',
        'Your internet connection was lost. API queries and session synchronization will fail until reconnected.'
      );
    };

    const handleOnline = () => {
      toast.info(
        'Connection Restored',
        'Internet connection is active. You can resume statutory analysis.'
      );
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('ip-sakti-toast', handleCustomToast);
      window.addEventListener('offline', handleOffline);
      window.addEventListener('online', handleOnline);
    }

    return () => {
      unsubscribe();
      if (typeof window !== 'undefined') {
        window.removeEventListener('ip-sakti-toast', handleCustomToast);
        window.removeEventListener('offline', handleOffline);
        window.removeEventListener('online', handleOnline);
      }
    };
  }, [addToast]);

  // Set individual auto-dismiss timers
  useEffect(() => {
    if (toasts.length === 0) return;

    const latest = toasts[toasts.length - 1];
    const duration = latest.duration ?? 5000;
    const timer = setTimeout(() => {
      removeToast(latest.id);
    }, duration);

    return () => clearTimeout(timer);
  }, [toasts, removeToast]);

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      className="toast-container"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {toasts.map((item) => {
        let IconComponent = Info;
        if (item.type === 'warning') IconComponent = AlertTriangle;
        else if (item.type === 'error') IconComponent = AlertCircle;
        else if (item.type === 'success') IconComponent = CheckCircle2;

        return (
          <div
            key={item.id}
            className={`toast-item toast-${item.type}`}
            role="status"
          >
            <div className="toast-icon">
              <IconComponent size={18} />
            </div>
            <div className="toast-content">
              <span className="toast-title">{item.title}</span>
              <span className="toast-message">{item.message}</span>
            </div>
            <button
              className="toast-close-btn"
              onClick={() => removeToast(item.id)}
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
