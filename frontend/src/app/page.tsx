"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowRightIcon, ChartBarIcon, ServerStackIcon, TrophyIcon, BoltIcon } from "@heroicons/react/24/outline";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white flex flex-col relative overflow-hidden font-sans">

      {/* BACKGROUND EFFECTS */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-primary/10 blur-[150px] rounded-full pointer-events-none" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 pointer-events-none" />

      {/* HEADER */}
      <header className="relative z-10 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <div className="w-18 h-18 relative">
            <Image src="/icon.png" alt="Sports-Analyzer Logo" fill className="object-contain" />
          </div>
          <span className="text-2xl font-black tracking-tighter text-white uppercase italic">Sports-Analyzer</span>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/login" className="text-sm font-semibold text-slate-300 hover:text-white transition-colors">
            Giriş Yap
          </Link>
          <Link href="/register" className="text-sm font-bold bg-white text-black px-5 py-2.5 rounded-full hover:bg-slate-200 hover:scale-105 transition-all shadow-[0_0_15px_rgba(255,255,255,0.2)]">
            Hemen Başla
          </Link>
        </div>
      </header>



      {/* HERO SECTION */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 relative z-10 py-20 mt-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold mb-8 uppercase tracking-widest animate-pulse">
          <BoltIcon className="w-4 h-4" />
          Profesyonel Bahis Analizi Artık Seninle
        </div>

        <h1 className="text-5xl md:text-7xl font-black tracking-tighter mb-8 leading-tight max-w-4xl">
          SEZGİLERİNİ BIRAK, <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-emerald-400">MATEMATİĞE GÜVEN.</span>
        </h1>

        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 font-medium">
          Duygusal bahisleri kenara bırakın. Gelişmiş veri algoritmalarımız geçmiş maçların dinamiklerini hesaplayarak sıradan bahisçilerin göremediği fırsatları ortaya çıkarır.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Link href="/register" className="flex items-center gap-2 bg-primary text-black px-8 py-4 rounded-full font-black text-lg hover:scale-105 transition-all shadow-[0_0_30px_rgba(16,185,129,0.4)]">
            Sisteme Katıl <ArrowRightIcon className="w-5 h-5 stroke-[3]" />
          </Link>
          <Link href="/pricing" className="px-8 py-4 rounded-full font-bold text-white bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
            Planları İncele
          </Link>
        </div>
      </main>

      {/* HOW IT WORKS SECTION */}
      <section className="relative z-10 max-w-7xl mx-auto w-full px-8 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-4">SİSTEM NASIL ÇALIŞIR?</h2>
          <p className="text-slate-400">İleri düzey veri işleme altyapısıyla hata payını en aza indirin.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 backdrop-blur-md hover:bg-white/[0.05] hover:-translate-y-2 transition-all duration-300">
            <div className="w-14 h-14 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mb-6">
              <ServerStackIcon className="w-7 h-7 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold mb-3">Derin Veri Toplama</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Dünya genelindeki tüm liglerden anlık oran verileri, takım form durumları ve tarihsel eşleşmeler milisaniyeler içinde toplanır.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 backdrop-blur-md hover:bg-white/[0.05] hover:-translate-y-2 transition-all duration-300">
            <div className="w-14 h-14 bg-primary/10 border border-primary/20 rounded-2xl flex items-center justify-center mb-6">
              <ChartBarIcon className="w-7 h-7 text-primary" />
            </div>
            <h3 className="text-xl font-bold mb-3">Matematiksel Filtreleme</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Geliştirdiğimiz özel algoritmalar, binlerce geçmiş maçı matematiksel mesafe formülleriyle analiz ederek en yüksek benzerlikteki şablonları bulur.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 backdrop-blur-md hover:bg-white/[0.05] hover:-translate-y-2 transition-all duration-300">
            <div className="w-14 h-14 bg-yellow-500/10 border border-yellow-500/20 rounded-2xl flex items-center justify-center mb-6">
              <TrophyIcon className="w-7 h-7 text-yellow-400" />
            </div>
            <h3 className="text-xl font-bold mb-3">Kazandıran Strateji</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Duygusal yanılmalardan arınmış, tamamen geçmiş verilere ve istatistiksel trendlere dayanan net analizlerle daima bir adım önde olun.
            </p>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="relative z-10 py-24 px-8 mt-12 bg-gradient-to-b from-transparent to-primary/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-6xl font-black tracking-tight mb-8">
            KAZANANLAR KULÜBÜNE <br /> ADIM ATIN.
          </h2>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Sıradan oyuncular tahminde bulunur. Profesyoneller analiz eder. Analiz altyapımızın gücünü arkanıza alarak fark yaratın.
          </p>
          <Link href="/register" className="inline-flex items-center justify-center w-full sm:w-auto bg-white text-black px-12 py-5 rounded-full font-black text-xl hover:bg-slate-200 hover:scale-105 transition-all shadow-[0_0_40px_rgba(255,255,255,0.3)]">
            HEMEN HESAP OLUŞTUR
          </Link>
        </div>
      </section>

      {/* LEGAL & INFO SECTION */}
      <section className="relative z-10 py-16 px-8 bg-gradient-to-b from-primary/10 to-transparent">
        <div className="max-w-7xl mx-auto flex flex-col gap-12">

          {/* WARNING */}
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-[10px] font-black uppercase tracking-widest mb-4">
              Önemli Bilgilendirme
            </div>
            <p className="text-xs text-slate-500 max-w-4xl mx-auto leading-relaxed">
              Platformumuzdaki oranlar uluslararası Bet365 altyapısından sağlanmaktadır ve yerel (Türkiye) oranlarına kıyasla daha yüksek değerler gösterebilir.
            </p>
          </div>

          {/* DISCLAIMER */}
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-widest mb-4">
              Yasal Uyarı
            </div>
            <p className="text-xs text-slate-500 max-w-4xl mx-auto leading-relaxed">
              Sports-Analyzer platformu, yalnızca geçmiş maç verileri ve matematiksel hesaplamalara dayalı istatistiksel sonuçlar sunar. <strong>Sistemimizde yer alan hiçbir veri, analiz veya tahmin kesinlikle bahis tavsiyesi, yönlendirme veya teşvik niteliği taşımaz.</strong> Platformumuz hiçbir şekilde bahis oynatmaz, yasadışı bahis faaliyetlerini desteklemez ve teşvik etmez. Sunulan verilerin kullanımından doğabilecek her türlü maddi/manevi zarar ve yasal sorumluluk tamamen kullanıcının kendisine aittir. Kullanıcılar bulundukları ülkenin yasalarına uymakla yükümlüdür.
            </p>
          </div>

        </div>
      </section>

      {/* FOOTER */}
      <footer className="relative z-10 border-t border-white/10 py-8 px-8 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 relative">
              <Image src="/icon.png" alt="Sports-Analyzer Logo" fill className="object-contain" />
            </div>
            <span className="text-sm font-bold text-white uppercase italic">Sports-Analyzer</span>
          </div>
          <p className="text-xs text-slate-500 font-medium">
            © {new Date().getFullYear()} Sports Analyzer. Tüm hakları saklıdır.
          </p>
        </div>
      </footer>
    </div>
  );
}
