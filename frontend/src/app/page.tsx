"use client";

import { useState, useEffect } from "react";
import { MatchResponse, SimilarMatchResult } from "@/types";
import Filters from "@/components/Filters";
import UpcomingMatchesTable from "@/components/UpcomingMatchesTable";
import HistoricalAnalysis from "@/components/HistoricalAnalysis";
import SimilarMatchesTable from "@/components/SimilarMatchesTable";
import SummaryStats from "@/components/SummaryStats";
import { API_URL } from "@/config/constants";

export default function Home() {
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeague, setSelectedLeague] = useState("");
  
  const [selectedMatch, setSelectedMatch] = useState<MatchResponse | null>(null);
  
  const [limit, setLimit] = useState(10);
  const [similarMatches, setSimilarMatches] = useState<SimilarMatchResult[]>([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [userTier, setUserTier] = useState<string>("standard"); // Default to standard

  // Fetch upcoming matches
  useEffect(() => {
    const fetchMatches = async (isSilent = false) => {
      if (!isSilent) {
        setLoading(true);
        setSelectedMatch(null);
        setSimilarMatches([]);
      }
      
      try {
        const url = selectedLeague
          ? `${API_URL}/api/v1/football/matches/?league=${selectedLeague}`
          : `${API_URL}/api/v1/football/matches/`;

        const response = await fetch(url);
        if (!response.ok) throw new Error("Backend unreachable");

        const json = await response.json();
        const data = json?.data || (Array.isArray(json) ? json : []);
        setMatches(data);
      } catch (error) {
        console.error("Fetch error:", error);
      } finally {
        if (!isSilent) setLoading(false);
      }
    };

    // Initial fetch
    fetchMatches();

    // Setup polling (every 2 minutes) with Visibility API check (Faz 5 Fix)
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchMatches(true);
      }
    }, 120000);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchMatches(true);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [selectedLeague]);

  // Fetch User Tier
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/me`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          setUserTier(data.tier);
          if (data.tier === "elite") setLimit(20);
          if (data.tier === "pro") setLimit(10);
          if (data.tier === "standard") setLimit(3);
        } else {
          setUserTier("standard");
          setLimit(3);
        }
      } catch (err) {
        console.error("User fetch error:", err);
        setUserTier("standard");
        setLimit(3);
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
    setSimilarMatches([]); // Clear previous results to show loading state clearly
    
    try {
      console.log(`Analiz başlatılıyor: ${selectedMatch.external_id} | Limit: ${limit}`);
      const res = await fetch(`${API_URL}/api/v1/football/analysis/similar/${selectedMatch.external_id}?limit=${limit}`, {
        credentials: "include",
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Bilinmeyen bir hata oluştu" }));
        const errMsg = Array.isArray(errorData.detail) ? errorData.detail.map((e: any) => e.msg).join(", ") : errorData.detail;
        throw new Error(errMsg || "Analiz yapılamadı.");
      }

      const data = await res.json();
      console.log("Backend'den gelen veri:", data);
      
      // Backend bazen direkt liste, bazen {data: [...]} şeklinde dönebilir. Her iki durumu da handle edelim.
      const resultList = Array.isArray(data) ? data : (data.results || data.data || []);
      setSimilarMatches(resultList);
      
      if (resultList.length === 0) {
        console.warn("Benzer maç bulunamadı.");
      }
    } catch (err: any) {
      console.error("Analiz Hatası:", err);
      alert(err.message || "Analiz hatası");
      setSimilarMatches([]);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const recommendedMatches = [...matches]
    .sort((a, b) => {
      const maxA = Math.max(a.odds.h2h?.home || 0, a.odds.h2h?.draw || 0, a.odds.h2h?.away || 0);
      const maxB = Math.max(b.odds.h2h?.home || 0, b.odds.h2h?.draw || 0, b.odds.h2h?.away || 0);
      return maxB - maxA;
    })
    .slice(0, 5);

  const stats = similarMatches.reduce((acc, item) => {
    const hg = item.match.metrics.home_goals || 0;
    const ag = item.match.metrics.away_goals || 0;
    if (hg > ag) acc.home++;
    else if (hg < ag) acc.away++;
    else acc.draw++;
    return acc;
  }, { home: 0, draw: 0, away: 0 });

  const totalSimilar = similarMatches.length;
  const homePct = totalSimilar > 0 ? Math.round((stats.home / totalSimilar) * 100) : 0;
  const drawPct = totalSimilar > 0 ? Math.round((stats.draw / totalSimilar) * 100) : 0;
  const awayPct = totalSimilar > 0 ? Math.round((stats.away / totalSimilar) * 100) : 0;

  return (
    <div className="flex flex-col gap-8">
      
      {/* TOP ROW: RECOMMENDED MATCHES */}
      <div className="grid grid-cols-1 gap-6">
        <div className="glass rounded-[2rem] p-8 card-shadow emerald-glow relative overflow-hidden">
          <div className="flex flex-col gap-6 relative z-10">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Günün Önerilen Maçları (En Yüksek Oranlar)</span>
              <div className="flex gap-2">
                <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-black uppercase">Top 5 Maç</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {recommendedMatches.length > 0 ? recommendedMatches.map((m) => (
                <div key={m.external_id} onClick={() => handleSelectMatch(m)} className="bg-white/5 border border-white/5 hover:border-primary/30 p-4 rounded-2xl transition-all cursor-pointer group">
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase truncate">{m.league_title}</span>
                    <span className="text-sm font-black text-white truncate">{m.home_team}</span>
                    <span className="text-sm font-black text-white truncate">{m.away_team}</span>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-[10px] font-black text-primary">En Yüksek Oran: {Math.max(m.odds.h2h?.home || 0, m.odds.h2h?.draw || 0, m.odds.h2h?.away || 0).toFixed(2)}</span>
                  </div>
                </div>
              )) : (
                <div className="col-span-5 text-center py-8 text-slate-600 text-xs font-bold uppercase tracking-widest">Maç bulunamadı</div>
              )}
            </div>
          </div>
          {/* Decorative Background */}
          <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-primary/10 blur-[100px] rounded-full"></div>
        </div>
      </div>

      {/* MAIN CONTENT GRID */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        
        {/* LEFT: MATCHES TABLE */}
        <div className="xl:col-span-3 flex flex-col gap-6">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              Yaklaşan Maçlar
            </h2>
            <div className="flex items-center gap-4">
              <div className="w-48">
                <Filters onLeagueChange={setSelectedLeague} />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="glass rounded-[2rem] p-20 flex flex-col items-center justify-center gap-4">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-primary"></div>
              <span className="text-slate-500 font-bold text-xs uppercase tracking-widest">Maçlar Yükleniyor...</span>
            </div>
          ) : (
            <div className="glass rounded-[2rem] overflow-hidden card-shadow">
              <UpcomingMatchesTable 
                matches={matches} 
                selectedMatchId={selectedMatch?.external_id || null}
                onSelectMatch={handleSelectMatch}
              />
            </div>
          )}
        </div>

        {/* RIGHT: REPARTITION / STATS AREA */}
        <div className="xl:col-span-1 flex flex-col gap-6">
           <h2 className="text-lg font-bold text-white px-2">Dağılım</h2>
           <div className="glass rounded-[2rem] p-8 card-shadow flex-1 flex flex-col items-center justify-center min-h-[400px]">
              {similarMatches.length > 0 ? (
                <div className="w-full flex flex-col gap-8">
                   <div className="relative w-48 h-48 mx-auto">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                        {/* Background */}
                        <circle cx="50" cy="50" r="40" fill="transparent" stroke="currentColor" strokeWidth="10" className="text-white/5" />
                        {/* Home Win Segment */}
                        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#10b981" strokeWidth="10" strokeDasharray={`${homePct * 2.51} 251`} strokeLinecap="round" />
                        {/* Draw Segment (approximate positioning) */}
                        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#eab308" strokeWidth="10" strokeDasharray={`${drawPct * 2.51} 251`} strokeDashoffset={`${-homePct * 2.51}`} strokeLinecap="round" />
                        {/* Away Win Segment */}
                        <circle cx="50" cy="50" r="40" fill="transparent" stroke="#ef4444" strokeWidth="10" strokeDasharray={`${awayPct * 2.51} 251`} strokeDashoffset={`${-(homePct + drawPct) * 2.51}`} strokeLinecap="round" />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                         <span className="text-3xl font-black text-white">%{Math.max(homePct, drawPct, awayPct)}</span>
                         <span className="text-[10px] font-bold text-slate-500 uppercase">
                           {homePct >= drawPct && homePct >= awayPct ? "MS 1" : drawPct >= awayPct ? "MS 0" : "MS 2"}
                         </span>
                      </div>
                   </div>
                   <div className="space-y-3 mt-4 w-full">
                      <div className="flex items-center justify-between text-xs font-bold">
                         <div className="flex items-center gap-2 text-slate-400">
                            <span className="w-2 h-2 rounded-full bg-[#10b981]"></span> Ev Sahibi (MS 1)
                         </div>
                         <span className="text-white">{stats.home} Maç (%{homePct})</span>
                      </div>
                      <div className="flex items-center justify-between text-xs font-bold">
                         <div className="flex items-center gap-2 text-slate-400">
                            <span className="w-2 h-2 rounded-full bg-[#eab308]"></span> Beraberlik (MS 0)
                         </div>
                         <span className="text-white">{stats.draw} Maç (%{drawPct})</span>
                      </div>
                      <div className="flex items-center justify-between text-xs font-bold">
                         <div className="flex items-center gap-2 text-slate-400">
                            <span className="w-2 h-2 rounded-full bg-[#ef4444]"></span> Deplasman (MS 2)
                         </div>
                         <span className="text-white">{stats.away} Maç (%{awayPct})</span>
                      </div>
                   </div>
                </div>
              ) : (
                <div className="text-center opacity-20">
                   <svg className="mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                   <p className="text-sm font-bold uppercase tracking-widest">Analiz Bekleniyor</p>
                </div>
              )}
           </div>
        </div>
      </div>

      {/* LOWER SECTION: HISTORICAL ANALYSIS */}
      {selectedMatch && (
        <section className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between px-2">
             <h2 className="text-lg font-bold text-white">Detaylı Benzerlik Analizi</h2>
             <span className="text-xs font-bold text-primary/50 uppercase tracking-widest">Seçili Maç: {selectedMatch.home_team} vs {selectedMatch.away_team}</span>
          </div>
          
          <div className="glass rounded-[2rem] p-8 card-shadow">
            <HistoricalAnalysis 
              match={selectedMatch}
              limit={limit}
              onLimitChange={setLimit}
              userTier={userTier}
              onFetch={handleFetchAnalysis}
              loading={loadingAnalysis}
            />
          </div>

          {similarMatches.length > 0 ? (
            <div className="grid grid-cols-1 gap-8 mt-4">
              <div className="glass rounded-[2rem] overflow-hidden card-shadow">
                <SimilarMatchesTable results={similarMatches} />
              </div>
              
              <div className="glass rounded-[2rem] p-8 card-shadow">
                <h3 className="text-lg font-bold text-white mb-6">İstatistik Özeti</h3>
                <SummaryStats results={similarMatches} />
              </div>
            </div>
          ) : !loadingAnalysis && (
            <div className="mt-8 glass rounded-[2rem] p-12 flex flex-col items-center justify-center gap-4 card-shadow border border-white/5 opacity-60">
               <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
               </div>
               <p className="text-slate-500 text-xs font-black uppercase tracking-widest text-center">Veritabanında benzer oranlara sahip maç bulunamadı.</p>
               <p className="text-slate-700 text-[10px] font-bold uppercase tracking-tight text-center max-w-[250px]">Lütfen farklı bir maç seçin veya benzerlik limitini değiştirerek tekrar deneyin.</p>
            </div>
          )}
        </section>
      )}

    </div>
  );
}