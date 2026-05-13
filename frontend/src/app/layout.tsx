import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sports Analyzer | Oran Analizi ve Tahmin Platformu",
  description:
    "Geçmiş maç verilerini yapay zeka ile analiz ederek yaklaşan maçlar için benzerlik tabanlı tahminler sunan profesyonel futbol analiz platformu.",
  keywords: ["futbol analizi", "oran analizi", "maç tahmini", "bahis analizi", "istatistik"],
  authors: [{ name: "Sports Analyzer" }],
  openGraph: {
    title: "Sports Analyzer | Oran Analizi ve Tahmin Platformu",
    description:
      "Geçmiş maç verilerini analiz ederek yaklaşan maçlar için benzerlik tabanlı tahminler sunan profesyonel platform.",
    type: "website",
    locale: "tr_TR",
    siteName: "Sports Analyzer",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sports Analyzer | Oran Analizi ve Tahmin Platformu",
    description:
      "Geçmiş maç verilerini analiz ederek yaklaşan maçlar için benzerlik tabanlı tahminler sunan profesyonel platform.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

import ClientLayout from "@/components/ClientLayout";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <meta name="theme-color" content="#050505" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="min-h-full bg-[#050505] text-slate-100 flex">
        <ClientLayout>
          {children}
        </ClientLayout>
      </body>
    </html>
  );
}
