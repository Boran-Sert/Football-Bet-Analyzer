"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function ConfirmEmailChangePage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState("Email adresiniz doğrulanıyor...");
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage("Geçersiz veya eksik doğrulama linki.");
      return;
    }

    const confirmChange = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/auth/confirm-email-change?token=${token}`);
        const data = await res.json();
        
        if (res.ok) {
          setStatus('success');
          setMessage("Email adresiniz başarıyla güncellendi. Lütfen yeni e-posta adresinizle giriş yapın.");
          // Clear old token since email changed
          localStorage.removeItem("token");
          window.dispatchEvent(new Event('auth-change'));
        } else {
          setStatus('error');
          setMessage(data.detail || "Email doğrulaması başarısız oldu.");
        }
      } catch (err) {
        setStatus('error');
        setMessage("Bir ağ hatası oluştu.");
      }
    };

    confirmChange();
  }, [token]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="glass max-w-md w-full p-10 rounded-[2.5rem] card-shadow border border-white/5 text-center">
        {status === 'loading' && (
          <div className="flex flex-col items-center gap-6">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary"></div>
            <p className="text-slate-400 font-bold text-xs uppercase tracking-widest">{message}</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center gap-6 animate-in fade-in zoom-in duration-500">
            <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center text-primary emerald-glow">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
            </div>
            <h1 className="text-2xl font-black text-white uppercase tracking-tight">Harika!</h1>
            <p className="text-slate-400 text-sm font-medium leading-relaxed">{message}</p>
            <Link 
              href="/login"
              className="mt-4 w-full py-4 bg-primary text-black font-black rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all emerald-glow uppercase text-xs tracking-widest"
            >
              Giriş Yap
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center gap-6 animate-in fade-in zoom-in duration-500">
            <div className="w-16 h-16 rounded-2xl bg-red-500/20 flex items-center justify-center text-red-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </div>
            <h1 className="text-2xl font-black text-white uppercase tracking-tight">Hata Oluştu</h1>
            <p className="text-red-400/80 text-sm font-medium leading-relaxed">{message}</p>
            <Link 
              href="/"
              className="mt-4 w-full py-4 bg-white/5 text-white font-black rounded-2xl hover:bg-white/10 transition-all uppercase text-xs tracking-widest"
            >
              Ana Sayfaya Dön
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
