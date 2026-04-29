"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkToken = () => {
      const token = localStorage.getItem("token");
      setIsLoggedIn(!!token);
    };

    // Initial check
    checkToken();

    // Listen for custom auth-change event
    window.addEventListener("auth-change", checkToken);
    
    // Cleanup
    return () => window.removeEventListener("auth-change", checkToken);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.dispatchEvent(new Event('auth-change'));
    router.push("/login");
  };

  return (
    <nav className="bg-slate-900 border-b border-slate-800 text-slate-100 py-4 px-6 shadow-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center font-bold text-slate-950">
            SA
          </div>
          <span className="text-xl font-bold tracking-tight text-white group-hover:text-cyan-400 transition-colors">
            Sports-Analyzer
          </span>
        </Link>
        
        <div className="flex items-center gap-4">
          {isLoggedIn ? (
            <>
              <div className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold tracking-wider text-slate-300">
                PRO TIER
              </div>
              <button 
                onClick={handleLogout}
                className="px-4 py-2 rounded-md border border-red-900/50 text-red-400 hover:bg-red-900/20 font-medium transition-all text-sm"
              >
                Çıkış Yap
              </button>
            </>
          ) : (
            <>
              <Link 
                href="/login" 
                className="text-slate-300 hover:text-white text-sm font-medium transition-colors"
              >
                Giriş Yap
              </Link>
              <Link 
                href="/register" 
                className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors text-sm"
              >
                Kayıt Ol
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
