"use client";

import Link from "next/link";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white py-20 px-8">
      <div className="max-w-4xl mx-auto glass p-10 rounded-3xl border border-white/10 card-shadow">
        <h1 className="text-3xl font-black mb-8 text-primary uppercase tracking-tighter">Kullanıcı Sözleşmesi ve Yasal Uyarı</h1>
        
        <div className="space-y-6 text-slate-300 text-sm leading-relaxed">
          <section>
            <h2 className="text-xl font-bold mb-3 text-white">1. Taraflar ve Konu</h2>
            <p>
              Bu sözleşme, Sports-Analyzer platformuna (bundan sonra "Platform" veya "Sistem" olarak anılacaktır) üye olan kullanıcılar (bundan sonra "Kullanıcı" olarak anılacaktır) arasında akdedilmiştir. Konusu, Platformun sunduğu istatistiksel veri analiz hizmetlerinin kullanım şartlarının belirlenmesidir.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3 text-white">2. Hizmetin Niteliği ve Sorumluluk Reddi (ÖNEMLİ)</h2>
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-4">
              <p className="text-red-400 font-bold mb-2">Sports-Analyzer kesinlikle bir bahis sitesi değildir ve bahis oynamaya teşvik etmez.</p>
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
            <h2 className="text-xl font-bold mb-3 text-white">3. Yasal Uyumluluk</h2>
            <p>
              Kullanıcılar, Platformu kullanırken bulundukları ülkenin yasalarına tam ve eksiksiz olarak uymakla yükümlüdür. Yasadışı bahis ve kumar oynamak Türkiye Cumhuriyeti kanunlarına göre suçtur. Sports-Analyzer, yasadışı faaliyetlerde bulunan kullanıcıların hesaplarını bildirim yapmaksızın kapatma hakkını saklı tutar ve yetkili mercilerle bilgi paylaşımında bulunabilir.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3 text-white">4. Hizmet Bedeli ve İptal Şartları</h2>
            <p>
              Kullanıcılar, seçtikleri abonelik planına göre belirlenen ücreti ödemekle yükümlüdür. Sunulan hizmet tamamen dijital veri analizine dayandığından ve anında ifa edildiğinden, iade ve iptal koşulları Mesafeli Sözleşmeler Yönetmeliği'ne (Cayma Hakkı İstisnaları) tabidir.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3 text-white">5. Veri ve Fikri Mülkiyet</h2>
            <p>
              Sistemdeki analiz metodolojisi, kodlar ve görsel tasarımlar Sports-Analyzer'a aittir. Kullanıcılar, verileri yalnızca bireysel kullanım amacıyla inceleyebilir; bunları satamaz, kopyalayamaz, bot/script ile çekemez veya ticari amaçla dağıtamaz.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-6 border-t border-white/10 text-center">
          <button onClick={() => window.close()} className="inline-block px-6 py-3 bg-primary text-black font-black text-xs uppercase tracking-widest rounded-xl hover:scale-105 transition-all cursor-pointer">
            Anladım, Kapat
          </button>
        </div>
      </div>
    </div>
  );
}
