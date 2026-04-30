"use client";

import { useState, useEffect } from "react";
import { MatchResponse, SimilarMatchResult } from "@/types";
import Filters from "@/components/Filters";
import UpcomingMatchesTable from "@/components/UpcomingMatchesTable";
import HistoricalAnalysis from "@/components/HistoricalAnalysis";
import SimilarMatchesTable from "@/components/SimilarMatchesTable";
import SummaryStats from "@/components/SummaryStats";

export default function Home() {
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeague, setSelectedLeague] = useState("");
  
  const [selectedMatch, setSelectedMatch] = useState<MatchResponse | null>(null);
  
  const [limit, setLimit] = useState(10);
  const [similarMatches, setSimilarMatches] = useState<SimilarMatchResult[]>([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [userTier, setUserTier] = useState<string>("pro"); // Defaulting to pro for slider access

  // Fetch upcoming matches
  useEffect(() => {
    const fetchMatches = async () => {
      setLoading(true);
      setSelectedMatch(null);
      setSimilarMatches([]);
      try {
        const url = selectedLeague
          ? `http://127.0.0.1:8000/api/v1/football/matches/?league=${selectedLeague}`
          : `http://127.0.0.1:8000/api/v1/football/matches/`;

        const response = await fetch(url);
        if (!response.ok) throw new Error("Backend unreachable");

        const json = await response.json();

        if (json && Array.isArray(json.data)) {
          setMatches(json.data);
        } else if (Array.isArray(json)) {
          setMatches(json);
        } else {
          setMatches([]);
        }
      } catch (error) {
        console.error("Fetch error:", error);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [selectedLeague]);

  // Fetch User Tier
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;
        const res = await fetch("http://127.0.0.1:8000/api/v1/auth/me", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUserTier(data.tier);
          if (data.tier === "elite") setLimit(20);
          if (data.tier === "free") setLimit(3);
        }
      } catch (err) {
        console.error("User fetch error:", err);
      }
    };
    fetchUser();
  }, []);

  const handleSelectMatch = (match: MatchResponse) => {
    // If selecting the same match, toggle it off
    if (selectedMatch?.external_id === match.external_id) {
      setSelectedMatch(null);
      setSimilarMatches([]);
    } else {
      setSelectedMatch(match);
      setSimilarMatches([]); // Clear previous analysis
    }
  };

  const handleFetchAnalysis = async () => {
    if (!selectedMatch) return;
    setLoadingAnalysis(true);
    try {
      const token = localStorage.getItem("token");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`http://127.0.0.1:8000/api/v1/football/analysis/similar/${selectedMatch.external_id}?limit=${limit}`, {
        headers,
      });

      const data = await res.json();

      if (!res.ok) {
        const errMsg = Array.isArray(data.detail) ? data.detail.map((e: any) => e.msg).join(", ") : data.detail;
        throw new Error((typeof errMsg === "string" ? errMsg : null) || "Analiz yapılamadı.");
      }

      setSimilarMatches(data);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Analiz hatası");
      setSimilarMatches([]);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0a0a0f] text-slate-300 font-sans p-4 md:p-8 w-full max-w-[1600px] mx-auto gap-8">
      
      {/* HEADER SECTION */}
      <div>
        <h1 className="text-2xl md:text-3xl font-black text-white mb-2 tracking-tight">
          Canlı İddaa Oran Benzerlik Analizi
        </h1>
        <p className="text-slate-400 text-xs md:text-sm">
          Sistem, Canlı Yaklaşan maçların canlı oranlarını geçmiş sezonlarla karşılaştırarak, benzer oran profillerinin nasıl sonuçlandığını gösterir. Analiz için tablodan bir maç seçin.
        </p>
      </div>

      {/* TOP SECTION: UPCOMING MATCHES */}
      <section className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <h2 className="text-lg font-bold text-white">Yaklaşan Maçlar ve Güncel Oranlar</h2>
          <div className="w-full md:w-64">
            <Filters onLeagueChange={setSelectedLeague} />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20 bg-[#0a0f18] rounded-xl border border-slate-800">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            <span className="ml-4 text-slate-400 font-medium text-sm">Maçlar yükleniyor...</span>
          </div>
        ) : (
          <UpcomingMatchesTable 
            matches={matches} 
            selectedMatchId={selectedMatch?.external_id || null}
            onSelectMatch={handleSelectMatch}
          />
        )}
      </section>

      {/* MIDDLE & BOTTOM SECTION: ANALYSIS */}
      {selectedMatch && (
        <section className="flex flex-col gap-4 mt-4">
          <h2 className="text-lg font-bold text-white">Geçmiş Sezon Karşılaştırması</h2>
          
          <HistoricalAnalysis 
            match={selectedMatch}
            limit={limit}
            onLimitChange={setLimit}
            userTier={userTier}
            onFetch={handleFetchAnalysis}
            loading={loadingAnalysis}
          />

          {similarMatches.length > 0 && (
            <>
              <SimilarMatchesTable results={similarMatches} />
              
              <div className="mt-8 border-t border-slate-800 pt-6">
                <h3 className="text-lg font-bold text-white mb-4 px-4">İstatistik Özeti</h3>
                <SummaryStats results={similarMatches} />
              </div>
            </>
          )}

        </section>
      )}

    </div>
  );
}