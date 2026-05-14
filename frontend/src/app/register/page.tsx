"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { API_URL } from "@/config/constants";

// ── Kullanıcı Sözleşmesi Modal ──────────────────────────────────────────────
function TermsModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl max-h-[80vh] glass rounded-3xl border border-white/10 card-shadow overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-xl font-black text-primary uppercase tracking-tighter">Kullanıcı Sözleşmesi ve Yasal Uyarı</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="overflow-y-auto p-6 space-y-6 text-slate-300 text-sm leading-relaxed">
          <section>
            <h3 className="text-lg font-bold mb-2 text-white">1. Taraflar ve Konu</h3>
            <p>
              Bu sözleşme, Sports-Analyzer platformuna (bundan sonra &quot;Platform&quot; veya &quot;Sistem&quot; olarak anılacaktır) üye olan kullanıcılar (bundan sonra &quot;Kullanıcı&quot; olarak anılacaktır) arasında akdedilmiştir. Konusu, Platformun sunduğu istatistiksel veri analiz hizmetlerinin kullanım şartlarının belirlenmesidir.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold mb-2 text-white">2. Hizmetin Niteliği ve Sorumluluk Reddi (ÖNEMLİ)</h3>
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-3">
              <p className="text-red-400 font-bold mb-1">Sports-Analyzer kesinlikle bir bahis sitesi değildir ve bahis oynamaya teşvik etmez.</p>
              <p className="text-xs text-red-400/80">Platformumuz, yalnızca geçmiş maç verileri, takım istatistikleri ve matematiksel mesafe hesaplamalarına dayanan sonuçlar sunan bir veri aracıdır.</p>
            </div>
            <ul className="list-disc pl-5 mt-2 space-y-2">
              <li>Sistemde yer alan hiçbir oran, tahmin, analiz veya veri <strong>bahis tavsiyesi veya finansal danışmanlık niteliği taşımaz.</strong></li>
              <li>Platformumuz üzerinden bahis oynanması mümkün değildir ve hiçbir yasadışı bahis faaliyetine aracılık edilmez.</li>
              <li>Sistemdeki verilere dayanılarak alınan her türlü karar ve doğabilecek maddi veya manevi zararlar tamamen <strong>Kullanıcının kendi sorumluluğundadır.</strong> Sistemimiz doğabilecek hiçbir mali kayıptan sorumlu tutulamaz.</li>
              <li>Sports-Analyzer, sunulan verilerin doğruluğunu, güncelliğini veya başarılı sonuç vereceğini garanti etmez ve hiçbir sorumluluk kabul etmez.</li>
            </ul>
          </section>

          <section>
            <h3 className="text-lg font-bold mb-2 text-white">3. Yasal Uyumluluk</h3>
            <p>
              Kullanıcılar, Platformu kullanırken bulundukları ülkenin yasalarına tam ve eksiksiz olarak uymakla yükümlüdür. Yasadışı bahis ve kumar oynamak Türkiye Cumhuriyeti kanunlarına göre suçtur. Sports-Analyzer, yasadışı faaliyetlerde bulunan kullanıcıların hesaplarını bildirim yapmaksızın kapatma hakkını saklı tutar ve yetkili mercilerle bilgi paylaşımında bulunabilir.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold mb-2 text-white">4. Hizmet Bedeli ve İptal Şartları</h3>
            <p>
              Kullanıcılar, seçtikleri abonelik planına göre belirlenen ücreti ödemekle yükümlüdür. Sunulan hizmet tamamen dijital veri analizine dayandığından ve anında ifa edildiğinden, iade ve iptal koşulları Mesafeli Sözleşmeler Yönetmeliği&apos;ne (Cayma Hakkı İstisnaları) tabidir.
            </p>
          </section>

          <section>
            <h3 className="text-lg font-bold mb-2 text-white">5. Veri ve Fikri Mülkiyet</h3>
            <p>
              Sistemdeki analiz metodolojisi, kodlar ve görsel tasarımlar Sports-Analyzer&apos;a aittir. Kullanıcılar, verileri yalnızca bireysel kullanım amacıyla inceleyebilir; bunları satamaz, kopyalayamaz, bot/script ile çekemez veya ticari amaçla dağıtamaz.
            </p>
          </section>
        </div>

        <div className="p-6 border-t border-white/10">
          <button onClick={onClose} className="w-full bg-primary text-black font-black py-3 rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all uppercase text-xs tracking-widest">
            Anladım, Kapat
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Kayıt Formu ─────────────────────────────────────────────────────────────
function RegisterContent() {
  const [formData, setFormData] = useState({ display_name: "", email: "", password: "" });
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan");

  useEffect(() => {
    if (!planId) {
      router.replace("/pricing");
    }
  }, [planId, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/guest-checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          plan_id: planId
        }),
      });

      const data = await response.json();
      if (response.ok && data.checkout_url) {
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

          {/* Kullanıcı Sözleşmesi Onayı */}
          <div className="flex items-start gap-3 mt-4">
            <input
              type="checkbox"
              id="terms"
              checked={acceptedTerms}
              onChange={(e) => setAcceptedTerms(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary focus:ring-offset-0 transition-colors cursor-pointer"
            />
            <label htmlFor="terms" className="text-[10px] text-slate-400 leading-relaxed cursor-pointer">
              <button type="button" onClick={() => setShowTermsModal(true)} className="text-primary hover:underline font-bold">Kullanıcı Sözleşmesi</button> ve Aydınlatma Metni&apos;ni okudum, anladım ve kabul ediyorum. Platformun kesinlikle bahis tavsiyesi vermediğini, yalnızca istatistiksel veri sunduğunu onaylıyorum.
            </label>
          </div>

          <button type="submit" disabled={loading || !acceptedTerms} className="w-full bg-primary text-black font-black py-4 rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all mt-4 emerald-glow uppercase text-xs tracking-widest disabled:opacity-50">
            {loading ? "İşleniyor..." : "Ödemeye Geç"}
          </button>
        </form>

        <div className="mt-10 text-center space-y-4">
          <p className="text-slate-500 text-[10px] font-black uppercase tracking-widest">
            Zaten hesabın var mı?{" "}
            <Link href="/login" className="text-primary hover:underline underline-offset-4 decoration-2">Giriş Yap</Link>
          </p>
          <div className="pt-4">
            <Link href="/pricing" className="text-slate-600 hover:text-slate-400 text-[10px] font-black uppercase tracking-widest transition-colors flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              Planlara Geri Dön
            </Link>
          </div>
        </div>
      </div>

      <TermsModal isOpen={showTermsModal} onClose={() => setShowTermsModal(false)} />
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
