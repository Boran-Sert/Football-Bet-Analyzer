"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password: password }),
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        window.dispatchEvent(new Event('auth-change'));
        router.push("/");
      } else {
        setError(data.detail || "Giriş yapılamadı. Bilgilerinizi kontrol edin.");
      }
    } catch (err) {
      setError("Sunucuya bağlanılamadı.");
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl w-full max-w-md shadow-xl">
        <h1 className="text-2xl font-black text-white mb-6 text-center">Giriş Yap</h1>
        {error && <p className="text-red-400 text-sm mb-4 text-center bg-red-900/20 p-2 rounded border border-red-900/50">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-slate-400 text-xs font-bold uppercase mb-1 block">E-posta</label>
            <input
              type="email"
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs font-bold uppercase mb-1 block">Şifre</label>
            <input
              type="password"
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white outline-none focus:border-blue-500 transition-colors"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-colors mt-2 shadow-lg shadow-blue-900/20">
            Giriş Yap
          </button>
        </form>
        <p className="text-slate-500 text-sm mt-6 text-center">
          Hesabın yok mu? <Link href="/register" className="text-blue-400 hover:underline">Kayıt Ol</Link>
        </p>
      </div>
    </div>
  );
}
