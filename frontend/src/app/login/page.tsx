"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, password: password }),
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        window.dispatchEvent(new Event('auth-change'));
        router.push("/");
      } else {
        const errMsg = Array.isArray(data.detail) ? data.detail.map((e: any) => e.msg).join(", ") : data.detail;
        setError(typeof errMsg === "string" ? errMsg : "Giriş yapılamadı. Bilgilerinizi kontrol edin.");
      }
    } catch (err) {
      setError("Sunucuya bağlanılamadı.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full pointer-events-none"></div>
      
      <div className="glass rounded-[2.5rem] p-12 w-full max-w-md card-shadow relative z-10 border border-white/5">
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-6 emerald-glow border border-primary/20">
             <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
          </div>
          <h1 className="text-3xl font-black text-white text-center uppercase tracking-tighter">Hoş Geldiniz</h1>
          <p className="text-slate-500 text-xs font-bold uppercase tracking-widest mt-2">Hesabınıza giriş yapın</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl animate-in fade-in zoom-in duration-300">
            <p className="text-red-400 text-xs font-bold text-center uppercase tracking-wider">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">E-posta Adresi</label>
            <input
              type="email"
              required
              placeholder="email@adresiniz.com"
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all placeholder:text-slate-700 font-medium"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center px-4">
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Şifre</label>
              <Link href="/forgot-password" title="Şifremi Unuttum" className="text-[10px] font-black text-primary/60 hover:text-primary uppercase tracking-widest transition-colors">Unuttun mu?</Link>
            </div>
            <input
              type="password"
              required
              placeholder="••••••••"
              className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all placeholder:text-slate-700 font-medium"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-primary text-black font-black py-4 rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all mt-4 emerald-glow uppercase text-xs tracking-widest disabled:opacity-50"
          >
            {loading ? "Giriş Yapılıyor..." : "Giriş Yap"}
          </button>
        </form>

        <div className="mt-10 text-center">
          <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest">
            Henüz hesabın yok mu?{" "}
            <Link href="/register" className="text-primary hover:underline underline-offset-4 decoration-2">Hemen Kayıt Ol</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
