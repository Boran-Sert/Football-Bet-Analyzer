"use client";

import { useState, useEffect, useCallback, createContext, useContext } from "react";

// ── Types ─────────────────────────────────────────

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType, duration?: number) => void;
}

// ── Context ───────────────────────────────────────

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

// ── Provider ──────────────────────────────────────

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, type: ToastType = "info", duration: number = 4000) => {
      const id = `toast_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      setToasts((prev) => [...prev, { id, message, type, duration }]);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ── Toast Item ────────────────────────────────────

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

const COLORS: Record<ToastType, string> = {
  success: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  error: "border-red-500/40 bg-red-500/10 text-red-400",
  warning: "border-amber-500/40 bg-amber-500/10 text-amber-400",
  info: "border-sky-500/40 bg-sky-500/10 text-sky-400",
};

const ICON_BG: Record<ToastType, string> = {
  success: "bg-emerald-500/20 text-emerald-400",
  error: "bg-red-500/20 text-red-400",
  warning: "bg-amber-500/20 text-amber-400",
  info: "bg-sky-500/20 text-sky-400",
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLeaving(true);
      setTimeout(() => onRemove(toast.id), 300);
    }, toast.duration);

    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  return (
    <div
      className={`
        pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-2xl border backdrop-blur-xl
        shadow-[0_8px_32px_rgba(0,0,0,0.5)] min-w-[320px] max-w-[440px]
        transition-all duration-300 ease-out
        ${COLORS[toast.type]}
        ${isLeaving ? "opacity-0 translate-x-8" : "opacity-100 translate-x-0 animate-slide-in"}
      `}
    >
      <div className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-sm font-black ${ICON_BG[toast.type]}`}>
        {ICONS[toast.type]}
      </div>
      <span className="text-xs font-bold text-white/90 flex-1">{toast.message}</span>
      <button
        onClick={() => {
          setIsLeaving(true);
          setTimeout(() => onRemove(toast.id), 300);
        }}
        className="flex-shrink-0 text-white/30 hover:text-white/60 transition-colors text-sm"
      >
        ✕
      </button>
    </div>
  );
}
