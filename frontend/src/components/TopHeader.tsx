"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function TopHeader() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState<{name: string, tier: string} | null>(null);
  const router = useRouter();

  const fetchUser = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setIsLoggedIn(false);
      setUserData(null);
      return;
    }
    setIsLoggedIn(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserData({
          name: data.display_name,
          tier: data.tier
        });
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        setUserData(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchUser();
    window.addEventListener("auth-change", fetchUser);
    return () => window.removeEventListener("auth-change", fetchUser);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.dispatchEvent(new Event('auth-change'));
    router.push("/login");
  };

  const getTierDisplay = (tier: string) => {
    if (tier === "standard") return "Standard Tier";
    if (tier === "pro") return "Pro Tier";
    if (tier === "elite") return "Elite Tier";
    return tier.toUpperCase() + " Tier";
  };

  return (
    <header className="h-20 glass sticky top-0 z-40 px-8 flex items-center justify-between border-b border-white/5">
      {/* BREADCRUMBS & TITLE */}
      <div>
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">
          <span>Spor</span>
          <span className="opacity-30">/</span>
          <span className="text-primary/80">Dashboard</span>
        </div>
        <h1 className="text-xl font-bold text-white tracking-tight">Ana Dashboard</h1>
      </div>

      {/* SEARCH & ACTIONS */}
      <div className="flex items-center gap-6">
        {/* SEARCH */}
        <div className="relative group hidden md:block">
           <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
           <input 
            type="text" 
            placeholder="Maç veya lig ara..."
            className="bg-white/5 border border-white/5 rounded-full py-2 pl-10 pr-4 text-xs text-white placeholder:text-slate-600 outline-none focus:border-primary/30 focus:bg-white/[0.07] transition-all w-64"
           />
        </div>

        {/* NOTIFICATIONS */}
        <button className="relative p-2 rounded-full hover:bg-white/5 transition-colors group">
            <svg className="text-slate-400 group-hover:text-white transition-colors" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
            <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-[#050505]"></span>
        </button>

        {/* AUTH BUTTONS */}
        <div className="flex items-center gap-3 border-l border-white/10 pl-6 ml-2">
          {isLoggedIn ? (
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                <span className="text-xs font-bold text-white">{userData?.name || "Kullanıcı"}</span>
                <span className="text-[10px] text-primary font-black uppercase tracking-tighter">
                  {getTierDisplay(userData?.tier || "standard")}
                </span>
              </div>
              <button 
                onClick={handleLogout}
                className="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center hover:bg-red-500/10 hover:border-red-500/20 transition-all group"
              >
                <svg className="text-slate-400 group-hover:text-red-400 transition-colors" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
              </button>
            </div>
          ) : (
            <>
              <Link 
                href="/login" 
                className="text-xs font-bold text-slate-400 hover:text-white transition-colors"
              >
                Giriş Yap
              </Link>
              <Link 
                href="/register" 
                className="px-5 py-2.5 rounded-full bg-primary text-black text-xs font-black hover:scale-105 transition-transform emerald-glow"
              >
                Kayıt Ol
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
