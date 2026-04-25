import "./globals.css";

export const metadata = {
  title: "Football SaaS — Canlı Oran Analiz Sistemi",
  description: "Geçmiş maç verilerine dayalı Öklid benzerlik analizi ile bahis oranlarını karşılaştırın.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
