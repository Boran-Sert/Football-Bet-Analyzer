import { MatchResponse } from "@/types";

interface HistoricalAnalysisProps {
  match: MatchResponse;
  limit: number;
  onLimitChange: (limit: number) => void;
  userTier: string;
  onFetch: () => void;
  loading: boolean;
}

export default function HistoricalAnalysis({ 
  match, 
  limit, 
  onLimitChange, 
  userTier, 
  onFetch,
  loading
}: HistoricalAnalysisProps) {
  
  const h2h = match.odds.h2h;
  const totals = match.odds.totals;
  
  const maxLimit = userTier === "elite" ? 20 : 10;
  const isPro = userTier !== "free";

  // Tarih formati sadece YYYY-MM-DD
  const dateStr = match.commence_time.split("T")[0];

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Baslik */}
      <div className="w-full bg-[#1e293b] px-4 py-3 rounded-lg border border-slate-700">
        <h2 className="text-blue-400 font-bold text-sm tracking-wide">
          {match.home_team} vs {match.away_team} <span className="text-slate-400">({dateStr})</span>
        </h2>
      </div>

      {/* Buyuk Oranlar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-2 mb-2">
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 1</span>
          <span className="text-3xl font-black text-slate-100">{h2h?.home ? h2h.home.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 0</span>
          <span className="text-3xl font-black text-slate-100">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 2</span>
          <span className="text-3xl font-black text-slate-100">{h2h?.away ? h2h.away.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">2.5 Alt</span>
          <span className="text-3xl font-black text-slate-100">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">2.5 Üst</span>
          <span className="text-3xl font-black text-slate-100">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</span>
        </div>
      </div>

      <div className="w-full h-px bg-slate-800 my-2"></div>

      {/* Kontroller */}
      <div className="flex flex-col md:flex-row gap-6 items-start md:items-center">
        <div className="flex flex-col flex-1 max-w-sm">
          <div className="flex justify-between items-center mb-2">
            <label className="text-xs font-bold text-slate-400">Benzer maç sayısı</label>
            <span className="text-xs font-black text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">{limit}</span>
          </div>
          
          {isPro ? (
            <input
              type="range"
              min="1"
              max={maxLimit}
              step="1"
              value={limit}
              onChange={(e) => onLimitChange(Number(e.target.value))}
              className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
          ) : (
            <div className="flex items-center gap-3">
              <select
                value={limit}
                onChange={(e) => onLimitChange(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 text-slate-200 text-xs p-1.5 rounded outline-none w-full"
              >
                <option value={3}>3 Maç</option>
              </select>
              <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-1 rounded font-black whitespace-nowrap">
                PRO'ya Geç
              </span>
            </div>
          )}
        </div>

        <button
          onClick={onFetch}
          disabled={loading}
          className="px-6 py-2 border border-slate-700 rounded-lg bg-[#0a0f18] hover:bg-slate-800 text-slate-300 font-bold text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-500 border-t-slate-200 rounded-full animate-spin"></div>
              Hesaplanıyor...
            </>
          ) : (
            "Benzerleri Bul"
          )}
        </button>
      </div>
      
    </div>
  );
}
