"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/config/constants";

export default function ProfilePage() {
  const [userData, setUserData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [passwordData, setPasswordData] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [submittingEmail, setSubmittingEmail] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/me`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setUserData(data);
        } else {
          router.push("/login");
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [router]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError("Yeni şifreler eşleşmiyor.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          current_password: passwordData.current_password,
          new_password: passwordData.new_password
        })
      });

      const data = await res.json();
      if (res.ok) {
        setSuccess("Şifreniz başarıyla değiştirildi.");
        setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
      } else {
        setError(data.detail || "Şifre değiştirilemedi.");
      }
    } catch (err) {
      setError("Bir hata oluştu.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEmailChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmittingEmail(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/request-email-change`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ new_email: newEmail })
      });

      const data = await res.json();
      if (res.ok) {
        setSuccess("Yeni email adresinize doğrulama linki gönderildi.");
        setNewEmail("");
      } else {
        setError(data.detail || "Email değişikliği başlatılamadı.");
      }
    } catch (err) {
      setError("Bir hata oluştu.");
    } finally {
      setSubmittingEmail(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary"></div>
        <span className="text-slate-500 font-bold text-xs uppercase tracking-widest">Profil Yükleniyor...</span>
      </div>
    );
  }

  const getTierDisplay = (tier: string) => {
    if (tier === "standard") return "Standard Tier";
    if (tier === "pro") return "Pro Tier";
    if (tier === "elite") return "Elite Tier";
    return tier.toUpperCase() + " Tier";
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>

      <div className="flex flex-col gap-10 relative z-10">
        <div>
           <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-2">Profil Ayarları</h1>
           <p className="text-slate-500 text-sm font-bold uppercase tracking-widest">Hesap bilgilerinizi yönetin</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* USER INFO CARD */}
          <div className="lg:col-span-1 flex flex-col gap-6">
             <div className="glass rounded-[2rem] p-8 card-shadow border border-white/5 flex flex-col items-center text-center">
                <div className="w-24 h-24 rounded-[2rem] bg-primary/10 flex items-center justify-center mb-6 emerald-glow border border-primary/20">
                   <span className="text-4xl font-black text-primary">{userData?.display_name?.charAt(0).toUpperCase()}</span>
                </div>
                <h2 className="text-xl font-black text-white">{userData?.display_name}</h2>
                <span className="text-xs font-bold text-slate-500 mt-1">{userData?.email}</span>
                
                <div className="mt-8 pt-8 border-t border-white/5 w-full">
                   <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Üyelik Katmanı</span>
                      <span className="text-primary font-black uppercase tracking-tighter">{getTierDisplay(userData?.tier)}</span>
                   </div>
                </div>
             </div>
          </div>

          {/* CHANGE PASSWORD & EMAIL FORMS */}
          <div className="lg:col-span-2 flex flex-col gap-8">
             {/* PASSWORD FORM */}
             <div className="glass rounded-[2rem] p-10 card-shadow border border-white/5">
                <h3 className="text-lg font-black text-white uppercase tracking-tight mb-8">Şifre Değiştir</h3>
                {/* ... (existing error/success/form logic for password) ... */}
                {/* (I will re-write it correctly below) */}
                
                {error && (
                  <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl">
                    <p className="text-red-400 text-xs font-bold uppercase tracking-wider">{error}</p>
                  </div>
                )}
                {success && (
                  <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-2xl">
                    <p className="text-primary text-xs font-bold uppercase tracking-wider">{success}</p>
                  </div>
                )}

                <form onSubmit={handlePasswordChange} className="space-y-6">
                   <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Mevcut Şifre</label>
                      <input
                        type="password"
                        required
                        className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all font-medium"
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      />
                   </div>
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                         <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Yeni Şifre</label>
                         <input
                           type="password"
                           required
                           minLength={8}
                           className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all font-medium"
                           value={passwordData.new_password}
                           onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                         />
                      </div>
                      <div className="space-y-2">
                         <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Yeni Şifre (Tekrar)</label>
                         <input
                           type="password"
                           required
                           className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all font-medium"
                           value={passwordData.confirm_password}
                           onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                         />
                      </div>
                   </div>
                   <div className="pt-4">
                      <button type="submit" disabled={submitting} className="px-10 py-4 bg-primary text-black font-black rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all emerald-glow uppercase text-xs tracking-widest disabled:opacity-50">
                        {submitting ? "Güncelleniyor..." : "Şifreyi Güncelle"}
                      </button>
                   </div>
                </form>
             </div>

             {/* EMAIL FORM */}
             <div className="glass rounded-[2rem] p-10 card-shadow border border-white/5">
                <h3 className="text-lg font-black text-white uppercase tracking-tight mb-8">E-posta Adresini Değiştir</h3>
                <form onSubmit={handleEmailChange} className="space-y-6">
                   <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-4">Yeni E-posta Adresi</label>
                      <input
                        type="email"
                        required
                        className="w-full bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-white outline-none focus:border-primary/50 transition-all font-medium"
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        placeholder="örnek@mail.com"
                      />
                   </div>
                   <div className="pt-4">
                      <button type="submit" disabled={submittingEmail} className="px-10 py-4 bg-white/5 text-white font-black rounded-2xl hover:bg-white/10 transition-all uppercase text-xs tracking-widest disabled:opacity-50">
                        {submittingEmail ? "Gönderiliyor..." : "Değişiklik İsteği Gönder"}
                      </button>
                   </div>
                </form>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
