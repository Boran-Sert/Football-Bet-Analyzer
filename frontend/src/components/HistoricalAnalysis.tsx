import { MatchResponse } from "@/types";
import { useRouter } from "next/navigation";

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
  const router = useRouter();
  
  const h2h = match.odds.h2h;
  const totals = match.odds.totals;
  
  const maxLimit = userTier === "elite" ? 20 : 10;
  const isPro = userTier !== "standard";

  return (
    <div className="w-full flex flex-col gap-8">
      {/* Odds Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 1</span>
          <span className="text-3xl font-black text-white">{h2h?.home ? h2h.home.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 0</span>
          <span className="text-3xl font-black text-white">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">MS 2</span>
          <span className="text-3xl font-black text-white">{h2h?.away ? h2h.away.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">2.5 Alt</span>
          <span className="text-3xl font-black text-slate-400">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">2.5 Üst</span>
          <span className="text-3xl font-black text-slate-400">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</span>
        </div>
      </div>

      {/* Controls Row */}
      <div className="flex flex-col md:flex-row gap-8 items-end">
        <div className="flex-1 space-y-4">
          <div className="flex justify-between items-center">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Benzer maç sayısı</label>
            <span className="text-xs font-black text-primary">{limit} Maç</span>
          </div>
          
          {isPro ? (
            <input
              type="range"
              min="1"
              max={maxLimit}
              step="1"
              value={limit}
              onChange={(e) => onLimitChange(Number(e.target.value))}
              className="w-full h-1.5 bg-white/5 rounded-full appearance-none cursor-pointer accent-primary"
            />
          ) : (
            <div className="flex items-center gap-3">
              <select
                value={limit}
                onChange={(e) => onLimitChange(Number(e.target.value))}
                className="bg-white/5 border border-white/5 text-white text-xs p-2 rounded-xl outline-none w-full"
              >
                <option value={3} className="bg-[#050505]">3 Maç</option>
              </select>
            </div>
          )}
        </div>

        <button
          onClick={userTier ? onFetch : () => router.push("/login")}
          disabled={loading}
          className="px-8 py-3 bg-primary text-black font-black text-xs uppercase tracking-widest rounded-xl hover:scale-105 transition-all disabled:opacity-30 emerald-glow"
        >
          {loading ? "Hesaplanıyor..." : userTier ? "Benzerleri Bul →" : "Giriş Yaparak Kullan →"}
        </button>
      </div>
    </div>
  );
}
