"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

function RegisterContent() {
  const [formData, setFormData] = useState({ display_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan");

  useEffect(() => {
    if (!planId) {
      router.push("/pricing");
    }
  }, [planId, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // Guest Checkout: Kayıt ve Ödeme birlikte
      const response = await fetch("http://127.0.0.1:8000/api/v1/billing/guest-checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          plan_id: planId
        }),
      });

      const data = await response.json();
      if (response.ok && data.checkout_url) {
        // Iyzico ödeme sayfasına yönlendir
        window.location.href = data.checkout_url;
      } else {
        const errMsg = Array.isArray(data.detail) ? data.detail.map((e: any) => e.msg).join(", ") : data.detail;
        setError(typeof errMsg === "string" ? errMsg : "İşlem sırasında bir hata oluştu.");
      }
    } catch (err) {
      setError("Sunucuya bağlanılamadı.");
    } finally {
      setLoading(false);
    }
  };

  if (!planId) return null;

  return (
    <div className="min-h-[90vh] flex items-center justify-center relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full pointer-events-none"></div>
      
      <div className="glass rounded-[2.5rem] p-12 w-full max-w-md card-shadow relative z-10 border border-white/5">
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 emerald-glow border border-primary/20">
             <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
          </div>
          <h1 className="text-3xl font-black text-white text-center uppercase tracking-tighter">Hesap Oluştur</h1>
          <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-2">Seçilen Plan: <span className="text-primary">{planId.toUpperCase()}</span></p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl animate-in fade-in zoom-in duration-300">
            <p className="text-red-400 text-xs font-bold text-center uppercase tracking-wider">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Ad Soyad</label>
            <input
              type="text"
              required
              placeholder="Adınız Soyadınız"
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all placeholder:text-slate-700 font-medium"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">E-posta Adresi</label>
            <input
              type="email"
              required
              placeholder="email@adresiniz.com"
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all placeholder:text-slate-700 font-medium"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Şifre</label>
            <input
              type="password"
              required
              minLength={8}
              placeholder="••••••••"
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all placeholder:text-slate-700 font-medium"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>
          <button type="submit" disabled={loading} className="w-full bg-primary text-black font-black py-4 rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all mt-4 emerald-glow uppercase text-xs tracking-widest disabled:opacity-50">
            {loading ? "İşleniyor..." : "Ödemeye Geç"}
          </button>
        </form>

        <div className="mt-10 text-center">
          <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest">
            Zaten hesabın var mı?{" "}
            <Link href="/login" className="text-primary hover:underline underline-offset-4 decoration-2">Giriş Yap</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function Register() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary"></div></div>}>
      <RegisterContent />
    </Suspense>
  );
}
