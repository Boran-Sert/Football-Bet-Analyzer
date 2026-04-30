import { useState, Fragment } from "react";
import { SimilarMatchResult } from "@/types";

interface SimilarMatchesTableProps {
  results: SimilarMatchResult[];
}

export default function SimilarMatchesTable({ results }: SimilarMatchesTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!results || results.length === 0) {
    return null;
  }

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="w-full">
      <div className="w-full bg-white/[0.03] px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <h3 className="text-xs font-black text-white uppercase tracking-widest">En Yakın {results.length} Eşleşme</h3>
        <span className="text-[10px] font-bold text-slate-500 uppercase">Detaylar için tıkla</span>
      </div>
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left text-[10px] md:text-xs whitespace-nowrap">
          <thead className="bg-white/[0.02] text-slate-500 border-b border-white/5">
            <tr>
              <th className="px-4 py-3 font-black uppercase tracking-widest">Tarih</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest">Ev Sahibi</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest">Deplasman</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-center">G</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-center">İY</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-center">Sarı</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-center">Kırmızı</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-center">Korner</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-right">MS 1</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-right">MS 0</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-right">MS 2</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-right">2.5 A/Ü</th>
              <th className="px-4 py-3 font-black uppercase tracking-widest text-right">Benzerlik</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {results.map((item) => {
              const match = item.match;
              const h2h = match.odds.h2h;
              const totals = match.odds.totals;
              const m = match.metrics;
              
              const hg = m.home_goals ?? 0;
              const ag = m.away_goals ?? 0;
              
              const homeWon = hg > ag;
              const awayWon = ag > hg;
              const draw = hg === ag;

              const isExpanded = expandedId === match.external_id;

              // Cell Styles
              const homeColor = homeWon ? 'text-primary' : (awayWon ? 'text-red-400' : 'text-yellow-400');
              const awayColor = awayWon ? 'text-primary' : (homeWon ? 'text-red-400' : 'text-yellow-400');

              const dateStr = match.commence_time.split("T")[0];

              return (
                <Fragment key={match.external_id}>
                  <tr 
                    onClick={() => toggleExpand(match.external_id)}
                    className={`cursor-pointer transition-all hover:bg-white/[0.04] ${isExpanded ? 'bg-white/[0.06]' : ''}`}
                  >
                    <td className="px-4 py-3 text-slate-500 font-medium">{dateStr}</td>
                    <td className={`px-4 py-3 font-bold ${homeColor}`}>{match.home_team}</td>
                    <td className={`px-4 py-3 font-bold ${awayColor}`}>{match.away_team}</td>
                    
                    <td className="px-4 py-3 text-center font-black text-white">{hg}-{ag}</td>
                    <td className="px-4 py-3 text-center text-slate-500 italic">{m.home_ht_goals}-{m.away_ht_goals}</td>
                    
                    <td className="px-4 py-3 text-center text-yellow-500/80 font-bold">{m.total_yellow ?? '-'}</td>
                    <td className="px-4 py-3 text-center text-red-500/80 font-bold">{m.total_red ?? '-'}</td>
                    <td className="px-4 py-3 text-center text-cyan-500/80 font-bold">{m.total_corners ?? '-'}</td>
                    
                    <td className="px-4 py-3 text-right font-black text-white">{h2h?.home ? h2h.home.toFixed(2) : '-'}</td>
                    <td className="px-4 py-3 text-right font-black text-white">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</td>
                    <td className="px-4 py-3 text-right font-black text-white">{h2h?.away ? h2h.away.toFixed(2) : '-'}</td>
                    
                    <td className="px-4 py-3 text-right font-black text-slate-500">
                      {totals?.under_2_5 != null ? totals.under_2_5.toFixed(2) : '-'} / {totals?.over_2_5 != null ? totals.over_2_5.toFixed(2) : '-'}
                    </td>
                    
                    <td className="px-4 py-3 text-right">
                       <span className="px-2 py-1 rounded bg-primary/10 text-primary font-black text-[10px]">%{item.similarity_percentage}</span>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr className="bg-white/[0.01]">
                      <td colSpan={13} className="px-8 py-6">
                        <div className="flex flex-wrap gap-12">
                          <div className="flex flex-col gap-2">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Şut İstatistikleri</span>
                            <div className="flex items-center gap-4">
                               <div className="flex flex-col">
                                  <span className="text-xl font-black text-white">{m.home_shots ?? '-'}/{m.away_shots ?? '-'}</span>
                                  <span className="text-[9px] font-bold text-slate-600 uppercase">Ev/Dep Şut</span>
                               </div>
                               <div className="w-px h-8 bg-white/5"></div>
                               <div className="flex flex-col">
                                  <span className="text-xl font-black text-white">{m.home_shots_on_target ?? '-'}/{m.away_shots_on_target ?? '-'}</span>
                                  <span className="text-[9px] font-bold text-slate-600 uppercase">İsabetli</span>
                               </div>
                            </div>
                          </div>

                          <div className="flex flex-col gap-2">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Disiplin</span>
                            <div className="flex items-center gap-4">
                               <div className="flex flex-col">
                                  <span className="text-xl font-black text-yellow-500">{m.home_yellow ?? '-'}/{m.away_yellow ?? '-'}</span>
                                  <span className="text-[9px] font-bold text-slate-600 uppercase">Sarı Kart</span>
                               </div>
                               <div className="w-px h-8 bg-white/5"></div>
                               <div className="flex flex-col">
                                  <span className="text-xl font-black text-red-500">{m.home_red ?? '-'}/{m.away_red ?? '-'}</span>
                                  <span className="text-[9px] font-bold text-slate-600 uppercase">Kırmızı</span>
                               </div>
                            </div>
                          </div>

                          <div className="flex flex-col gap-2">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Kornerler</span>
                            <div className="flex flex-col">
                               <span className="text-xl font-black text-cyan-500">{m.home_corners ?? '-'}/{m.away_corners ?? '-'}</span>
                               <span className="text-[9px] font-bold text-slate-600 uppercase">Ev/Dep</span>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
