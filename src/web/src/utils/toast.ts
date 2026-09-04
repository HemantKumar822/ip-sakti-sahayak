// src/utils/toast.ts
export type ToastType = 'info' | 'warning' | 'error' | 'success';

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message: string;
  duration?: number;
  timestamp: number;
}

export type ToastListener = (toast: ToastItem) => void;

const listeners: Set<ToastListener> = new Set();

export function subscribeToasts(listener: ToastListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function emitToast(item: Omit<ToastItem, 'id' | 'timestamp'> & { id?: string; duration?: number }): string {
  const id = item.id || `toast-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  const toastItem: ToastItem = {
    id,
    type: item.type,
    title: item.title,
    message: item.message,
    duration: item.duration ?? 5000,
    timestamp: Date.now(),
  };

  // Notify registered callbacks
  listeners.forEach((listener) => {
    try {
      listener(toastItem);
    } catch {
      // Ignore listener errors
    }
  });

  // Also dispatch window custom event for broad DOM interop
  if (typeof window !== 'undefined') {
    try {
      window.dispatchEvent(new CustomEvent('ip-sakti-toast', { detail: toastItem }));
    } catch {
      // Ignore event dispatch failure in non-browser environments
    }
  }

  return id;
}

export const toast = {
  show: (item: Omit<ToastItem, 'id' | 'timestamp'>) => emitToast(item),
  warning: (title: string, message: string, duration?: number) =>
    emitToast({ type: 'warning', title, message, duration }),
  error: (title: string, message: string, duration?: number) =>
    emitToast({ type: 'error', title, message, duration }),
  info: (title: string, message: string, duration?: number) =>
    emitToast({ type: 'info', title, message, duration }),
  success: (title: string, message: string, duration?: number) =>
    emitToast({ type: 'success', title, message, duration }),
};
