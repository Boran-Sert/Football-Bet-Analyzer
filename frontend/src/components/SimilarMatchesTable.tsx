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
    <div className="w-full mt-4">
      <div className="w-full bg-[#166534] px-4 py-2 text-xs font-bold text-green-100 rounded-t-lg border-b-0 border border-slate-700">
        En yakın {results.length} benzer iş eşleşmesi (Detaylar için maça tıklayın)
      </div>
      <div className="w-full overflow-x-auto border border-slate-800 bg-[#0a0f18] rounded-b-lg">
        <table className="w-full text-left text-[10px] md:text-xs whitespace-nowrap">
          <thead className="bg-[#111827] text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-3 py-2 font-medium">Tarih</th>
              <th className="px-3 py-2 font-medium">Ev Sahibi</th>
              <th className="px-3 py-2 font-medium">Deplasman</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Gol</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Gol</th>
              <th className="px-3 py-2 font-medium text-center">İY Ev</th>
              <th className="px-3 py-2 font-medium text-center">İY Dep</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Kırmızı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Kırmızı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Ev Sahibi Korner</th>
              <th className="px-3 py-2 font-medium text-center">Deplasman Korner</th>
              <th className="px-3 py-2 font-medium text-right">MS 1</th>
              <th className="px-3 py-2 font-medium text-right">MS 0</th>
              <th className="px-3 py-2 font-medium text-right">MS 2</th>
              <th className="px-3 py-2 font-medium text-right">2.5 Alt</th>
              <th className="px-3 py-2 font-medium text-right">2.5 Üst</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Korner</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Sarı Kart</th>
              <th className="px-3 py-2 font-medium text-center">Toplam Kırmızı Kart</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
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

              // Cell Backgrounds
              const homeBg = homeWon ? 'bg-green-900/40 text-green-300' : (awayWon ? 'bg-red-900/40 text-red-300' : 'bg-yellow-900/40 text-yellow-300');
              const awayBg = awayWon ? 'bg-green-900/40 text-green-300' : (homeWon ? 'bg-red-900/40 text-red-300' : 'bg-yellow-900/40 text-yellow-300');

              const dateStr = match.commence_time.split("T")[0];

              return (
                <Fragment key={match.external_id}>
                  <tr 
                    onClick={() => toggleExpand(match.external_id)}
                    className={`cursor-pointer transition-colors ${isExpanded ? 'bg-blue-900/10' : 'hover:bg-slate-800/30'}`}
                  >
                    <td className="px-3 py-2 text-slate-400">{dateStr}</td>
                    <td className={`px-3 py-2 font-bold ${homeBg}`}>{match.home_team}</td>
                    <td className={`px-3 py-2 font-bold ${awayBg}`}>{match.away_team}</td>
                    
                    <td className="px-3 py-2 text-center text-slate-300">{hg}</td>
                    <td className="px-3 py-2 text-center text-slate-300">{ag}</td>
                    
                    <td className="px-3 py-2 text-center text-slate-500 italic">{m.home_ht_goals ?? '-'}</td>
                    <td className="px-3 py-2 text-center text-slate-500 italic">{m.away_ht_goals ?? '-'}</td>
                    
                    <td className="px-3 py-2 text-center text-slate-400">{m.home_yellow ?? '-'}</td>
                    <td className="px-3 py-2 text-center text-slate-400">{m.away_yellow ?? '-'}</td>
                    
                    <td className="px-3 py-2 text-center text-slate-400">{m.home_red ?? '-'}</td>
                    <td className="px-3 py-2 text-center text-slate-400">{m.away_red ?? '-'}</td>
                    
                    <td className="px-3 py-2 text-center text-slate-400">{m.home_corners ?? '-'}</td>
                    <td className="px-3 py-2 text-center text-slate-400">{m.away_corners ?? '-'}</td>
                    
                    <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.home ? h2h.home.toFixed(2) : '-'}</td>
                    <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.draw ? h2h.draw.toFixed(2) : '-'}</td>
                    <td className="px-3 py-2 text-right font-medium text-slate-300">{h2h?.away ? h2h.away.toFixed(2) : '-'}</td>
                    
                    <td className="px-3 py-2 text-right font-medium text-slate-300">{totals?.under_2_5 ? totals.under_2_5.toFixed(2) : '-'}</td>
                    <td className="px-3 py-2 text-right font-medium text-slate-300">{totals?.over_2_5 ? totals.over_2_5.toFixed(2) : '-'}</td>
                    
                    <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_corners ?? '-'}</td>
                    <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_yellow ?? '-'}</td>
                    <td className="px-3 py-2 text-center font-bold text-slate-300">{m.total_red ?? '-'}</td>
                  </tr>
                  {isExpanded && (
                    <tr className="bg-slate-900/50 border-x border-slate-800">
                      <td colSpan={21} className="px-6 py-4">
                        <div className="flex flex-wrap gap-8 text-[11px] md:text-xs">
                          {/* Sut İstatistikleri */}
                          <div className="flex flex-col gap-2">
                            <span className="text-blue-400 font-bold uppercase tracking-wider">Şutlar</span>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                              <span className="text-slate-500">Toplam Şut (Ev/Dep):</span>
                              <span className="text-slate-200 font-bold">{m.home_shots ?? '-'} / {m.away_shots ?? '-'}</span>
                              <span className="text-slate-500">İsabetli Şut (Ev/Dep):</span>
                              <span className="text-slate-200 font-bold">{m.home_shots_on_target ?? '-'} / {m.away_shots_on_target ?? '-'}</span>
                              <span className="text-slate-500 font-medium">Toplam Şut:</span>
                              <span className="text-blue-300 font-black">{m.total_shots ?? '-'}</span>
                            </div>
                          </div>

                          <div className="w-px h-12 bg-slate-800 self-center hidden md:block"></div>

                          {/* Faul İstatistikleri */}
                          <div className="flex flex-col gap-2">
                            <span className="text-yellow-500 font-bold uppercase tracking-wider">Fauller</span>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                              <span className="text-slate-500">Faul (Ev/Dep):</span>
                              <span className="text-slate-200 font-bold">{m.home_fouls ?? '-'} / {m.away_fouls ?? '-'}</span>
                              <span className="text-slate-500 font-medium">Toplam Faul:</span>
                              <span className="text-yellow-300 font-black">{m.total_fouls ?? '-'}</span>
                            </div>
                          </div>

                          <div className="w-px h-12 bg-slate-800 self-center hidden md:block"></div>

                          {/* Oklid Mesafesi */}
                          <div className="flex flex-col gap-2">
                            <span className="text-green-500 font-bold uppercase tracking-wider">Analiz Skoru</span>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                              <span className="text-slate-500">Benzerlik Oranı:</span>
                              <span className="text-green-400 font-bold">%{item.similarity_percentage}</span>
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
